"""Apply node: execute the policy-cleared mitigation on the live target (AegisOps Slice 1 & 4)."""

from __future__ import annotations

from opentelemetry import trace

from agent.state import AgentState
from audit.ledger import get_incident_ledger
from observability.tracing import traced


@traced("apply.execute")
async def apply_node(state: AgentState, applier, engine, verifier=None) -> dict:
    mitigation = state["plan"].mitigation
    incident = state.get("incident")
    incident_id = incident.incident_id if incident else "unknown-incident"
    before_metrics = None
    if verifier is not None and hasattr(verifier, "get_live_metrics"):
        try:
            before_metrics = await verifier.get_live_metrics(state["incident"].fault_kind)
        except Exception:
            before_metrics = None

    try:
        applier.apply(mitigation)
    except Exception as exc:
        trace.get_current_span().set_attribute("apply.outcome", "error")
        get_incident_ledger().record_event(
            incident_id=incident_id,
            event_type="REMEDY_FAILED",
            actor="live-applier",
            payload={
                "action": mitigation.action.value,
                "error": str(exc),
                "before_metrics": before_metrics,
            },
        )
        res = {"applied": False, "apply_error": str(exc)}
        if before_metrics is not None:
            res["live_metrics_before"] = before_metrics
        return res

    engine.record_apply(mitigation, state["policy_verdict"].decision)
    trace.get_current_span().set_attribute("apply.outcome", "applied")

    get_incident_ledger().record_event(
        incident_id=incident_id,
        event_type="REMEDY_APPLIED",
        actor="live-applier",
        payload={
            "action": mitigation.action.value,
            "params": mitigation.model_dump(exclude_none=True),
            "before_metrics": before_metrics,
        },
    )

    res = {"applied": True}
    if before_metrics is not None:
        res["live_metrics_before"] = before_metrics
    return res
