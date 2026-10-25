"""Unit and integration tests for Sprint 3:
- Kubernetes Operator Applier (rollout restarts, replica scaling, inverse actions)
- Anti-Flap Circuit Breakers (per-service 15m cooldown, cascading failure protection)
- Two-Phase Canary & Sustained Soak Verification (canary probe -> soak window -> auto-rollback)
- Ledger audit recording of ROLLBACK_TRIGGERED
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import pytest

from agent.actions import ActionType, ProposedAction
from agent.state import PolicyDecision
from apply.kubernetes_applier import KubernetesApplier
from apply.two_phase_verifier import TwoPhaseVerificationResult, TwoPhaseVerifier
from audit.ledger import get_incident_ledger
from policy.circuit_breaker import AntiFlapCircuitBreaker
from policy.engine import PolicyEngine
from stream.schema import FaultKind


# ==============================================================================
# 1. Kubernetes Operator Applier Tests (Acceptance Criterion 1)
# ==============================================================================

@pytest.mark.asyncio
async def test_k8s_applier_scale_deployment():
    applier = KubernetesApplier(namespace="production")
    result = await applier.scale_deployment(
        deployment="mock-app",
        replicas=6,
        previous_replicas=2,
    )

    assert result.success is True
    assert result.action is ActionType.scale_out
    assert result.service_name == "mock-app"
    assert result.k8s_api_endpoint == "/apis/apps/v1/namespaces/production/deployments/mock-app/scale"
    assert result.k8s_patch["spec"]["replicas"] == 6

    # Automated inverse action calculation
    assert result.inverse_action is not None
    assert result.inverse_action.action is ActionType.scale_out
    assert result.inverse_action.workers == 2


@pytest.mark.asyncio
async def test_k8s_applier_rollout_restart():
    applier = KubernetesApplier(namespace="production")
    result = await applier.rollout_restart(deployment="mock-app")

    assert result.success is True
    assert result.action is ActionType.restart_service
    assert result.service_name == "mock-app"
    assert result.k8s_api_endpoint == "/apis/apps/v1/namespaces/production/deployments/mock-app"
    annotations = result.k8s_patch["spec"]["template"]["metadata"]["annotations"]
    assert "kubectl.kubernetes.io/restartedAt" in annotations


@pytest.mark.asyncio
async def test_k8s_applier_rollback_and_inverse():
    applier = KubernetesApplier(namespace="production")
    result = await applier.rollback_deployment(
        deployment="mock-app",
        image_tag_previous="mock-app:v1.4.1",
        image_tag_current="mock-app:v1.4.2",
    )

    assert result.success is True
    assert result.action is ActionType.rollback
    containers = result.k8s_patch["spec"]["template"]["spec"]["containers"]
    assert containers[0]["image"] == "mock-app:v1.4.1"
    assert result.inverse_action is not None
    assert result.inverse_action.action is ActionType.rollback


# ==============================================================================
# 2. Anti-Flap Circuit Breakers Tests (Acceptance Criterion 2)
# ==============================================================================

def test_anti_flap_blocks_second_action_within_15_mins():
    now = 1000.0
    cb = AntiFlapCircuitBreaker(service_cooldown_s=900.0, clock=lambda: now)

    # 1. First action allowed
    allowed, reason, dec = cb.evaluate("mock-app", "scale_out", timestamp=now)
    assert allowed is True
    assert dec == PolicyDecision.allow
    cb.record_action("mock-app", "scale_out", timestamp=now)

    # 2. Second action 5 minutes later (T+300s) -> BLOCKED by flap protection
    now = 1300.0
    allowed2, reason2, dec2 = cb.evaluate("mock-app", "restart_service", timestamp=now)
    assert allowed2 is False
    assert dec2 == PolicyDecision.block
    assert "Flap protection active" in reason2
    assert "mock-app" in reason2

    # 3. Third action 16 minutes later (T+960s) -> ALLOWED (cooldown expired)
    now = 1960.0
    allowed3, reason3, dec3 = cb.evaluate("mock-app", "restart_service", timestamp=now)
    assert allowed3 is True
    assert dec3 == PolicyDecision.allow


def test_global_circuit_breaker_cascading_failure_protection():
    now = 1000.0
    cb = AntiFlapCircuitBreaker(
        service_cooldown_s=900.0,
        global_window_s=300.0,
        global_threshold=3,
        clock=lambda: now,
    )

    # Mitigate 4 distinct services within 3 minutes
    cb.record_action("service-auth", "restart_service", timestamp=now + 10)
    cb.record_action("service-payments", "scale_out", timestamp=now + 30)
    cb.record_action("service-orders", "toggle_feature_flag", timestamp=now + 50)
    cb.record_action("service-inventory", "drain_connections", timestamp=now + 70)

    # 5th service evaluates -> global circuit tripped!
    allowed, reason, dec = cb.evaluate("service-search", "scale_out", timestamp=now + 80)
    assert allowed is False
    assert dec == PolicyDecision.needs_approval
    assert "Global circuit breaker TRIPPED" in reason
    assert "4 distinct services" in reason


def test_policy_engine_integration_with_circuit_breaker():
    now = {"t": 1000.0}
    cb = AntiFlapCircuitBreaker(service_cooldown_s=900.0, clock=lambda: now["t"])
    engine = PolicyEngine(clock=lambda: now["t"], circuit_breaker=cb)

    proposal = ProposedAction(action=ActionType.scale_out, workers=4, target="mock-app", reason="traffic surge")
    engine.record_apply(proposal, PolicyDecision.allow)

    # Attempt second action 2 minutes later
    now["t"] += 120.0
    restart = ProposedAction(action=ActionType.restart_service, target="mock-app", reason="try restart")
    
    # Needs dummy sandbox and triage
    from agent.state import SandboxResult, TriageResult
    sb = SandboxResult(passed=True, exit_code=0, stdout="", stderr="", duration_ms=10.0, before_metrics={}, after_metrics={})
    tr = TriageResult(fault_kind=FaultKind.traffic_surge, root_cause="surge", confidence=0.9, reasoning="", what_broke="", why_it_broke="", what_changed_recently="")

    verdict = engine.evaluate(proposal=restart, sandbox=sb, triage=tr)
    assert verdict.decision is PolicyDecision.block
    assert "flap_protection" in verdict.violated_rules


# ==============================================================================
# 3. Two-Phase Canary & Soak Verification Tests (Acceptance Criterion 3)
# ==============================================================================

class MockApplierTracker:
    def __init__(self):
        self.rolled_back = False
        self.rollback_action_called = None
        self.previous_state = None

    def rollback_action(self, action: ProposedAction, previous_state: dict | None = None):
        self.rolled_back = True
        self.rollback_action_called = action
        self.previous_state = previous_state


@pytest.mark.asyncio
async def test_two_phase_verifier_soak_latency_spike_triggers_rollback():
    """Verify Criterion 3: If p95 latency spikes during soak window, triggers rollback & ledger update."""
    applier = MockApplierTracker()
    now_t = 0.0

    verifier = TwoPhaseVerifier(
        canary_duration_s=0.2,
        canary_interval_s=0.05,
        soak_duration_s=0.4,
        soak_interval_s=0.08,
        max_p95_latency_ms=150.0,
        clock=lambda: now_t,
    )

    action = ProposedAction(action=ActionType.scale_out, workers=6, target="mock-app", reason="scale out pods")
    incident_id = "inc-soak-spike-test"

    # Simulate metrics: Phase 1 passes (p95=50ms, err=0%), but during Phase 2 soak p95 spikes to 230ms!
    call_count = 0
    async def mock_metrics(fault_kind=None):
        nonlocal call_count, now_t
        call_count += 1
        now_t += 0.06
        if call_count <= 4:
            # Canary phase: healthy
            return {"p95_latency_ms": 48.0, "error_rate_pct": 0.0, "db_lock_wait_ms": 0.0}
        else:
            # Soak phase: latency spike!
            return {"p95_latency_ms": 230.0, "error_rate_pct": 0.0, "db_lock_wait_ms": 0.0}

    verifier.get_live_metrics = mock_metrics

    result = await verifier.verify_recovery(
        fault_kind=FaultKind.traffic_surge,
        before_metrics={"p95_latency_ms": 200.0, "error_rate_pct": 0.0},
        action=action,
        applier=applier,
        incident_id=incident_id,
    )

    # Verification must fail in soak phase
    assert result.passed is False
    assert result.phase == "soak"
    assert result.canary_passed is True
    assert result.soak_passed is False
    assert "p95 latency spiked to 230.0ms during soak window" in result.failure_reason

    # Automated rollback safeguard must have executed
    assert applier.rolled_back is True
    assert applier.rollback_action_called == action
    assert result.rollback_triggered is True

    # Audit ledger must contain ROLLBACK_TRIGGERED event
    ledger = get_incident_ledger()
    trail = ledger.get_audit_trail(incident_id)
    assert any(e.event_type == "ROLLBACK_TRIGGERED" for e in trail)
    rb_entry = next(e for e in trail if e.event_type == "ROLLBACK_TRIGGERED")
    assert rb_entry.payload["phase"] == "soak"
    assert "230.0ms" in rb_entry.payload["reason"]


@pytest.mark.asyncio
async def test_two_phase_verifier_canary_failure_triggers_immediate_rollback():
    """Verify Canary failure: if error rate >= 1% during canary, halts and triggers rollback."""
    applier = MockApplierTracker()
    now_t = 0.0

    verifier = TwoPhaseVerifier(
        canary_duration_s=0.2,
        canary_interval_s=0.05,
        soak_duration_s=0.5,
        soak_interval_s=0.1,
        max_error_rate_pct=1.0,
        clock=lambda: now_t,
    )

    action = ProposedAction(action=ActionType.restart_service, target="mock-app", reason="restart service")
    incident_id = "inc-canary-fail-test"

    # Always erroring
    async def mock_metrics(fault_kind=None):
        nonlocal now_t
        now_t += 0.06
        return {"p95_latency_ms": 60.0, "error_rate_pct": 25.0, "db_lock_wait_ms": 0.0}

    verifier.get_live_metrics = mock_metrics

    result = await verifier.verify_recovery(
        fault_kind=FaultKind.error_spike,
        before_metrics={"error_rate_pct": 30.0},
        action=action,
        applier=applier,
        incident_id=incident_id,
    )

    assert result.passed is False
    assert result.phase == "canary"
    assert result.canary_passed is False
    assert result.soak_passed is False
    assert applier.rolled_back is True
    assert result.rollback_triggered is True


@pytest.mark.asyncio
async def test_two_phase_verifier_full_pass():
    """Verify clean recovery: both Canary and Soak pass without rollback."""
    applier = MockApplierTracker()
    now_t = 0.0

    verifier = TwoPhaseVerifier(
        canary_duration_s=0.1,
        canary_interval_s=0.03,
        soak_duration_s=0.2,
        soak_interval_s=0.05,
        clock=lambda: now_t,
    )

    action = ProposedAction(action=ActionType.scale_out, workers=4, target="mock-app", reason="scale out pods")
    incident_id = "inc-full-pass-test"

    async def mock_metrics(fault_kind=None):
        nonlocal now_t
        now_t += 0.04
        return {"p95_latency_ms": 40.0, "error_rate_pct": 0.0, "db_lock_wait_ms": 0.0}

    verifier.get_live_metrics = mock_metrics

    result = await verifier.verify_recovery(
        fault_kind=FaultKind.traffic_surge,
        before_metrics={"p95_latency_ms": 180.0},
        action=action,
        applier=applier,
        incident_id=incident_id,
    )

    assert result.passed is True
    assert result.phase == "soak_complete"
    assert result.canary_passed is True
    assert result.soak_passed is True
    assert applier.rolled_back is False
    assert result.rollback_triggered is False
