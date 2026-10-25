"""Async approval gate: evidence briefs with TTL expiry (ADR-0005)."""

from __future__ import annotations

import asyncio
import os
import time

from agent.state import HitlChoice, HitlDecision
from audit.ledger import get_incident_ledger

DEFAULT_TTL_S = 600.0


def build_brief(*, incident, plan, sandbox, verdict, triage, expires_at: float) -> dict:
    """Decision brief, not raw data: everything the approver needs on one card."""
    return {
        "incident_id": incident.incident_id,
        "title": incident.title,
        "summary": incident.summary,
        "fault_kind": incident.fault_kind.value,
        "triage": triage.model_dump() if triage else None,
        "mitigation": plan.mitigation.model_dump(),
        "evidence": {
            "passed": sandbox.passed,
            "before_metrics": sandbox.before_metrics,
            "after_metrics": sandbox.after_metrics,
            "failure_reason": sandbox.failure_reason,
            "duration_ms": sandbox.duration_ms,
        } if sandbox else None,
        "policy": verdict.model_dump(),
        "durable_fix": plan.durable_fix.model_dump() if plan.durable_fix else None,
        "expires_at": expires_at,
    }


class ApprovalGate:
    def __init__(self, ttl_s: float | None = None):
        env_ttl = os.environ.get("HITL_TTL_S")
        self._ttl_s = ttl_s if ttl_s is not None else (
            float(env_ttl) if env_ttl else DEFAULT_TTL_S)
        self._pending: dict[str, asyncio.Future] = {}
        self._briefs: dict[str, dict] = {}
        self._contexts: dict[str, dict] = {}  # typed objects for promote-from-brief

    @property
    def ttl_s(self) -> float:
        return self._ttl_s

    async def request_approval(self, *, incident, plan, sandbox, verdict, triage) -> HitlDecision:
        fut: asyncio.Future[HitlDecision] = asyncio.get_running_loop().create_future()
        iid = incident.incident_id
        self._pending[iid] = fut
        brief = build_brief(
            incident=incident, plan=plan, sandbox=sandbox, verdict=verdict,
            triage=triage, expires_at=time.time() + self._ttl_s)
        self._briefs[iid] = brief
        self._contexts[iid] = {"incident": incident, "triage": triage,
                               "durable_fix": plan.durable_fix}
        get_incident_ledger().record_event(
            incident_id=iid,
            event_type="HITL_REQUESTED",
            actor="approval-gate",
            payload={
                "title": incident.title,
                "mitigation": plan.mitigation.action.value,
                "expires_at": brief["expires_at"],
            },
        )
        try:
            return await asyncio.wait_for(fut, timeout=self._ttl_s)
        except asyncio.TimeoutError:
            # Unanswered != wait forever: expiry escalates (PagerDuty model).
            decision = HitlDecision(choice=HitlChoice.expired, decided_by="ttl")
            get_incident_ledger().record_event(
                incident_id=iid,
                event_type="HITL_EXPIRED",
                actor="system-ttl",
                payload={"choice": "expired"},
            )
            return decision
        finally:
            self._pending.pop(iid, None)
            self._briefs.pop(iid, None)
            self._contexts.pop(iid, None)

    def list_pending(self) -> list[dict]:
        return list(self._briefs.values())

    def get_context(self, incident_id: str) -> dict | None:
        return self._contexts.get(incident_id)

    def get_brief(self, incident_id: str) -> dict | None:
        return self._briefs.get(incident_id)

    def resolve(self, incident_id: str, choice: HitlChoice, decided_by: str = "local-ui", note: str | None = None) -> None:
        fut = self._pending.get(incident_id)
        if fut and not fut.done():
            get_incident_ledger().record_event(
                incident_id=incident_id,
                event_type="HITL_DECIDED",
                actor=decided_by,
                payload={"choice": choice.value, "decided_by": decided_by, "note": note},
            )
            fut.set_result(HitlDecision(choice=choice, decided_by=decided_by, note=note))


_GATE: ApprovalGate | None = None


def get_approval_gate() -> ApprovalGate:
    global _GATE
    if _GATE is None:
        _GATE = ApprovalGate()
    return _GATE


def set_approval_gate(gate: ApprovalGate) -> None:
    global _GATE
    _GATE = gate

