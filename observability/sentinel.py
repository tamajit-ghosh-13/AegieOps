"""Real-time Prometheus telemetry sentinel (AegisOps Dual-Signal Detection).

Continuously monitors live Prometheus RED metrics and topology anomalies.
When an SLO breach occurs (e.g. p95 latency > 100ms, error rate > 5%, memory leak > 50MB),
it dynamically synthesizes an IncidentEvent and triggers autonomous closed-loop recovery.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from observability.hub import ObservabilityHub, SystemTelemetrySnapshot, get_observability_hub
from stream.schema import FaultKind, IncidentEvent, Severity


class TelemetrySentinel:
    def __init__(
        self,
        hub: ObservabilityHub | None = None,
        cooldown_s: float = 15.0,
    ) -> None:
        self.hub = hub or get_observability_hub()
        self.cooldown_s = cooldown_s
        self._last_alert_ts: dict[FaultKind, float] = {}

    def _infer_fault(self, snapshot: SystemTelemetrySnapshot) -> tuple[FaultKind, Severity] | None:
        red = snapshot.red_metrics
        # 1. Direct fault flags or metric thresholds
        if red.active_faults.get("error_spike") or red.error_rate_pct > 10.0:
            return FaultKind.error_spike, Severity.critical
        if red.active_faults.get("db_deadlock") or red.db_lock_wait_ms > 100.0:
            return FaultKind.db_deadlock, Severity.critical
        if red.active_faults.get("memory_leak") or red.memory_rss_mb > 50.0:
            return FaultKind.memory_leak, Severity.error
        if red.active_faults.get("traffic_surge") or red.p95_latency_ms > 100.0:
            return FaultKind.traffic_surge, Severity.error

        # 2. Inferred from active anomalies
        if snapshot.active_anomalies:
            first = snapshot.active_anomalies[0].lower()
            if "latency" in first:
                return FaultKind.traffic_surge, Severity.error
            if "error" in first:
                return FaultKind.error_spike, Severity.critical
            if "memory" in first:
                return FaultKind.memory_leak, Severity.error
            if "deadlock" in first or "lock" in first:
                return FaultKind.db_deadlock, Severity.critical

        return None

    async def check(self, current_time: float | None = None) -> IncidentEvent | None:
        """Poll telemetry snapshot and return an IncidentEvent if an unhandled SLO breach exists."""
        snapshot = await self.hub.get_snapshot(trace_limit=2)
        if not snapshot.active_anomalies:
            return None

        inferred = self._infer_fault(snapshot)
        if inferred is None:
            return None

        fault_kind, severity = inferred

        # Suppress duplicate re-triggers while an incident for this fault is already pending in HITL gate
        from hitl.gate import get_approval_gate
        try:
            gate = get_approval_gate()
            if gate and any(b.get("fault_kind") == fault_kind.value for b in gate.list_pending()):
                return None
        except Exception:
            pass

        now_ts = current_time if current_time is not None else datetime.now(timezone.utc).timestamp()
        last_ts = self._last_alert_ts.get(fault_kind, 0.0)

        # Flap / cooldown protection
        if (now_ts - last_ts) < self.cooldown_s:
            return None

        self._last_alert_ts[fault_kind] = now_ts
        now = datetime.now(timezone.utc)
        summary = "; ".join(snapshot.active_anomalies)

        return IncidentEvent(
            incident_id=str(uuid.uuid4()),
            fault_kind=fault_kind,
            severity=severity,
            source="observability.prometheus",
            title=f"Live Telemetry SLO Breach: {snapshot.active_anomalies[0]}",
            summary=f"Automated Prometheus anomaly detection: {summary}",
            first_seen=now,
            last_seen=now,
            event_count=1,
            duplicate_count=0,
            sample_events=[],
            correlation_window_s=2.0,
        )

    def reset_cooldown(self, fault_kind: FaultKind | None = None) -> None:
        if fault_kind:
            self._last_alert_ts.pop(fault_kind, None)
        else:
            self._last_alert_ts.clear()
