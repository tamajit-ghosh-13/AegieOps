"""Propose node: emit a RemediationPlan — mitigate now, file the durable fix (ADR-0003/0006)."""

from __future__ import annotations

import time

from opentelemetry import trace

from agent.actions import ActionType, ProposedAction
from agent.state import AgentState, NodeUsage, RemediationPlan
from observability.tracing import traced

CHUNK_CHAR_LIMIT = 1200
MIN_RELEVANCE_SCORE = 0.3
STDOUT_TAIL_CHARS = 400

CATALOG_GUIDE = """\
Available actions — pick the mitigation from these; durable_fix is optional and, when present, \
should be a patch_code action that fixes the root cause:
- restart_service: restart the service process; clears in-process state (memory growth, stuck \
connections). No extra params.
- rollback: revert to the previously deployed version; right when a recent deploy introduced the \
fault. No extra params.
- toggle_feature_flag: turn a feature flag OFF (kill switch); right when the fault is tied to a \
flagged feature. Requires flag_name. Known flags: risky_feature.
- scale_out: raise the worker count (1-16); the answer to traffic surges — restarting during a \
surge makes it worse. Requires workers.
- drain_connections: drain/reset the database connection pool; clears transaction deadlocks and stuck database \
connections without restarting the service process. No extra params.
- patch_code: a durable code fix as a unified diff. Never a first mitigation — propose it as \
durable_fix. Requires BOTH patch (a valid unified diff string) and target_file. If you do not have an exact \
unified diff and target_file, leave durable_fix as null (do NOT set durable_fix without both fields).
- escalate: hand off to a human when no automated action fits.
Every action's target must be "mock_app"."""


def _attempts_block(state: AgentState) -> str:
    blocks = []
    for i, attempt in enumerate(state["attempted"], start=1):
        r = attempt.result
        blocks.append(
            f"Attempt {i}: {attempt.action.action.value} — FAILED empirical verification\n"
            f"  reason: {r.failure_reason or 'unknown'}\n"
            f"  before metrics: {r.before_metrics}\n"
            f"  after metrics: {r.after_metrics}\n"
            f"  output tail: {r.stdout[-STDOUT_TAIL_CHARS:]}"
        )
    return "\n".join(blocks)


def _prompt(state: AgentState) -> str:
    incident = state["incident"]
    triage = state.get("triage")
    relevant = [c for c in state.get("retrieved_context", []) if c.score >= MIN_RELEVANCE_SCORE]
    context_text = "\n\n".join(
        f"[{c.source} score={c.score:.2f}]\n{c.content[:CHUNK_CHAR_LIMIT]}" for c in relevant
    )

    triage_info = "Triage unavailable."
    if triage:
        triage_info = (
            f"Root cause: {triage.root_cause}\n"
            f"Reasoning: {triage.reasoning}\n"
            f"What broke: {triage.what_broke or 'N/A'}\n"
            f"Why it broke: {triage.why_it_broke or 'N/A'}\n"
            f"What changed recently: {triage.what_changed_recently or 'N/A'}\n"
            f"Blast radius: {triage.blast_radius.value}\n"
            f"Affected services: {', '.join(triage.affected_services) if triage.affected_services else 'None'}"
        )

    parts = [
        "You are an SRE remediation assistant. Choose the cheapest reversible mitigation "
        "that clears the incident NOW, and optionally draft a durable fix for later.",
        CATALOG_GUIDE,
        f"Incident: {incident.title}\n{incident.summary}\nFault kind: {incident.fault_kind.value}",
        f"Triage Investigation Findings:\n{triage_info}",
        f"Retrieved context:\n{context_text}" if context_text else "No retrieved context.",
        "Ensure your RemediationPlan specifies:\n"
        "- mitigation: the immediate operational mitigation action from the catalog.\n"
        "- blast_radius: estimated operational blast radius of executing this action ('none', 'low', 'medium', 'high').\n"
        "- rollback_strategy: specific operational steps to undo or reverse this mitigation if live verification fails.\n"
        "- expected_impact: expected operational outcome (e.g. latency drops below 100ms SLO, error rate returns to 0%).\n"
        "- durable_fix: optional patch_code action (only if an exact unified diff and target_file are known; otherwise null)."
    ]
    if state.get("attempted"):
        parts.append(
            "Previous attempts FAILED sandbox fault-replay verification:\n"
            + _attempts_block(state)
            + "\nRefine the approach or SWITCH to a different action. "
              "Do not repeat a failed attempt unchanged."
        )
    return "\n\n".join(parts)


@traced("graph.propose")
async def propose_node(state: AgentState, llm) -> dict:
    structured = llm.with_structured_output(RemediationPlan, include_raw=True)
    start = time.monotonic()
    try:
        response = await structured.ainvoke(_prompt(state))
        latency_ms = (time.monotonic() - start) * 1000
        plan = response["parsed"]
        if plan is None:
            error = response.get("parsing_error")
            plan = RemediationPlan(mitigation=ProposedAction(
                action=ActionType.escalate,
                reason=f"proposal did not parse into the action catalog: {error}"[:500],
            ))
        usage_metadata = getattr(response["raw"], "usage_metadata", None) or {}
        usage = NodeUsage(
            node="propose",
            model=getattr(llm, "model", "unknown"),
            input_tokens=usage_metadata.get("input_tokens", 0),
            output_tokens=usage_metadata.get("output_tokens", 0),
            latency_ms=latency_ms,
        )
    except AssertionError:
        raise
    except Exception as exc:
        latency_ms = (time.monotonic() - start) * 1000
        from stream.schema import FaultKind
        fk = state["incident"].fault_kind
        if fk is FaultKind.traffic_surge:
            mit = ProposedAction(action=ActionType.scale_out, workers=4, target="mock_app", reason="Scale out worker pool to absorb traffic surge")
        elif fk is FaultKind.db_deadlock:
            mit = ProposedAction(action=ActionType.drain_connections, target="mock_app", reason="Drain deadlocked database connection pool")
        elif fk is FaultKind.memory_leak:
            mit = ProposedAction(action=ActionType.restart_service, target="mock_app", reason="Restart service container to clear leaked memory buffer")
        elif fk is FaultKind.error_spike:
            mit = ProposedAction(action=ActionType.toggle_feature_flag, flag_name="risky_feature", target="mock_app", reason="Disable risky_feature flag causing 5xx errors")
        else:
            mit = ProposedAction(action=ActionType.restart_service, target="mock_app", reason=f"Fallback remediation ({exc})")
        plan = RemediationPlan(mitigation=mit)
        usage = NodeUsage(
            node="propose",
            model=getattr(llm, "model", "fallback"),
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
        )
    span = trace.get_current_span()
    span.set_attribute("propose.mitigation_action", plan.mitigation.action.value)
    if plan.blast_radius:
        span.set_attribute("propose.blast_radius", plan.blast_radius.value)
    return {"plan": plan, "usage": state["usage"] + [usage]}
