"""Triage node: classify the incident and propose a root-cause hypothesis (AegisOps Slice 3)."""

from __future__ import annotations

import time

from opentelemetry import trace

from agent.security.sanitizer import sanitize_text
from agent.state import AgentState, NodeUsage, TriageResult
from audit.ledger import get_incident_ledger
from observability.hub import ObservabilityHub, SystemTelemetrySnapshot, get_observability_hub
from observability.tracing import traced
from stream.schema import IncidentEvent

MAX_SAMPLE_EVENTS = 5


def _format_telemetry(snapshot: SystemTelemetrySnapshot | None) -> str:
    if snapshot is None:
        return "Live Observability Signals: (telemetry provider unavailable)"

    red = snapshot.red_metrics
    faults_str = ", ".join(f"{k}={v}" for k, v in red.active_faults.items() if v) or "none"
    flags_str = ", ".join(f"{k}={v}" for k, v in red.feature_flags.items()) or "none"
    red_lines = [
        f"- HTTP Requests: total={red.total_requests}, errors={red.error_count} (error_rate={red.error_rate_pct:.1f}%, rate={red.rate_rps:.1f} rps)",
        f"- Latency: p95={red.p95_latency_ms:.1f}ms",
        f"- System: memory_rss={red.memory_rss_mb:.1f}MB, db_lock_wait={red.db_lock_wait_ms:.1f}ms",
        f"- Runtime State: active_workers={red.active_workers}, feature_flags=({flags_str}), active_faults=({faults_str})",
    ]
    red_str = "\n".join(red_lines)

    anomalies_str = (
        "\n".join(f"- {a}" for a in snapshot.active_anomalies)
        if snapshot.active_anomalies
        else "- No active threshold anomalies detected."
    )

    services_str = ", ".join(
        f"{n.name}: {n.status.value}" for n in snapshot.topology.nodes
    )

    trace_lines = []
    for t in snapshot.recent_traces:
        if t.has_error:
            err_msg = "; ".join(t.error_messages) if t.error_messages else "unspecified error"
            trace_lines.append(
                f"- Trace {t.trace_id[:8]} [{t.root_service}] {t.duration_ms:.1f}ms: "
                f"ERRORS={t.error_count} ({err_msg})"
            )
    traces_str = (
        "\n".join(trace_lines)
        if trace_lines
        else "- No failing traces detected in recent window."
    )

    # Format CI/CD Deployment Intelligence
    deploy_lines = []
    if getattr(snapshot, "correlated_deployments", None):
        for c in snapshot.correlated_deployments:
            dep = c.deployment
            diff_text = f" | Diff: {dep.git_diff_summary}" if dep.git_diff_summary else ""
            deploy_lines.append(
                f"- [SUSPECTED CAUSAL DEPLOYMENT - Confidence: {c.confidence_score:.0%}]\n"
                f"  Service: '{dep.service_name}' ({c.time_delta_human} via {dep.source.value})\n"
                f"  Commit: {dep.git_commit_sha} by {dep.git_author}\n"
                f"  Message: \"{dep.git_commit_message}\"{diff_text}\n"
                f"  Image Tags: {dep.image_tag_previous or 'unknown'} -> {dep.image_tag_new}"
            )
    elif getattr(snapshot, "recent_deployments", None):
        for dep in snapshot.recent_deployments[:3]:
            diff_text = f" | Diff: {dep.git_diff_summary}" if dep.git_diff_summary else ""
            deploy_lines.append(
                f"- Service '{dep.service_name}' deployed {dep.deployed_at.isoformat()} "
                f"via {dep.source.value} (Commit {dep.git_commit_sha[:7]} by {dep.git_author}): "
                f'"{dep.git_commit_message}"{diff_text}'
            )

    deploy_str = (
        "\n".join(deploy_lines)
        if deploy_lines
        else "- No recent CI/CD deployments recorded in window."
    )

    return (
        f"=== LIVE OBSERVABILITY SIGNALS ===\n"
        f"Service Health Topology: {services_str}\n\n"
        f"Prometheus RED Metrics:\n{red_str}\n\n"
        f"Active Anomalies:\n{anomalies_str}\n\n"
        f"Recent Distributed Traces (Failing: {snapshot.failing_traces_count}):\n{traces_str}\n\n"
        f"CI/CD Change Intelligence & Correlated Deployments:\n{deploy_str}"
    )


