"""Anti-Flap Circuit Breakers & Cascading Failure Protection (AegisOps Sprint 3).

Prevents automated remediation from causing flapping remediation loops or cascading failures:
1. Per-Service Flap Protection: Max 1 automated action on the same service within 15 minutes.
2. Global Cascading Failure Circuit Breaker: If >3 distinct services trigger mitigations
   within 5 minutes, pause all auto-apply actions and escalate to human operators (HITL).
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import logging
import time
from typing import Any, Callable

from agent.state import PolicyDecision

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_COOLDOWN_S = 900.0  # 15 minutes
DEFAULT_GLOBAL_WINDOW_S = 300.0     # 5 minutes
DEFAULT_GLOBAL_THRESHOLD = 3        # >3 services


class AntiFlapCircuitBreaker:
    """Enterprise safety circuit breaker and anti-flap controller."""

    def __init__(
        self,
        service_cooldown_s: float = DEFAULT_SERVICE_COOLDOWN_S,
        global_window_s: float = DEFAULT_GLOBAL_WINDOW_S,
        global_threshold: int = DEFAULT_GLOBAL_THRESHOLD,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.service_cooldown_s = service_cooldown_s
        self.global_window_s = global_window_s
        self.global_threshold = global_threshold
        self._clock = clock

        # service_norm -> deque of (action_name, timestamp)
        self._service_actions: dict[str, deque[tuple[str, float]]] = {}
        # deque of (service_norm, timestamp)
        self._global_events: deque[tuple[str, float]] = deque()
        self._global_tripped_override: bool = False

    def _norm(self, service: str) -> str:
        return service.strip().lower().replace("-", "_")

    def record_action(
        self,
        service: str,
        action: str,
        timestamp: float | None = None,
    ) -> None:
        """Record an applied action on a service."""
        now = timestamp if timestamp is not None else self._clock()
        svc = self._norm(service)

        if svc not in self._service_actions:
            self._service_actions[svc] = deque()
        self._service_actions[svc].append((action, now))

        self._global_events.append((svc, now))
        logger.info("CircuitBreaker recorded action '%s' on '%s' at %.1f", action, svc, now)

    def is_service_flapping(
        self,
        service: str,
        action: str | None = None,
        timestamp: float | None = None,
    ) -> tuple[bool, str | None]:
        """Check if service is in cooldown (flapping protection: 1 action per 15 min)."""
        now = timestamp if timestamp is not None else self._clock()
        svc = self._norm(service)
        history = self._service_actions.get(svc)
        if not history:
            return False, None

        cutoff = now - self.service_cooldown_s
        # Prune expired
        while history and history[0][1] < cutoff:
            history.popleft()

        if len(history) >= 1:
            last_action, last_ts = history[-1]
            elapsed_s = max(0.0, now - last_ts)
            elapsed_m = elapsed_s / 60.0
            cooldown_m = self.service_cooldown_s / 60.0
            reason = (
                f"Flap protection active: service '{service}' received automated action '{last_action}' "
                f"{elapsed_m:.1f}m ago. Max 1 automated action allowed per {int(cooldown_m)}m cooldown."
            )
            return True, reason

        return False, None

    def is_global_circuit_tripped(
        self,
        timestamp: float | None = None,
    ) -> tuple[bool, str | None]:
        """Check if global cascading failure circuit breaker is open (>3 services in 5 min)."""
        if self._global_tripped_override:
            return True, "Global circuit breaker tripped manually."

        now = timestamp if timestamp is not None else self._clock()
        cutoff = now - self.global_window_s
        # Prune expired global events
        while self._global_events and self._global_events[0][1] < cutoff:
            self._global_events.popleft()

        distinct_services = {svc for svc, ts in self._global_events}
        if len(distinct_services) > self.global_threshold:
            reason = (
                f"Global circuit breaker TRIPPED: {len(distinct_services)} distinct services mitigated "
                f"within {int(self.global_window_s/60)}m (threshold > {self.global_threshold}). "
                f"Auto-apply paused across cluster. Escalating to human on-call engineer."
            )
            return True, reason

        return False, None

    def evaluate(
        self,
        service: str,
        action: str,
        timestamp: float | None = None,
    ) -> tuple[bool, str | None, PolicyDecision]:
        """Comprehensive check before allowing automated remediation.

        Returns (allowed, reason, recommended_policy_decision).
        """
        now = timestamp if timestamp is not None else self._clock()

        # 1. Global Cascading Failure Check
        global_tripped, global_reason = self.is_global_circuit_tripped(timestamp=now)
        if global_tripped:
            return False, global_reason, PolicyDecision.needs_approval

        # 2. Per-Service Anti-Flap Check
        flapping, flap_reason = self.is_service_flapping(service, action=action, timestamp=now)
        if flapping:
            return False, flap_reason, PolicyDecision.block

        return True, "Passed anti-flap and circuit breaker checks.", PolicyDecision.allow

    def reset(self) -> None:
        """Clear all active history."""
        self._service_actions.clear()
        self._global_events.clear()
        self._global_tripped_override = False

    def get_active_cooldowns(self, timestamp: float | None = None) -> dict[str, float]:
        """Return remaining cooldown seconds for services."""
        now = timestamp if timestamp is not None else self._clock()
        cooldowns: dict[str, float] = {}
        for svc, history in self._service_actions.items():
            if history:
                _, last_ts = history[-1]
                remaining = self.service_cooldown_s - (now - last_ts)
                if remaining > 0:
                    cooldowns[svc] = remaining
        return cooldowns


_CIRCUIT_BREAKER: AntiFlapCircuitBreaker | None = None


def get_circuit_breaker() -> AntiFlapCircuitBreaker:
    global _CIRCUIT_BREAKER
    if _CIRCUIT_BREAKER is None:
        _CIRCUIT_BREAKER = AntiFlapCircuitBreaker()
    return _CIRCUIT_BREAKER
