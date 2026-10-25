"""Service topology and dependency graph engine (AegisOps Slice 2).

Maintains a real-time topology map of services, databases, and dependencies,
dynamically updating health status from live telemetry.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from observability.prometheus import REDMetrics


class HealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    failing = "failing"


class ServiceNode(BaseModel):
    id: str
    name: str
    type: str  # "gateway", "service", "database", "cache"
    status: HealthStatus = HealthStatus.healthy
    latency_ms: float = 0.0
    error_rate_pct: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DependencyEdge(BaseModel):
    id: str
    source: str
    target: str
    protocol: str  # "HTTP", "TCP/Postgres", "RESP/Redis"
    status: HealthStatus = HealthStatus.healthy
    latency_ms: float = 0.0
    call_volume: int = 0


class TopologySnapshot(BaseModel):
    nodes: list[ServiceNode]
    edges: list[DependencyEdge]
    overall_status: HealthStatus = HealthStatus.healthy
    active_anomalies: list[str] = Field(default_factory=list)


def build_topology(red: REDMetrics | None = None) -> TopologySnapshot:
    """Build dynamic service dependency graph evaluating health against live RED metrics."""
    from observability.k8s_topology import get_dynamic_topology_engine
    return get_dynamic_topology_engine().build_topology_sync(red)

