"""Policy node: gate the plan's mitigation against the deterministic rule engine (AegisOps Slice 4)."""

from __future__ import annotations

from opentelemetry import trace

from agent.state import AgentState
from audit.ledger import get_incident_ledger
from observability.tracing import traced


@traced("graph.policy")
async def policy_node(state: AgentState, engine) -> dict:
    verdict = engine.evaluate(
        proposal=state["plan"].mitigation,
        sandbox=state.get("sandbox_result"),
        triage=state.get("triage"),
    )
    trace.get_current_span().set_attribute("policy.decision", verdict.decision.value)

    incident = state.get("incident")
    incident_id = incident.incident_id if incident else "unknown-incident"

    get_incident_ledger().record_event(
        incident_id=incident_id,
        event_type="POLICY_EVALUATED",
        actor="policy-engine",
        payload={
            "decision": verdict.decision.value,
            "violated_rules": verdict.violated_rules,
            "reasons": verdict.reasons,
            "blast_radius": verdict.blast_radius.value if verdict.blast_radius else None,
            "risk_assessment": verdict.risk_assessment,
        },
    )

    return {"policy_verdict": verdict}
