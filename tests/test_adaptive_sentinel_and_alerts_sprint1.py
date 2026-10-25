"""Sprint 1 Unit Tests: Adaptive Statistical Sentinel & Multi-Source Alert Ingestion Gateway."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from hitl.gate import ApprovalGate
from hitl.registry import DurableFixRegistry
from hitl.web import create_hitl_app
from observability.adaptive_sentinel import (
    AdaptiveBaselineDetector,
    AdaptiveTelemetrySentinel,
    MetricSample,
)
from observability.alerts_gateway import (
    AlertIngestionGateway,
    AlertmanagerAlertItem,
    AlertmanagerWebhookPayload,
    PagerDutyIncident,
    PagerDutyMessage,
    PagerDutyWebhookPayload,
)
from stream.schema import FaultKind, Severity


# ==============================================================================
# 1. Tests for AdaptiveBaselineDetector (EWMA, Z-Score, IQR)
# ==============================================================================

def test_detector_warmup():
    detector = AdaptiveBaselineDetector(min_samples=5)
    for _ in range(4):
        sample = MetricSample(
            timestamp=time.time(),
            p95_latency_ms=50.0,
            error_rate_pct=0.0,
            rate_rps=10.0,
            memory_rss_mb=10.0,
            db_lock_wait_ms=0.0,
        )
        diag = detector.evaluate_sample(sample)
        assert diag.is_anomaly is False
        assert "Warming up" in diag.explanation


def test_detector_nominal_traffic():
    detector = AdaptiveBaselineDetector(min_samples=5)
    # Prime baseline around 50ms
    for _ in range(10):
        sample = MetricSample(
            timestamp=time.time(),
            p95_latency_ms=50.0,
            error_rate_pct=0.0,
            rate_rps=10.0,
            memory_rss_mb=10.0,
            db_lock_wait_ms=0.0,
        )
        diag = detector.evaluate_sample(sample)

    assert diag.is_anomaly is False
    assert diag.baseline_mean == pytest.approx(50.0, abs=1.0)


def test_detector_catches_latency_step_change():
    detector = AdaptiveBaselineDetector(min_samples=5, z_threshold=2.5)
    # 1. Establish baseline at 50ms
    for _ in range(15):
        detector.evaluate_sample(
            MetricSample(
                timestamp=time.time(),
                p95_latency_ms=50.0,
                error_rate_pct=0.0,
                rate_rps=15.0,
                memory_rss_mb=12.0,
                db_lock_wait_ms=0.0,
            )
        )

    # 2. Step jump to 210ms under heavy load (15 rps)
    surge_sample = MetricSample(
        timestamp=time.time(),
        p95_latency_ms=210.0,
        error_rate_pct=0.0,
        rate_rps=15.0,
        memory_rss_mb=12.0,
        db_lock_wait_ms=0.0,
    )
    diag = detector.evaluate_sample(surge_sample)

    assert diag.is_anomaly is True
    assert diag.fault_kind == FaultKind.traffic_surge
    assert diag.severity == Severity.critical
    assert diag.z_score >= 2.5
    assert "Adaptive anomaly on p95 latency" in diag.explanation


def test_detector_low_qps_noise_suppression():
    """Ensures low-traffic periods with high variance don't cause false positives."""
    detector = AdaptiveBaselineDetector(min_samples=5, z_threshold=3.0)
    for _ in range(10):
        detector.evaluate_sample(
            MetricSample(
                timestamp=time.time(),
                p95_latency_ms=50.0,
                error_rate_pct=0.0,
                rate_rps=0.5,  # Very low QPS (1 request every 2s)
                memory_rss_mb=10.0,
                db_lock_wait_ms=0.0,
            )
        )

    # Mild bump under near-zero traffic should have reduced effective Z
    mild_bump = MetricSample(
        timestamp=time.time(),
        p95_latency_ms=68.0,
        error_rate_pct=0.0,
        rate_rps=0.5,
        memory_rss_mb=10.0,
        db_lock_wait_ms=0.0,
    )
    diag = detector.evaluate_sample(mild_bump)
    assert diag.is_anomaly is False


def test_detector_error_spike_and_db_deadlock():
    detector = AdaptiveBaselineDetector(min_samples=5)
    for _ in range(10):
        detector.evaluate_sample(
            MetricSample(
                timestamp=time.time(),
                p95_latency_ms=45.0,
                error_rate_pct=0.1,
                rate_rps=10.0,
                memory_rss_mb=10.0,
                db_lock_wait_ms=0.0,
            )
        )

    # Test error rate anomaly
    err_diag = detector.evaluate_sample(
        MetricSample(
            timestamp=time.time(),
            p95_latency_ms=45.0,
            error_rate_pct=12.5,
            rate_rps=10.0,
            memory_rss_mb=10.0,
            db_lock_wait_ms=0.0,
        )
    )
    assert err_diag.is_anomaly is True
    assert err_diag.fault_kind == FaultKind.error_spike

    # Test deadlock anomaly
    deadlock_diag = detector.evaluate_sample(
        MetricSample(
            timestamp=time.time(),
            p95_latency_ms=45.0,
            error_rate_pct=0.0,
            rate_rps=10.0,
            memory_rss_mb=10.0,
            db_lock_wait_ms=250.0,
        )
    )
    assert deadlock_diag.is_anomaly is True
    assert deadlock_diag.fault_kind == FaultKind.db_deadlock


