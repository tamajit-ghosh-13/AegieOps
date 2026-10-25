"""Unit tests for Multi-Modal Investigation & Root-Cause Reasoning (AegisOps Slice 3)."""

from __future__ import annotations

import pytest

from agent.actions import ActionType, BlastRadius, ProposedAction
from agent.nodes.propose import _prompt as propose_prompt, propose_node
from agent.nodes.report import report_node
from agent.nodes.triage import _format_telemetry, _prompt as triage_prompt, triage_node
from agent.state import (
    HitlChoice,
    HitlDecision,
    Outcome,
    PolicyDecision,
    PolicyVerdict,
    RemediationPlan,
    SandboxResult,
    TriageResult,
    initial_state,
)
from observability.hub import SystemTelemetrySnapshot
from observability.prometheus import REDMetrics
from observability.topology import HealthStatus, ServiceNode, TopologySnapshot
from stream.schema import FaultKind, IncidentEvent
from tests.test_agent_nodes import FakeStructuredLLM, make_incident
from tests.test_report_node import FakeRegistry, FakeSink


def test_triage_prompt_includes_live_telemetry_signals():
    incident = make_incident(fault_kind=FaultKind.traffic_surge)
    snapshot = SystemTelemetrySnapshot(
        timestamp="2026-10-24T10:00:00Z",
        red_metrics=REDMetrics(
            total_requests=150,
            error_count=25,
            error_rate_pct=16.7,
            rate_rps=30.0,
            p95_latency_ms=220.5,
            memory_rss_mb=42.0,
            db_lock_wait_ms=0.0,
            active_workers=2,
            feature_flags={"risky_feature": False},
            active_faults={"traffic_surge": True},
        ),
        topology=TopologySnapshot(
            nodes=[
                ServiceNode(id="mock_app", name="API Service", type="api", status=HealthStatus.degraded),
                ServiceNode(id="postgres", name="PostgreSQL DB", type="database", status=HealthStatus.healthy),
            ],
            edges=[],
            overall_status=HealthStatus.degraded,
            active_anomalies=["API Service elevated latency (>100ms SLO)"],
        ),
        recent_traces=[],
        failing_traces_count=0,
        active_anomalies=["API Service elevated latency (>100ms SLO)"],
    )

    prompt = triage_prompt(incident, snapshot=snapshot)

    assert "LIVE OBSERVABILITY SIGNALS" in prompt
    assert "total=150, errors=25 (error_rate=16.7%" in prompt
    assert "p95=220.5ms" in prompt
    assert "API Service: degraded" in prompt
    assert "API Service elevated latency (>100ms SLO)" in prompt
    assert "what_broke" in prompt
    assert "why_it_broke" in prompt
    assert "what_changed_recently" in prompt
    assert "blast_radius" in prompt
    assert "affected_services" in prompt


def test_propose_prompt_includes_triage_investigation_findings():
    incident = make_incident(fault_kind=FaultKind.traffic_surge)
    triage = TriageResult(
        fault_kind=FaultKind.traffic_surge,
        root_cause="Incoming HTTP request volume exceeded 2-worker queue capacity",
        confidence=0.95,
        reasoning="Metrics show p95 latency spike to 220ms with active workers pinned at 2",
        what_broke="mock_app /work endpoint latency SLO breach (>100ms)",
        why_it_broke="Worker queue contention causing request buffering",
        what_changed_recently="Traffic surge fault injection on ingress route",
        blast_radius=BlastRadius.medium,
        affected_services=["mock_app", "ingress-gateway"],
    )
    state = initial_state(incident)
    state["triage"] = triage

    prompt = propose_prompt(state)

    assert "Triage Investigation Findings:" in prompt
    assert "Incoming HTTP request volume exceeded 2-worker queue capacity" in prompt
    assert "mock_app /work endpoint latency SLO breach (>100ms)" in prompt
    assert "Worker queue contention causing request buffering" in prompt
    assert "Traffic surge fault injection on ingress route" in prompt
    assert "Blast radius: medium" in prompt
    assert "Affected services: mock_app, ingress-gateway" in prompt
    assert "rollback_strategy" in prompt
    assert "expected_impact" in prompt


