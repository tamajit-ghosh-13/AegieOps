"""Jaeger distributed trace client and correlator (AegisOps Slice 2).

Extracts traces and failing span waterfalls directly from Jaeger REST API (:16686).
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel, Field

DEFAULT_JAEGER_API_URL = os.environ.get("JAEGER_API_URL", "http://localhost:16686/api")


class SpanSummary(BaseModel):
    span_id: str
    operation_name: str
    duration_ms: float
    start_time_us: int
    tags: dict[str, Any] = Field(default_factory=dict)
    has_error: bool = False
    error_message: str | None = None


class TraceSummary(BaseModel):
    trace_id: str
    root_operation: str
    duration_ms: float
    span_count: int
    has_error: bool = False
    failing_spans: list[SpanSummary] = Field(default_factory=list)
    tags: dict[str, Any] = Field(default_factory=dict)
    spans: list[SpanSummary] = Field(default_factory=list)


class JaegerClient:
    def __init__(self, api_url: str = DEFAULT_JAEGER_API_URL, client: httpx.AsyncClient | None = None) -> None:
        self._api_url = api_url.rstrip("/")
        self._client = client

    async def get_services(self) -> list[str]:
        """List all services instrumented in Jaeger."""
        async def _fetch(cli: httpx.AsyncClient) -> list[str]:
            resp = await cli.get(f"{self._api_url}/services")
            if resp.status_code != 200:
                return []
            return resp.json().get("data", [])

        try:
            if self._client is not None:
                return await _fetch(self._client)
            async with httpx.AsyncClient(timeout=3.0) as cli:
                return await _fetch(cli)
        except Exception:
            return []

    async def get_recent_traces(self, service: str = "aegis-agent", limit: int = 5) -> list[TraceSummary]:
        """Fetch recent traces for a given service."""
        async def _fetch(cli: httpx.AsyncClient) -> list[dict]:
            resp = await cli.get(f"{self._api_url}/traces", params={"service": service, "limit": limit})
            if resp.status_code != 200:
                return []
            return resp.json().get("data", [])

        try:
            if self._client is not None:
                raw_traces = await _fetch(self._client)
            else:
                async with httpx.AsyncClient(timeout=4.0) as cli:
                    raw_traces = await _fetch(cli)
            return [self._parse_trace(t) for t in raw_traces]
        except Exception:
            return []

    async def get_trace(self, trace_id: str) -> TraceSummary | None:
        """Fetch a specific trace by trace_id."""
        async def _fetch(cli: httpx.AsyncClient) -> list[dict]:
            resp = await cli.get(f"{self._api_url}/traces/{trace_id}")
            if resp.status_code != 200:
                return []
            return resp.json().get("data", [])

        try:
            if self._client is not None:
                raw = await _fetch(self._client)
            else:
                async with httpx.AsyncClient(timeout=4.0) as cli:
                    raw = await _fetch(cli)
            if not raw:
                return None
            return self._parse_trace(raw[0])
        except Exception:
            return None

    def _parse_trace(self, raw_trace: dict[str, Any]) -> TraceSummary:
        trace_id = raw_trace.get("traceID", "")
        raw_spans = raw_trace.get("spans", [])

        parsed_spans: list[SpanSummary] = []
        failing_spans: list[SpanSummary] = []
        root_op = "unknown"
        trace_duration_us = 0
        overall_tags: dict[str, Any] = {}

        for s in raw_spans:
            op_name = s.get("operationName", "")
            duration_us = s.get("duration", 0)
            duration_ms = duration_us / 1000.0
            start_us = s.get("startTime", 0)

            # Extract tags as a clean dict
            tag_dict = {t.get("key"): t.get("value") for t in s.get("tags", []) if "key" in t}
            overall_tags.update(tag_dict)

            has_error = False
            error_msg = None
            if tag_dict.get("error") is True or str(tag_dict.get("http.status_code", "")).startswith("5"):
                has_error = True
                error_msg = tag_dict.get("error.message") or "HTTP 5xx or unhandled error tag"

            span_summary = SpanSummary(
                span_id=s.get("spanID", ""),
                operation_name=op_name,
                duration_ms=duration_ms,
                start_time_us=start_us,
                tags=tag_dict,
                has_error=has_error,
                error_message=error_msg,
            )
            parsed_spans.append(span_summary)

            if has_error:
                failing_spans.append(span_summary)

            # Heuristic for root span: references is empty or operation is agent.process / consumer.correlate
            if not s.get("references") or op_name in ("agent.process", "consumer.correlate"):
                root_op = op_name
                trace_duration_us = max(trace_duration_us, duration_us)

        if trace_duration_us == 0 and parsed_spans:
            trace_duration_us = max(s.get("duration", 0) for s in raw_spans)

        return TraceSummary(
            trace_id=trace_id,
            root_operation=root_op,
            duration_ms=trace_duration_us / 1000.0,
            span_count=len(parsed_spans),
            has_error=len(failing_spans) > 0,
            failing_spans=failing_spans,
            tags=overall_tags,
            spans=parsed_spans,
        )
