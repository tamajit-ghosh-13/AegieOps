"""Interactive Slack & PagerDuty ChatOps (AegisOps Sprint 4).

Generates Slack Block Kit interactive approval cards for high blast-radius actions,
processes interactive webhooks (/api/hitl/slack-interaction) with HMAC-SHA256
signature verification, unblocks waiting LangGraph HITL gates, and synchronizes
post-mortem incident reports to Jira and PagerDuty.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any

from agent.state import HitlChoice, HitlDecision
from audit.ledger import get_incident_ledger
from hitl.gate import ApprovalGate

logger = logging.getLogger(__name__)

DEFAULT_SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "aegis-slack-signing-secret-prod-2026")


def build_slack_approval_card(
    incident_id: str,
    title: str,
    severity: str = "critical",
    fault_kind: str = "traffic_surge",
    root_cause: str = "Service degradation detected",
    confidence: float = 0.95,
    what_changed: str = "No recent deployments detected",
    proposed_action: str = "scale_out (workers: 4)",
    blast_radius: str = "medium",
    p95_latency_ms: float = 220.0,
    error_rate_pct: float = 12.5,
) -> dict[str, Any]:
    """Generate Slack Block Kit interactive card JSON with operational action buttons."""
    severity_icon = ":red_circle:" if severity.lower() in ("critical", "p0", "p1") else ":warning:"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_icon} AegisOps Incident Alert: {title[:75]}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident_id[:8]}`"},
                {"type": "mrkdwn", "text": f"*Severity:*\n*{severity.upper()}*"},
                {"type": "mrkdwn", "text": f"*Fault Kind:*\n`{fault_kind}`"},
                {"type": "mrkdwn", "text": f"*Blast Radius:*\n`{blast_radius.upper()}`"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root Cause Hypothesis ({confidence:.0%} Confidence):*\n{root_cause}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*What Changed Recently (CI/CD Correlation):*\n{what_changed}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Proposed Remediation:* `{proposed_action}`\n*Live Telemetry Before:* p95: `{p95_latency_ms:.0f}ms` | Errors: `{error_rate_pct:.1f}%`",
            },
        },
        {"type": "divider"},
        {
            "type": "actions",
            "block_id": f"hitl_actions_{incident_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve Action", "emoji": True},
                    "style": "primary",
                    "action_id": "hitl_approve",
                    "value": json.dumps({"incident_id": incident_id, "action": "approve"}),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject & Escalate", "emoji": True},
                    "style": "danger",
                    "action_id": "hitl_reject",
                    "value": json.dumps({"incident_id": incident_id, "action": "reject"}),
                },
            ],
        },
    ]

    return {
        "channel": "#incident-war-room",
        "text": f"AegisOps Incident Approval Required: {title}",
        "blocks": blocks,
    }


def verify_slack_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str = DEFAULT_SLACK_SIGNING_SECRET,
) -> bool:
    """Verify Slack HMAC-SHA256 request signature."""
    try:
        # Prevent replay attacks older than 5 minutes
        req_ts = float(timestamp)
        if abs(time.time() - req_ts) > 300:
            return False
    except Exception:
        return False

    sig_basestring = f"v0:{timestamp}:".encode("utf-8") + body
    expected_sig = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        sig_basestring,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, signature)


class SlackInteractionHandler:
    """Handles Slack Block Kit user clicks and unblocks LangGraph HITL approvals."""

    def __init__(self, signing_secret: str = DEFAULT_SLACK_SIGNING_SECRET) -> None:
        self.signing_secret = signing_secret

    def process_interaction(
        self,
        payload: dict[str, Any],
        approval_gate: ApprovalGate | None = None,
    ) -> dict[str, Any]:
        """Process interactive button click from Slack Block Kit."""
        user = payload.get("user", {})
        username = user.get("username") or user.get("name") or "oncall-sre"
        actions = payload.get("actions", [])
        if not actions:
            return {"status": "ignored", "reason": "No actions in payload"}

        first_action = actions[0]
        action_id = first_action.get("action_id")
        action_val_raw = first_action.get("value", "{}")

        try:
            action_data = json.loads(action_val_raw)
        except Exception:
            action_data = {"incident_id": "unknown", "action": "approve" if "approve" in action_id else "reject"}

        incident_id = action_data.get("incident_id", "unknown")
        choice = HitlChoice.approve if action_id == "hitl_approve" else HitlChoice.reject

        logger.info("Slack HITL interaction received for %s: %s by %s", incident_id, choice.value, username)

        # Unblock LangGraph gate
        unblocked = False
        from hitl.gate import get_approval_gate
        active_gate = approval_gate or get_approval_gate()
        fut = active_gate._pending.get(incident_id)
        if fut and not fut.done():
            active_gate.resolve(
                incident_id=incident_id,
                choice=choice,
                decided_by=username,
                note=f"Action {choice.value}d via Slack Block Kit by {username}",
            )
            unblocked = True

        # Record to immutable audit ledger
        get_incident_ledger().record_event(
            incident_id=incident_id,
            event_type="HITL_DECIDED_SLACK",
            actor=f"slack:{username}",
            payload={
                "choice": choice.value,
                "unblocked": unblocked,
                "user": user,
            },
        )

        status_msg = (
            f":white_check_mark: *Action Approved* by *{username}*. "
            f"Executing operational mitigation on Kubernetes cluster..."
            if choice == HitlChoice.approve
            else f":x: *Action Rejected* by *{username}*. Escalating to tier-3 response team."
        )

        return {
            "status": "success",
            "incident_id": incident_id,
            "choice": choice.value,
            "approver": username,
            "unblocked_gate": unblocked,
            "slack_reply_text": status_msg,
        }


def format_postmortem_for_jira_or_pagerduty(
    incident_id: str,
    postmortem_markdown: str,
    destination: str = "jira",
) -> dict[str, Any]:
    """Format an SRE post-mortem report for external ticketing sync (Jira / PagerDuty)."""
    now = datetime.now(timezone.utc).isoformat()
    if destination.lower() == "jira":
        return {
            "fields": {
                "project": {"key": "INC"},
                "summary": f"[Post-Mortem] Incident {incident_id}",
                "description": postmortem_markdown,
                "issuetype": {"name": "Post-Mortem"},
                "labels": ["aegisops", "autonomous-incident", "sre"],
            },
            "synced_at": now,
        }
    else:  # PagerDuty
        return {
            "note": {
                "content": f"AegisOps Automated Post-Mortem Report:\n\n{postmortem_markdown[:1000]}",
            },
            "incident_id": incident_id,
            "synced_at": now,
        }
