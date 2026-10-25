"""Unit and integration tests for Full-Stack Observability & Topology Engine (AegisOps Slice 2)."""

import pytest
import httpx
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from hitl.gate import ApprovalGate
from hitl.registry import DurableFixRegistry
from hitl.web import create_hitl_app
from observability.hub import ObservabilityHub
from observability.jaeger import JaegerClient
from observability.prometheus import PrometheusScraper, parse_prometheus_text, REDMetrics
from observability.topology import HealthStatus, build_topology


SAMPLE_PROMETHEUS_OUTPUT = """\
# HELP http_requests_total Total number of HTTP requests processed
# TYPE http_requests_total counter
http_requests_total{endpoint="/work",status="200"} 80
http_requests_total{endpoint="/work",status="500"} 20

# HELP http_request_duration_ms Current p95 request duration in milliseconds
# TYPE http_request_duration_ms gauge
http_request_duration_ms 165.5

# HELP app_memory_rss_mb Process resident memory set size in megabytes
# TYPE app_memory_rss_mb gauge
app_memory_rss_mb 16.2

# HELP app_db_lock_wait_ms Database lock wait time in milliseconds
# TYPE app_db_lock_wait_ms gauge
app_db_lock_wait_ms 350.0

# HELP app_active_workers Number of active worker processes
# TYPE app_active_workers gauge
app_active_workers 4
app_feature_flag_status{name="risky_feature"} 1
app_fault_active{kind="traffic_surge"} 1
"""


def test_parse_prometheus_text():
    metrics = parse_prometheus_text(SAMPLE_PROMETHEUS_OUTPUT)
    assert len(metrics) >= 6
    req_200 = next(m for m in metrics if m.name == "http_requests_total" and m.labels.get("status") == "200")
    assert req_200.value == 80.0
    req_500 = next(m for m in metrics if m.name == "http_requests_total" and m.labels.get("status") == "500")
    assert req_500.value == 20.0


@pytest.mark.asyncio
async def test_prometheus_scraper_calculates_red_metrics():
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(200, text=SAMPLE_PROMETHEUS_OUTPUT)
    scraper = PrometheusScraper(metrics_url="http://mock:8000/metrics", client=mock_client)

    red = await scraper.get_red_metrics()
    assert red.total_requests == 100
    assert red.error_count == 20
    assert red.error_rate_pct == 20.0
    assert red.p95_latency_ms == 165.5
    assert red.memory_rss_mb == 16.2
    assert red.db_lock_wait_ms == 350.0
    assert red.active_workers == 4
    assert red.feature_flags.get("risky_feature") is True
    assert red.active_faults.get("traffic_surge") is True


def test_build_topology_evaluates_health_correctly():
    # Baseline
    normal_red = REDMetrics(p95_latency_ms=50.0, memory_rss_mb=8.0, db_lock_wait_ms=0.0)
    topo_normal = build_topology(normal_red)
    assert topo_normal.overall_status == HealthStatus.healthy
    assert len(topo_normal.nodes) == 4
    assert len(topo_normal.edges) == 3

    # Anomaly: High Latency & High Lock Wait
    degraded_red = REDMetrics(p95_latency_ms=220.0, db_lock_wait_ms=600.0)
    topo_degraded = build_topology(degraded_red)
    assert topo_degraded.overall_status == HealthStatus.failing
    app_node = next(n for n in topo_degraded.nodes if n.id == "mock-app")
    assert app_node.status == HealthStatus.degraded
    db_node = next(n for n in topo_degraded.nodes if n.id == "postgres-db")
    assert db_node.status == HealthStatus.failing
    assert len(topo_degraded.active_anomalies) >= 2


def test_jaeger_client_parses_raw_trace():
    client = JaegerClient()
    raw_trace = {
        "traceID": "trace-123",
        "spans": [
            {
                "spanID": "span-1",
                "operationName": "agent.process",
                "startTime": 1000,
                "duration": 50000,
                "tags": [{"key": "incident_id", "value": "inc-1"}],
                "references": [],
            },
            {
                "spanID": "span-2",
                "operationName": "work.endpoint",
                "startTime": 1200,
                "duration": 20000,
                "tags": [{"key": "error", "value": True}, {"key": "http.status_code", "value": 500}],
                "references": [{"refType": "CHILD_OF", "spanID": "span-1"}],
            },
        ],
    }
    trace_summary = client._parse_trace(raw_trace)
    assert trace_summary.trace_id == "trace-123"
    assert trace_summary.span_count == 2
    assert trace_summary.has_error is True
    assert len(trace_summary.failing_spans) == 1
    assert trace_summary.failing_spans[0].span_id == "span-2"


@pytest.mark.asyncio
async def test_observability_hub_get_snapshot():
    mock_scraper = AsyncMock()
    mock_scraper.get_red_metrics.return_value = REDMetrics(p95_latency_ms=70.0)

    mock_jaeger = AsyncMock()
    mock_jaeger.get_recent_traces.return_value = []

    hub = ObservabilityHub(scraper=mock_scraper, jaeger=mock_jaeger)
    snapshot = await hub.get_snapshot()

    assert snapshot.red_metrics.p95_latency_ms == 70.0
    assert snapshot.topology.overall_status == HealthStatus.healthy
    assert snapshot.failing_traces_count == 0


def test_fastapi_observability_routes():
    app = create_hitl_app(ApprovalGate(), DurableFixRegistry())
    client = TestClient(app)

    # Topology endpoint
    resp = client.get("/api/observability/topology")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 4

    # Metrics endpoint
    resp_metrics = client.get("/api/observability/metrics")
    assert resp_metrics.status_code == 200
    m_data = resp_metrics.json()
    assert "p95_latency_ms" in m_data
