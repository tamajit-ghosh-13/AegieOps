"""Demo entrypoint: run the full agent graph with HITL web UI."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import structlog
import uvicorn
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from redis.asyncio import Redis

from agent.graph import build_graph
from agent.llm import get_propose_llm, get_triage_llm
from agent.report_sink import PostgresReportSink, PrintSink
from agent.state import RemediationPlan, initial_state
from apply.appliers import LiveApplier
from hitl.gate import ApprovalGate
from hitl.registry import DurableFixRegistry
from hitl.web import create_hitl_app
from observability.adaptive_sentinel import AdaptiveTelemetrySentinel
from observability.alerts_gateway import get_alert_gateway
from observability.langsmith import run_config, setup_langsmith
from observability.logging import setup_logging
from observability.sentinel import TelemetrySentinel
from observability.tracing import current_trace_id, extract_trace_context, get_tracer, setup_tracing, shutdown_tracing
from policy.engine import PolicyEngine
from sandbox.executor import SandboxExecutor
from stream.consumer import INCIDENTS_STREAM
from stream.schema import IncidentEvent

# Load .env before the os.environ reads below, so a host-run agent picks up the
# same config (ANTHROPIC_API_KEY, POSTGRES_*, model tiers) that docker compose
# interpolates from .env. No-op if the file is absent.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
REPO_ROOT = Path(__file__).resolve().parents[1]
HITL_PORT = int(os.environ.get("HITL_PORT", "8001"))


async def _read_latest_incidents(redis: Redis, count: int) -> list[tuple[IncidentEvent, dict]]:
    entries = await redis.xrevrange(INCIDENTS_STREAM, count=count)
    out: list[tuple[IncidentEvent, dict]] = []
    for _, fields in reversed(entries):  # process oldest to newest within the batch
        incident = IncidentEvent.model_validate_json(fields["incident"])
        carrier = {k: fields[k] for k in ("traceparent", "tracestate") if k in fields}
        out.append((incident, carrier))
    return out


def promoted_incident(incident: IncidentEvent) -> IncidentEvent:
    """Derived identity for a promoted durable-fix run, so its report
    upserts a separate row instead of overwriting the mitigation run's."""
    return incident.model_copy(update={"incident_id": f"{incident.incident_id}#promo"})


async def _process_incident(graph, incident: IncidentEvent, carrier: dict) -> None:
    structlog.contextvars.bind_contextvars(incident_id=incident.incident_id)
    try:
        print(f"\nProcessing: {incident.title} ({incident.incident_id})")
        ctx = extract_trace_context(carrier)
        with get_tracer().start_as_current_span("agent.process", context=ctx) as span:
            span.set_attribute("incident_id", incident.incident_id)
            span.set_attribute("fault_kind", incident.fault_kind.value)
            await graph.ainvoke(
                initial_state(incident),
                config=run_config(incident, current_trace_id()),
            )
    except Exception as exc:
        print(f"[Error] Failed processing incident {incident.incident_id}: {exc}")
    finally:
        structlog.contextvars.clear_contextvars()


async def _process_promotion(graph, entry: dict) -> None:
    incident = entry["incident"]
    promoted = promoted_incident(incident)
    structlog.contextvars.bind_contextvars(incident_id=promoted.incident_id)
    try:
        print(f"\nPromoted durable fix for {incident.incident_id}")
        with get_tracer().start_as_current_span("agent.process") as span:
            span.set_attribute("incident_id", promoted.incident_id)
            span.set_attribute("fault_kind", promoted.fault_kind.value)
            await graph.ainvoke(
                initial_state(
                    promoted,
                    plan=RemediationPlan(mitigation=entry["fix"]),
                    triage=entry["triage"],
                ),
                config=run_config(promoted, current_trace_id()),
            )
    except Exception as exc:
        print(f"[Error] Failed processing promotion {promoted.incident_id}: {exc}")
    finally:
        structlog.contextvars.clear_contextvars()