# ==============================================================================
# 2. Tests for AdaptiveTelemetrySentinel Orchestration
# ==============================================================================

@pytest.mark.asyncio
async def test_adaptive_sentinel_produces_incident_and_cooldown():
    mock_hub = MagicMock()
    mock_snapshot = MagicMock()
    mock_snapshot.red_metrics.p95_latency_ms = 220.0
    mock_snapshot.red_metrics.error_rate_pct = 0.0
    mock_snapshot.red_metrics.rate_rps = 10.0
    mock_snapshot.red_metrics.memory_rss_mb = 10.0
    mock_snapshot.red_metrics.db_lock_wait_ms = 0.0
    mock_hub.get_snapshot = AsyncMock(return_value=mock_snapshot)

    detector = AdaptiveBaselineDetector(min_samples=2)
    # Prime detector
    detector.evaluate_sample(MetricSample(time.time(), 50.0, 0.0, 10.0, 10.0, 0.0))
    detector.evaluate_sample(MetricSample(time.time(), 50.0, 0.0, 10.0, 10.0, 0.0))

    sentinel = AdaptiveTelemetrySentinel(hub=mock_hub, detector=detector, cooldown_s=15.0)

    # First check triggers incident
    inc = await sentinel.check(current_time=100.0)
    assert inc is not None
    assert inc.fault_kind == FaultKind.traffic_surge
    assert "Adaptive Baseline Anomaly" in inc.title

    # Immediate second check is suppressed by cooldown
    inc2 = await sentinel.check(current_time=105.0)
    assert inc2 is None

    # After cooldown expires, triggers again
    inc3 = await sentinel.check(current_time=120.0)
    assert inc3 is not None


# ==============================================================================
# 3. Tests for Multi-Source Alert Ingestion Gateway (Alertmanager & PagerDuty)
# ==============================================================================

def test_alertmanager_ingestion_and_dedup():
    gateway = AlertIngestionGateway(dedup_window_s=60.0)

    payload = AlertmanagerWebhookPayload(
        status="firing",
        alerts=[
            AlertmanagerAlertItem(
                status="firing",
                labels={"alertname": "CoreAPILatencySpike", "service": "mock_app", "severity": "critical"},
                annotations={"summary": "p95 latency exceeded dynamic threshold"},
            ),
            # Resolved alert should be skipped
            AlertmanagerAlertItem(
                status="resolved",
                labels={"alertname": "OldResolvedAlert", "service": "mock_app"},
                annotations={"summary": "All clear"},
            ),
        ],
    )

    emitted = gateway.ingest_alertmanager(payload)
    assert len(emitted) == 1
    assert emitted[0].fault_kind == FaultKind.traffic_surge
    assert emitted[0].severity == Severity.critical
    assert "CoreAPILatencySpike" in emitted[0].title
    assert gateway.has_pending_alerts() is True

    # Duplicate firing alert sent 5s later should be suppressed by dedup window
    emitted_dupe = gateway.ingest_alertmanager(payload)
    assert len(emitted_dupe) == 0


def test_pagerduty_ingestion():
    gateway = AlertIngestionGateway(dedup_window_s=60.0)

    pd_payload = PagerDutyWebhookPayload(
        messages=[
            PagerDutyMessage(
                event="incident.trigger",
                incident=PagerDutyIncident(
                    id="PD12345",
                    title="Database Deadlock detected on customer-db",
                    urgency="high",
                    status="triggered",
                    service={"name": "postgres_db"},
                ),
            )
        ]
    )

    events = gateway.ingest_pagerduty(pd_payload)
    assert len(events) == 1
    assert events[0].fault_kind == FaultKind.db_deadlock
    assert events[0].source == "pagerduty:postgres_db"
    assert "Database Deadlock" in events[0].title


# ==============================================================================
# 4. Tests for FastAPI Webhook Endpoints
# ==============================================================================

def test_api_alert_webhooks():
    gate = ApprovalGate()
    registry = DurableFixRegistry()
    app = create_hitl_app(gate, registry)
    client = TestClient(app)

    # Test Alertmanager endpoint
    am_data = {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighMemoryLeak", "service": "mock_app", "severity": "warning"},
                "annotations": {"summary": "RSS memory steadily rising"},
            }
        ],
    }
    resp_am = client.post("/api/observability/alerts/webhook/alertmanager", json=am_data)
    assert resp_am.status_code == 200
    res_json = resp_am.json()
    assert res_json["status"] == "received"
    assert res_json["processed_count"] == 1

    # Test PagerDuty endpoint
    pd_data = {
        "messages": [
            {
                "event": "incident.trigger",
                "incident": {
                    "id": "PD-TEST-1",
                    "title": "Error Spike: HTTP 500 rate elevated",
                    "urgency": "high",
                    "status": "triggered",
                    "service": {"name": "mock_app"},
                },
            }
        ]
    }
    resp_pd = client.post("/api/observability/alerts/webhook/pagerduty", json=pd_data)
    assert resp_pd.status_code == 200
    assert resp_pd.json()["status"] == "received"

    # Test listing recent alerts
    resp_recent = client.get("/api/observability/alerts/recent")
    assert resp_recent.status_code == 200
    recent = resp_recent.json()
    assert len(recent) >= 2
