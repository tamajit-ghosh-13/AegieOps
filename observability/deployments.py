"""CI/CD Change & Deployment Intelligence (AegisOps Sprint 2).

Ingests deployment events from GitHub Actions, ArgoCD, and custom CI/CD pipelines,
persists them to PostgreSQL, and correlates deployments temporally with active incidents
to pinpoint code authors, commit SHAs, and configuration diffs.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from typing import Any
import uuid

import psycopg
from pydantic import BaseModel, Field

from retrieval.db import conn_string

logger = logging.getLogger(__name__)

DEPLOYMENTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS deployment_events (
    deployment_id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'production',
    git_commit_sha TEXT NOT NULL,
    git_author TEXT NOT NULL,
    git_commit_message TEXT NOT NULL,
    git_diff_summary TEXT,
    image_tag_previous TEXT,
    image_tag_new TEXT NOT NULL,
    deployed_at TIMESTAMPTZ NOT NULL,
    rollback_supported BOOLEAN NOT NULL DEFAULT true,
    environment TEXT NOT NULL DEFAULT 'production',
    source TEXT NOT NULL DEFAULT 'manual',
    status TEXT NOT NULL DEFAULT 'success',
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_deployments_service_time ON deployment_events(service_name, deployed_at DESC);
"""

UPSERT_DEPLOYMENT_SQL = """
INSERT INTO deployment_events (
    deployment_id, service_name, namespace, git_commit_sha, git_author,
    git_commit_message, git_diff_summary, image_tag_previous, image_tag_new,
    deployed_at, rollback_supported, environment, source, status, raw_payload
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (deployment_id) DO UPDATE SET
    status = EXCLUDED.status,
    git_diff_summary = COALESCE(EXCLUDED.git_diff_summary, deployment_events.git_diff_summary),
    image_tag_previous = COALESCE(EXCLUDED.image_tag_previous, deployment_events.image_tag_previous);
"""

SELECT_RECENT_DEPLOYMENTS_SQL = """
SELECT deployment_id, service_name, namespace, git_commit_sha, git_author,
       git_commit_message, git_diff_summary, image_tag_previous, image_tag_new,
       deployed_at, rollback_supported, environment, source, status, raw_payload, created_at
FROM deployment_events
ORDER BY deployed_at DESC
LIMIT %s;
"""


class DeploymentSource(str, Enum):
    GITHUB_ACTIONS = "github_actions"
    ARGOCD = "argocd"
    GITLAB = "gitlab"
    MANUAL = "manual"
    MOCK = "mock"


class DeploymentStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"
    ROLLED_BACK = "rolled_back"


class DeploymentEvent(BaseModel):
    deployment_id: str = Field(default_factory=lambda: f"dep-{uuid.uuid4().hex[:12]}")
    service_name: str
    namespace: str = "production"
    git_commit_sha: str
    git_author: str
    git_commit_message: str
    git_diff_summary: str | None = None
    image_tag_previous: str | None = None
    image_tag_new: str = "latest"
    deployed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rollback_supported: bool = True
    environment: str = "production"
    source: DeploymentSource = DeploymentSource.MANUAL
    status: DeploymentStatus = DeploymentStatus.SUCCESS
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeploymentCorrelation(BaseModel):
    deployment: DeploymentEvent
    confidence_score: float  # 0.0 - 1.0
    time_delta_seconds: float
    time_delta_human: str  # e.g., "2m 15s before incident onset"
    relation: str  # "direct_service_immediate", "direct_service_recent", "downstream_dependency", "coincidental"
    summary: str  # Human-readable correlation summary for prompt & UI