async def main(count: int = 1, follow: bool = False) -> None:
    setup_logging()
    setup_tracing("aegis-agent")
    if setup_langsmith():
        print("LangSmith tracing: enabled")

    redis = Redis.from_url(REDIS_URL, decode_responses=True)

    # Build dependencies
    import docker

    try:
        docker_client = docker.from_env()
    except Exception as exc:
        print(f"Docker unavailable ({exc}); running with fallback client.")
        docker_client = None

    client = MultiServerMCPClient(
        {
            "retrieval": {
                "command": sys.executable,
                "args": ["-m", "tools.retrieval_server"],
                "transport": "stdio",
                "cwd": str(REPO_ROOT),
                "env": {**os.environ},
            }
        }
    )
    tools = await client.get_tools()
    search_tool = next(t for t in tools if t.name == "search_knowledge")

    from hitl.gate import set_approval_gate
    gate = ApprovalGate()  # HITL_TTL_S env controls the demo TTL
    set_approval_gate(gate)
    registry = DurableFixRegistry()
    executor = SandboxExecutor(docker_client)
    from apply.kubernetes_applier import KubernetesApplier
    from apply.two_phase_verifier import TwoPhaseVerifier
    from policy.circuit_breaker import get_circuit_breaker

    circuit_breaker = get_circuit_breaker()
    policy_engine = PolicyEngine(circuit_breaker=circuit_breaker)
    applier = KubernetesApplier(docker_client=docker_client)
    verifier = TwoPhaseVerifier(
        canary_duration_s=1.5,
        canary_interval_s=0.5,
        soak_duration_s=2.0,
        soak_interval_s=0.5,
    )
    try:
        sink = PostgresReportSink()
    except Exception as exc:
        print(f"Postgres unavailable ({exc}); falling back to stdout reports.")
        sink = PrintSink()

    graph = build_graph(
        get_triage_llm(),
        get_propose_llm(),
        search_tool,
        executor,
        policy_engine,
        gate,
        applier,
        sink,
        registry,
        verifier=verifier,
    )

    # Start HITL web UI in background
    hitl_app = create_hitl_app(gate, registry)
    config = uvicorn.Config(hitl_app, host="0.0.0.0", port=HITL_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    print(f"HITL approval UI running at http://localhost:{HITL_PORT}")

    try:
        if not follow:
            incidents = await _read_latest_incidents(redis, count)
            if not incidents:
                print("No incidents found on aegis:incidents.")
            else:
                for incident, carrier in incidents:
                    await _process_incident(graph, incident, carrier)

            print("Waiting for durable-fix promotions (Ctrl+C to exit)...")
            while True:
                entry = await registry.next_promotion()
                await _process_promotion(graph, entry)
        else:
            # Follow mode: process most recent incident if count > 0, then listen continuously
            if count > 0:
                incidents = await _read_latest_incidents(redis, count)
                for incident, carrier in incidents:
                    await _process_incident(graph, incident, carrier)

            latest = await redis.xrevrange(INCIDENTS_STREAM, count=1)
            last_id = latest[0][0] if latest else "$"

            from observability.adaptive_sentinel import get_adaptive_sentinel
            sentinel = get_adaptive_sentinel()
            alert_gateway = get_alert_gateway()
            print(f"\n[Aegis Live] Multi-Signal Mesh Active: Redis ({INCIDENTS_STREAM}), Adaptive Sentinel (EWMA/Z-Score/IQR) & Webhook Gateway...")
            last_sentinel_check = 0.0
            while True:
                if registry.has_promotions():
                    entry = await registry.next_promotion()
                    await _process_promotion(graph, entry)

                # 1. Check Multi-Source Alert Ingestion Gateway (Alertmanager / PagerDuty webhooks)
                if alert_gateway.has_pending_alerts():
                    gateway_incident = await alert_gateway.next_alert()
                    print(f"\n[Gateway Alert] Ingested alert from {gateway_incident.source}: {gateway_incident.title}")
                    await _process_incident(graph, gateway_incident, carrier={})

                # 2. Check Prometheus Adaptive Telemetry Sentinel every 2 seconds
                now_mono = asyncio.get_running_loop().time()
                if now_mono - last_sentinel_check >= 2.0:
                    last_sentinel_check = now_mono
                    telemetry_incident = await sentinel.check()
                    if telemetry_incident is not None:
                        print(f"\n[Sentinel Alert] Prometheus detected adaptive SLO anomaly: {telemetry_incident.title}")
                        await _process_incident(graph, telemetry_incident, carrier={})

                # 3. Check Redis Event Stream
                streams = None
                try:
                    streams = await redis.xread({INCIDENTS_STREAM: last_id}, count=1, block=500)
                except (TimeoutError, asyncio.TimeoutError, Exception) as exc:
                    if "timeout" in str(exc).lower():
                        streams = None
                    else:
                        print(f"[Warning] Redis stream read error: {exc}")
                        streams = None
                if streams:
                    for _, entries in streams:
                        for entry_id, fields in entries:
                            last_id = entry_id
                            incident = IncidentEvent.model_validate_json(fields["incident"])
                            carrier = {k: fields[k] for k in ("traceparent", "tracestate") if k in fields}
                            await _process_incident(graph, incident, carrier)
                await asyncio.sleep(0.05)
    finally:
        server.should_exit = True
        await server_task
        await redis.aclose()
        shutdown_tracing()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="Number of past incidents to process")
    parser.add_argument("--follow", "-f", action="store_true", help="Continuously listen for live incidents")
    args = parser.parse_args()
    asyncio.run(main(count=args.count, follow=args.follow))
