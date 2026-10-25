"""Unit and integration tests for closed-loop recovery and verification (AegisOps Slice 1)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agent.actions import ActionType, ProposedAction
from agent.nodes.verify import verify_node
from agent.nodes.rollback import rollback_node
from agent.graph import route_after_apply, route_after_verify
from agent.state import AgentState, LiveVerificationResult, Outcome
from stream.schema import FaultKind, IncidentEvent, Severity


def _make_incident(fault_kind: FaultKind = FaultKind.traffic_surge) -> IncidentEvent:
    return IncidentEvent(
        incident_id="inc-test-1",
        fault_kind=fault_kind,
        severity=Severity.error,
        source="mock_app",
        title=f"{fault_kind.value} detected",
        summary="Test incident",
        event_count=5,
        duplicate_count=0,
        first_seen="2026-10-24T00:00:00Z",
        last_seen="2026-10-24T00:00:10Z",
        correlation_window_s=10.0,
        sample_events=[],
    )


@pytest.mark.asyncio
async def test_verify_node_invokes_verifier_and_sets_result():
    incident = _make_incident()
    state = {
        "incident": incident,
        "live_metrics_before": {"latency_ms": 200.0},
    }
    mock_verifier = MagicMock()
    mock_verifier.verify_recovery = AsyncMock(return_value=LiveVerificationResult(
        passed=True,
        fault_kind=FaultKind.traffic_surge,
        before_metrics={"latency_ms": 200.0},
        after_metrics={"latency_ms": 50.0},
        duration_ms=120.0,
    ))

    out = await verify_node(state, verifier=mock_verifier)
    assert out["verification_result"].passed is True
    assert out["verification_result"].after_metrics["latency_ms"] == 50.0
    mock_verifier.verify_recovery.assert_awaited_once_with(
        FaultKind.traffic_surge, before_metrics={"latency_ms": 200.0}
    )


def test_route_after_apply_routes_to_verify_when_applied():
    assert route_after_apply({"applied": True}) == "verify"
    assert route_after_apply({"applied": False}) == "report"


def test_route_after_verify_routes_to_report_on_success():
    verif = LiveVerificationResult(passed=True, fault_kind=FaultKind.traffic_surge)
    assert route_after_verify({"verification_result": verif}) == "report"
    assert route_after_verify({"verification_result": None}) == "report"


def test_route_after_verify_routes_to_rollback_on_failure():
    verif = LiveVerificationResult(
        passed=False, fault_kind=FaultKind.traffic_surge, failure_reason="latency remained high"
    )
    assert route_after_verify({"verification_result": verif}) == "rollback"


@pytest.mark.asyncio
async def test_rollback_node_invokes_applier_rollback():
    action = ProposedAction(action=ActionType.scale_out, workers=8, reason="scale for traffic")
    mock_plan = MagicMock()
    mock_plan.mitigation = action
    state = {"plan": mock_plan}
    mock_applier = MagicMock()

    out = await rollback_node(state, applier=mock_applier)
    assert out == {"rollback_performed": True}
    mock_applier.rollback_action.assert_called_once_with(action, previous_state=None)


def test_drain_connections_action_in_catalog():
    from agent.actions import CATALOG, ActionMetadata
    assert ActionType.drain_connections in CATALOG
    meta = CATALOG[ActionType.drain_connections]
    assert isinstance(meta, ActionMetadata)
    assert meta.reversible is True
    assert meta.requires_approval is False