def parse_github_webhook(payload: dict[str, Any]) -> DeploymentEvent:
    """Parse GitHub Actions workflow_run, deployment_status, or generic webhook payload."""
    now = datetime.now(timezone.utc)
    
    # 1. GitHub Actions workflow_run completed event
    if "workflow_run" in payload:
        wr = payload["workflow_run"]
        head_commit = wr.get("head_commit") or {}
        author_info = head_commit.get("author") or {}
        author = author_info.get("name") or author_info.get("email") or "GitHub Actions"
        repo = wr.get("repository", {}).get("name") or payload.get("repository", {}).get("name") or "mock_app"
        commit_sha = wr.get("head_sha") or head_commit.get("id") or f"sha-{uuid.uuid4().hex[:8]}"
        commit_msg = head_commit.get("message") or wr.get("name") or "Deploy production"
        
        updated_at_str = wr.get("updated_at")
        deployed_at = now
        if updated_at_str:
            try:
                deployed_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            except Exception:
                deployed_at = now

        return DeploymentEvent(
            deployment_id=f"gh-{wr.get('id', uuid.uuid4().hex[:8])}",
            service_name=repo,
            namespace=payload.get("namespace", "production"),
            git_commit_sha=commit_sha,
            git_author=author,
            git_commit_message=commit_msg,
            git_diff_summary=payload.get("diff_summary"),
            image_tag_previous=payload.get("image_tag_previous"),
            image_tag_new=payload.get("image_tag_new", f"{repo}:{commit_sha[:7]}"),
            deployed_at=deployed_at,
            source=DeploymentSource.GITHUB_ACTIONS,
            status=DeploymentStatus.SUCCESS if wr.get("conclusion") == "success" else DeploymentStatus.FAILURE,
            raw_payload=payload,
        )

    # 2. GitHub deployment_status event
    if "deployment_status" in payload:
        ds = payload["deployment_status"]
        dep = payload.get("deployment") or {}
        repo = payload.get("repository", {}).get("name") or "mock_app"
        commit_sha = dep.get("sha") or f"sha-{uuid.uuid4().hex[:8]}"
        creator = dep.get("creator", {}).get("login") or ds.get("creator", {}).get("login") or "GitHub Deployer"
        return DeploymentEvent(
            deployment_id=f"gh-dep-{dep.get('id', uuid.uuid4().hex[:8])}",
            service_name=repo,
            namespace=payload.get("namespace", "production"),
            git_commit_sha=commit_sha,
            git_author=creator,
            git_commit_message=dep.get("description") or ds.get("description") or "Deploy release",
            git_diff_summary=payload.get("diff_summary"),
            image_tag_previous=payload.get("image_tag_previous"),
            image_tag_new=payload.get("image_tag_new", f"{repo}:{commit_sha[:7]}"),
            source=DeploymentSource.GITHUB_ACTIONS,
            status=DeploymentStatus.SUCCESS if ds.get("state") == "success" else DeploymentStatus.FAILURE,
            raw_payload=payload,
        )

    # 3. Direct/Normalized GitHub payload
    service = payload.get("service") or payload.get("service_name") or payload.get("repository") or "mock_app"
    commit_sha = payload.get("commit_sha") or payload.get("git_commit_sha") or payload.get("head_sha") or f"sha-{uuid.uuid4().hex[:8]}"
    author = payload.get("author") or payload.get("git_author") or "Engineering Team"
    message = payload.get("message") or payload.get("commit_message") or payload.get("git_commit_message") or "Code deployment"

    deployed_at = now
    if "deployed_at" in payload:
        try:
            val = payload["deployed_at"]
            deployed_at = datetime.fromisoformat(val.replace("Z", "+00:00")) if isinstance(val, str) else val
        except Exception:
            deployed_at = now

    return DeploymentEvent(
        deployment_id=payload.get("deployment_id") or f"gh-{uuid.uuid4().hex[:8]}",
        service_name=service,
        namespace=payload.get("namespace", "production"),
        git_commit_sha=commit_sha,
        git_author=author,
        git_commit_message=message,
        git_diff_summary=payload.get("diff_summary") or payload.get("git_diff_summary"),
        image_tag_previous=payload.get("image_tag_previous"),
        image_tag_new=payload.get("image_tag_new") or f"{service}:{commit_sha[:7]}",
        deployed_at=deployed_at,
        source=DeploymentSource.GITHUB_ACTIONS,
        status=DeploymentStatus.SUCCESS,
        raw_payload=payload,
    )


