"""Verify node: live telemetry assertion for closed-loop recovery (AegisOps Slice 1 & 4)."""

from __future__ import annotations

from opentelemetry import trace

from agent.state import AgentState
from audit.ledger import get_incident_ledger
from observability.tracing import traced


@traced("verify.telemetry")
async def verify_node(state: AgentState, verifier, applier: Any = None) -> dict:
    if verifier is None:
        return {"verification_result": None}

    fault_kind = state["incident"].fault_kind
    before = state.get("live_metrics_before")
    incident = state.get("incident")
    incident_id = incident.incident_id if incident else "unknown-incident"

    import inspect
    sig = inspect.signature(verifier.verify_recovery)
    kwargs = {}
    if "action" in sig.parameters and state.get("plan"):
        kwargs["action"] = state["plan"].mitigation
    if "applier" in sig.parameters:
        kwargs["applier"] = applier
    if "incident_id" in sig.parameters:
        kwargs["incident_id"] = incident_id

    result = await verifier.verify_recovery(fault_kind, before_metrics=before, **kwargs)

    current_span = trace.get_current_span()
    current_span.set_attribute("verify.passed", result.passed)
    if result.failure_reason:
        current_span.set_attribute("verify.failure_reason", result.failure_reason)

    incident = state.get("incident")
    incident_id = incident.incident_id if incident else "unknown-incident"

    get_incident_ledger().record_event(
        incident_id=incident_id,
        event_type="VERIFICATION_COMPLETED",
        actor="live-verifier",
        payload={
            "passed": result.passed,
            "fault_kind": fault_kind.value,
            "before_metrics": result.before_metrics,
            "after_metrics": result.after_metrics,
            "failure_reason": result.failure_reason,
            "duration_ms": result.duration_ms,
        },
    )

    return {"verification_result": result}
