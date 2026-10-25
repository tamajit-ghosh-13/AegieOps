"""Unified observability hub (AegisOps Sprint 2).

Aggregates Prometheus RED metrics, Jaeger distributed traces, dynamic service
topology, and CI/CD deployment change intelligence into a single real-time
observability control plane.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from observability.deployments import (
    DeploymentCorrelation,
    DeploymentEvent,
    DeploymentIntelligenceStore,
    get_deployment_store,
)
from observability.jaeger import JaegerClient, TraceSummary
from observability.k8s_topology import DynamicTopologyEngine, get_dynamic_topology_engine
from observability.prometheus import PrometheusScraper, REDMetrics
from observability.topology import TopologySnapshot, build_topology


class SystemTelemetrySnapshot(BaseModel):
    timestamp: str
    red_metrics: REDMetrics
    topology: TopologySnapshot
    recent_traces: list[TraceSummary] = Field(default_factory=list)
    failing_traces_count: int = 0
    active_anomalies: list[str] = Field(default_factory=list)
    recent_deployments: list[DeploymentEvent] = Field(default_factory=list)
    correlated_deployments: list[DeploymentCorrelation] = Field(default_factory=list)


class ObservabilityHub:
    def __init__(
        self,
        scraper: PrometheusScraper | None = None,
        jaeger: JaegerClient | None = None,
        topology_engine: DynamicTopologyEngine | None = None,
        deployment_store: DeploymentIntelligenceStore | None = None,
    ) -> None:
        self.scraper = scraper or PrometheusScraper()
        self.jaeger = jaeger or JaegerClient()
        self.topology_engine = topology_engine or get_dynamic_topology_engine()
        self.deployment_store = deployment_store or get_deployment_store()

    async def get_snapshot(self, trace_limit: int = 5) -> SystemTelemetrySnapshot:
        """Fetch real-time unified telemetry snapshot across all observability signals."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Concurrent async fetch of Prometheus RED metrics and Jaeger traces
        red_task = asyncio.create_task(self.scraper.get_red_metrics())
        trace_task = asyncio.create_task(self.jaeger.get_recent_traces(service="aegis-agent", limit=trace_limit))

        red_metrics, recent_traces = await asyncio.gather(red_task, trace_task, return_exceptions=True)

        if isinstance(red_metrics, Exception):
            red_metrics = REDMetrics()
        if isinstance(recent_traces, Exception):
            recent_traces = []

        # Dynamic topology evaluation with runtime trace dependency discovery
        topology = await self.topology_engine.build_dynamic_topology(red=red_metrics, discover_traces=True)
        failing_count = sum(1 for t in recent_traces if t.has_error)

        # Ingest recent CI/CD deployments and correlate with active state
        recent_deps = self.deployment_store.get_recent(limit=10)
        correlated = self.deployment_store.correlate_incident(
            incident_time=now,
            affected_services=["mock_app", "mock-app"],
            dependency_services=self.topology_engine.get_downstream_dependencies("mock-app"),
        )

        return SystemTelemetrySnapshot(
            timestamp=now_iso,
            red_metrics=red_metrics,
            topology=topology,
            recent_traces=recent_traces,
            failing_traces_count=failing_count,
            active_anomalies=topology.active_anomalies,
            recent_deployments=recent_deps,
            correlated_deployments=correlated,
        )


_HUB: ObservabilityHub | None = None


def get_observability_hub() -> ObservabilityHub:
    global _HUB
    if _HUB is None:
        _HUB = ObservabilityHub()
    return _HUB