def parse_argocd_webhook(payload: dict[str, Any]) -> DeploymentEvent:
    """Parse ArgoCD Application sync, notification, or webhook payload."""
    now = datetime.now(timezone.utc)
    
    # 1. ArgoCD standard Application object
    if "app" in payload:
        app = payload["app"]
        meta = app.get("metadata", {})
        spec = app.get("spec", {})
        status = app.get("status", {})
        
        service_name = meta.get("name") or "mock_app"
        namespace = spec.get("destination", {}).get("namespace") or "production"
        revision = status.get("sync", {}).get("revision") or payload.get("revision") or f"rev-{uuid.uuid4().hex[:8]}"
        
        op_state = status.get("operationState", {})
        finished_at_str = op_state.get("finishedAt")
        deployed_at = now
        if finished_at_str:
            try:
                deployed_at = datetime.fromisoformat(finished_at_str.replace("Z", "+00:00"))
            except Exception:
                deployed_at = now

        author = payload.get("commit_author") or payload.get("author") or "ArgoCD Automation"
        message = payload.get("commit_message") or payload.get("message") or f"ArgoCD Sync Application {service_name}"
        sync_phase = op_state.get("phase") or status.get("sync", {}).get("status")

        return DeploymentEvent(
            deployment_id=f"argo-{uuid.uuid4().hex[:8]}",
            service_name=service_name,
            namespace=namespace,
            git_commit_sha=revision,
            git_author=author,
            git_commit_message=message,
            git_diff_summary=payload.get("diff_summary"),
            image_tag_previous=payload.get("image_tag_previous"),
            image_tag_new=payload.get("image_tag_new", f"{service_name}:{revision[:7]}"),
            deployed_at=deployed_at,
            source=DeploymentSource.ARGOCD,
            status=DeploymentStatus.SUCCESS if sync_phase in ("Succeeded", "Synced", "Healthy") else DeploymentStatus.FAILURE,
            raw_payload=payload,
        )

    # 2. ArgoCD Notification / Flat payload
    service_name = payload.get("application") or payload.get("service") or payload.get("service_name") or "mock_app"
    revision = payload.get("revision") or payload.get("commit_sha") or payload.get("git_commit_sha") or f"sha-{uuid.uuid4().hex[:8]}"
    author = payload.get("author") or payload.get("commit_author") or "ArgoCD Operator"
    message = payload.get("message") or payload.get("commit_message") or f"Sync {service_name}"
    
    deployed_at = now
    if "deployed_at" in payload:
        try:
            val = payload["deployed_at"]
            deployed_at = datetime.fromisoformat(val.replace("Z", "+00:00")) if isinstance(val, str) else val
        except Exception:
            deployed_at = now

    return DeploymentEvent(
        deployment_id=payload.get("deployment_id") or f"argo-{uuid.uuid4().hex[:8]}",
        service_name=service_name,
        namespace=payload.get("namespace", "production"),
        git_commit_sha=revision,
        git_author=author,
        git_commit_message=message,
        git_diff_summary=payload.get("diff_summary") or payload.get("git_diff_summary"),
        image_tag_previous=payload.get("image_tag_previous"),
        image_tag_new=payload.get("image_tag_new") or f"{service_name}:{revision[:7]}",
        deployed_at=deployed_at,
        source=DeploymentSource.ARGOCD,
        status=DeploymentStatus.SUCCESS,
        raw_payload=payload,
    )