@pytest.mark.asyncio
async def test_triage_node_populates_full_investigation_fields():
    triage_data = TriageResult(
        fault_kind=FaultKind.memory_leak,
        root_cause="Unbounded cache list retention in mock_app",
        confidence=0.92,
        reasoning="Memory RSS grew beyond 50MB baseline steadily over 20s window",
        what_broke="mock_app memory allocator",
        why_it_broke="Leak simulator appending byte arrays to static list",
        what_changed_recently="Memory leak endpoint triggered",
        blast_radius=BlastRadius.low,
        affected_services=["mock_app"],
    )
    llm = FakeStructuredLLM([triage_data])
    state = initial_state(make_incident(fault_kind=FaultKind.memory_leak))

    res = await triage_node(state, llm=llm)

    triage = res["triage"]
    assert triage.fault_kind == FaultKind.memory_leak
    assert triage.what_broke == "mock_app memory allocator"
    assert triage.why_it_broke == "Leak simulator appending byte arrays to static list"
    assert triage.what_changed_recently == "Memory leak endpoint triggered"
    assert triage.blast_radius == BlastRadius.low
    assert triage.affected_services == ["mock_app"]


@pytest.mark.asyncio
async def test_propose_node_populates_remediation_plan_metadata():
    plan_data = RemediationPlan(
        mitigation=ProposedAction(
            action=ActionType.scale_out,
            workers=4,
            reason="Scale workers to absorb incoming request rate",
            target="mock_app",
        ),
        blast_radius=BlastRadius.low,
        rollback_strategy="Scale workers back to 2",
        expected_impact="p95 latency drops below 100ms SLO immediately",
    )
    llm = FakeStructuredLLM([plan_data])
    state = initial_state(make_incident(fault_kind=FaultKind.traffic_surge))
    state["triage"] = TriageResult(
        fault_kind=FaultKind.traffic_surge,
        root_cause="Worker queue contention",
        confidence=0.9,
        reasoning="Latency spiked",
        what_broke="mock_app",
        why_it_broke="Traffic surge",
        what_changed_recently="Surge injected",
        blast_radius=BlastRadius.medium,
        affected_services=["mock_app"],
    )

    res = await propose_node(state, llm=llm)

    plan = res["plan"]
    assert plan.mitigation.action == ActionType.scale_out
    assert plan.mitigation.workers == 4
    assert plan.blast_radius == BlastRadius.low
    assert plan.rollback_strategy == "Scale workers back to 2"
    assert plan.expected_impact == "p95 latency drops below 100ms SLO immediately"


@pytest.mark.asyncio
async def test_report_node_persists_investigation_and_rollback_fields():
    incident = make_incident(fault_kind=FaultKind.traffic_surge)
    triage = TriageResult(
        fault_kind=FaultKind.traffic_surge,
        root_cause="Worker pool exhaustion",
        confidence=0.94,
        reasoning="Requests queuing",
        what_broke="mock_app API",
        why_it_broke="Under-provisioned workers for surge",
        what_changed_recently="Incoming traffic increased 5x",
        blast_radius=BlastRadius.medium,
        affected_services=["mock_app", "ingress-gateway"],
    )
    plan = RemediationPlan(
        mitigation=ProposedAction(
            action=ActionType.scale_out,
            workers=4,
            reason="Scale out to 4 workers",
            target="mock_app",
        ),
        blast_radius=BlastRadius.low,
        rollback_strategy="Scale workers back to 2",
        expected_impact="Restores latency to <50ms",
    )
    state = initial_state(incident)
    state["triage"] = triage
    state["plan"] = plan
    state["applied"] = True
    state["policy_verdict"] = PolicyVerdict(decision=PolicyDecision.allow)

    sink = FakeSink()
    registry = FakeRegistry()

    res = await report_node(state, sink=sink, registry=registry)
    report = res["report"]

    assert report.what_broke == "mock_app API"
    assert report.why_it_broke == "Under-provisioned workers for surge"
    assert report.what_changed_recently == "Incoming traffic increased 5x"
    assert report.blast_radius == BlastRadius.low
    assert report.affected_services == ["mock_app", "ingress-gateway"]
    assert report.rollback_strategy == "Scale workers back to 2"
    assert report.expected_impact == "Restores latency to <50ms"

    # Verify JSON serialization for Postgres / REST API
    serialized = report.model_dump(mode="json")
    assert serialized["what_broke"] == "mock_app API"
    assert serialized["why_it_broke"] == "Under-provisioned workers for surge"
    assert serialized["what_changed_recently"] == "Incoming traffic increased 5x"
    assert serialized["blast_radius"] == "low"
    assert serialized["rollback_strategy"] == "Scale workers back to 2"
    assert serialized["expected_impact"] == "Restores latency to <50ms"
