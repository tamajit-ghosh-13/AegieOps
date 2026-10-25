"""Deterministic, deny-by-default, stateful policy engine (ADR-0004).

Seven ordered rules over the typed action catalog, sandbox evidence, triage
confidence, and action history. No LLM, no wall clock inside rules (clock is
injected), no randomness — every verdict is reproducible and auditable.
"""

from __future__ import annotations

import time
from collections import deque
from pathlib import PurePosixPath
from typing import Any, Callable

from pydantic import ValidationError

from agent.actions import CATALOG, ActionType, BlastRadius, ProposedAction
from agent.state import PolicyDecision, PolicyVerdict, SandboxResult, TriageResult

CONFIDENCE_FLOOR = 0.7
FLAP_WINDOW_S = 600.0
FLAP_MAX_APPLIES = 2
RATE_WINDOW_S = 3600.0
RATE_MAX_AUTO_APPLIES = 5
ALLOWED_PATH_PREFIXES = ("mock_app/",)
PROTECTED_PATHS = (
    "docker-compose.yml", "policy/", "agent/", ".env",
    "stream/", "retrieval/", "sandbox/", "hitl/", "apply/",
)
MAX_PATCH_LINES = 80
KNOWN_TARGETS = frozenset({"mock_app", "mock-app"})

_SEVERITY = {PolicyDecision.allow: 0, PolicyDecision.needs_approval: 1, PolicyDecision.block: 2}