class DeploymentIntelligenceStore:
    """Enterprise store for deployment events with PostgreSQL persistence & in-memory sliding cache."""

    def __init__(self, cache_size: int = 200, db_enabled: bool = True) -> None:
        self._cache: deque[DeploymentEvent] = deque(maxlen=cache_size)
        self._db_enabled = db_enabled
        self._schema_initialized = False

    def _ensure_schema(self) -> None:
        if not self._db_enabled or self._schema_initialized:
            return
        try:
            with psycopg.connect(conn_string(), connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute(DEPLOYMENTS_SCHEMA_SQL)
                conn.commit()
            self._schema_initialized = True
        except Exception as exc:
            logger.debug("PostgreSQL schema initialization skipped or failed: %s", exc)

    def record_deployment(self, deployment: DeploymentEvent) -> DeploymentEvent:
        """Persist a deployment event to memory and PostgreSQL."""
        # 1. Update in-memory sliding cache (newest first or chronological)
        # Remove any existing with same deployment_id
        for idx, item in enumerate(self._cache):
            if item.deployment_id == deployment.deployment_id:
                del self._cache[idx]
                break
        self._cache.appendleft(deployment)

        # 2. Persist to PostgreSQL if available
        if self._db_enabled:
            try:
                self._ensure_schema()
                with psycopg.connect(conn_string(), connect_timeout=3) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            UPSERT_DEPLOYMENT_SQL,
                            (
                                deployment.deployment_id,
                                deployment.service_name,
                                deployment.namespace,
                                deployment.git_commit_sha,
                                deployment.git_author,
                                deployment.git_commit_message,
                                deployment.git_diff_summary,
                                deployment.image_tag_previous,
                                deployment.image_tag_new,
                                deployment.deployed_at,
                                deployment.rollback_supported,
                                deployment.environment,
                                deployment.source.value,
                                deployment.status.value,
                                json.dumps(deployment.raw_payload),
                            ),
                        )
                    conn.commit()
            except Exception as exc:
                logger.debug("Could not persist deployment to Postgres: %s", exc)

        return deployment

    def get_recent(self, limit: int = 20, service: str | None = None) -> list[DeploymentEvent]:
        """Fetch recent deployments from in-memory cache, falling back to PostgreSQL."""
        results: list[DeploymentEvent] = []
        target_norm = service.lower().replace("-", "_") if service else None

        for dep in self._cache:
            if target_norm:
                dep_norm = dep.service_name.lower().replace("-", "_")
                if target_norm not in dep_norm and dep_norm not in target_norm:
                    continue
            results.append(dep)
            if len(results) >= limit:
                return results

        # If cache is low and db enabled, query Postgres
        if len(results) < limit and self._db_enabled:
            try:
                self._ensure_schema()
                with psycopg.connect(conn_string(), connect_timeout=3) as conn:
                    with conn.cursor() as cur:
                        cur.execute(SELECT_RECENT_DEPLOYMENTS_SQL, (limit,))
                        rows = cur.fetchall()
                        for r in rows:
                            dep_obj = DeploymentEvent(
                                deployment_id=r[0],
                                service_name=r[1],
                                namespace=r[2],
                                git_commit_sha=r[3],
                                git_author=r[4],
                                git_commit_message=r[5],
                                git_diff_summary=r[6],
                                image_tag_previous=r[7],
                                image_tag_new=r[8],
                                deployed_at=r[9],
                                rollback_supported=r[10],
                                environment=r[11],
                                source=DeploymentSource(r[12]) if r[12] in DeploymentSource._value2member_map_ else DeploymentSource.MANUAL,
                                status=DeploymentStatus(r[13]) if r[13] in DeploymentStatus._value2member_map_ else DeploymentStatus.SUCCESS,
                                raw_payload=r[14] if isinstance(r[14], dict) else json.loads(r[14] or "{}"),
                                created_at=r[15],
                            )
                            # Avoid duplicates with cache
                            if not any(x.deployment_id == dep_obj.deployment_id for x in results):
                                if target_norm:
                                    dep_norm = dep_obj.service_name.lower().replace("-", "_")
                                    if target_norm not in dep_norm and dep_norm not in target_norm:
                                        continue
                                results.append(dep_obj)
                                if len(results) >= limit:
                                    break
            except Exception as exc:
                logger.debug("Could not query deployments from Postgres: %s", exc)

        return results

    def correlate_incident(
        self,
        incident_time: datetime | None = None,
        affected_services: list[str] | None = None,
        dependency_services: list[str] | None = None,
        window_seconds: float = 1800.0,  # 30-minute default correlation window
    ) -> list[DeploymentCorrelation]:
        """Correlate an incident with recent deployments, scoring causal confidence."""
        now = datetime.now(timezone.utc)
        target_time = incident_time or now
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        aff_norm = [s.lower().replace("-", "_") for s in (affected_services or ["mock_app"])]
        dep_norm = [s.lower().replace("-", "_") for s in (dependency_services or [])]

        all_deployments = self.get_recent(limit=50)
        correlations: list[DeploymentCorrelation] = []

        for dep in all_deployments:
            dep_time = dep.deployed_at
            if dep_time.tzinfo is None:
                dep_time = dep_time.replace(tzinfo=timezone.utc)

            delta_s = (target_time - dep_time).total_seconds()

            # Ignore future deployments with > 60s clock skew
            if delta_s < -60:
                continue

            # Check if outside correlation window
            if delta_s > window_seconds:
                continue

            svc = dep.service_name.lower().replace("-", "_")
            is_direct_service = any(a in svc or svc in a for a in aff_norm)
            is_dependency_service = any(d in svc or svc in d for d in dep_norm)

            confidence = 0.10
            relation = "coincidental"

            if is_direct_service:
                if delta_s <= 180:  # <= 3 minutes
                    confidence = 0.95
                    relation = "direct_service_immediate"
                elif delta_s <= 600:  # <= 10 minutes
                    confidence = 0.85
                    relation = "direct_service_recent"
                else:  # <= 30 minutes
                    confidence = 0.65
                    relation = "direct_service_window"
            elif is_dependency_service:
                if delta_s <= 300:  # <= 5 minutes
                    confidence = 0.70
                    relation = "downstream_dependency"
                else:
                    confidence = 0.40
                    relation = "dependency_window"
            else:
                # Any deployment on the cluster within 5 mins still has minor suspicion
                if delta_s <= 300:
                    confidence = 0.35
                    relation = "cluster_wide_recent"
                else:
                    confidence = 0.10
                    relation = "coincidental"

            # Format human-readable delta
            abs_delta = max(0.0, delta_s)
            if abs_delta < 60:
                time_human = f"{int(abs_delta)}s before incident onset"
            else:
                mins = int(abs_delta // 60)
                secs = int(abs_delta % 60)
                time_human = f"{mins}m {secs}s before incident onset"

            summary = (
                f"Service '{dep.service_name}' deployed {time_human} via {dep.source.value}. "
                f"Commit {dep.git_commit_sha[:7]} by {dep.git_author}: '{dep.git_commit_message}'. "
                f"Confidence: {confidence:.0%}"
            )

            correlations.append(
                DeploymentCorrelation(
                    deployment=dep,
                    confidence_score=confidence,
                    time_delta_seconds=delta_s,
                    time_delta_human=time_human,
                    relation=relation,
                    summary=summary,
                )
            )

        # Sort correlations by confidence descending, then by time proximity
        correlations.sort(key=lambda c: (-c.confidence_score, abs(c.time_delta_seconds)))
        return correlations


_DEPLOYMENT_STORE: DeploymentIntelligenceStore | None = None


def get_deployment_store() -> DeploymentIntelligenceStore:
    global _DEPLOYMENT_STORE
    if _DEPLOYMENT_STORE is None:
        _DEPLOYMENT_STORE = DeploymentIntelligenceStore()
    return _DEPLOYMENT_STORE
