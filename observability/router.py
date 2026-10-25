"""FastAPI router for real-time observability APIs (AegisOps Slice 2).

Endpoints consumed by SRE operations dashboards and agent reasoning nodes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from observability.hub import SystemTelemetrySnapshot, get_observability_hub
from observability.jaeger import TraceSummary
from observability.postmortem import PostMortem, generate_postmortem
from observability.prometheus import REDMetrics
from observability.topology import TopologySnapshot
from audit.ledger import LedgerEntry, get_incident_ledger

router = APIRouter(prefix="/api/observability", tags=["observability"])


class FaultControlRequest(BaseModel):
    kind: str
    action: str


@router.get("/snapshot", response_model=SystemTelemetrySnapshot)
async def get_snapshot(trace_limit: int = Query(default=5, ge=1, le=50)):
    """Unified system snapshot containing RED metrics, service topology, and Jaeger traces."""
    hub = get_observability_hub()
    return await hub.get_snapshot(trace_limit=trace_limit)


@router.get("/metrics", response_model=REDMetrics)
async def get_metrics():
    """Scraped and aggregated Prometheus RED metrics."""
    hub = get_observability_hub()
    return await hub.scraper.get_red_metrics()


@router.get("/topology", response_model=TopologySnapshot)
async def get_topology():
    """Live service dependency graph and node health statuses."""
    hub = get_observability_hub()
    red = await hub.scraper.get_red_metrics()
    from observability.topology import build_topology
    return build_topology(red)


@router.get("/traces", response_model=list[TraceSummary])
async def get_traces(service: str = "aegis-agent", limit: int = Query(default=5, ge=1, le=50)):
    """Recent distributed traces from Jaeger with error indicators."""
    hub = get_observability_hub()
    return await hub.jaeger.get_recent_traces(service=service, limit=limit)


@router.get("/ledger/verify")
async def verify_entire_ledger_integrity():
    """Verify cryptographic SHA-256 Merkle hash chain across all ledger entries."""
    ledger = get_incident_ledger()
    valid, message, corrupted = ledger.verify_chain_integrity()
    return {
        "integrity_verified": valid,
        "message": message,
        "corrupted_ledger_ids": corrupted,
    }


@router.get("/ledger/verify/{incident_id}")
async def verify_incident_ledger_integrity(incident_id: str):
    """Verify cryptographic SHA-256 Merkle hash chain for a specific incident."""
    ledger = get_incident_ledger()
    valid, message, corrupted = ledger.verify_chain_integrity(incident_id)
    return {
        "incident_id": incident_id,
        "integrity_verified": valid,
        "message": message,
        "corrupted_ledger_ids": corrupted,
    }


@router.get("/ledger", response_model=list[LedgerEntry])
async def get_all_audit_ledger(limit: int = Query(default=50, ge=1, le=200)):
    """Retrieve recent immutable audit ledger entries across all incidents."""
    ledger = get_incident_ledger()
    return ledger.get_all_entries(limit=limit)


@router.get("/ledger/{incident_id}", response_model=list[LedgerEntry])
async def get_incident_audit_ledger(incident_id: str):
    """Retrieve the immutable, append-only audit trail for an incident (AegisOps Slice 4)."""
    ledger = get_incident_ledger()
    return ledger.get_audit_trail(incident_id)


@router.get("/reports")
async def get_incident_reports():
    """Retrieve all past incident reports from Postgres for the operations dashboard."""
    try:
        from dashboard.operations_data import fetch_incident_rows
        rows = fetch_incident_rows()
        return [
            {
                "incident_id": r.incident_id,
                "fault_kind": r.fault_kind,
                "outcome": r.outcome,
                "created_at": r.created_at.isoformat(),
                "report": r.report.model_dump(mode="json"),
            }
            for r in rows
        ]
    except Exception:
        return []


@router.get("/postmortem/{incident_id}", response_model=PostMortem)
async def get_incident_postmortem(incident_id: str):
    """Retrieve auto-generated SRE post-mortem for an incident."""
    pm = generate_postmortem(incident_id)
    if pm is None:
        raise HTTPException(status_code=404, detail="Incident not found or no report filed")
    return pm


@router.post("/controls/fault")
async def control_fault(req: FaultControlRequest):
    """Trigger or clear a fault on mock_app for interactive demonstration."""
    import httpx
    from observability.adaptive_sentinel import get_adaptive_sentinel
    from policy.circuit_breaker import get_circuit_breaker

    # Reset anti-flap circuit breaker and sentinel cooldown on manual Chaos Injection Toolbar
    # actions so interactive demos are never locked out by the 15-minute cooldown window.
    get_circuit_breaker().reset()
    get_adaptive_sentinel().reset_cooldown()

    base_url = "http://localhost:8000"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            if req.kind == "all" and req.action == "clear":
                for k in ["traffic_surge", "memory_leak", "db_deadlock", "error_spike"]:
                    try:
                        await client.post(f"{base_url}/faults/{k}/clear")
                    except Exception:
                        pass
                try:
                    await client.post(f"{base_url}/scale", json={"workers": 2})
                except Exception:
                    pass
                try:
                    await client.post(f"{base_url}/connections/drain")
                except Exception:
                    pass
                return {"status": "all faults cleared, circuit breaker reset, and workers reset to 2"}

            endpoint = f"{base_url}/faults/{req.kind}/{req.action}"
            resp = await client.post(endpoint)
            return resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed communicating with mock_app: {exc}")


# ==============================================================================
# Sprint 1: Multi-Source Alert Ingestion Webhook Endpoints
# ==============================================================================

from observability.alerts_gateway import (
    AlertmanagerWebhookPayload,
    PagerDutyWebhookPayload,
    get_alert_gateway,
)


@router.post("/alerts/webhook/alertmanager")
async def ingest_alertmanager_webhook(payload: AlertmanagerWebhookPayload):
    """Ingest, deduplicate, and normalize Prometheus Alertmanager v4 JSON webhook alerts."""
    import httpx
    from observability.adaptive_sentinel import get_adaptive_sentinel
    from policy.circuit_breaker import get_circuit_breaker

    gateway = get_alert_gateway()

    # Unless the caller explicitly sets label "enforce_cooldown": "true", clear the
    # 60s alert dedup cache and 15m anti-flap circuit breaker so CLI curl injections
    # during live walkthroughs always execute immediately.
    enforce_cooldown = any(
        a.labels.get("enforce_cooldown", "").lower() == "true" for a in payload.alerts
    )
    if not enforce_cooldown:
        gateway._active_alerts.clear()
        get_circuit_breaker().reset()
        get_adaptive_sentinel().reset_cooldown()

    events = gateway.ingest_alertmanager(payload)

    # Also activate the corresponding fault on mock_app (:8000) so the Cockpit UI
    # metrics ribbon and dependency topology visibly degrade and then heal live.
    if events:
        async with httpx.AsyncClient(timeout=1.5) as client:
            for ev in events:
                try:
                    await client.post(f"http://localhost:8000/faults/{ev.fault_kind.value}/trigger")
                except Exception:
                    pass

    return {
        "status": "received",
        "processed_count": len(payload.alerts),
        "emitted_incidents": len(events),
        "incident_ids": [e.incident_id for e in events],
    }


@router.post("/alerts/webhook/pagerduty")
async def ingest_pagerduty_webhook(payload: PagerDutyWebhookPayload):
    """Ingest and normalize PagerDuty V2 incident webhook events."""
    import httpx
    from observability.adaptive_sentinel import get_adaptive_sentinel
    from policy.circuit_breaker import get_circuit_breaker

    gateway = get_alert_gateway()
    gateway._active_alerts.clear()
    get_circuit_breaker().reset()
    get_adaptive_sentinel().reset_cooldown()

    events = gateway.ingest_pagerduty(payload)

    if events:
        async with httpx.AsyncClient(timeout=1.5) as client:
            for ev in events:
                try:
                    await client.post(f"http://localhost:8000/faults/{ev.fault_kind.value}/trigger")
                except Exception:
                    pass

    return {
        "status": "received",
        "processed_count": len(payload.messages),
        "emitted_incidents": len(events),
        "incident_ids": [e.incident_id for e in events],
    }


@router.get("/alerts/recent")
async def get_recent_ingested_alerts(limit: int = Query(default=10, ge=1, le=50)):
    """List recent normalized alerts ingested through Alertmanager and PagerDuty webhooks."""
    gateway = get_alert_gateway()
    return gateway.get_recent_alerts(limit=limit)


# ==============================================================================
# Sprint 2: CI/CD Deployment Intelligence & Dynamic Service Mesh Endpoints
# ==============================================================================

from observability.deployments import (
    DeploymentCorrelation,
    DeploymentEvent,
    get_deployment_store,
    parse_argocd_webhook,
    parse_github_webhook,
)
from observability.k8s_topology import get_dynamic_topology_engine
from observability.topology import DependencyEdge, ServiceNode


@router.post("/events/deployments/github", response_model=DeploymentEvent)
async def ingest_github_deployment(payload: dict):
    """Ingest GitHub Actions workflow_run or deployment_status webhook."""
    from policy.circuit_breaker import get_circuit_breaker
    get_circuit_breaker().reset()
    store = get_deployment_store()
    event = parse_github_webhook(payload)
    return store.record_deployment(event)


@router.post("/events/deployments/argocd", response_model=DeploymentEvent)
async def ingest_argocd_deployment(payload: dict):
    """Ingest ArgoCD Application sync or notification webhook."""
    from policy.circuit_breaker import get_circuit_breaker
    get_circuit_breaker().reset()
    store = get_deployment_store()
    event = parse_argocd_webhook(payload)
    return store.record_deployment(event)


@router.post("/events/deployments", response_model=DeploymentEvent)
async def ingest_generic_deployment(event: DeploymentEvent):
    """Directly register a typed deployment event."""
    store = get_deployment_store()
    return store.record_deployment(event)


@router.get("/events/deployments/recent", response_model=list[DeploymentEvent])
async def get_recent_deployments(limit: int = Query(default=20, ge=1, le=100), service: str | None = None):
    """Retrieve recent deployments with commit metadata and diffs."""
    store = get_deployment_store()
    return store.get_recent(limit=limit, service=service)


@router.get("/topology/dynamic", response_model=TopologySnapshot)
async def get_dynamic_topology():
    """Retrieve live service dependency graph with runtime Jaeger trace discovery."""
    hub = get_observability_hub()
    red = await hub.scraper.get_red_metrics()
    engine = get_dynamic_topology_engine()
    return await engine.build_dynamic_topology(red=red, discover_traces=True)


@router.post("/topology/nodes", response_model=ServiceNode)
async def register_dynamic_topology_node(node: ServiceNode):
    """Dynamically register a new service/pod node in the topology mesh without backend restart."""
    engine = get_dynamic_topology_engine()
    engine.register_service(node)
    return node


@router.delete("/topology/nodes/{node_id}")
async def unregister_dynamic_topology_node(node_id: str):
    """Remove a dynamic node from the topology mesh."""
    engine = get_dynamic_topology_engine()
    engine.unregister_service(node_id)
    return {"status": "unregistered", "node_id": node_id}


@router.post("/topology/edges", response_model=DependencyEdge)
async def register_dynamic_topology_edge(edge: DependencyEdge):
    """Register a new dependency connection between services."""
    engine = get_dynamic_topology_engine()
    engine.register_edge(edge)
    return edge


# ==============================================================================
# Sprint 4: Cryptographic Audit Ledger & ChatOps Endpoints
# ==============================================================================

from hitl.slack_bot import (
    SlackInteractionHandler,
    build_slack_approval_card,
    format_postmortem_for_jira_or_pagerduty,
)


@router.post("/hitl/slack-interaction")
async def handle_slack_interaction(payload: dict):
    """Process interactive button approvals from Slack Block Kit."""
    handler = SlackInteractionHandler()
    from hitl.gate import get_approval_gate
    return handler.process_interaction(payload, approval_gate=get_approval_gate())


@router.post("/hitl/slack/card")
async def preview_slack_approval_card(payload: dict):
    """Generate and preview Slack Block Kit interactive card JSON."""
    return build_slack_approval_card(
        incident_id=payload.get("incident_id", "inc-preview-01"),
        title=payload.get("title", "High Latency & DB Lock Contention"),
        severity=payload.get("severity", "critical"),
        fault_kind=payload.get("fault_kind", "traffic_surge"),
        root_cause=payload.get("root_cause", "Database connection pool saturated"),
        confidence=payload.get("confidence", 0.95),
        what_changed=payload.get("what_changed", "Commit 8f4b2a9 deployed 3m ago"),
        proposed_action=payload.get("proposed_action", "scale_out (workers: 6)"),
        blast_radius=payload.get("blast_radius", "medium"),
    )


@router.post("/hitl/postmortem/sync")
async def sync_postmortem_ticket(incident_id: str, destination: str = Query(default="jira")):
    """Sync incident post-mortem markdown to Jira issue or PagerDuty incident notes."""
    pm = generate_postmortem(incident_id)
    if pm is None:
        raise HTTPException(status_code=404, detail="Incident not found or no report filed")
    return format_postmortem_for_jira_or_pagerduty(
        incident_id=incident_id,
        postmortem_markdown=getattr(pm, "markdown_report", getattr(pm, "markdown", str(pm))),
        destination=destination,
    )



