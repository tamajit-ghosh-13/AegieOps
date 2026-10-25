"""Adaptive Statistical Telemetry Sentinel (Sprint 1: Dynamic Anomaly Detection).

Replaces static alert boundaries with rolling statistical baselining:
- Online Exponentially Weighted Moving Average (EWMA) for baseline mean & variance.
- Rolling Z-Score with traffic-volume weighting (avoids false alerts during low-traffic hours).
- Non-parametric Interquartile Range (IQR) for fat-tailed latency distributions.
- Multi-signal fault classification generating typed IncidentEvents.
"""

from __future__ import annotations

import math
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from observability.hub import ObservabilityHub, SystemTelemetrySnapshot, get_observability_hub
from stream.schema import FaultKind, IncidentEvent, Severity


@dataclass
class MetricSample:
    timestamp: float
    p95_latency_ms: float
    error_rate_pct: float
    rate_rps: float
    memory_rss_mb: float
    db_lock_wait_ms: float


@dataclass
class AnomalyDiagnosis:
    is_anomaly: bool
    fault_kind: FaultKind | None = None
    severity: Severity = Severity.info
    metric_name: str = ""
    current_value: float = 0.0
    baseline_mean: float = 0.0
    z_score: float = 0.0
    iqr_upper_bound: float = 0.0
    explanation: str = ""


class AdaptiveBaselineDetector:
    """Computes rolling online EWMA, Z-Score, and IQR baselines across telemetry samples."""

    def __init__(
        self,
        window_size: int = 450,  # 450 samples at 2s = 15 min rolling window
        min_samples: int = 5,
        alpha: float = 0.1,      # EWMA mean smoothing factor
        beta: float = 0.05,     # EWMA variance smoothing factor
        z_threshold: float = 2.5,
        min_latency_delta_ms: float = 25.0,
    ) -> None:
        self.window: deque[MetricSample] = deque(maxlen=window_size)
        self.min_samples = min_samples
        self.alpha = alpha
        self.beta = beta
        self.z_threshold = z_threshold
        self.min_latency_delta_ms = min_latency_delta_ms

        # Online EWMA statistics
        self._ewma_mean: dict[str, float] = {}
        self._ewma_var: dict[str, float] = {}

    def _update_ewma(self, metric: str, value: float) -> tuple[float, float]:
        if metric not in self._ewma_mean:
            self._ewma_mean[metric] = value
            self._ewma_var[metric] = 1.0  # Initial non-zero variance
            return value, 1.0

        prev_mean = self._ewma_mean[metric]
        new_mean = self.alpha * value + (1.0 - self.alpha) * prev_mean
        diff_sq = (value - new_mean) ** 2
        new_var = self.beta * diff_sq + (1.0 - self.beta) * self._ewma_var[metric]

        self._ewma_mean[metric] = new_mean
        self._ewma_var[metric] = max(0.01, new_var)
        return new_mean, math.sqrt(self._ewma_var[metric])

    def _calculate_iqr(self, values: list[float]) -> tuple[float, float, float]:
        """Calculate Q1, Q3, and upper fence Q3 + 1.5 * IQR."""
        if len(values) < 4:
            val = values[-1] if values else 50.0
            return val, val, val + self.min_latency_delta_ms

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        q1 = sorted_vals[q1_idx]
        q3 = sorted_vals[q3_idx]
        iqr = q3 - q1
        upper_fence = q3 + 1.5 * iqr
        return q1, q3, upper_fence

    def evaluate_sample(self, sample: MetricSample) -> AnomalyDiagnosis:
        self.window.append(sample)

        # Update EWMA estimators for all tracked metrics
        mean_lat, std_lat = self._update_ewma("latency", sample.p95_latency_ms)
        mean_err, std_err = self._update_ewma("error", sample.error_rate_pct)
        mean_mem, std_mem = self._update_ewma("memory", sample.memory_rss_mb)
        mean_lock, std_lock = self._update_ewma("lock", sample.db_lock_wait_ms)

        # Baseline warmup check
        if len(self.window) < self.min_samples:
            return AnomalyDiagnosis(
                is_anomaly=False,
                explanation=f"Warming up baseline ({len(self.window)}/{self.min_samples} samples)",
            )

        # 1. Evaluate Latency Anomaly (EWMA Z-score + IQR)
        lat_window = [s.p95_latency_ms for s in self.window]
        q1, q3, upper_fence = self._calculate_iqr(lat_window)
        raw_z_lat = (sample.p95_latency_ms - mean_lat) / max(0.5, std_lat)
        
        # Volume weighting: Scale Z down if traffic volume is near-zero to prevent low-QPS false positives
        traffic_factor = math.sqrt(min(1.0, max(0.1, sample.rate_rps / 10.0)))
        effective_z_lat = raw_z_lat * traffic_factor
        lat_delta = sample.p95_latency_ms - mean_lat

        is_latency_outlier = (
            (effective_z_lat >= self.z_threshold and lat_delta >= self.min_latency_delta_ms)
            or (sample.p95_latency_ms >= upper_fence and lat_delta >= self.min_latency_delta_ms)
            or sample.p95_latency_ms > 150.0  # Hard safety ceiling
        )

        if is_latency_outlier:
            severity = Severity.critical if sample.p95_latency_ms > 200.0 else Severity.error
            return AnomalyDiagnosis(
                is_anomaly=True,
                fault_kind=FaultKind.traffic_surge,
                severity=severity,
                metric_name="p95_latency_ms",
                current_value=sample.p95_latency_ms,
                baseline_mean=round(mean_lat, 2),
                z_score=round(effective_z_lat, 2),
                iqr_upper_bound=round(upper_fence, 2),
                explanation=(
                    f"Adaptive anomaly on p95 latency: {sample.p95_latency_ms:.1f}ms "
                    f"(baseline: {mean_lat:.1f}ms, Z={effective_z_lat:.2f}, upper_iqr={upper_fence:.1f}ms, QPS={sample.rate_rps:.1f})"
                ),
            )

        # 2. Evaluate Error Rate Anomaly
        raw_z_err = (sample.error_rate_pct - mean_err) / max(0.1, std_err)
        if sample.error_rate_pct > 5.0 or (raw_z_err >= self.z_threshold and sample.error_rate_pct > 2.0):
            return AnomalyDiagnosis(
                is_anomaly=True,
                fault_kind=FaultKind.error_spike,
                severity=Severity.critical,
                metric_name="error_rate_pct",
                current_value=sample.error_rate_pct,
                baseline_mean=round(mean_err, 2),
                z_score=round(raw_z_err, 2),
                explanation=(
                    f"Adaptive anomaly on error rate: {sample.error_rate_pct:.1f}% "
                    f"(baseline: {mean_err:.1f}%, Z={raw_z_err:.2f})"
                ),
            )

        # 3. Evaluate Database Deadlock / Lock Wait Anomaly
        if sample.db_lock_wait_ms > 100.0:
            return AnomalyDiagnosis(
                is_anomaly=True,
                fault_kind=FaultKind.db_deadlock,
                severity=Severity.critical,
                metric_name="db_lock_wait_ms",
                current_value=sample.db_lock_wait_ms,
                baseline_mean=round(mean_lock, 2),
                z_score=round((sample.db_lock_wait_ms - mean_lock) / max(1.0, std_lock), 2),
                explanation=f"Database lock contention spike: {sample.db_lock_wait_ms:.1f}ms (threshold 100ms)",
            )

        # 4. Evaluate Memory Leak Anomaly
        if sample.memory_rss_mb > 50.0:
            return AnomalyDiagnosis(
                is_anomaly=True,
                fault_kind=FaultKind.memory_leak,
                severity=Severity.error,
                metric_name="memory_rss_mb",
                current_value=sample.memory_rss_mb,
                baseline_mean=round(mean_mem, 2),
                z_score=round((sample.memory_rss_mb - mean_mem) / max(1.0, std_mem), 2),
                explanation=f"Memory RSS growth anomaly: {sample.memory_rss_mb:.1f}MB (threshold 50MB)",
            )

        return AnomalyDiagnosis(
            is_anomaly=False,
            current_value=sample.p95_latency_ms,
            baseline_mean=round(mean_lat, 2),
            z_score=round(effective_z_lat, 2),
            explanation=f"Nominal operating conditions (p95={sample.p95_latency_ms:.1f}ms, baseline={mean_lat:.1f}ms)",
        )


