"""Unit tests for Enterprise Safety, Explainability & Immutable Audit Ledger (AegisOps Slice 4)."""

from __future__ import annotations

import pytest

from agent.actions import ActionType, BlastRadius, ProposedAction
from agent.nodes.policy import policy_node
from agent.nodes.rollback import rollback_node
from agent.state import (
    AgentState,
    Outcome,
    PolicyDecision,
    PolicyVerdict,
    RemediationPlan,
    SandboxResult,
    TriageResult,
    initial_state,
)
from audit.ledger import IncidentLedger, LedgerEntry, get_incident_ledger
from policy.engine import PolicyEngine
from stream.schema import FaultKind
from tests.test_agent_nodes import make_incident


def test_policy_engine_populates_explainability_and_blast_radius():
    engine = PolicyEngine()
    proposal = ProposedAction(action=ActionType.scale_out, workers=4, reason="Absorb load", target="mock_app")
    triage = TriageResult(
        fault_kind=FaultKind.traffic_surge,
        root_cause="Queue saturation",
        confidence=0.88,
        reasoning="Spike in p95 latency",
        blast_radius=BlastRadius.low,
    )
    sandbox = SandboxResult(passed=True, exit_code=0, stdout="", stderr="", duration_ms=10.0)

    verdict = engine.evaluate(proposal=proposal, sandbox=sandbox, triage=triage)

    assert verdict.decision == PolicyDecision.allow
    assert verdict.blast_radius == BlastRadius.low
    assert verdict.risk_assessment is not None
    assert "Authorized for auto-apply" in verdict.risk_assessment


def test_policy_engine_explains_approval_requirement():
    engine = PolicyEngine()
    # Unverified proposal (sandbox failed)
    proposal = ProposedAction(action=ActionType.restart_service, reason="Restart", target="mock_app")
    triage = TriageResult(
        fault_kind=FaultKind.memory_leak,
        root_cause="Heap growth",
        confidence=0.85,
        reasoning="RSS growing",
        blast_radius=BlastRadius.medium,
    )
    sandbox = SandboxResult(passed=False, exit_code=1, stdout="", stderr="Crash", duration_ms=15.0)

    verdict = engine.evaluate(proposal=proposal, sandbox=sandbox, triage=triage)

    assert verdict.decision == PolicyDecision.needs_approval
    assert "sandbox_proof_required" in verdict.violated_rules
    assert verdict.blast_radius == BlastRadius.medium
    assert verdict.risk_assessment is not None
    assert "requires operator authorization" in verdict.risk_assessment


def test_immutable_incident_ledger_in_memory():
    ledger = IncidentLedger(conn_str="postgresql://invalid:5432/none")
    iid = "test-incident-1234"

    entry1 = ledger.record_event(
        incident_id=iid,
        event_type="INCIDENT_DETECTED",
        actor="aegis-sentinel",
        payload={"fault": "traffic_surge", "p95": 220.0},
    )
    assert entry1.incident_id == iid
    assert entry1.event_type == "INCIDENT_DETECTED"

    entry2 = ledger.record_event(
        incident_id=iid,
        event_type="REMEDY_APPLIED",
        actor="live-applier",
        payload={"action": "scale_out", "workers": 4},
    )
    assert entry2.event_type == "REMEDY_APPLIED"

    trail = ledger.get_audit_trail(iid)
    assert len(trail) == 2
    assert trail[0].event_type == "INCIDENT_DETECTED"
    assert trail[1].event_type == "REMEDY_APPLIED"
    assert trail[1].payload["workers"] == 4


@pytest.mark.asyncio
async def test_policy_node_records_audit_ledger_event():
    ledger = get_incident_ledger()
    iid = "inc-policy-test-999"
    incident = make_incident(incident_id=iid)
    state = initial_state(incident)
    state["plan"] = RemediationPlan(
        mitigation=ProposedAction(action=ActionType.scale_out, workers=4, reason="scale"),
    )
    state["sandbox_result"] = SandboxResult(passed=True, exit_code=0, stdout="", stderr="", duration_ms=5.0)
    state["triage"] = TriageResult(
        fault_kind=FaultKind.traffic_surge,
        root_cause="traffic",
        confidence=0.9,
        reasoning="surge",
        blast_radius=BlastRadius.low,
    )

    engine = PolicyEngine()
    res = await policy_node(state, engine=engine)

    assert res["policy_verdict"].decision == PolicyDecision.allow
    trail = ledger.get_audit_trail(iid)
    policy_events = [e for e in trail if e.event_type == "POLICY_EVALUATED"]
    assert len(policy_events) >= 1
    assert policy_events[0].payload["decision"] == "allow"
    assert policy_events[0].payload["blast_radius"] == "low"


@pytest.mark.asyncio
async def test_rollback_safeguard_records_ledger_event():
    class SpyApplier:
        def __init__(self):
            self.reverted = []

        def rollback_action(self, action, previous_state=None):
            self.reverted.append((action, previous_state))

    applier = SpyApplier()
    ledger = get_incident_ledger()
    iid = "inc-rollback-test-888"
    incident = make_incident(incident_id=iid)
    state = initial_state(incident)
    state["plan"] = RemediationPlan(
        mitigation=ProposedAction(action=ActionType.scale_out, workers=4, reason="scale"),
    )
    state["live_metrics_before"] = {"workers": 2, "latency_ms": 150.0}

    res = await rollback_node(state, applier=applier)
    assert res["rollback_performed"] is True
    assert len(applier.reverted) == 1
    assert applier.reverted[0][1] == {"workers": 2, "latency_ms": 150.0}

    trail = ledger.get_audit_trail(iid)
    rb_events = [e for e in trail if e.event_type == "ROLLBACK_TRIGGERED"]
    assert len(rb_events) >= 1
    assert rb_events[0].payload["mitigation_action"] == "scale_out"
    assert rb_events[0].payload["reverted_to"]["workers"] == 2
