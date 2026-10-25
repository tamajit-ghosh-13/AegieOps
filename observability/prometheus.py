"""Prometheus metrics scraper and parser (AegisOps Slice 2).

Extracts standard RED metrics (Rate, Errors, Duration) and system gauges from
Prometheus text exposition format endpoints.
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field

DEFAULT_METRICS_URL = os.environ.get("PROMETHEUS_METRICS_URL", "http://localhost:8000/metrics")

_METRIC_LINE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{(?P<labels>[^}]*)\})?"
    r"\s+(?P<value>[+-]?(?:[0-9]*[.])?[0-9]+(?:[eE][+-]?[0-9]+)?)"
    r"(?:\s+(?P<timestamp>[0-9]+))?$"
)
_LABEL_RE = re.compile(r'(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)="(?P<val>[^"]*)"')


class RawMetric(BaseModel):
    name: str
    labels: dict[str, str] = Field(default_factory=dict)
    value: float


class REDMetrics(BaseModel):
    rate_rps: float = 0.0
    error_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    error_rate_pct: float = 0.0
    p95_latency_ms: float = 50.0
    memory_rss_mb: float = 8.0
    db_lock_wait_ms: float = 0.0
    active_workers: int = 2
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    active_faults: dict[str, bool] = Field(default_factory=dict)


def parse_prometheus_text(text: str) -> list[RawMetric]:
    """Parse raw Prometheus line protocol text into typed RawMetric objects."""
    metrics: list[RawMetric] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _METRIC_LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name")
        val = float(m.group("value"))
        labels_str = m.group("labels")
        labels: dict[str, str] = {}
        if labels_str:
            for l_match in _LABEL_RE.finditer(labels_str):
                labels[l_match.group("key")] = l_match.group("val")
        metrics.append(RawMetric(name=name, labels=labels, value=val))
    return metrics


class PrometheusScraper:
    def __init__(self, metrics_url: str = DEFAULT_METRICS_URL, client: httpx.AsyncClient | None = None) -> None:
        self._url = metrics_url
        self._client = client

    async def scrape(self) -> list[RawMetric]:
        """Scrape raw Prometheus metrics from the target endpoint."""
        async def _fetch(cli: httpx.AsyncClient) -> str:
            resp = await cli.get(self._url)
            if resp.status_code != 200:
                return ""
            return resp.text

        try:
            if self._client is not None:
                text = await _fetch(self._client)
            else:
                async with httpx.AsyncClient(timeout=3.0) as cli:
                    text = await _fetch(cli)
            return parse_prometheus_text(text)
        except Exception:
            return []

    async def get_red_metrics(self) -> REDMetrics:
        """Fetch and aggregate metrics into standard RED (Rate, Errors, Duration) structure."""
        raw_list = await self.scrape()
        red = REDMetrics()

        for m in raw_list:
            if m.name == "http_requests_total":
                status = m.labels.get("status")
                if status == "500":
                    red.error_count = int(m.value)
                elif status == "200":
                    red.success_count = int(m.value)
            elif m.name == "http_request_duration_ms":
                red.p95_latency_ms = m.value
            elif m.name == "app_memory_rss_mb":
                red.memory_rss_mb = m.value
            elif m.name == "app_db_lock_wait_ms":
                red.db_lock_wait_ms = m.value
            elif m.name == "app_active_workers":
                red.active_workers = int(m.value)
            elif m.name == "app_feature_flag_status":
                flag_name = m.labels.get("name")
                if flag_name:
                    red.feature_flags[flag_name] = (m.value == 1.0)
            elif m.name == "app_fault_active":
                kind = m.labels.get("kind")
                if kind:
                    red.active_faults[kind] = (m.value == 1.0)

        red.total_requests = red.success_count + red.error_count
        if red.total_requests > 0:
            red.error_rate_pct = (red.error_count / red.total_requests) * 100.0
        return red
