# Graph Report - Aegis  (2026-10-23)

## Corpus Check
- 154 files · ~195,676 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 7, .patch 2, .example 1)

## Summary
- 1217 nodes · 3677 edges · 74 communities (46 shown, 28 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 411 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9f0c8dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_agent_graph.py
- graph.py
- agent/main.py
- PolicyDecision
- get_conn
- LiveApplier
- mock_app/main.py
- test_faults.py
- test_run_evals_tier4.py
- state.py
- ActionType
- RawEvent
- run_evals.py
- HitlChoice
- SandboxExecutor
- SandboxResult
- test_run_evals_tier2.py
- test_dashboard_evals_data.py
- test_agent_nodes.py
- test_sandbox_node.py
- test_eval_metrics.py
- executor.py
- _run_tier2_cli
- test_eval_driver.py
- FaultKind
- test_model_tiering.py
- test_run_evals_tier3.py
- Correlator
- model_tiering.py
- test_report_node.py
- sandbox/demo.py
- score_root_cause
- tracing.py
- test_controls.py
- PolicyVerdict
- setup_tracing
- RemediationPlan
- test_traced_decorator_logs_the_node_with_incident_context
- MemoryLeakFault
- promoted_incident
- _generate.py
- test_obs_defaults.py
- Graphify Agent Instructions and Rules
- dashboard/__init__.py
- observability/__init__.py
- entrypoint.sh
- Continuous Integration Workflow
- Jaeger Tracing Collector
- Mock Target App Service
- PostgreSQL pgvector Store
- Redis Event Stream Service
- aegis
- Aegis Self-Healing Agent Architecture
- schema.py
- get_tracer
- IncidentEvent
- test_consumer_integration.py
- os
- langchain_anthropic

## God Nodes (most connected - your core abstractions)
1. `ActionType` - 131 edges
2. `ProposedAction` - 120 edges
3. `FaultKind` - 107 edges
4. `PolicyDecision` - 66 edges
5. `make_incident()` - 48 edges
6. `SandboxExecutor` - 45 edges
7. `RemediationPlan` - 44 edges
8. `SandboxResult` - 40 edges
9. `initial_state()` - 38 edges
10. `RawEvent` - 37 edges

## Surprising Connections (you probably didn't know these)
- `Policy Test Cases Dataset` --references--> `PolicyEngine`  [INFERRED]
  evals/policy_cases.yaml → policy/engine.py
- `Deterministic Policy Gate` --conceptually_related_to--> `PolicyEngine`  [INFERRED]
  README.md → policy/engine.py
- `test_hitl_choice_has_expired()` --uses--> `HitlChoice`  [INFERRED]
  tests/test_agent_state.py → agent/state.py
- `Database Deadlock Runbook` --references--> `DbDeadlockFault`  [EXTRACTED]
  retrieval/runbooks/db_deadlock.md → mock_app/faults/db_deadlock.py
- `Error Spike Runbook` --references--> `ErrorSpikeFault`  [EXTRACTED]
  retrieval/runbooks/error_spike.md → mock_app/faults/error_spike.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Incident Lifecycle Stages** — readme_incident_lifecycle, readme_sandbox_fault_replay, readme_policy_engine_gate, readme_hitl_approval_brief [EXTRACTED 1.00]
- **Incident Runbooks** — retrieval_runbooks_db_deadlock_runbook, retrieval_runbooks_error_spike_runbook, retrieval_runbooks_memory_leak_runbook, retrieval_runbooks_traffic_surge_runbook [EXTRACTED 1.00]

## Communities (74 total, 28 thin omitted)

### Community 0 - "test_agent_graph.py"
Cohesion: 0.16
Nodes (27): route_after_sandbox(), HitlDecision, Outcome, _Built, _graph(), _plan(), RaisingGate, RaisingLLM (+19 more)

### Community 1 - "graph.py"
Cohesion: 0.12
Nodes (29): build_graph(), LangGraph state machine: Triage -> Retrieve -> Propose -> Sandbox -> Policy ->…, route_after_hitl(), route_entry(), hitl_node(), HITL node: suspend on an evidence brief until a human resolves or the TTL fires., policy_node(), Policy node: gate the plan's mitigation against the deterministic rule engine. (+21 more)

### Community 2 - "agent/main.py"
Cohesion: 0.20
Nodes (14): main(), _process_incident(), _process_promotion(), Redis, Demo entrypoint: run the full agent graph with HITL web UI., _read_latest_incidents(), langchain_mcp_adapters_client, LangGraph .ainvoke config that tags the run for LangSmith + Jaeger cross-link. (+6 more)

### Community 3 - "PolicyDecision"
Cohesion: 0.12
Nodes (51): route_after_policy(), PolicyDecision, Incident Remediation Approval UI Walkthrough, Policy Test Cases Dataset, _seed_history(), PolicyEngine, Any, HITL Approval Brief (+43 more)

### Community 4 - "get_conn"
Cohesion: 0.07
Nodes (53): Path, Shared patch rendering: containment guard + git apply in a temp tree. Used by…, Apply `patch` to repo_root/target_file in a temp tree; return the patched bytes., render_patched_file(), Connection, dotenv, mcp, mcp_client_stdio (+45 more)

### Community 5 - "LiveApplier"
Cohesion: 0.08
Nodes (21): LiveApplier, Path, Applies a policy-cleared, sandbox-proven mitigation to the live target., _tar_single_file(), docker_client_or_skip(), FakeContainer, FakeDocker, run() (+13 more)

### Community 6 - "mock_app/main.py"
Cohesion: 0.14
Nodes (22): contextlib, get, clear_fault(), _emit_loop(), FlagUpdate, _get_fault(), get_scale(), healthz() (+14 more)

### Community 7 - "test_faults.py"
Cohesion: 0.08
Nodes (19): ErrorSpikeFault, Called by GET /work; 500s only while the risky feature flag is on., Deterministic capacity model: latency grows with load per worker., TrafficSurgeFault, Error Spike Runbook, Traffic Surge Runbook, FakeProducer, test_db_deadlock_emits_on_alternate_ticks() (+11 more)

### Community 8 - "test_run_evals_tier4.py"
Cohesion: 0.11
Nodes (25): get_llm(), get_propose_llm(), get_triage_llm(), Any, Chat models used by the agent graph. Triage is a bounded classification +…, DirectSearchAdapter, Wraps a sync psycopg connection as an async search tool `retrieve_node` accepts., _expected_outcome() (+17 more)

### Community 9 - "state.py"
Cohesion: 0.08
Nodes (55): PostgresReportSink, PrintSink, Report sinks: stdout for demos, Postgres for the dashboard (spec section 12)., IncidentReport, NodeUsage, Agent state contract: typed models for all graph nodes., _incident_rows(), main() (+47 more)

### Community 10 - "ActionType"
Cohesion: 0.14
Nodes (27): ActionMetadata, ActionType, BlastRadius, ProposedAction, BaseModel, Enum, str, Typed remediation action catalog: the agent's entire action space (ADR-0001). (+19 more)

### Community 11 - "RawEvent"
Cohesion: 0.08
Nodes (27): ABC, hashlib, app_version(), Runtime controls the remediation actions manipulate: feature flags and worker…, Deploy version this process simulates; 'previous' = the rollback target, i.e.…, Fault, make_dedup_key(), Fault ABC shared by all injectable faults. (+19 more)

### Community 12 - "run_evals.py"
Cohesion: 0.14
Nodes (20): Fraction of category='unsafe' cases NOT auto-allowed. Headline: must be 1.0., Fraction of all cases whose decision exactly matches ground truth., unsafe_blocked_rate(), verdict_accuracy(), load_cases(), _NoopApplier, _NoopRegistry, _NoopSink (+12 more)

### Community 13 - "HitlChoice"
Cohesion: 0.05
Nodes (64): HitlChoice, Enum, str, fastapi_responses, fastapi_testclient, Future, AutoApprover, Auto-approver stub: eval runs measure the apply path unattended (ADR-0005). (+56 more)

### Community 14 - "SandboxExecutor"
Cohesion: 0.10
Nodes (20): SandboxExecutor, BoomContainer, DummyContainer, FakeContainer, FakeContainers, FakeDocker, GoneContainer, Stands in for a running app container in _verify_sync flow tests below; the… (+12 more)

### Community 15 - "SandboxResult"
Cohesion: 0.12
Nodes (7): SandboxResult, Empirical fault replay (ADR-0002): reproduce the fault in a disposable…, FakeExecutor, Queue of sandbox results, one per verify() call (last one repeats)., test_sandbox_result_validates(), test_sandbox_result_v2_carries_evidence(), test_sandbox_result_v2_fields_default_none()

### Community 16 - "test_run_evals_tier2.py"
Cohesion: 0.08
Nodes (20): argparse, _apply_geval(), Path, Shared results envelope for all tiers., Replay each case through triage->retrieve->propose, then override the retrieved…, Score G-Eval root-cause quality in the MAIN thread, AFTER the async graph…, First case per distinct fault_kind, preserving fixture order — the default…, _representative_cases() (+12 more)

### Community 17 - "test_dashboard_evals_data.py"
Cohesion: 0.11
Nodes (39): cache_data, _eval_runs(), _format_metric(), _render_evaluation(), EvalRun, headline_scorecard(), latest_per_tier(), load_eval_runs() (+31 more)

### Community 18 - "test_agent_nodes.py"
Cohesion: 0.11
Nodes (19): propose_node(), initial_state(), Seed a graph run. Promoted durable-fix runs preset `plan` (and reuse the…, FakeLLM, FakeRaw, FakeSearchTool, FakeStructuredLLM, _FakeStructuredResult (+11 more)

### Community 19 - "test_sandbox_node.py"
Cohesion: 0.29
Nodes (12): Sandbox node: empirical fault replay of the plan's mitigation (ADR-0002)., sandbox_node(), AttemptRecord, One sandbox-verified attempt: what was tried, what the replay proved (ADR-0006)., FakeExecutor, Sandbox node: verify() wiring, attempt tracking, skip logic (ADR-0002/0006)., _result(), _state() (+4 more)

### Community 20 - "test_eval_metrics.py"
Cohesion: 0.19
Nodes (21): action_selection_accuracy(), durable_fix_valid_path_rate(), mean_confidence(), pct_below_confidence_floor(), Path, Deterministic Tier-1 metrics — owned plain functions, not framework-wrapped…, Of the drafted patch_code durable fixes, the fraction whose target_file…, remediation_success_rate() (+13 more)

### Community 21 - "executor.py"
Cohesion: 0.17
Nodes (16): Per-action live appliers: act on the running mock_app compose service., docker_errors, docker_types, httpx, io, Docker-based sandbox: apply patch, run pytest in an isolated container., check_degraded(), check_recovered() (+8 more)

### Community 22 - "_run_tier2_cli"
Cohesion: 0.21
Nodes (12): _dependency_status(), _dispatch(), main(), Cheap, exception-swallowing probes for the optional eval dependencies, used to…, Graceful skip if required dependencies are unavailable; never touches exit…, Route a parsed args namespace to the right tier(s). Tier 1 is the sole exit-…, _run_tier2_cli(), Tests for `--tier all` orchestration and the shared `_dependency_status` skip… (+4 more)

### Community 23 - "test_eval_driver.py"
Cohesion: 0.27
Nodes (7): run_propose(), _case(), _FakeLLM, _FakeSearch, _FakeStructured, test_driver_handles_triage_parse_failure(), test_driver_returns_scorable_result()

### Community 24 - "FaultKind"
Cohesion: 0.16
Nodes (20): FaultKind, is_reproducible(), test_all_v1_faults_are_reproducible(), app_image(), executor(), _patch_action(), fixture, Empirical fault-replay verification against real containers. Requires Docker… (+12 more)

### Community 25 - "test_model_tiering.py"
Cohesion: 0.12
Nodes (17): dataclasses, EvalCase, load_cases(), Load the offline-replay incident corpus + ground truth (ADR-0007)., test_corpus_has_expected_distribution(), test_every_case_parses_and_is_well_formed(), test_traffic_surge_is_scale_out_only(), _case() (+9 more)

### Community 26 - "test_run_evals_tier3.py"
Cohesion: 0.20
Nodes (9): Replay each case's proposed mitigation through the Docker sandbox and score…, run_tier3(), _tier3_metrics(), app_image(), fixture, Tier-3 remediation replay: proposed mitigation -> Docker sandbox fault replay., test_tier3_assembles_result(), verify() (+1 more)

### Community 27 - "Correlator"
Cohesion: 0.23
Nodes (11): datetime, Correlator, Close windows that have gone idle or exceeded the max window; return their…, Deduplicates raw events and groups them into IncidentEvents over a correlation…, Clock, make_event(), test_burst_then_idle_closes_one_incident_with_all_events(), test_dedup_collapses_repeats_into_single_event() (+3 more)

### Community 28 - "model_tiering.py"
Cohesion: 0.14
Nodes (19): _case_record(), _compare(), main(), Path, Model-tiering experiment: compare per-node model choices on accuracy and cost…, Graceful skip (print + return, no write) if the API key is unset or Postgres is…, Trimmed per-case row for the artifact: enough to see WHICH incident's action…, Delta of a candidate config against the baseline. cost_delta is the… (+11 more)

### Community 29 - "test_report_node.py"
Cohesion: 0.24
Nodes (22): _determine_outcome(), Report node: emit the final IncidentReport; file the durable fix (ADR-0003)., report_node(), _attempt(), FakeRegistry, FakeSink, _patch_action(), Report node v2 tests: outcome derivation, durable-fix filing, report… (+14 more)

### Community 30 - "sandbox/demo.py"
Cohesion: 0.43
Nodes (6): docker, build_action(), ensure_images(), main(), Phase-2 demo CLI: inject a fault, apply an action, print verified before/after…, run_one()

### Community 31 - "score_root_cause"
Cohesion: 0.16
Nodes (8): _deepeval_available(), DeepEval G-Eval root-cause reasoning quality, judged by a custom Claude model.…, # NOTE: verified end-to-end against deepeval 4.1.3 + a live ANTHROPIC_API_KEY at, score_root_cause(), Defensive-wrapper proof: even if _deepeval_available() claims deepeval is…, test_score_is_none_when_deepeval_missing(), test_score_is_none_without_key(), test_scored_path_error_degrades_to_none()

### Community 32 - "tracing.py"
Cohesion: 0.16
Nodes (18): observability, OpenTelemetry tracing setup and helpers (ADR-0009). One trace per incident,…, opentelemetry, opentelemetry_exporter_otlp_proto_http_trace_exporter, opentelemetry_propagate, opentelemetry_sdk_resources, opentelemetry_sdk_trace, opentelemetry_sdk_trace_export (+10 more)

### Community 33 - "test_controls.py"
Cohesion: 0.17
Nodes (6): FeatureFlags, ScaleState, test_flag_set_and_unknown_flag_raises(), test_flags_default_off(), test_scale_defaults_and_bounds(), test_scale_env_misconfig_clamped_not_crashing()

### Community 34 - "PolicyVerdict"
Cohesion: 0.21
Nodes (11): apply_node(), Apply node: execute the policy-cleared mitigation on the live target., PolicyVerdict, test_policy_verdict_validates(), SpyApplier, SpyEngine, _state(), test_apply_failure_is_caught_and_not_recorded() (+3 more)

### Community 35 - "setup_tracing"
Cohesion: 0.29
Nodes (7): Install a global TracerProvider exporting to OTLP/HTTP. Idempotent., Force-flush + shutdown so short-lived processes export their spans. When Jaeger…, setup_tracing(), shutdown_tracing(), main(), test_setup_tracing_is_idempotent_and_returns_provider(), TracerProvider

### Community 36 - "RemediationPlan"
Cohesion: 0.14
Nodes (20): BaseModel, Mitigate-first plan: mitigation executes now, durable_fix is filed as follow-up…, RemediationPlan, TriageResult, _action(), make_incident(), _result(), test_attempt_record_pairs_action_with_evidence() (+12 more)

### Community 37 - "test_traced_decorator_logs_the_node_with_incident_context"
Cohesion: 0.29
Nodes (5): fault_kind, _Incident, Each traced node emits one log line, so the lifecycle is visible in the…, test_traced_decorator_logs_the_node_with_incident_context(), test_traced_decorator_opens_span_with_incident_attrs()

### Community 38 - "MemoryLeakFault"
Cohesion: 0.25
Nodes (3): Incident Ground Truth Dataset, MemoryLeakFault, Memory Leak Runbook

### Community 39 - "promoted_incident"
Cohesion: 0.47
Nodes (5): promoted_incident(), Derived identity for a promoted durable-fix run, so its report upserts a…, agent.main pure helpers: promoted-run identity so promotion reports don't…, test_promoted_incident_does_not_mutate_original(), test_promoted_incident_suffixes_id_and_preserves_other_fields()

### Community 42 - "_generate.py"
Cohesion: 0.29
Nodes (5): _incident(), One-shot: emit schema-authentic IncidentEvent fixtures. Re-run to regenerate., _raw(), itertools, json

### Community 71 - "schema.py"
Cohesion: 0.15
Nodes (14): asyncio, Durable-fix follow-up registry + promotion queue (ADR-0003/0005)., Phase 5 demo: trigger a fault, run the pipeline, print the Jaeger trace URL.…, redis_asyncio, redis_exceptions, Consumes aegis:events, deduplicates and correlates them into IncidentEvents., _Window, from_stream_fields() (+6 more)

### Community 72 - "get_tracer"
Cohesion: 0.29
Nodes (7): get_tracer(), inject_trace_context(), Serialize the current context into a W3C carrier (traceparent/tracestate)., decorator(), wrapper(), test_traceparent_round_trip_preserves_trace_id(), Tracer

### Community 73 - "IncidentEvent"
Cohesion: 0.23
Nodes (7): Consumer, Redis, XREADGROUP loop with bounded in-flight processing (backpressure) feeding a…, One-time read of this consumer's previously-pending entries on startup., Process one poll cycle: drain backlog if high, read new entries, sweep…, IncidentEvent, BaseModel

### Community 75 - "test_consumer_integration.py"
Cohesion: 0.19
Nodes (13): fakeredis_aioredis, mock_app_faults, client(), fake_redis(), fixture, Snapshot + restore the global OTel tracer provider around every test.…, reset_faults(), reset_tracer_provider() (+5 more)

### Community 76 - "os"
Cohesion: 0.28
Nodes (8): add_trace_context(), structlog configuration: every line carries incident_id + trace_id (ADR-0009)., structlog processor: stamp the active span's trace_id/span_id onto the line., setup_logging(), os, structlog, test_add_trace_context_stamps_active_span(), test_log_line_carries_incident_id_and_trace_id()

## Knowledge Gaps
- **18 isolated node(s):** `aegis`, `entrypoint.sh script`, `fault_kind`, `Sandbox Fault Replay`, `Policy Test Cases Dataset` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 400 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FaultKind` connect `FaultKind` to `test_agent_graph.py`, `PolicyDecision`, `mock_app/main.py`, `test_faults.py`, `state.py`, `ActionType`, `RawEvent`, `run_evals.py`, `HitlChoice`, `SandboxExecutor`, `SandboxResult`, `test_agent_nodes.py`, `test_sandbox_node.py`, `executor.py`, `test_eval_driver.py`, `test_model_tiering.py`, `test_run_evals_tier3.py`, `Correlator`, `sandbox/demo.py`, `RemediationPlan`, `MemoryLeakFault`, `_generate.py`, `schema.py`, `test_consumer_integration.py`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `ProposedAction` connect `ActionType` to `test_agent_graph.py`, `graph.py`, `PolicyDecision`, `LiveApplier`, `state.py`, `run_evals.py`, `HitlChoice`, `SandboxExecutor`, `SandboxResult`, `test_agent_nodes.py`, `test_sandbox_node.py`, `executor.py`, `test_eval_driver.py`, `FaultKind`, `test_model_tiering.py`, `test_run_evals_tier3.py`, `test_report_node.py`, `sandbox/demo.py`, `PolicyVerdict`, `RemediationPlan`, `schema.py`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `ActionType` connect `ActionType` to `test_agent_graph.py`, `graph.py`, `PolicyVerdict`, `PolicyDecision`, `RemediationPlan`, `LiveApplier`, `state.py`, `HitlChoice`, `SandboxExecutor`, `test_agent_nodes.py`, `test_sandbox_node.py`, `executor.py`, `test_eval_driver.py`, `FaultKind`, `test_model_tiering.py`, `test_run_evals_tier3.py`, `test_report_node.py`, `sandbox/demo.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 94 inferred relationships involving `ActionType` (e.g. with `route_after_policy()` and `propose_node()`) actually correct?**
  _`ActionType` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ProposedAction` (e.g. with `propose_node()` and `AttemptRecord`) actually correct?**
  _`ProposedAction` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 67 inferred relationships involving `FaultKind` (e.g. with `IncidentReport` and `TriageResult`) actually correct?**
  _`FaultKind` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `PolicyDecision` (e.g. with `route_after_policy()` and `_determine_outcome()`) actually correct?**
  _`PolicyDecision` has 46 INFERRED edges - model-reasoned connections that need verification._