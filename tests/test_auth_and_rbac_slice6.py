"""Unit tests for Team Authentication, RBAC & Operator Attribution (AegisOps Slice 6)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent.actions import ActionType, BlastRadius, ProposedAction
from agent.state import HitlChoice, RemediationPlan, SandboxResult, TriageResult
from auth.models import Role, User
from auth.security import create_access_token, decode_access_token, hash_password, verify_password
from auth.service import AuthService, get_auth_service
from hitl.gate import ApprovalGate
from hitl.registry import DurableFixRegistry
from hitl.web import create_hitl_app
from policy.engine import PolicyEngine
from stream.schema import FaultKind, IncidentEvent, Severity
from tests.test_agent_nodes import make_incident


def test_password_hashing_and_verification():
    raw = "MySecurePassword2026!"
    hashed, salt = hash_password(raw)
    assert hashed != raw
    assert len(salt) == 32
    assert verify_password(raw, hashed, salt) is True
    assert verify_password("WrongPassword", hashed, salt) is False


def test_jwt_token_roundtrip():
    payload = {"sub": "usr-123", "email": "test@aegisops.io", "role": "admin", "team_id": "team-infra"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr-123"
    assert decoded["email"] == "test@aegisops.io"
    assert decoded["role"] == "admin"


def test_auth_service_personas():
    service = AuthService()

    admin = service.authenticate("admin@aegisops.io", "admin123")
    assert admin is not None
    assert admin.role == Role.admin
    assert admin.team_id == "team-core-infra"

    sre = service.authenticate("sre@aegisops.io", "sre123")
    assert sre is not None
    assert sre.role == Role.responder

    viewer = service.authenticate("viewer@aegisops.io", "viewer123")
    assert viewer is not None
    assert viewer.role == Role.viewer

    invalid = service.authenticate("admin@aegisops.io", "wrongpassword")
    assert invalid is None


def test_rbac_approval_matrix():
    service = AuthService()
    admin = service.authenticate("admin@aegisops.io", "admin123")
    sre = service.authenticate("sre@aegisops.io", "sre123")
    viewer = service.authenticate("viewer@aegisops.io", "viewer123")

    # Viewer cannot approve anything
    ok, reason = service.can_approve(viewer, action="scale_out", blast_radius="low")
    assert ok is False
    assert "Viewers have read-only access" in reason

    # Responder can approve low/medium actions
    ok, _ = service.can_approve(sre, action="scale_out", blast_radius="low")
    assert ok is True
    ok, _ = service.can_approve(sre, action="restart_service", blast_radius="medium")
    assert ok is True

    # Responder CANNOT approve high blast-radius actions
    ok, reason = service.can_approve(sre, action="patch_code", blast_radius="high")
    assert ok is False
    assert "requires Lead SRE / Admin" in reason

    # Admin can approve high blast-radius actions
    ok, _ = service.can_approve(admin, action="patch_code", blast_radius="high")
    assert ok is True


@pytest.fixture
def client_app():
    gate = ApprovalGate()
    registry = DurableFixRegistry()
    app = create_hitl_app(gate, registry)
    client = TestClient(app)
    return client, gate, registry


def test_api_auth_login_and_me(client_app):
    client, _, _ = client_app

    # 1. Successful login
    resp = client.post("/api/auth/login", json={"email": "sre@aegisops.io", "password": "sre123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "responder"
    token = data["access_token"]

    # 2. Get /me with Bearer token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "sre@aegisops.io"

    # 3. Bad credentials
    bad_resp = client.post("/api/auth/login", json={"email": "sre@aegisops.io", "password": "bad"})
    assert bad_resp.status_code == 401


def test_api_users_requires_sre_or_admin(client_app):
    client, _, _ = client_app

    # Login as viewer
    v_resp = client.post("/api/auth/login", json={"email": "viewer@aegisops.io", "password": "viewer123"})
    v_token = v_resp.json()["access_token"]

    # Viewer forbidden from listing team users
    resp = client.get("/api/auth/users", headers={"Authorization": f"Bearer {v_token}"})
    assert resp.status_code == 403

    # Admin allowed
    a_resp = client.post("/api/auth/login", json={"email": "admin@aegisops.io", "password": "admin123"})
    a_token = a_resp.json()["access_token"]
    resp2 = client.get("/api/auth/users", headers={"Authorization": f"Bearer {a_token}"})
    assert resp2.status_code == 200
    assert len(resp2.json()) == 3


@pytest.mark.asyncio
async def test_hitl_enforces_rbac_and_operator_attribution(client_app):
    client, gate, _ = client_app
    iid = "inc-rbac-test-1"
    incident = make_incident(incident_id=iid)
    plan = RemediationPlan(
        mitigation=ProposedAction(
            action=ActionType.patch_code,
            reason="Fix code memory leak",
            patch="+fix",
            target_file="mock_app/main.py",
        ),
    )
    triage = TriageResult(
        fault_kind=FaultKind.memory_leak,
        root_cause="leak",
        confidence=0.9,
        reasoning="r",
        blast_radius=BlastRadius.high,
    )
    sandbox = SandboxResult(passed=True, exit_code=0, stdout="", stderr="", duration_ms=1.0)
    verdict = PolicyEngine().evaluate(proposal=plan.mitigation, sandbox=sandbox, triage=triage)

    # Queue pending request
    import asyncio
    task = asyncio.create_task(
        gate.request_approval(incident=incident, plan=plan, sandbox=sandbox, verdict=verdict, triage=triage)
    )
    await asyncio.sleep(0.01)

    # Login personas
    v_token = client.post("/api/auth/login", json={"email": "viewer@aegisops.io", "password": "viewer123"}).json()["access_token"]
    s_token = client.post("/api/auth/login", json={"email": "sre@aegisops.io", "password": "sre123"}).json()["access_token"]
    a_token = client.post("/api/auth/login", json={"email": "admin@aegisops.io", "password": "admin123"}).json()["access_token"]

    # 1. Viewer attempts approval -> 403 Forbidden
    res_v = client.post(
        f"/decision/{iid}",
        data={"choice": "approve"},
        headers={"Authorization": f"Bearer {v_token}"},
        follow_redirects=False,
    )
    assert res_v.status_code == 403
    assert "Viewers have read-only access" in res_v.json()["detail"]

    # 2. Responder attempts approval for patch_code (High blast radius) -> 403 Forbidden
    res_s = client.post(
        f"/decision/{iid}",
        data={"choice": "approve"},
        headers={"Authorization": f"Bearer {s_token}"},
        follow_redirects=False,
    )
    assert res_s.status_code == 403
    assert "requires Lead SRE / Admin" in res_s.json()["detail"]

    # 3. Admin approves -> 303 Redirect, operator attributed
    res_a = client.post(
        f"/decision/{iid}",
        data={"choice": "approve", "note": "Authorized code fix"},
        headers={"Authorization": f"Bearer {a_token}"},
        follow_redirects=False,
    )
    assert res_a.status_code == 303

    decision = await task
    assert decision.choice == HitlChoice.approve
    assert "admin@aegisops.io" in decision.decided_by
    assert "admin" in decision.decided_by
    assert decision.note == "Authorized code fix"
