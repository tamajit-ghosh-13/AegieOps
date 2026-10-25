"""Unit and integration tests for Sprint 2:
- Dynamic Service Mesh & Kubernetes Topology Discovery (NetworkX graph, Jaeger trace discovery, runtime node registration)
- CI/CD Deployment Intelligence & Change Correlation (GitHub Actions, ArgoCD webhooks, PostgreSQL persistence, temporal causal scoring)
- Triage prompt telemetry formatting and citation instructions
- FastAPI REST endpoints
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
from starlette.testclient import TestClient

from agent.nodes.triage import _format_telemetry, _prompt
from observability.deployments import (
    DeploymentCorrelation,
    DeploymentEvent,
    DeploymentIntelligenceStore,
    DeploymentSource,
    DeploymentStatus,
    parse_argocd_webhook,
    parse_github_webhook,
)
from observability.hub import ObservabilityHub, SystemTelemetrySnapshot
from observability.k8s_topology import DynamicTopologyEngine
from observability.prometheus import REDMetrics
from observability.router import router
from observability.topology import DependencyEdge, HealthStatus, ServiceNode, build_topology
from stream.schema import FaultKind, IncidentEvent, Severity


# ==============================================================================
# 1. Dynamic Topology Engine Tests
# ==============================================================================

def test_dynamic_topology_engine_base_and_metrics():
    engine = DynamicTopologyEngine()
    
    # Baseline
    normal_red = REDMetrics(p95_latency_ms=45.0, error_rate_pct=0.0, db_lock_wait_ms=0.0)
    topo_normal = engine.build_topology_sync(normal_red)
    assert topo_normal.overall_status == HealthStatus.healthy
    assert len(topo_normal.nodes) == 4
    assert len(topo_normal.edges) == 3

    # Anomaly injection
    failing_red = REDMetrics(p95_latency_ms=250.0, error_rate_pct=40.0, db_lock_wait_ms=300.0)
    topo_failing = engine.build_topology_sync(failing_red)
    assert topo_failing.overall_status == HealthStatus.failing
    app_node = next(n for n in topo_failing.nodes if n.id == "mock-app")
    assert app_node.status == HealthStatus.failing
    db_node = next(n for n in topo_failing.nodes if n.id == "postgres-db")
    assert db_node.status == HealthStatus.failing
    assert len(topo_failing.active_anomalies) >= 3


def test_dynamic_service_registration_and_traversal():
    engine = DynamicTopologyEngine()
    
    # Register dynamic Kubernetes mock service
    new_node = ServiceNode(
        id="k8s-billing-service",
        name="Billing Microservice (k8s)",
        type="service",
        status=HealthStatus.healthy,
        metadata={"port": 8080, "namespace": "payments", "discovered_via": "k8s_api"},
    )
    new_edge = DependencyEdge(
        id="edge-app-billing",
        source="mock-app",
        target="k8s-billing-service",
        protocol="gRPC",
        status=HealthStatus.healthy,
        call_volume=250,
    )

    engine.register_service(new_node)
    engine.register_edge(new_edge)

    snapshot = engine.build_topology_sync()
    node_ids = {n.id for n in snapshot.nodes}
    edge_ids = {e.id for e in snapshot.edges}
    assert "k8s-billing-service" in node_ids
    assert "edge-app-billing" in edge_ids

    # NetworkX Graph traversal
    downstream = engine.get_downstream_dependencies("mock-app")
    assert "k8s-billing-service" in downstream
    assert "postgres-db" in downstream
    assert "redis-cache" in downstream

    upstream = engine.get_upstream_dependencies("k8s-billing-service")
    assert "mock-app" in upstream

    # Unregister service
    engine.unregister_service("k8s-billing-service")
    snapshot_after = engine.build_topology_sync()
    assert "k8s-billing-service" not in {n.id for n in snapshot_after.nodes}
    assert "edge-app-billing" not in {e.id for e in snapshot_after.edges}


@pytest.mark.asyncio
async def test_jaeger_dependency_discovery_mock():
    engine = DynamicTopologyEngine()
    
    # Mock discover_jaeger_dependencies
    async def mock_discover():
        return [
            DependencyEdge(
                id="jaeger-mock-app->fraud-detector",
                source="mock-app",
                target="fraud-detector",
                protocol="HTTP/gRPC",
                status=HealthStatus.healthy,
                call_volume=80,
            )
        ]
    engine.discover_jaeger_dependencies = mock_discover

    snapshot = await engine.build_dynamic_topology(discover_traces=True)
    edge_ids = {e.id for e in snapshot.edges}
    node_ids = {n.id for n in snapshot.nodes}
    assert "jaeger-mock-app->fraud-detector" in edge_ids
    assert "fraud-detector" in node_ids


# ==============================================================================
# 2. CI/CD Deployment Parsers & Intelligence Store Tests
# ==============================================================================

def test_github_actions_webhook_parser():
    payload = {
        "action": "completed",
        "workflow_run": {
            "id": 98765432,
            "name": "Deploy Production App",
            "head_sha": "a1b2c3d4e5f6",
            "head_commit": {
                "id": "a1b2c3d4e5f6",
                "message": "Update database pool connection timeout",
                "author": {"name": "Devin Engineer", "email": "devin@acme.corp"},
            },
            "repository": {"name": "mock-app"},
            "conclusion": "success",
            "updated_at": "2026-10-25T12:00:00Z",
        },
        "diff_summary": "db/pool.py: -timeout=30, +timeout=1",
        "image_tag_previous": "mock-app:v2.1.0",
        "image_tag_new": "mock-app:v2.2.0",
    }
    dep = parse_github_webhook(payload)
    assert dep.service_name == "mock-app"
    assert dep.git_commit_sha == "a1b2c3d4e5f6"
    assert dep.git_author == "Devin Engineer"
    assert "pool connection timeout" in dep.git_commit_message
    assert dep.git_diff_summary == "db/pool.py: -timeout=30, +timeout=1"
    assert dep.source == DeploymentSource.GITHUB_ACTIONS
    assert dep.status == DeploymentStatus.SUCCESS


def test_argocd_webhook_parser():
    payload = {
        "app": {
            "metadata": {"name": "mock-app"},
            "spec": {"destination": {"namespace": "production"}},
            "status": {
                "sync": {"status": "Synced", "revision": "f9e8d7c6b5a4"},
                "operationState": {
                    "finishedAt": "2026-10-25T12:05:00Z",
                    "phase": "Succeeded",
                },
            },
        },
        "commit_author": "Alex Rivers <alex@corp.io>",
        "commit_message": "Refactor connection pool timeout logic",
        "diff_summary": "-max_connections=50, +max_connections=5",
        "image_tag_previous": "mock-app:v1.4.1",
        "image_tag_new": "mock-app:v1.4.2",
    }
    dep = parse_argocd_webhook(payload)
    assert dep.service_name == "mock-app"
    assert dep.git_commit_sha == "f9e8d7c6b5a4"
    assert dep.git_author == "Alex Rivers <alex@corp.io>"
    assert dep.git_commit_message == "Refactor connection pool timeout logic"
    assert dep.git_diff_summary == "-max_connections=50, +max_connections=5"
    assert dep.source == DeploymentSource.ARGOCD
    assert dep.status == DeploymentStatus.SUCCESS


def test_deployment_intelligence_store_and_temporal_correlation():
    store = DeploymentIntelligenceStore(db_enabled=False)
    now = datetime.now(timezone.utc)

    # 1. Immediate deployment 2 minutes ago on target service
    dep_immediate = DeploymentEvent(
        deployment_id="dep-1",
        service_name="mock-app",
        git_commit_sha="8f4b2a9e",
        git_author="Alex Rivers",
        git_commit_message="Refactor connection pool timeout logic",
        git_diff_summary="-max_connections=50, +max_connections=5",
        deployed_at=now - timedelta(minutes=2),
        source=DeploymentSource.ARGOCD,
    )
    store.record_deployment(dep_immediate)

    # 2. Older deployment 25 minutes ago on target service
    dep_older = DeploymentEvent(
        deployment_id="dep-2",
        service_name="mock-app",
        git_commit_sha="11223344",
        git_author="Sam Developer",
        git_commit_message="Update readme docs",
        deployed_at=now - timedelta(minutes=25),
        source=DeploymentSource.GITHUB_ACTIONS,
    )
    store.record_deployment(dep_older)

    # 3. Downstream service deployment 4 minutes ago
    dep_downstream = DeploymentEvent(
        deployment_id="dep-3",
        service_name="postgres-db",
        git_commit_sha="55667788",
        git_author="DBA Team",
        git_commit_message="Update index configuration",
        deployed_at=now - timedelta(minutes=4),
        source=DeploymentSource.MANUAL,
    )
    store.record_deployment(dep_downstream)

    # Run correlation
    correlations = store.correlate_incident(
        incident_time=now,
        affected_services=["mock_app", "mock-app"],
        dependency_services=["postgres-db"],
    )

    assert len(correlations) >= 3
    # First correlation must be the immediate deployment with highest confidence (0.95)
    c0 = correlations[0]
    assert c0.deployment.deployment_id == "dep-1"
    assert c0.confidence_score == 0.95
    assert c0.relation == "direct_service_immediate"
    assert "Alex Rivers" in c0.summary

    # Downstream correlation should be 0.70
    c_down = next(c for c in correlations if c.deployment.deployment_id == "dep-3")
    assert c_down.confidence_score == 0.70
    assert c_down.relation == "downstream_dependency"

    # Older correlation should be 0.65
    c_old = next(c for c in correlations if c.deployment.deployment_id == "dep-2")
    assert c_old.confidence_score == 0.65
    assert c_old.relation == "direct_service_window"


# ==============================================================================
# 3. Triage Telemetry Formatting & Citation Guidance Tests
# ==============================================================================

def test_format_telemetry_with_correlated_deployments():
    now = datetime.now(timezone.utc)
    dep = DeploymentEvent(
        deployment_id="dep-test-1",
        service_name="mock-app",
        git_commit_sha="8f4b2a9e1d2c",
        git_author="Alex Rivers <alex@corp.io>",
        git_commit_message="Refactor connection pool timeout logic",
        git_diff_summary="-max_connections=50, +max_connections=5",
        image_tag_previous="mock-app:v1.4.1",
        image_tag_new="mock-app:v1.4.2",
        deployed_at=now - timedelta(minutes=2, seconds=15),
        source=DeploymentSource.ARGOCD,
    )
    correlation = DeploymentCorrelation(
        deployment=dep,
        confidence_score=0.95,
        time_delta_seconds=135.0,
        time_delta_human="2m 15s before incident onset",
        relation="direct_service_immediate",
        summary="Service 'mock-app' deployed 2m 15s before incident onset",
    )

    snapshot = SystemTelemetrySnapshot(
        timestamp=now.isoformat(),
        red_metrics=REDMetrics(p95_latency_ms=220.0, error_rate_pct=15.0),
        topology=build_topology(),
        correlated_deployments=[correlation],
        recent_deployments=[dep],
    )

    formatted = _format_telemetry(snapshot)
    assert "CI/CD Change Intelligence & Correlated Deployments:" in formatted
    assert "[SUSPECTED CAUSAL DEPLOYMENT - Confidence: 95%]" in formatted
    assert "mock-app" in formatted
    assert "8f4b2a9e1d2c" in formatted
    assert "Alex Rivers <alex@corp.io>" in formatted
    assert "Refactor connection pool timeout logic" in formatted
    assert "-max_connections=50, +max_connections=5" in formatted

    # Test prompt generation includes instructions
    from stream.schema import RawEvent
    sample = RawEvent(
        event_id="evt-test-1",
        fault_kind=FaultKind.db_deadlock,
        severity=Severity.critical,
        source="alertmanager",
        message="lock wait > 500ms",
        metric=500.0,
        ts=now,
        dedup_key="dk-test-1",
    )
    incident = IncidentEvent(
        incident_id="inc-test",
        fault_kind=FaultKind.db_deadlock,
        severity=Severity.critical,
        source="alertmanager",
        title="Database lock exhaustion",
        summary="Connections exhausted",
        event_count=5,
        duplicate_count=0,
        first_seen=now.isoformat(),
        last_seen=now.isoformat(),
        correlation_window_s=60,
        sample_events=[sample],
    )
    prompt_str = _prompt(incident, snapshot)
    assert "what_changed_recently" in prompt_str
    assert "explicitly cite the commit SHA, author, and code diff" in prompt_str


# ==============================================================================
# 4. FastAPI Endpoints Integration Tests (Acceptance Criteria 1, 2, 3)
# ==============================================================================

def test_api_deployment_and_topology_endpoints():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # 1. Ingest ArgoCD Deployment
    argo_payload = {
        "application": "mock-app",
        "revision": "c7a8b9e0f1",
        "author": "Jane SRE <jane@corp.io>",
        "message": "Reduce Redis maxmemory-policy cache size",
        "diff_summary": "redis.conf: maxmemory=512mb -> maxmemory=64mb",
    }
    resp = client.post("/api/observability/events/deployments/argocd", json=argo_payload)
    assert resp.status_code == 200
    dep_data = resp.json()
    assert dep_data["service_name"] == "mock-app"
    assert dep_data["git_commit_sha"] == "c7a8b9e0f1"
    assert dep_data["git_author"] == "Jane SRE <jane@corp.io>"

    # 2. Ingest GitHub Actions Deployment
    gh_payload = {
        "service": "auth-service",
        "commit_sha": "1234abcd",
        "author": "Security Bot",
        "message": "Rotate JWT signing keys",
    }
    resp = client.post("/api/observability/events/deployments/github", json=gh_payload)
    assert resp.status_code == 200
    assert resp.json()["service_name"] == "auth-service"

    # 3. Retrieve Recent Deployments
    resp = client.get("/api/observability/events/deployments/recent?limit=5")
    assert resp.status_code == 200
    recent = resp.json()
    assert len(recent) >= 2
    assert any(d["git_commit_sha"] == "c7a8b9e0f1" for d in recent)

    # 4. Dynamic Node Registration without Restart (Acceptance Criterion 3)
    k8s_node = {
        "id": "k8s-order-service",
        "name": "Order Management Microservice (k8s)",
        "type": "service",
        "status": "healthy",
        "latency_ms": 12.0,
        "error_rate_pct": 0.0,
        "metadata": {"namespace": "ecommerce", "replicas": 3, "port": 9090},
    }
    resp = client.post("/api/observability/topology/nodes", json=k8s_node)
    assert resp.status_code == 200

    # 5. Verify node appears immediately in live topology
    resp = client.get("/api/observability/topology")
    assert resp.status_code == 200
    topo = resp.json()
    node_ids = {n["id"] for n in topo["nodes"]}
    assert "k8s-order-service" in node_ids

    # 6. Verify snapshot endpoint includes dynamic node and deployments
    resp = client.get("/api/observability/snapshot")
    assert resp.status_code == 200
    snap = resp.json()
    snap_node_ids = {n["id"] for n in snap["topology"]["nodes"]}
    assert "k8s-order-service" in snap_node_ids
    assert len(snap["recent_deployments"]) >= 1

    # Clean up node
    resp = client.delete("/api/observability/topology/nodes/k8s-order-service")
    assert resp.status_code == 200
