"""Rollback node: automated rollback safeguard when live verification fails (AegisOps Slice 1 & 4)."""

from __future__ import annotations

from opentelemetry import trace

from agent.state import AgentState
from audit.ledger import get_incident_ledger
from observability.tracing import traced


@traced("apply.rollback")
async def rollback_node(state: AgentState, applier) -> dict:
    incident = state.get("incident")
    incident_id = incident.incident_id if incident else "unknown-incident"
    mitigation = state["plan"].mitigation
    previous_state = state.get("live_metrics_before")
    error_msg = None
    try:
        applier.rollback_action(mitigation, previous_state=previous_state)
        trace.get_current_span().set_attribute("rollback.executed", True)
    except Exception as exc:
        error_msg = str(exc)
        trace.get_current_span().set_attribute("rollback.error", error_msg)

    # Record into immutable audit ledger
    get_incident_ledger().record_event(
        incident_id=incident_id,
        event_type="ROLLBACK_TRIGGERED",
        actor="aegis-safeguard",
        payload={
            "mitigation_action": mitigation.action.value,
            "reverted_to": previous_state,
            "success": error_msg is None,
            "error": error_msg,
        },
    )

    return {"rollback_performed": True}
