"""Unit tests for LiveVerifier (AegisOps Slice 1)."""

import pytest
import httpx
from unittest.mock import AsyncMock

from apply.verifier import LiveVerifier
from stream.schema import FaultKind


@pytest.mark.asyncio
async def test_get_live_metrics_returns_parsed_dict():
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(200, json={"status": "ok", "metrics": {"latency_ms": 75.0, "workers": 4}})
    verifier = LiveVerifier(base_url="http://mock-service:8000", client=mock_client)

    metrics = await verifier.get_live_metrics()
    assert metrics == {"latency_ms": 75.0, "workers": 4.0}


@pytest.mark.asyncio
async def test_verify_recovery_passes_when_metrics_recover():
    mock_client = AsyncMock()
    # Target recovered ceiling for traffic_surge is latency_ms <= 100.0
    mock_client.get.return_value = httpx.Response(200, json={"status": "ok", "metrics": {"latency_ms": 50.0}})
    verifier = LiveVerifier(base_url="http://mock-service:8000", timeout_s=0.5, poll_interval_s=0.05, client=mock_client)

    result = await verifier.verify_recovery(
        FaultKind.traffic_surge,
        before_metrics={"latency_ms": 200.0},
    )
    assert result.passed is True
    assert result.after_metrics["latency_ms"] == 50.0
    assert result.failure_reason is None


@pytest.mark.asyncio
async def test_verify_recovery_fails_when_metrics_remain_degraded():
    mock_client = AsyncMock()
    # Still elevated latency > 100.0
    mock_client.get.return_value = httpx.Response(200, json={"status": "ok", "metrics": {"latency_ms": 180.0}})
    verifier = LiveVerifier(base_url="http://mock-service:8000", timeout_s=0.2, poll_interval_s=0.05, client=mock_client)

    result = await verifier.verify_recovery(
        FaultKind.traffic_surge,
        before_metrics={"latency_ms": 200.0},
    )
    assert result.passed is False
    assert result.after_metrics["latency_ms"] == 180.0
    assert "above recovery ceiling" in result.failure_reason
