"""Unit tests for TelemetrySentinel (AegisOps Dual-Signal Detection)."""

from __future__ import annotations

import pytest

from observability.hub import SystemTelemetrySnapshot
from observability.prometheus import REDMetrics
from observability.sentinel import TelemetrySentinel
from observability.topology import HealthStatus, ServiceNode, TopologySnapshot
from stream.schema import FaultKind, Severity


class FakeHub:
    def __init__(self, snapshot: SystemTelemetrySnapshot) -> None:
        self.snapshot = snapshot

    async def get_snapshot(self, trace_limit: int = 5) -> SystemTelemetrySnapshot:
        return self.snapshot


@pytest.mark.asyncio
async def test_sentinel_returns_none_when_healthy():
    snapshot = SystemTelemetrySnapshot(
        timestamp="2026-10-24T10:00:00Z",
        red_metrics=REDMetrics(
            total_requests=100,
            error_count=0,
            p95_latency_ms=45.0,
            memory_rss_mb=12.0,
            active_workers=2,
        ),
        topology=TopologySnapshot(nodes=[], edges=[], overall_status=HealthStatus.healthy, active_anomalies=[]),
        recent_traces=[],
        failing_traces_count=0,
        active_anomalies=[],
    )
    sentinel = TelemetrySentinel(hub=FakeHub(snapshot))
    incident = await sentinel.check()
    assert incident is None


@pytest.mark.asyncio
async def test_sentinel_detects_latency_slo_breach():
    snapshot = SystemTelemetrySnapshot(
        timestamp="2026-10-24T10:00:00Z",
        red_metrics=REDMetrics(
            total_requests=250,
            error_count=0,
            p95_latency_ms=180.0,
            memory_rss_mb=14.0,
            active_workers=2,
            active_faults={"traffic_surge": True},
        ),
        topology=TopologySnapshot(
            nodes=[],
            edges=[],
            overall_status=HealthStatus.degraded,
            active_anomalies=["mock_app elevated latency (>100ms SLO)"],
        ),
        recent_traces=[],
        failing_traces_count=0,
        active_anomalies=["mock_app elevated latency (>100ms SLO)"],
    )
    sentinel = TelemetrySentinel(hub=FakeHub(snapshot), cooldown_s=10.0)
    incident = await sentinel.check(current_time=100.0)

    assert incident is not None
    assert incident.fault_kind == FaultKind.traffic_surge
    assert incident.severity == Severity.error
    assert incident.source == "observability.prometheus"
    assert "mock_app elevated latency" in incident.title


@pytest.mark.asyncio
async def test_sentinel_enforces_cooldown_window():
    snapshot = SystemTelemetrySnapshot(
        timestamp="2026-10-24T10:00:00Z",
        red_metrics=REDMetrics(p95_latency_ms=180.0, active_faults={"traffic_surge": True}),
        topology=TopologySnapshot(nodes=[], edges=[], active_anomalies=["latency spike"]),
        active_anomalies=["latency spike"],
    )
    sentinel = TelemetrySentinel(hub=FakeHub(snapshot), cooldown_s=10.0)

    # First check triggers incident
    inc1 = await sentinel.check(current_time=100.0)
    assert inc1 is not None

    # Immediate second check is suppressed by cooldown
    inc2 = await sentinel.check(current_time=105.0)
    assert inc2 is None

    # Check after cooldown triggers new incident
    inc3 = await sentinel.check(current_time=111.0)
    assert inc3 is not None
