"""Mock target app: injectable faults that emit RawEvents onto the aegis:events stream."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from mock_app.controls import FLAGS, SCALE
from mock_app.faults import FAULTS, Fault
from mock_app.faults.error_spike import ErrorSpikeFault
from stream.producer import Producer
from stream.schema import FaultKind

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
EMIT_INTERVAL_S = float(os.environ.get("EMIT_INTERVAL_S", "0.5"))


async def _emit_loop(producer: Producer) -> None:
    while True:
        await asyncio.sleep(EMIT_INTERVAL_S)
        for fault in FAULTS.values():
            if fault.is_active():
                await fault.emit_signals(producer)


class NullProducer:
    """Stream-disabled mode (sandbox containers): emit loop ticks, nothing is published."""

    async def publish(self, event) -> None:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("AEGIS_STREAM_DISABLED") == "1":
        app.state.producer = NullProducer()
        task = asyncio.create_task(_emit_loop(app.state.producer))
        try:
            yield
        finally:
            task.cancel()
        return

    from redis.asyncio import Redis

    redis = Redis.from_url(REDIS_URL)
    app.state.producer = Producer(redis)
    task = asyncio.create_task(_emit_loop(app.state.producer))
    try:
        yield
    finally:
        task.cancel()
        await redis.aclose()


app = FastAPI(title="Aegis mock app", lifespan=lifespan)
router = APIRouter(prefix="/faults", tags=["faults"])


@router.get("")
async def list_faults():
    return {kind.value: fault.is_active() for kind, fault in FAULTS.items()}


@router.post("/{kind}/trigger")
async def trigger_fault(kind: str):
    fault_kind, fault = _get_fault(kind)
    if fault.is_active():
        raise HTTPException(status_code=409, detail=f"{fault_kind.value} is already active")
    await fault.trigger()
    return {"kind": fault_kind.value, "active": fault.is_active()}


@router.post("/{kind}/clear")
async def clear_fault(kind: str):
    fault_kind, fault = _get_fault(kind)
    await fault.clear()
    return {"kind": fault_kind.value, "active": False}


def _get_fault(kind: str) -> tuple[FaultKind, Fault]:
    try:
        fault_kind = FaultKind(kind)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"unknown fault kind: {kind}")
    return fault_kind, FAULTS[fault_kind]


app.include_router(router)


class FlagUpdate(BaseModel):
    enabled: bool


class ScaleUpdate(BaseModel):
    workers: int = Field(ge=1, le=16)


@app.get("/flags")
async def list_flags():
    return FLAGS.all()


@app.post("/flags/{name}")
async def set_flag(name: str, body: FlagUpdate):
    try:
        FLAGS.set(name, body.enabled)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown flag: {name}")
    return {"name": name, "enabled": body.enabled}


@app.get("/scale")
async def get_scale():
    return {"workers": SCALE.workers}


@app.post("/scale")
async def set_scale(body: ScaleUpdate):
    SCALE.set_workers(body.workers)
    return {"workers": SCALE.workers}


@app.post("/connections/drain")
async def drain_connections():
    """Operational remediation: drain connection pool and clear deadlocks/locks."""
    deadlock = FAULTS.get(FaultKind.db_deadlock)
    if deadlock:
        await deadlock.clear()
    return {"status": "ok", "drained": True, "active_locks": 0}


@app.get("/healthz")
async def healthz():
    metrics: dict[str, float] = {}
    for fault in FAULTS.values():
        metrics.update(fault.metric_snapshot())
    return {
        "status": "ok",
        "workers": SCALE.workers,
        "flags": FLAGS.all(),
        "metrics": metrics,
    }


REQUEST_COUNTS: dict[str, int] = {"work_200": 0, "work_500": 0}


@app.get("/work")
async def work():
    error_spike = FAULTS[FaultKind.error_spike]
    assert isinstance(error_spike, ErrorSpikeFault)
    if error_spike.should_fail():
        REQUEST_COUNTS["work_500"] += 1
        return Response(status_code=500, content="internal error")
    REQUEST_COUNTS["work_200"] += 1
    return {"status": "ok"}


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus standard metrics exposition format (AegisOps Slice 2)."""
    current_metrics: dict[str, float] = {}
    for fault in FAULTS.values():
        current_metrics.update(fault.metric_snapshot())

    latency = current_metrics.get("latency_ms", 50.0)
    rss_mb = current_metrics.get("rss_mb", 8.0)
    lock_wait_ms = current_metrics.get("lock_wait_ms", 0.0)

    lines = [
        "# HELP http_requests_total Total number of HTTP requests processed",
        "# TYPE http_requests_total counter",
        f'http_requests_total{{endpoint="/work",status="200"}} {REQUEST_COUNTS["work_200"]}',
        f'http_requests_total{{endpoint="/work",status="500"}} {REQUEST_COUNTS["work_500"]}',
        "",
        "# HELP http_request_duration_ms Current p95 request duration in milliseconds",
        "# TYPE http_request_duration_ms gauge",
        f"http_request_duration_ms {latency:.1f}",
        "",
        "# HELP app_memory_rss_mb Process resident memory set size in megabytes",
        "# TYPE app_memory_rss_mb gauge",
        f"app_memory_rss_mb {rss_mb:.1f}",
        "",
        "# HELP app_db_lock_wait_ms Database lock wait time in milliseconds",
        "# TYPE app_db_lock_wait_ms gauge",
        f"app_db_lock_wait_ms {lock_wait_ms:.1f}",
        "",
        "# HELP app_active_workers Number of active worker processes",
        "# TYPE app_active_workers gauge",
        f"app_active_workers {SCALE.workers}",
    ]

    for name, enabled in FLAGS.all().items():
        val = 1 if enabled else 0
        lines.append(f'app_feature_flag_status{{name="{name}"}} {val}')

    for kind, fault in FAULTS.items():
        val = 1 if fault.is_active() else 0
        lines.append(f'app_fault_active{{kind="{kind.value}"}} {val}')

    lines.append("")
    return Response(content="\n".join(lines), media_type="text/plain; version=0.0.4; charset=utf-8")