class AdaptiveTelemetrySentinel:
    """Orchestrates telemetry ingestion from ObservabilityHub and evaluates adaptive baselines."""

    def __init__(
        self,
        hub: ObservabilityHub | None = None,
        detector: AdaptiveBaselineDetector | None = None,
        cooldown_s: float = 45.0,
    ) -> None:
        self.hub = hub or get_observability_hub()
        self.detector = detector or AdaptiveBaselineDetector()
        self.cooldown_s = cooldown_s
        self._last_alert_ts: dict[FaultKind, float] = {}

    async def check(self, current_time: float | None = None) -> IncidentEvent | None:
        snapshot = await self.hub.get_snapshot(trace_limit=2)
        red = snapshot.red_metrics

        sample = MetricSample(
            timestamp=datetime.now(timezone.utc).timestamp(),
            p95_latency_ms=red.p95_latency_ms,
            error_rate_pct=red.error_rate_pct,
            rate_rps=red.rate_rps,
            memory_rss_mb=red.memory_rss_mb,
            db_lock_wait_ms=red.db_lock_wait_ms,
        )

        diagnosis = self.detector.evaluate_sample(sample)
        if not diagnosis.is_anomaly or diagnosis.fault_kind is None:
            return None

        # Suppress duplicate re-triggers while an incident for this fault is already pending in HITL gate
        from hitl.gate import get_approval_gate
        try:
            gate = get_approval_gate()
            if gate and any(b.get("fault_kind") == diagnosis.fault_kind.value for b in gate.list_pending()):
                return None
        except Exception:
            pass

        now_ts = current_time if current_time is not None else datetime.now(timezone.utc).timestamp()
        last_ts = self._last_alert_ts.get(diagnosis.fault_kind, 0.0)

        # Flap / cooldown protection
        if (now_ts - last_ts) < self.cooldown_s:
            return None

        self._last_alert_ts[diagnosis.fault_kind] = now_ts
        now = datetime.now(timezone.utc)

        return IncidentEvent(
            incident_id=str(uuid.uuid4()),
            fault_kind=diagnosis.fault_kind,
            severity=diagnosis.severity,
            source="observability.adaptive_sentinel",
            title=f"Adaptive Baseline Anomaly: {diagnosis.explanation}",
            summary=(
                f"Statistical baseline deviation detected on {diagnosis.metric_name}: "
                f"Observed={diagnosis.current_value}, Baseline={diagnosis.baseline_mean}, Z={diagnosis.z_score}. "
                f"Context: {diagnosis.explanation}"
            ),
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


_ADAPTIVE_SENTINEL: AdaptiveTelemetrySentinel | None = None


def get_adaptive_sentinel() -> AdaptiveTelemetrySentinel:
    global _ADAPTIVE_SENTINEL
    if _ADAPTIVE_SENTINEL is None:
        _ADAPTIVE_SENTINEL = AdaptiveTelemetrySentinel(cooldown_s=15.0)
    return _ADAPTIVE_SENTINEL