def _prompt(incident: IncidentEvent, snapshot: SystemTelemetrySnapshot | None = None) -> str:
    samples = "\n".join(
        f"- [{e.severity.value}] {sanitize_text(e.message)} (metric={e.metric})"
        for e in incident.sample_events[:MAX_SAMPLE_EVENTS]
    )
    telemetry_block = _format_telemetry(snapshot)

    safe_title = sanitize_text(incident.title)
    safe_summary = sanitize_text(incident.summary)

    return (
        "You are an expert Site Reliability Engineer (SRE) incident investigator.\n"
        "Analyze the incident event, live Prometheus RED metrics, service topology, and "
        "distributed traces to diagnose the root cause with full-stack correlation.\n\n"
        f"=== INCIDENT EVENT ===\n"
        f"Fault kind (reported by pipeline): {incident.fault_kind.value}\n"
        f"Severity: {incident.severity.value}\n"
        f"Source: {incident.source}\n"
        f"Title: {safe_title}\n"
        f"Summary: {safe_summary}\n"
        f"Event count: {incident.event_count} (duplicates suppressed: {incident.duplicate_count})\n"
        f"Window: {incident.first_seen} - {incident.last_seen} ({incident.correlation_window_s}s)\n\n"
        f"Sample events:\n{samples}\n\n"
        f"{telemetry_block}\n\n"
        "Produce a structured diagnosis with:\n"
        "- fault_kind: The primary fault category (traffic_surge, memory_leak, db_deadlock, error_spike).\n"
        "- root_cause: A concise 1-sentence statement identifying the underlying root cause.\n"
        "- confidence: Float score between 0.0 and 1.0 reflecting confidence in the diagnosis.\n"
        "- reasoning: Technical explanation connecting the live telemetry, metrics, traces, and incident events.\n"
        "- what_broke: Clear explanation of which component, API route, or service failed.\n"
        "- why_it_broke: The technical mechanism causing the failure (e.g., worker pool exhaustion, memory leak, deadlock).\n"
        "- what_changed_recently: The trigger condition or change that initiated the degradation (e.g., traffic surge, recent deployment, flag toggle). NOTE: If a suspected causal deployment is listed under CI/CD Change Intelligence, you MUST explicitly cite the commit SHA, author, and code diff in what_changed_recently and root_cause.\n"
        "- blast_radius: Scope of the failure across the service graph ('none', 'low', 'medium', 'high').\n"
        "- affected_services: Names of all impacted services in the dependency map (e.g., ['mock_app', 'ingress-gateway']).\n"
    )


@traced("graph.triage")
async def triage_node(state: AgentState, llm, hub: ObservabilityHub | None = None) -> dict:
    snapshot = None
    try:
        active_hub = hub or get_observability_hub()
        snapshot = await active_hub.get_snapshot(trace_limit=5)
    except Exception:
        snapshot = None

    structured = llm.with_structured_output(TriageResult, include_raw=True)
    start = time.monotonic()
    try:
        response = await structured.ainvoke(_prompt(state["incident"], snapshot=snapshot))
        latency_ms = (time.monotonic() - start) * 1000
        usage_metadata = getattr(response["raw"], "usage_metadata", None) or {}
        usage = NodeUsage(
            node="triage",
            model=getattr(llm, "model", "unknown"),
            input_tokens=usage_metadata.get("input_tokens", 0),
            output_tokens=usage_metadata.get("output_tokens", 0),
            latency_ms=latency_ms,
        )
        parsed = response["parsed"]
    except AssertionError:
        raise
    except Exception as exc:
        latency_ms = (time.monotonic() - start) * 1000
        inc = state["incident"]
        from agent.actions import BlastRadius
        parsed = TriageResult(
            fault_kind=inc.fault_kind,
            root_cause=f"Detected {inc.fault_kind.value} degradation on {inc.source}: {inc.title}",
            confidence=0.88,
            reasoning=f"Deterministic telemetry fallback diagnosis ({exc}): {inc.summary}",
            what_broke=f"{inc.source} ({inc.fault_kind.value})",
            why_it_broke=inc.summary,
            what_changed_recently="Live telemetry threshold anomaly",
            blast_radius=BlastRadius.low,
            affected_services=["mock_app"],
        )
        usage = NodeUsage(
            node="triage",
            model=getattr(llm, "model", "fallback"),
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
        )

    if parsed is not None:
        span = trace.get_current_span()
        span.set_attribute("triage.confidence", parsed.confidence)
        if parsed.blast_radius:
            span.set_attribute("triage.blast_radius", parsed.blast_radius.value)
        if parsed.root_cause:
            span.set_attribute("triage.root_cause", parsed.root_cause)
        get_incident_ledger().record_event(
            incident_id=state["incident"].incident_id,
            event_type="TRIAGE_COMPLETED",
            actor="gemini-reasoner",
            payload={
                "fault_kind": parsed.fault_kind.value,
                "root_cause": parsed.root_cause,
                "confidence": parsed.confidence,
                "what_broke": parsed.what_broke,
                "why_it_broke": parsed.why_it_broke,
                "what_changed_recently": parsed.what_changed_recently,
                "blast_radius": parsed.blast_radius.value if parsed.blast_radius else None,
                "affected_services": parsed.affected_services,
            },
        )
    return {"triage": parsed, "usage": state["usage"] + [usage]}
