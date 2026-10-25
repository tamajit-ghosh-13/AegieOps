"""Live closed-loop telemetry verifier (AegisOps Slice 1).

Monitors live application metrics after an operational remediation is applied,
asserting that the target service recovers below defined SLO thresholds.
"""

from __future__ import annotations

import asyncio
import os
import time

import httpx

from agent.state import LiveVerificationResult
from sandbox.recovery import RECOVERED_CEILING, check_recovered
from stream.schema import FaultKind

LIVE_APP_URL = os.environ.get("LIVE_APP_URL", "http://localhost:8000")
DEFAULT_VERIFY_TIMEOUT_S = 6.0
DEFAULT_POLL_INTERVAL_S = 0.5
ERROR_PROBE_REQUESTS = 10


class LiveVerifier:
    """Samples live telemetry to assert that an applied operational fix actually cured the system."""

    def __init__(
        self,
        base_url: str = LIVE_APP_URL,
        timeout_s: float = DEFAULT_VERIFY_TIMEOUT_S,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s
        self._poll_interval_s = poll_interval_s
        self._client = client

    async def get_live_metrics(self, fault_kind: FaultKind | None = None) -> dict[str, float]:
        """Fetch real-time metrics directly from the live service."""
        async def _fetch(cli: httpx.AsyncClient) -> dict[str, float]:
            resp = await cli.get(f"{self._base_url}/healthz")
            if resp.status_code != 200:
                return {}
            data = resp.json()
            metrics = {k: float(v) for k, v in data.get("metrics", {}).items()}

            if fault_kind is FaultKind.error_spike:
                errors = 0
                total = ERROR_PROBE_REQUESTS
                for _ in range(total):
                    r = await cli.get(f"{self._base_url}/work")
                    if r.status_code >= 500:
                        errors += 1
                metrics["error_rate_pct"] = (errors / total) * 100.0
            return metrics

        try:
            if self._client is not None:
                return await _fetch(self._client)
            async with httpx.AsyncClient(timeout=3.0) as cli:
                return await _fetch(cli)
        except Exception:
            return {}

    async def verify_recovery(
        self,
        fault_kind: FaultKind,
        before_metrics: dict[str, float] | None = None,
    ) -> LiveVerificationResult:
        """Polls live metrics until recovery is asserted or timeout expires."""
        start = time.monotonic()
        deadline = start + self._timeout_s

        before = before_metrics or await self.get_live_metrics(fault_kind)
        last_metrics = dict(before)
        last_reason = "telemetry did not recover within timeout"

        while time.monotonic() < deadline:
            await asyncio.sleep(self._poll_interval_s)
            current_metrics = await self.get_live_metrics(fault_kind)
            last_metrics = current_metrics

            metric_name, _ = RECOVERED_CEILING.get(fault_kind, ("", 0.0))
            current_metrics.setdefault(metric_name, 0.0)

            passed, reason = check_recovered(fault_kind, before, current_metrics)
            if passed:
                duration_ms = (time.monotonic() - start) * 1000.0
                return LiveVerificationResult(
                    passed=True,
                    fault_kind=fault_kind,
                    before_metrics=before,
                    after_metrics=current_metrics,
                    duration_ms=duration_ms,
                    failure_reason=None,
                )
            last_reason = reason

        duration_ms = (time.monotonic() - start) * 1000.0
        return LiveVerificationResult(
            passed=False,
            fault_kind=fault_kind,
            before_metrics=before,
            after_metrics=last_metrics,
            duration_ms=duration_ms,
            failure_reason=last_reason,
        )