class PolicyEngine:
    def __init__(
        self,
        clock: Callable[[], float] = time.time,
        circuit_breaker: Any = None,
    ) -> None:
        self._clock = clock
        self._circuit_breaker = circuit_breaker
        self._applies: deque[tuple[str, str, float]] = deque()  # (action, target, ts)
        self._auto_applies: deque[float] = deque()

    def evaluate(
        self,
        *,
        proposal: ProposedAction | dict[str, Any],
        sandbox: SandboxResult | None,
        triage: TriageResult | None,
    ) -> PolicyVerdict:
        # Rule 1 — deny-by-default: anything that does not parse into the
        # typed catalog is blocked. The only rule that short-circuits.
        if not isinstance(proposal, ProposedAction):
            try:
                proposal = ProposedAction.model_validate(proposal)
            except ValidationError as exc:
                return PolicyVerdict(
                    decision=PolicyDecision.block,
                    violated_rules=["deny_by_default"],
                    reasons=[f"proposal does not parse into the action catalog: {exc.errors()[0]['msg']}"],
                )

        # Rule 1 (cont.) — deny-by-default also covers targets: an action aimed
        # at a service we do not manage is outside the catalog's contract.
        if proposal.target not in KNOWN_TARGETS:
            return PolicyVerdict(
                decision=PolicyDecision.block,
                violated_rules=["deny_by_default"],
                reasons=[f"target {proposal.target!r} is not a known service"],
            )

        # Escalate is the safe terminal hand-off to a human: it executes
        # nothing, so no further rule applies. Deliberate, not an oversight.
        if proposal.action is ActionType.escalate:
            return PolicyVerdict(
                decision=PolicyDecision.allow, violated_rules=[],
                reasons=["escalate: terminal hand-off to a human"],
            )

        meta = CATALOG[proposal.action]
        violations: list[tuple[str, str, PolicyDecision]] = []

        # Rule 2 — sandbox proof required
        if sandbox is None or not sandbox.passed:
            detail = "no sandbox verification was run" if sandbox is None else "sandbox verification failed"
            violations.append(("sandbox_proof_required", detail, PolicyDecision.needs_approval))

        # Rule 3 — irreversibility gate
        if not meta.reversible or meta.requires_approval:
            violations.append((
                "irreversibility_gate",
                f"{proposal.action.value} is irreversible or catalog-flagged for approval",
                PolicyDecision.needs_approval,
            ))

        # Rule 4 — confidence floor
        confidence = triage.confidence if triage is not None else 0.0
        if confidence < CONFIDENCE_FLOOR:
            violations.append((
                "confidence_floor",
                f"triage confidence {confidence:.2f} below floor {CONFIDENCE_FLOOR}",
                PolicyDecision.needs_approval,
            ))

        # Rule 5 — flap protection (stateful; Task 3)
        violations.extend(self._flap_violations(proposal))

        # Rule 6 — rate limit circuit (stateful; Task 3)
        violations.extend(self._rate_violations())

        # Rule 7 — patch rules
        if proposal.action is ActionType.patch_code:
            violations.extend(self._patch_violations(proposal))

        blast_radius = meta.blast_radius
        if triage and triage.blast_radius is not None:
            if triage.blast_radius == BlastRadius.high or blast_radius == BlastRadius.high:
                blast_radius = BlastRadius.high
            elif triage.blast_radius == BlastRadius.medium and blast_radius != BlastRadius.high:
                blast_radius = BlastRadius.medium

        if not violations:
            risk = (
                f"Action {proposal.action.value} is reversible with {blast_radius.value} blast radius "
                f"and triage confidence {confidence:.2f} >= {CONFIDENCE_FLOOR}. Authorized for auto-apply."
            )
            return PolicyVerdict(
                decision=PolicyDecision.allow,
                violated_rules=[],
                reasons=[],
                blast_radius=blast_radius,
                risk_assessment=risk,
            )
        decision = max((v[2] for v in violations), key=_SEVERITY.__getitem__)
        risk = (
            f"Action {proposal.action.value} requires operator authorization due to: {', '.join(v[0] for v in violations)}."
            if decision == PolicyDecision.needs_approval
            else f"Action {proposal.action.value} blocked due to critical safety rule violations: {', '.join(v[0] for v in violations)}."
        )
        return PolicyVerdict(
            decision=decision,
            violated_rules=[v[0] for v in violations],
            reasons=[f"{v[0]}: {v[1]}" for v in violations],
            blast_radius=blast_radius,
            risk_assessment=risk,
        )

    def _patch_violations(self, proposal: ProposedAction) -> list[tuple[str, str, PolicyDecision]]:
        out: list[tuple[str, str, PolicyDecision]] = []
        tgt = proposal.target_file or ""
        if "\\" in tgt or ".." in PurePosixPath(tgt).parts:
            out.append((
                "patch_protected_path",
                f"{tgt!r} uses path traversal or non-portable separators",
                PolicyDecision.block,
            ))
        elif any(tgt.startswith(p) for p in PROTECTED_PATHS):
            out.append(("patch_protected_path", f"{tgt!r} is a protected control-plane path", PolicyDecision.block))
        elif not any(tgt.startswith(p) for p in ALLOWED_PATH_PREFIXES):
            out.append(("patch_path_allowlist", f"{tgt!r} outside allowlisted paths", PolicyDecision.needs_approval))
        if (proposal.patch or "").count("\n") > MAX_PATCH_LINES:
            out.append(("patch_size_cap", f"patch exceeds {MAX_PATCH_LINES} lines", PolicyDecision.needs_approval))
        return out

    def _flap_violations(self, proposal: ProposedAction) -> list[tuple[str, str, PolicyDecision]]:
        if self._circuit_breaker is not None:
            flapping, reason = self._circuit_breaker.is_service_flapping(
                proposal.target, action=proposal.action.value, timestamp=self._clock()
            )
            if flapping:
                return [("flap_protection", reason or "Flap protection cooldown active", PolicyDecision.block)]
            return []

        cutoff = self._clock() - FLAP_WINDOW_S
        while self._applies and self._applies[0][2] < cutoff:
            self._applies.popleft()
        key = (proposal.action.value, proposal.target)
        count = sum(1 for a, t, _ in self._applies if (a, t) == key)
        if count >= FLAP_MAX_APPLIES:
            return [(
                "flap_protection",
                f"{proposal.action.value} on {proposal.target!r} applied "
                f"{count}x within {int(FLAP_WINDOW_S)}s cooldown",
                PolicyDecision.block,
            )]
        return []

    def _rate_violations(self) -> list[tuple[str, str, PolicyDecision]]:
        if self._circuit_breaker is not None:
            tripped, reason = self._circuit_breaker.is_global_circuit_tripped(timestamp=self._clock())
            if tripped:
                return [("rate_limit", reason or "Global circuit breaker tripped", PolicyDecision.needs_approval)]
            return []

        cutoff = self._clock() - RATE_WINDOW_S
        while self._auto_applies and self._auto_applies[0] < cutoff:
            self._auto_applies.popleft()
        if len(self._auto_applies) >= RATE_MAX_AUTO_APPLIES:
            return [(
                "rate_limit",
                f"circuit open: {len(self._auto_applies)} auto-applies within "
                f"{int(RATE_WINDOW_S)}s (max {RATE_MAX_AUTO_APPLIES})",
                PolicyDecision.needs_approval,
            )]
        return []

    def record_apply(self, proposal: ProposedAction, decision: PolicyDecision) -> None:
        now = self._clock()
        self._applies.append((proposal.action.value, proposal.target, now))
        if decision is PolicyDecision.allow:
            self._auto_applies.append(now)
        if self._circuit_breaker is not None:
            self._circuit_breaker.record_action(proposal.target, proposal.action.value, timestamp=now)
