"""Multi-Source Alert Ingestion Gateway (Sprint 1: Alertmanager & PagerDuty Integration).

Ingests, deduplicates, and normalizes external alerts from:
- Prometheus Alertmanager v4 Webhook JSON format
- PagerDuty V2 Webhook event streams
- Datadog / Custom Webhooks

Converts incoming alerts into unified IncidentEvents for the LangGraph reasoner.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from stream.schema import FaultKind, IncidentEvent, Severity


# ==============================================================================
# Pydantic Schemas for External Alert Payloads
# ==============================================================================

class AlertmanagerAlertItem(BaseModel):
    status: str = "firing"  # "firing" or "resolved"
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = None
    endsAt: str | None = None
    generatorURL: str | None = None
    fingerprint: str | None = None


class AlertmanagerWebhookPayload(BaseModel):
    version: str = "4"
    groupKey: str | None = None
    status: str = "firing"
    receiver: str | None = None
    groupLabels: dict[str, str] = Field(default_factory=dict)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
    externalURL: str | None = None
    alerts: list[AlertmanagerAlertItem] = Field(default_factory=list)


class PagerDutyIncident(BaseModel):
    id: str
    title: str
    urgency: str = "high"
    status: str = "triggered"
    service: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class PagerDutyMessage(BaseModel):
    event: str = "incident.trigger"
    incident: PagerDutyIncident


class PagerDutyWebhookPayload(BaseModel):
    messages: list[PagerDutyMessage] = Field(default_factory=list)


# ==============================================================================
# Alert Deduplication and Normalization Engine
# ==============================================================================

@dataclass
class AlertRecord:
    fingerprint: str
    incident_id: str
    first_seen: float
    last_seen: float
    count: int = 1


class AlertIngestionGateway:
    """Ingests multi-source webhooks, deduplicates firing alerts, and normalizes into IncidentEvents."""

    def __init__(self, dedup_window_s: float = 60.0) -> None:
        self.dedup_window_s = dedup_window_s
        self._active_alerts: dict[str, AlertRecord] = {}
        self._incident_queue: asyncio.Queue[IncidentEvent] = asyncio.Queue()
        self._recent_events: list[IncidentEvent] = []

    def _infer_fault_kind(self, text: str) -> FaultKind:
        t = text.lower()
        if "deadlock" in t or "lock" in t or "db_" in t:
            return FaultKind.db_deadlock
        if "memory" in t or "leak" in t or "rss" in t:
            return FaultKind.memory_leak
        if "5xx" in t or "error" in t or "failed" in t:
            return FaultKind.error_spike
        return FaultKind.traffic_surge

    def _infer_severity(self, sev_str: str) -> Severity:
        s = sev_str.lower()
        if "crit" in s or "p0" in s:
            return Severity.critical
        if "err" in s or "p1" in s or "high" in s:
            return Severity.error
        if "warn" in s or "p2" in s or "medium" in s:
            return Severity.warning
        return Severity.info

    def _generate_fingerprint(self, service: str, alertname: str, namespace: str = "default") -> str:
        raw = f"{service}:{alertname}:{namespace}".lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def ingest_alertmanager(self, payload: AlertmanagerWebhookPayload) -> list[IncidentEvent]:
        """Normalize Alertmanager v4 payload into IncidentEvents with deduplication."""
        now_mono = time.monotonic()
        now_utc = datetime.now(timezone.utc)
        events_emitted: list[IncidentEvent] = []

        for alert in payload.alerts:
            # Skip resolved notifications for remediation triggering
            if alert.status.lower() == "resolved":
                continue

            labels = alert.labels
            annotations = alert.annotations

            service = labels.get("service") or labels.get("app") or labels.get("job") or "mock_app"
            alertname = labels.get("alertname") or "OperationalSLOBreach"
            namespace = labels.get("namespace") or "production"
            severity_raw = labels.get("severity") or "error"

            fingerprint = alert.fingerprint or self._generate_fingerprint(service, alertname, namespace)
            summary = annotations.get("summary") or annotations.get("description") or f"Alertmanager firing: {alertname}"
            combined_text = f"{alertname} {summary} {service}"

            # Deduplication & Flap Grouping
            record = self._active_alerts.get(fingerprint)
            if record and (now_mono - record.last_seen) < self.dedup_window_s:
                record.last_seen = now_mono
                record.count += 1
                continue  # Suppress duplicate alert within correlation window

            iid = str(uuid.uuid4())
            self._active_alerts[fingerprint] = AlertRecord(
                fingerprint=fingerprint,
                incident_id=iid,
                first_seen=now_mono,
                last_seen=now_mono,
                count=1,
            )

            incident = IncidentEvent(
                incident_id=iid,
                fault_kind=self._infer_fault_kind(combined_text),
                severity=self._infer_severity(severity_raw),
                source=f"alertmanager:{service}",
                title=f"[{severity_raw.upper()}] {alertname} on {service}",
                summary=summary,
                first_seen=now_utc,
                last_seen=now_utc,
                event_count=1,
                duplicate_count=0,
                sample_events=[],
                correlation_window_s=self.dedup_window_s,
            )

            self._recent_events.append(incident)
            self._incident_queue.put_nowait(incident)
            events_emitted.append(incident)

        return events_emitted

    def ingest_pagerduty(self, payload: PagerDutyWebhookPayload) -> list[IncidentEvent]:
        """Normalize PagerDuty V2 messages into IncidentEvents."""
        now_mono = time.monotonic()
        now_utc = datetime.now(timezone.utc)
        events_emitted: list[IncidentEvent] = []

        for msg in payload.messages:
            if msg.event != "incident.trigger":
                continue

            inc = msg.incident
            service_name = inc.service.get("name") or "mock_app"
            fingerprint = self._generate_fingerprint(service_name, inc.title)

            record = self._active_alerts.get(fingerprint)
            if record and (now_mono - record.last_seen) < self.dedup_window_s:
                record.last_seen = now_mono
                record.count += 1
                continue

            iid = str(uuid.uuid4())
            self._active_alerts[fingerprint] = AlertRecord(
                fingerprint=fingerprint,
                incident_id=iid,
                first_seen=now_mono,
                last_seen=now_mono,
                count=1,
            )

            incident = IncidentEvent(
                incident_id=iid,
                fault_kind=self._infer_fault_kind(inc.title),
                severity=self._infer_severity(inc.urgency),
                source=f"pagerduty:{service_name}",
                title=f"PagerDuty Alert: {inc.title}",
                summary=f"Incident {inc.id} triggered on service {service_name}",
                first_seen=now_utc,
                last_seen=now_utc,
                event_count=1,
                duplicate_count=0,
                sample_events=[],
                correlation_window_s=self.dedup_window_s,
            )

            self._recent_events.append(incident)
            self._incident_queue.put_nowait(incident)
            events_emitted.append(incident)

        return events_emitted

    async def next_alert(self) -> IncidentEvent:
        """Async dequeue of incoming alerts for the LangGraph agent runner."""
        return await self._incident_queue.get()

    def has_pending_alerts(self) -> bool:
        return not self._incident_queue.empty()

    def get_recent_alerts(self, limit: int = 20) -> list[IncidentEvent]:
        return list(reversed(self._recent_events[-limit:]))


# Global gateway singleton
_GLOBAL_GATEWAY: AlertIngestionGateway | None = None


def get_alert_gateway() -> AlertIngestionGateway:
    global _GLOBAL_GATEWAY
    if _GLOBAL_GATEWAY is None:
        _GLOBAL_GATEWAY = AlertIngestionGateway()
    return _GLOBAL_GATEWAY
