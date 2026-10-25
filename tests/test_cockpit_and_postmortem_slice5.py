"""Slice 5 Unit Tests: SRE Cockpit, Incident Reports, and Post-Mortem Generator."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from agent.actions import ActionType, ProposedAction
from agent.state import BlastRadius, FaultKind, IncidentReport, Outcome, PolicyDecision
from dashboard.operations_data import IncidentRow
from hitl.gate import ApprovalGate
from hitl.registry import DurableFixRegistry
from hitl.web import create_hitl_app
from observability.postmortem import generate_postmortem
from dashboard.cockpit import render_cockpit_html


@pytest.fixture
def mock_incident_report():
    return IncidentReport(
        incident_id="inc-test-slice5",
        fault_kind=FaultKind.traffic_surge,
        outcome=Outcome.applied,
        mitigation_action=ActionType.scale_out,
        what_broke="High latency p95 > 200ms",
        why_it_broke="Inbound request spike exceeded 2 worker capacity",
        what_changed_recently="Marketing campaign launch",
        blast_radius=BlastRadius.high,
        affected_services=["api-gateway", "mock_app"],
        rollback_strategy="Scale down workers back to 2",
        live_verified=True,
        live_metrics_before={"p95_latency_ms": 220.0, "error_rate_pct": 0.0},
        live_metrics_after={"p95_latency_ms": 50.0, "error_rate_pct": 0.0},
        total_latency_ms=1450.0,
    )


@pytest.fixture
def mock_incident_row(mock_incident_report):
    return IncidentRow(
        incident_id="inc-test-slice5",
        fault_kind="traffic_surge",
        outcome="applied",
        created_at=datetime.now(timezone.utc),
        report=mock_incident_report,
    )


def test_postmortem_generator_structure(mock_incident_row):
    with patch("observability.postmortem.fetch_incident_rows", return_value=[mock_incident_row]):
        pm = generate_postmortem("inc-test-slice5")

    assert pm is not None
    assert pm.incident_id == "inc-test-slice5"
    assert pm.what_broke == "High latency p95 > 200ms"
    assert pm.why_it_broke == "Inbound request spike exceeded 2 worker capacity"
    assert pm.blast_radius == "high"
    assert "mock_app" in pm.affected_services
    assert pm.mitigation_action == "scale_out"
    assert pm.live_verified is True
    assert "# AegisOps SRE Incident Post-Mortem" in pm.markdown_report
    assert "## 1. Executive Summary" in pm.markdown_report
    assert "## 2. Recovery & Closed-Loop Verification" in pm.markdown_report


def test_cockpit_html_rendering():
    html_content = render_cockpit_html(cards_html="<div>Card 1</div>", fixes_html="<div>Fix 1</div>")

    assert "<!DOCTYPE html>" in html_content
    assert "AegisOps &mdash; SRE Incident Management Cockpit" in html_content
    assert 'id="root"' in html_content
    assert "Card 1" in html_content
    assert "Fix 1" in html_content
    assert "admin@aegisops.io" in html_content
    assert "sre@aegisops.io" in html_content
    assert "viewer@aegisops.io" in html_content


def test_api_reports_and_postmortem_endpoints(mock_incident_row):
    gate = ApprovalGate()
    registry = DurableFixRegistry()
    app = create_hitl_app(gate, registry)
    client = TestClient(app)

    with patch("dashboard.operations_data.fetch_incident_rows", return_value=[mock_incident_row]), \
         patch("observability.postmortem.fetch_incident_rows", return_value=[mock_incident_row]):
        resp_reports = client.get("/api/observability/reports")
        assert resp_reports.status_code == 200
        data = resp_reports.json()
        assert len(data) == 1
        assert data[0]["incident_id"] == "inc-test-slice5"
        assert data[0]["report"]["blast_radius"] == "high"

        resp_pm = client.get("/api/observability/postmortem/inc-test-slice5")
        assert resp_pm.status_code == 200
        pm_data = resp_pm.json()
        assert pm_data["incident_id"] == "inc-test-slice5"
        assert pm_data["what_broke"] == "High latency p95 > 200ms"
        assert "# AegisOps SRE Incident Post-Mortem" in pm_data["markdown_report"]


def test_api_postmortem_not_found():
    gate = ApprovalGate()
    registry = DurableFixRegistry()
    app = create_hitl_app(gate, registry)
    client = TestClient(app)

    with patch("dashboard.operations_data.fetch_incident_rows", return_value=[]):
        resp = client.get("/api/observability/postmortem/non-existent-inc")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_controls_fault_trigger_and_clear():
    from unittest.mock import AsyncMock
    from httpx import AsyncClient, ASGITransport

    gate = ApprovalGate()
    registry = DurableFixRegistry()
    app = create_hitl_app(gate, registry)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "fault": "traffic_surge"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/observability/controls/fault",
                json={"kind": "traffic_surge", "action": "trigger"},
            )
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok", "fault": "traffic_surge"}
            assert mock_post.called
