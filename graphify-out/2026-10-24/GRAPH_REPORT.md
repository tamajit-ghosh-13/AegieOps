# Graph Report - Aegis  (2026-10-24)

## Corpus Check
- 181 files · ~208,730 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 7, .patch 2, .example 1)

## Summary
- 1497 nodes · 4621 edges · 89 communities (58 shown, 31 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 558 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9f0c8dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthService
- graph.py
- observability/router.py
- ActionType
- get_conn
- LiveApplier
- mock_app/main.py
- test_faults.py
- model_tiering.py
- test_dashboard_operations_data.py
- SystemTelemetrySnapshot
- RawEvent
- run_evals.py
- ApprovalGate
- test_sandbox_executor.py
- SandboxExecutor
- _run_tier2_cli
- test_dashboard_evals_data.py
- make_incident
- test_agent_graph.py
- test_eval_metrics.py
- conftest.py
- _dependency_status
- verifier.py
- FaultKind
- test_model_tiering.py
- _FakeStructuredResult
- datetime
- agent/main.py
- test_sandbox_node.py
- sandbox/demo.py
- score_root_cause
- tracing.py
- test_controls.py
- time
- app.py
- test_hitl_gate.py
- test_investigation_slice3.py
- propose.py
- test_run_evals_tier4.py
- IncidentReport
- test_observability_slice2.py
- NodeUsage
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
- _generate.py
- auth/__init__.py
- test_closed_loop_verify.py
- executor.py
- web.py
- DbDeadlockFault
- test_auth_and_rbac_slice6.py
- langchain_anthropic
- create_hitl_app
- state.py
- DurableFixRegistry
- TraceSummary
- parse_prometheus_text
- schema.py
- audit/__init__.py
- IncidentLedger
- TrafficSurgeFault
- test_run_evals_tier3.py
- test_traced_decorator_logs_the_node_with_incident_context
- Incident Lifecycle Pipeline

## God Nodes (most connected - your core abstractions)
1. `ActionType` - 146 edges
2. `FaultKind` - 139 edges
3. `ProposedAction` - 135 edges
4. `PolicyDecision` - 73 edges
5. `make_incident()` - 59 edges
6. `RemediationPlan` - 54 edges
7. `SandboxResult` - 47 edges
8. `initial_state()` - 46 edges
9. `SandboxExecutor` - 45 edges
10. `IncidentEvent` - 44 edges

## Surprising Connections (you probably didn't know these)
- `Deterministic Policy Gate` --conceptually_related_to--> `PolicyEngine`  [INFERRED]
  README.md → policy/engine.py
- `Policy Test Cases Dataset` --references--> `PolicyEngine`  [INFERRED]
  evals/policy_cases.yaml → policy/engine.py
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

## Communities (89 total, 31 thin omitted)

### Community 0 - "AuthService"
Cohesion: 0.06
Nodes (53): alias, get_current_user(), FastAPI dependencies for JWT authentication and RBAC validation (AegisOps Slice…, Extract and validate bearer token from Header, Query, or Cookie., Enforce that the authenticated user possesses one of the allowed roles., require_role(), LoginRequest, BaseModel (+45 more)

### Community 1 - "graph.py"
Cohesion: 0.17
Nodes (25): build_graph(), LangGraph state machine: Triage -> Retrieve -> Propose -> Sandbox -> Policy ->…, route_after_apply(), route_after_hitl(), route_entry(), apply_node(), Apply node: execute the policy-cleared mitigation on the live target (AegisOps…, hitl_node() (+17 more)

### Community 2 - "observability/router.py"
Cohesion: 0.09
Nodes (30): LedgerEntry, Immutable Incident Ledger (AegisOps Slice 4). Append-only, cryptographically…, generate_postmortem(), PostMortem, BaseModel, Automated SRE Post-Mortem Report Generator (AegisOps Slice 5). Generates…, Generate structured and Markdown post-mortem for a given incident., control_fault() (+22 more)

### Community 3 - "ActionType"
Cohesion: 0.05
Nodes (111): ActionMetadata, ActionType, BlastRadius, ProposedAction, BaseModel, Enum, str, route_after_policy() (+103 more)

### Community 4 - "get_conn"
Cohesion: 0.07
Nodes (50): Connection, dataclasses, drive_propose(), Tier-2 offline driver: replay a fixture through triage -> retrieve -> propose…, Shared core: run triage -> retrieve -> propose and return the scorable tier-2…, run_propose(), EvalCase, Load the offline-replay incident corpus + ground truth (ADR-0007). (+42 more)

### Community 5 - "LiveApplier"
Cohesion: 0.05
Nodes (37): LiveApplier, Path, Per-action live appliers: act on the running mock_app compose service., Applies a policy-cleared, sandbox-proven mitigation to the live target., Automated rollback safeguard: undoes an action if post-recovery verification…, _tar_single_file(), Path, Shared patch rendering: containment guard + git apply in a temp tree. Used by… (+29 more)

### Community 6 - "mock_app/main.py"
Cohesion: 0.12
Nodes (26): contextlib, clear_fault(), drain_connections(), _emit_loop(), FlagUpdate, _get_fault(), get_scale(), healthz() (+18 more)

### Community 7 - "test_faults.py"
Cohesion: 0.08
Nodes (19): Incident Ground Truth Dataset, ErrorSpikeFault, Called by GET /work; 500s only while the risky feature flag is on., MemoryLeakFault, Error Spike Runbook, Memory Leak Runbook, is_reproducible(), FakeProducer (+11 more)

### Community 8 - "model_tiering.py"
Cohesion: 0.15
Nodes (17): _case_record(), _compare(), main(), Path, Model-tiering experiment: compare per-node model choices on accuracy and cost…, Graceful skip (print + return, no write) if the API key is unset or Postgres is…, Trimmed per-case row for the artifact: enough to see WHICH incident's action…, Delta of a candidate config against the baseline. cost_delta is the… (+9 more)

### Community 9 - "test_dashboard_operations_data.py"
Cohesion: 0.15
Nodes (29): _render_operations(), expired_approvals(), incident_cost_usd(), IncidentRow, node_usage_stats(), open_durable_fixes(), outcome_breakdown(), _percentile() (+21 more)

### Community 10 - "SystemTelemetrySnapshot"
Cohesion: 0.30
Nodes (11): BaseModel, SystemTelemetrySnapshot, Poll telemetry snapshot and return an IncidentEvent if an unhandled SLO breach…, TelemetrySentinel, TopologySnapshot, FakeHub, asyncio, Unit tests for TelemetrySentinel (AegisOps Dual-Signal Detection). (+3 more)

### Community 11 - "RawEvent"
Cohesion: 0.11
Nodes (21): ABC, Fault, make_dedup_key(), Fault ABC shared by all injectable faults., Stable key for signals that represent the 'same' underlying condition., Start the fault's background misbehavior., Stop the fault and reset its state., Called periodically while active; publishes RawEvents reflecting current state. (+13 more)

### Community 12 - "run_evals.py"
Cohesion: 0.20
Nodes (16): Fraction of category='unsafe' cases NOT auto-allowed. Headline: must be 1.0., Fraction of all cases whose decision exactly matches ground truth., unsafe_blocked_rate(), verdict_accuracy(), load_cases(), Path, Tier-1/2/3/4 evals runner (ADR-0007). Tier 1: seeded safe/unsafe proposals ->…, Run tier 1 (pure Python, always runnable) and return its gate exit code: 0 iff… (+8 more)

### Community 13 - "ApprovalGate"
Cohesion: 0.15
Nodes (17): Future, ApprovalGate, test_env_ttl_used_when_not_passed(), _plan_with_fix(), HITL web app: brief rendering, decision verb validation, promote (ADR-0005)., _sandbox(), _seed_pending(), test_api_pending_and_durable_fixes() (+9 more)

### Community 14 - "test_sandbox_executor.py"
Cohesion: 0.09
Nodes (19): BoomContainer, DummyContainer, FakeContainer, FakeContainers, FakeDocker, GoneContainer, Stands in for a running app container in _verify_sync flow tests below; the…, M-2 carry-in: a recovered fault stops reporting its metric; the HITL brief must… (+11 more)

### Community 16 - "_run_tier2_cli"
Cohesion: 0.10
Nodes (19): _apply_geval(), _missing_runbooks(), Shared results envelope for all tiers., Replay each case through triage->retrieve->propose, then override the retrieved…, Score G-Eval root-cause quality in the MAIN thread, AFTER the async graph…, Reproducibility guard: which of the 4 expected fault-kind runbooks are absent…, Graceful skip if required dependencies are unavailable; never touches exit…, run_tier2() (+11 more)

### Community 17 - "test_dashboard_evals_data.py"
Cohesion: 0.12
Nodes (37): _eval_runs(), _render_evaluation(), EvalRun, headline_scorecard(), latest_per_tier(), load_eval_runs(), metric_series(), _normalize_tier() (+29 more)

### Community 18 - "make_incident"
Cohesion: 0.20
Nodes (17): Mitigate-first plan: mitigation executes now, durable_fix is filed as follow-up…, RemediationPlan, field_validator, FakeStructuredLLM, make_incident(), make_triage(), _plan(), Captures prompts; returns queued {'raw','parsed'} responses. (+9 more)

### Community 19 - "test_agent_graph.py"
Cohesion: 0.08
Nodes (58): route_after_sandbox(), _determine_outcome(), report_node(), HitlChoice, HitlDecision, initial_state(), Outcome, Enum (+50 more)

### Community 20 - "test_eval_metrics.py"
Cohesion: 0.19
Nodes (21): action_selection_accuracy(), durable_fix_valid_path_rate(), mean_confidence(), pct_below_confidence_floor(), Path, Deterministic Tier-1 metrics — owned plain functions, not framework-wrapped…, Of the drafted patch_code durable fixes, the fraction whose target_file…, remediation_success_rate() (+13 more)

### Community 21 - "conftest.py"
Cohesion: 0.19
Nodes (10): fakeredis_aioredis, mock_app_faults, Phase 5 demo: trigger a fault, run the pipeline, print the Jaeger trace URL.…, redis_asyncio, client(), fake_redis(), fixture, Snapshot + restore the global OTel tracer provider around every test.… (+2 more)

### Community 22 - "_dependency_status"
Cohesion: 0.19
Nodes (11): argparse, _dependency_status(), _dispatch(), main(), Cheap, exception-swallowing probes for the optional eval dependencies, used to…, Route a parsed args namespace to the right tier(s). Tier 1 is the sole exit-…, Tests for `--tier all` orchestration and the shared `_dependency_status` skip…, A failed get_conn() (Postgres restart, connection limit, DDL/lock error between… (+3 more)

### Community 23 - "verifier.py"
Cohesion: 0.16
Nodes (12): LiveVerifier, AsyncClient, Live closed-loop telemetry verifier (AegisOps Slice 1). Monitors live…, Samples live telemetry to assert that an applied operational fix actually cured…, Fetch real-time metrics directly from the live service., Polls live metrics until recovery is asserted or timeout expires., asyncio, Unit tests for LiveVerifier (AegisOps Slice 1). (+4 more)

### Community 24 - "FaultKind"
Cohesion: 0.14
Nodes (22): FaultKind, str, app_image(), executor(), _patch_action(), fixture, Empirical fault-replay verification against real containers. Requires Docker…, sandbox_image() (+14 more)

### Community 25 - "test_model_tiering.py"
Cohesion: 0.18
Nodes (9): _case(), _FakeLLM, _FakeSearch, _FakeStructured, Each config keeps a diagnosable per-case `results` list, and `comparisons`…, Fast, offline test for the model-tiering experiment runner. No network, no…, Same real pricing-table model string used for both roles (triage and propose…, test_run_experiment_sonnet_triage_costs_more_than_haiku() (+1 more)

### Community 26 - "_FakeStructuredResult"
Cohesion: 0.22
Nodes (4): FakeLLM, FakeRaw, _FakeStructuredResult, Backs FakeLLM.with_structured_output; keyed-by-type fake used by…

### Community 27 - "datetime"
Cohesion: 0.23
Nodes (11): datetime, Correlator, Close windows that have gone idle or exceeded the max window; return their…, Deduplicates raw events and groups them into IncidentEvents over a correlation…, Clock, make_event(), test_burst_then_idle_closes_one_incident_with_all_events(), test_dedup_collapses_repeats_into_single_event() (+3 more)

### Community 28 - "agent/main.py"
Cohesion: 0.06
Nodes (51): main(), _process_incident(), _process_promotion(), promoted_incident(), Redis, Demo entrypoint: run the full agent graph with HITL web UI., Derived identity for a promoted durable-fix run, so its report upserts a…, _read_latest_incidents() (+43 more)

### Community 29 - "test_sandbox_node.py"
Cohesion: 0.29
Nodes (12): Sandbox node: empirical fault replay of the plan's mitigation (ADR-0002)., sandbox_node(), AttemptRecord, One sandbox-verified attempt: what was tried, what the replay proved (ADR-0006)., FakeExecutor, Sandbox node: verify() wiring, attempt tracking, skip logic (ADR-0002/0006)., _result(), _state() (+4 more)

### Community 30 - "sandbox/demo.py"
Cohesion: 0.43
Nodes (6): docker, build_action(), ensure_images(), main(), Phase-2 demo CLI: inject a fault, apply an action, print verified before/after…, run_one()

### Community 31 - "score_root_cause"
Cohesion: 0.16
Nodes (8): _deepeval_available(), DeepEval G-Eval root-cause reasoning quality, judged by a custom Claude model.…, # NOTE: verified end-to-end against deepeval 4.1.3 + a live ANTHROPIC_API_KEY at, score_root_cause(), Defensive-wrapper proof: even if _deepeval_available() claims deepeval is…, test_score_is_none_when_deepeval_missing(), test_score_is_none_without_key(), test_scored_path_error_degrades_to_none()

### Community 32 - "tracing.py"
Cohesion: 0.14
Nodes (19): functools, observability, OpenTelemetry tracing setup and helpers (ADR-0009). One trace per incident,…, opentelemetry, opentelemetry_exporter_otlp_proto_http_trace_exporter, opentelemetry_propagate, opentelemetry_sdk_resources, opentelemetry_sdk_trace (+11 more)

### Community 33 - "test_controls.py"
Cohesion: 0.17
Nodes (6): FeatureFlags, ScaleState, test_flag_set_and_unknown_flag_raises(), test_flags_default_off(), test_scale_defaults_and_bounds(), test_scale_env_misconfig_clamped_not_crashing()

### Community 35 - "app.py"
Cohesion: 0.22
Nodes (9): cache_data, _format_metric(), _incident_rows(), main(), Aegis dashboard (spec section 12, ADR-0011): Operations from Postgres,…, fetch_incident_rows(), Every persisted incident report, newest first., pandas (+1 more)

### Community 36 - "test_hitl_gate.py"
Cohesion: 0.24
Nodes (14): asyncio, build_brief(), Async approval gate: evidence briefs with TTL expiry (ADR-0005)., Decision brief, not raw data: everything the approver needs on one card., _ask(), _passing_sandbox(), _plan_plain(), _plan_with_durable_fix() (+6 more)

### Community 37 - "test_investigation_slice3.py"
Cohesion: 0.18
Nodes (17): _format_telemetry(), _prompt(), Triage node: classify the incident and propose a root-cause hypothesis…, Fetch real-time unified telemetry snapshot across all observability signals., REDMetrics, build_topology(), DependencyEdge, HealthStatus (+9 more)

### Community 38 - "propose.py"
Cohesion: 0.60
Nodes (4): _attempts_block(), _prompt(), propose_node(), Propose node: emit a RemediationPlan — mitigate now, file the durable fix…

### Community 39 - "test_run_evals_tier4.py"
Cohesion: 0.15
Nodes (11): _expected_outcome(), _NoopApplier, _NoopRegistry, _NoopSink, Map ground-truth expected_policy -> the outcome the e2e run should land on…, Run each case through the WHOLE compiled graph with a real PolicyEngine and an…, run_tier4(), _tier4_metrics() (+3 more)

### Community 40 - "IncidentReport"
Cohesion: 0.26
Nodes (11): PostgresReportSink, PrintSink, Report sinks: stdout for demos, Postgres for the dashboard (spec section 12)., IncidentReport, conn_string(), docker, Report sink tests: PrintSink (stdout) and PostgresReportSink (dashboard…, _report() (+3 more)

### Community 41 - "test_observability_slice2.py"
Cohesion: 0.13
Nodes (18): httpx, get_observability_hub(), ObservabilityHub, Unified observability hub (AegisOps Slice 2). Aggregates Prometheus RED…, JaegerClient, AsyncClient, Jaeger distributed trace client and correlator (AegisOps Slice 2). Extracts…, List all services instrumented in Jaeger. (+10 more)

### Community 43 - "NodeUsage"
Cohesion: 0.44
Nodes (9): NodeUsage, cost_usd(), Static pricing table: NodeUsage tokens -> dollars (ADR-0010). Prices are $ per…, total_cost_usd(), test_node_usage_validates(), test_known_model_cost_is_tokens_times_price(), test_total_sums_across_usages(), test_unknown_model_costs_zero() (+1 more)

### Community 71 - "_generate.py"
Cohesion: 0.33
Nodes (4): _incident(), One-shot: emit schema-authentic IncidentEvent fixtures. Re-run to regenerate., _raw(), itertools

### Community 74 - "test_closed_loop_verify.py"
Cohesion: 0.27
Nodes (11): route_after_verify(), LiveVerificationResult, Post-remediation live telemetry assertion (AegisOps Slice 1)., _make_incident(), asyncio, Unit and integration tests for closed-loop recovery and verification (AegisOps…, test_rollback_node_invokes_applier_rollback(), test_route_after_apply_routes_to_verify_when_applied() (+3 more)

### Community 75 - "executor.py"
Cohesion: 0.20
Nodes (14): docker_errors, docker_types, Docker-based sandbox: apply patch, run pytest in an isolated container., check_degraded(), check_recovered(), Pure recovery-assertion rules for sandbox fault replay (ADR-0002). No Docker…, should_retrigger(), test_check_degraded_floors() (+6 more)

### Community 76 - "web.py"
Cohesion: 0.25
Nodes (14): fastapi_responses, _brief_card(), index(), _durable_fix_card(), _durable_fix_row(), _esc(), _evidence_table(), _policy_block() (+6 more)

### Community 77 - "DbDeadlockFault"
Cohesion: 0.11
Nodes (6): app_version(), Runtime controls the remediation actions manipulate: feature flags and worker…, Deploy version this process simulates; 'previous' = the rollback target, i.e.…, DbDeadlockFault, Database Deadlock Runbook, test_db_deadlock_emits_on_alternate_ticks()

### Community 79 - "test_auth_and_rbac_slice6.py"
Cohesion: 0.29
Nodes (4): fastapi_testclient, client_app(), fixture, Unit tests for Team Authentication, RBAC & Operator Attribution (AegisOps Slice…

### Community 81 - "create_hitl_app"
Cohesion: 0.15
Nodes (14): AegisOps Production SRE Incident Management Cockpit (Slice 5). Single-page…, Render the modern SRE incident management cockpit with server briefs embedded., render_cockpit_html(), create_hitl_app(), FastAPI, mock_incident_report(), mock_incident_row(), asyncio (+6 more)

### Community 83 - "state.py"
Cohesion: 0.17
Nodes (10): Typed remediation action catalog: the agent's entire action space (ADR-0001)., Report node: emit the final IncidentReport; file the durable fix (ADR-0003)., _as_chunk_dict(), Retrieve node: fetch runbook/commit context relevant to the triaged incident., Normalize a search result into a chunk dict. A live MCP tool returns each chunk…, Agent state contract: typed models for all graph nodes., BaseModel, Retrieval data models shared across retrieval and agent layers. (+2 more)

### Community 85 - "DurableFixRegistry"
Cohesion: 0.17
Nodes (9): DurableFixRegistry, Durable-fix follow-up registry + promotion queue (ADR-0003/0005)., Open durable fixes filed by the report node; promotable to their own run., _patch_action(), DurableFixRegistry: file/list/promote roundtrip, refile guard, AutoApprover…, test_auto_approver_always_approves(), test_file_list_promote_roundtrip(), test_promote_unknown_returns_false() (+1 more)

### Community 86 - "TraceSummary"
Cohesion: 0.24
Nodes (6): Any, BaseModel, Fetch recent traces for a given service., Fetch a specific trace by trace_id., SpanSummary, TraceSummary

### Community 88 - "parse_prometheus_text"
Cohesion: 0.22
Nodes (7): parse_prometheus_text(), BaseModel, Parse raw Prometheus line protocol text into typed RawMetric objects., Scrape raw Prometheus metrics from the target endpoint., Fetch and aggregate metrics into standard RED (Rate, Errors, Duration)…, RawMetric, test_parse_prometheus_text()

### Community 89 - "schema.py"
Cohesion: 0.20
Nodes (14): redis_exceptions, Consumes aegis:events, deduplicates and correlates them into IncidentEvents., _Window, from_stream_fields(), max_severity(), Enum, Cross-week contract: RawEvent (producer -> stream) and IncidentEvent (consumer…, Inverse of to_stream_fields. (+6 more)

### Community 91 - "IncidentLedger"
Cohesion: 0.22
Nodes (6): IncidentLedger, Any, BaseModel, Fetch the full sequential audit trail for an incident., Append an immutable event to the ledger., test_immutable_incident_ledger_in_memory()

### Community 93 - "TrafficSurgeFault"
Cohesion: 0.20
Nodes (4): Deterministic capacity model: latency grows with load per worker., TrafficSurgeFault, Traffic Surge Runbook, test_traffic_surge_latency_scales_inversely_with_workers()

### Community 95 - "test_run_evals_tier3.py"
Cohesion: 0.09
Nodes (32): get_llm(), with_structured_output(), get_propose_llm(), get_triage_llm(), Any, Chat models used by the agent graph. Triage is a bounded classification +…, DirectSearchAdapter, Wraps a sync psycopg connection as an async search tool `retrieve_node` accepts. (+24 more)

### Community 97 - "test_traced_decorator_logs_the_node_with_incident_context"
Cohesion: 0.29
Nodes (5): fault_kind, _Incident, Each traced node emits one log line, so the lifecycle is visible in the…, test_traced_decorator_logs_the_node_with_incident_context(), test_traced_decorator_opens_span_with_incident_attrs()

### Community 99 - "Incident Lifecycle Pipeline"
Cohesion: 0.40
Nodes (5): Incident Remediation Approval UI Walkthrough, HITL Approval Brief, Incident Lifecycle Pipeline, Deterministic Policy Gate, Sandbox Fault Replay

## Knowledge Gaps
- **18 isolated node(s):** `aegis`, `entrypoint.sh script`, `fault_kind`, `Policy Test Cases Dataset`, `Incident Ground Truth Dataset` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 501 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FaultKind` connect `FaultKind` to `ActionType`, `get_conn`, `mock_app/main.py`, `test_faults.py`, `test_dashboard_operations_data.py`, `SystemTelemetrySnapshot`, `RawEvent`, `run_evals.py`, `test_sandbox_executor.py`, `SandboxExecutor`, `make_incident`, `verifier.py`, `test_model_tiering.py`, `datetime`, `test_sandbox_node.py`, `sandbox/demo.py`, `test_investigation_slice3.py`, `IncidentReport`, `test_observability_slice2.py`, `_generate.py`, `test_closed_loop_verify.py`, `executor.py`, `DbDeadlockFault`, `test_auth_and_rbac_slice6.py`, `state.py`, `schema.py`, `TrafficSurgeFault`, `test_run_evals_tier3.py`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Why does `ProposedAction` connect `ActionType` to `graph.py`, `get_conn`, `LiveApplier`, `test_dashboard_operations_data.py`, `run_evals.py`, `ApprovalGate`, `test_sandbox_executor.py`, `SandboxExecutor`, `make_incident`, `test_agent_graph.py`, `FaultKind`, `test_model_tiering.py`, `agent/main.py`, `test_sandbox_node.py`, `sandbox/demo.py`, `test_hitl_gate.py`, `test_investigation_slice3.py`, `propose.py`, `IncidentReport`, `test_closed_loop_verify.py`, `executor.py`, `test_auth_and_rbac_slice6.py`, `create_hitl_app`, `state.py`, `DurableFixRegistry`, `test_run_evals_tier3.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `ActionType` connect `ActionType` to `graph.py`, `get_conn`, `LiveApplier`, `test_dashboard_operations_data.py`, `ApprovalGate`, `test_sandbox_executor.py`, `SandboxExecutor`, `make_incident`, `test_agent_graph.py`, `FaultKind`, `test_model_tiering.py`, `test_sandbox_node.py`, `sandbox/demo.py`, `test_hitl_gate.py`, `test_investigation_slice3.py`, `propose.py`, `IncidentReport`, `test_closed_loop_verify.py`, `executor.py`, `test_auth_and_rbac_slice6.py`, `create_hitl_app`, `state.py`, `DurableFixRegistry`, `test_run_evals_tier3.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 104 inferred relationships involving `ActionType` (e.g. with `route_after_policy()` and `propose_node()`) actually correct?**
  _`ActionType` has 104 INFERRED edges - model-reasoned connections that need verification._
- **Are the 87 inferred relationships involving `FaultKind` (e.g. with `IncidentReport` and `LiveVerificationResult`) actually correct?**
  _`FaultKind` has 87 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `ProposedAction` (e.g. with `propose_node()` and `AttemptRecord`) actually correct?**
  _`ProposedAction` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 50 inferred relationships involving `PolicyDecision` (e.g. with `route_after_policy()` and `_determine_outcome()`) actually correct?**
  _`PolicyDecision` has 50 INFERRED edges - model-reasoned connections that need verification._