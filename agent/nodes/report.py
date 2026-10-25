"""Report node: emit the final IncidentReport; file the durable fix (ADR-0003)."""

from __future__ import annotations

from opentelemetry import trace

from agent.actions import ActionType
from agent.state import (
    AgentState, HitlChoice, IncidentReport, Outcome, PolicyDecision,
)
from audit.ledger import get_incident_ledger
from observability.tracing import traced


def _determine_outcome(state: AgentState) -> Outcome:
    if state.get("rollback_performed"):
        return Outcome.escalated
    verif = state.get("verification_result")
    if verif is not None and not verif.passed:
        return Outcome.escalated
    if state.get("applied"):
        return Outcome.applied
    hitl = state.get("hitl_decision")
    if hitl and hitl.choice is HitlChoice.reject:
        return Outcome.rejected
    verdict = state.get("policy_verdict")
    if verdict and verdict.decision == PolicyDecision.block:
        return Outcome.blocked
    # escalate action, retry exhaustion, HITL expiry, and apply failure all land here
    return Outcome.escalated


@traced("report.persist")
async def report_node(state: AgentState, sink, registry) -> dict:
    incident = state["incident"]
    triage = state.get("triage")
    sandbox = state.get("sandbox_result")
    verdict = state.get("policy_verdict")
    hitl = state.get("hitl_decision")
    plan = state.get("plan")
    mitigation = plan.mitigation if plan else None
    durable_fix = plan.durable_fix if plan else None

    outcome = _determine_outcome(state)
    usage = state.get("usage", [])
    # File the durable fix regardless of terminal outcome (§5 "open durable fixes"):
    # a rejected/blocked/escalated incident still has an unfixed root cause worth ticketing.
    if durable_fix is not None:
        registry.file(incident=incident, triage=triage, fix=durable_fix)

    applied_target_file = (
        mitigation.target_file
        if outcome is Outcome.applied and mitigation
        and mitigation.action is ActionType.patch_code else None
    )
    verif = state.get("verification_result")
    report = IncidentReport(
        incident_id=incident.incident_id,
        fault_kind=incident.fault_kind,
        outcome=outcome,
        mitigation_action=mitigation.action if mitigation else None,
        attempted_actions=[a.action.action.value for a in state.get("attempted", [])],
        durable_fix=durable_fix,
        triage_confidence=triage.confidence if triage else None,
        what_broke=triage.what_broke if triage else None,
        why_it_broke=triage.why_it_broke if triage else None,
        what_changed_recently=triage.what_changed_recently if triage else None,
        blast_radius=plan.blast_radius if (plan and plan.blast_radius) else (triage.blast_radius if triage else None),
        affected_services=triage.affected_services if triage else [],
        rollback_strategy=plan.rollback_strategy if plan else None,
        expected_impact=plan.expected_impact if plan else None,
        retries=state.get("retries", 0),
        sandbox_passed=sandbox.passed if sandbox else None,
        policy_decision=verdict.decision if verdict else None,
        hitl_choice=hitl.choice if hitl else None,
        apply_error=state.get("apply_error"),
        applied_target_file=applied_target_file,
        live_verified=verif.passed if verif else None,
        live_metrics_before=verif.before_metrics if verif else state.get("live_metrics_before"),
        live_metrics_after=verif.after_metrics if verif else None,
        rollback_performed=state.get("rollback_performed", False),
        total_input_tokens=sum(u.input_tokens for u in usage),
        total_output_tokens=sum(u.output_tokens for u in usage),
        total_latency_ms=sum(u.latency_ms for u in usage),
        node_usage=list(usage),
    )
    sink.emit(report)
    trace.get_current_span().set_attribute("report.outcome", report.outcome.value)

    get_incident_ledger().record_event(
        incident_id=incident.incident_id,
        event_type="INCIDENT_CLOSED",
        actor="aegis-agent",
        payload={
            "outcome": outcome.value,
            "mitigation_action": report.mitigation_action.value if report.mitigation_action else None,
            "total_latency_ms": report.total_latency_ms,
            "total_input_tokens": report.total_input_tokens,
            "total_output_tokens": report.total_output_tokens,
            "live_verified": report.live_verified,
            "rollback_performed": report.rollback_performed,
        },
    )

    return {"report": report}
