# Graph Report - Aegis  (2026-10-25)

## Corpus Check
- 196 files · ~370,007 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 7, .patch 2, .example 1)

## Summary
- 1827 nodes · 5534 edges · 110 communities (76 shown, 34 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 651 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9f0c8dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_auth_and_rbac_slice6.py
- graph.py
- observability/router.py
- PolicyDecision
- os
- SandboxResult
- mock_app/main.py
- test_faults.py
- model_tiering.py
- alerts_gateway.py
- SystemTelemetrySnapshot
- schema.py
- run_evals.py
- test_cockpit_and_postmortem_slice5.py
- test_sandbox_executor.py
- test_report_node.py
- _run_tier2_cli
- test_dashboard_evals_data.py
- make_incident
- test_agent_graph.py
- test_eval_metrics.py
- consumer.py
- state.py
- LiveVerifier
- FaultKind
- test_eval_driver.py
- test_dashboard_operations_data.py
- Severity
- ProposedAction
- DynamicTopologyEngine
- test_k8s_recovery_and_two_phase_verification_sprint3.py
- score_root_cause
- tracing.py
- web.py
- test_agent_state.py
- KubernetesApplier
- HitlDecision
- test_dynamic_topology_and_deployments_sprint2.py
- SandboxExecutor
- sanitizer.py
- IncidentReport
- hub.py
- ActionType
- executor.py
- test_crypto_ledger_sanitizer_and_slack_sprint4.py
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
- test_model_tiering.py
- test_sandbox_recovery.py
- auth/__init__.py
- pytest
- test_closed_loop_verify.py
- DESIGN.md
- test_controls.py
- get_incident_ledger
- agent/main.py
- langchain_anthropic
- test_traced_decorator_logs_the_node_with_incident_context
- TraceSummary
- adaptive_sentinel.py
- crypto_ledger.py
- actions.py
- test_adaptive_sentinel_and_alerts_sprint1.py
- test_apply_node.py
- ApprovalGate
- conftest.py
- audit/__init__.py
- IncidentLedger
- SlackInteractionHandler
- _FakeStructuredResult
- NodeUsage
- test_run_evals_tier4.py
- DbDeadlockFault
- IncidentEvent
- HitlChoice
- app.py
- sandbox/demo.py
- postmortem.py
- TwoPhaseVerifier
- _generate.py
- Incident Lifecycle Pipeline
- sanitize_telemetry_dict
- FakeExecutor
- .get_services
- FakeSearchTool

## God Nodes (most connected - your core abstractions)
1. `FaultKind` - 166 edges
2. `ActionType` - 158 edges
3. `ProposedAction` - 151 edges
4. `PolicyDecision` - 80 edges
5. `make_incident()` - 59 edges
6. `IncidentEvent` - 55 edges
7. `RemediationPlan` - 54 edges
8. `Severity` - 52 edges
9. `SandboxResult` - 49 edges
10. `ApprovalGate` - 48 edges

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

## Communities (110 total, 34 thin omitted)

### Community 0 - "test_auth_and_rbac_slice6.py"
Cohesion: 0.06
Nodes (54): alias, get_current_user(), FastAPI dependencies for JWT authentication and RBAC validation (AegisOps Slice…, Extract and validate bearer token from Header, Query, or Cookie., Enforce that the authenticated user possesses one of the allowed roles., require_role(), LoginRequest, BaseModel (+46 more)

### Community 1 - "graph.py"
Cohesion: 0.17
Nodes (16): build_graph(), LangGraph state machine: Triage -> Retrieve -> Propose -> Sandbox -> Policy ->…, route_after_hitl(), route_entry(), hitl_node(), HITL node: suspend on an evidence brief until a human resolves or the TTL fires., policy_node(), Policy node: gate the plan's mitigation against the deterministic rule engine… (+8 more)

### Community 2 - "observability/router.py"
Cohesion: 0.06
Nodes (59): delete, get_adaptive_sentinel(), get_alert_gateway(), get_deployment_store(), get_dynamic_topology_engine(), control_fault(), FaultControlRequest, get_all_audit_ledger() (+51 more)

### Community 3 - "PolicyDecision"
Cohesion: 0.24
Nodes (35): PolicyDecision, _engine(), _patch(), Per-rule unit tests for the 7-rule deny-by-default policy engine (ADR-0004)., _restart(), _sandbox(), test_all_violated_rules_are_listed(), test_circuit_opens_after_max_auto_applies() (+27 more)

### Community 4 - "os"
Cohesion: 0.10
Nodes (38): Connection, mcp, mcp_client_stdio, mcp_server_fastmcp, os, pathlib, pgvector, pgvector_psycopg (+30 more)

### Community 5 - "SandboxResult"
Cohesion: 0.12
Nodes (23): BlastRadius, PolicyVerdict, BaseModel, SandboxResult, TriageResult, Policy Test Cases Dataset, _seed_history(), PolicyEngine (+15 more)

### Community 6 - "mock_app/main.py"
Cohesion: 0.09
Nodes (26): contextlib, clear_fault(), drain_connections(), _emit_loop(), FlagUpdate, _get_fault(), get_scale(), healthz() (+18 more)

### Community 7 - "test_faults.py"
Cohesion: 0.06
Nodes (23): Incident Ground Truth Dataset, ErrorSpikeFault, Called by GET /work; 500s only while the risky feature flag is on., MemoryLeakFault, Deterministic capacity model: latency grows with load per worker., TrafficSurgeFault, Error Spike Runbook, Memory Leak Runbook (+15 more)

### Community 8 - "model_tiering.py"
Cohesion: 0.15
Nodes (18): drive_propose(), Shared core: run triage -> retrieve -> propose and return the scorable tier-2…, _case_record(), _compare(), main(), Path, Model-tiering experiment: compare per-node model choices on accuracy and cost…, Graceful skip (print + return, no write) if the API key is unset or Postgres is… (+10 more)

### Community 9 - "alerts_gateway.py"
Cohesion: 0.36
Nodes (9): AlertmanagerAlertItem, AlertmanagerWebhookPayload, PagerDutyIncident, PagerDutyMessage, PagerDutyWebhookPayload, BaseModel, Multi-Source Alert Ingestion Gateway (Sprint 1: Alertmanager & PagerDuty…, test_alertmanager_ingestion_and_dedup() (+1 more)

### Community 10 - "SystemTelemetrySnapshot"
Cohesion: 0.20
Nodes (16): BaseModel, Fetch real-time unified telemetry snapshot across all observability signals., SystemTelemetrySnapshot, Synchronous topology evaluation (guarantees zero latency and backward…, Build full dynamic service topology with runtime discovery., REDMetrics, Poll telemetry snapshot and return an IncidentEvent if an unhandled SLO breach…, TelemetrySentinel (+8 more)

### Community 11 - "schema.py"
Cohesion: 0.11
Nodes (24): ABC, datetime, Runtime controls the remediation actions manipulate: feature flags and worker…, Fault, make_dedup_key(), Fault ABC shared by all injectable faults., Stable key for signals that represent the 'same' underlying condition., Start the fault's background misbehavior. (+16 more)

### Community 12 - "run_evals.py"
Cohesion: 0.19
Nodes (17): Fraction of category='unsafe' cases NOT auto-allowed. Headline: must be 1.0., Fraction of all cases whose decision exactly matches ground truth., unsafe_blocked_rate(), verdict_accuracy(), load_cases(), Path, Tier-1/2/3/4 evals runner (ADR-0007). Tier 1: seeded safe/unsafe proposals ->…, Run tier 1 (pure Python, always runnable) and return its gate exit code: 0 iff… (+9 more)

### Community 13 - "test_cockpit_and_postmortem_slice5.py"
Cohesion: 0.16
Nodes (13): AegisOps Production SRE Incident Management Cockpit (Slice 5). Single-page…, Render the modern SRE incident management cockpit with server briefs embedded., render_cockpit_html(), fastapi_testclient, mock_incident_report(), mock_incident_row(), asyncio, fixture (+5 more)

### Community 14 - "test_sandbox_executor.py"
Cohesion: 0.09
Nodes (19): BoomContainer, DummyContainer, FakeContainer, FakeContainers, FakeDocker, GoneContainer, Stands in for a running app container in _verify_sync flow tests below; the…, M-2 carry-in: a recovered fault stops reporting its metric; the HITL brief must… (+11 more)

### Community 15 - "test_report_node.py"
Cohesion: 0.28
Nodes (20): report_node(), _attempt(), FakeRegistry, FakeSink, _patch_action(), Report node v2 tests: outcome derivation, durable-fix filing, report…, _state(), test_applied_target_file_set_only_for_patch_code() (+12 more)

### Community 16 - "_run_tier2_cli"
Cohesion: 0.07
Nodes (30): argparse, _apply_geval(), _dependency_status(), _dispatch(), main(), Shared results envelope for all tiers., Replay each case through triage->retrieve->propose, then override the retrieved…, Score G-Eval root-cause quality in the MAIN thread, AFTER the async graph… (+22 more)

### Community 17 - "test_dashboard_evals_data.py"
Cohesion: 0.12
Nodes (34): EvalRun, headline_scorecard(), latest_per_tier(), load_eval_runs(), metric_series(), _normalize_tier(), Path, Evaluation-tab data access: timestamped eval-result JSONs (spec section 12,… (+26 more)

### Community 18 - "make_incident"
Cohesion: 0.13
Nodes (29): _prompt(), propose_node(), Mitigate-first plan: mitigation executes now, durable_fix is filed as follow-up…, RemediationPlan, field_validator, FakeStructuredLLM, make_incident(), make_triage() (+21 more)

### Community 19 - "test_agent_graph.py"
Cohesion: 0.18
Nodes (25): route_after_sandbox(), initial_state(), Outcome, Seed a graph run. Promoted durable-fix runs preset `plan` (and reuse the…, _Built, _graph(), _plan(), RaisingGate (+17 more)

### Community 20 - "test_eval_metrics.py"
Cohesion: 0.18
Nodes (22): action_selection_accuracy(), durable_fix_valid_path_rate(), mean_confidence(), pct_below_confidence_floor(), Path, Deterministic Tier-1 metrics — owned plain functions, not framework-wrapped…, Of the drafted patch_code durable fixes, the fraction whose target_file…, remediation_success_rate() (+14 more)

### Community 21 - "consumer.py"
Cohesion: 0.13
Nodes (13): Phase 5 demo: trigger a fault, run the pipeline, print the Jaeger trace URL.…, inject_trace_context(), Serialize the current context into a W3C carrier (traceparent/tracestate)., redis_asyncio, redis_exceptions, Consumer, Redis, Consumes aegis:events, deduplicates and correlates them into IncidentEvents. (+5 more)

### Community 22 - "state.py"
Cohesion: 0.18
Nodes (15): _attempts_block(), Propose node: emit a RemediationPlan — mitigate now, file the durable fix…, _as_chunk_dict(), Retrieve node: fetch runbook/commit context relevant to the triaged incident., Normalize a search result into a chunk dict. A live MCP tool returns each chunk…, retrieve_node(), Triage node: classify the incident and propose a root-cause hypothesis…, triage_node() (+7 more)

### Community 23 - "LiveVerifier"
Cohesion: 0.17
Nodes (11): LiveVerifier, AsyncClient, Samples live telemetry to assert that an applied operational fix actually cured…, Fetch real-time metrics directly from the live service., Polls live metrics until recovery is asserted or timeout expires., asyncio, Unit tests for LiveVerifier (AegisOps Slice 1)., test_get_live_metrics_returns_parsed_dict() (+3 more)

### Community 24 - "FaultKind"
Cohesion: 0.14
Nodes (22): FaultKind, str, app_image(), executor(), _patch_action(), fixture, Empirical fault-replay verification against real containers. Requires Docker…, sandbox_image() (+14 more)

### Community 25 - "test_eval_driver.py"
Cohesion: 0.19
Nodes (11): dataclasses, run_propose(), EvalCase, Load the offline-replay incident corpus + ground truth (ADR-0007)., _case(), _FakeLLM, _FakeSearch, _FakeStructured (+3 more)

### Community 26 - "test_dashboard_operations_data.py"
Cohesion: 0.17
Nodes (27): _render_operations(), expired_approvals(), incident_cost_usd(), IncidentRow, node_usage_stats(), open_durable_fixes(), outcome_breakdown(), _percentile() (+19 more)

### Community 27 - "Severity"
Cohesion: 0.14
Nodes (20): Correlator, Close windows that have gone idle or exceeded the max window; return their…, Deduplicates raw events and groups them into IncidentEvents over a correlation…, _Window, max_severity(), Enum, Severity, make_event() (+12 more)

### Community 28 - "ProposedAction"
Cohesion: 0.09
Nodes (23): ProposedAction, LiveApplier, Path, Applies a policy-cleared, sandbox-proven mitigation to the live target., Automated rollback safeguard: undoes an action if post-recovery verification…, model_validator, docker_client_or_skip(), FakeContainer (+15 more)

### Community 29 - "DynamicTopologyEngine"
Cohesion: 0.10
Nodes (19): DynamicTopologyEngine, Synchronize NetworkX DiGraph representation., Register or update a dynamic microservice at runtime., Remove a dynamic microservice., Register a dynamic dependency edge between services., Query Jaeger REST API for runtime call dependency graphs., Discover live containerized services running on local host., Return all downstream dependencies for a service via NetworkX graph traversal. (+11 more)

### Community 30 - "test_k8s_recovery_and_two_phase_verification_sprint3.py"
Cohesion: 0.08
Nodes (23): AntiFlapCircuitBreaker, Check if global cascading failure circuit breaker is open (>3 services in 5…, Comprehensive check before allowing automated remediation. Returns (allowed,…, Clear all active history., Return remaining cooldown seconds for services., Enterprise safety circuit breaker and anti-flap controller., Record an applied action on a service., Check if service is in cooldown (flapping protection: 1 action per 15 min). (+15 more)

### Community 31 - "score_root_cause"
Cohesion: 0.16
Nodes (8): _deepeval_available(), DeepEval G-Eval root-cause reasoning quality, judged by a custom Claude model.…, # NOTE: verified end-to-end against deepeval 4.1.3 + a live ANTHROPIC_API_KEY at, score_root_cause(), Defensive-wrapper proof: even if _deepeval_available() claims deepeval is…, test_score_is_none_when_deepeval_missing(), test_score_is_none_without_key(), test_scored_path_error_degrades_to_none()

### Community 32 - "tracing.py"
Cohesion: 0.13
Nodes (21): observability, add_trace_context(), structlog configuration: every line carries incident_id + trace_id (ADR-0009)., structlog processor: stamp the active span's trace_id/span_id onto the line., setup_logging(), OpenTelemetry tracing setup and helpers (ADR-0009). One trace per incident,…, opentelemetry_exporter_otlp_proto_http_trace_exporter, opentelemetry_propagate (+13 more)

### Community 33 - "web.py"
Cohesion: 0.27
Nodes (13): fastapi_responses, _brief_card(), index(), _durable_fix_card(), _durable_fix_row(), _esc(), _evidence_table(), _policy_block() (+5 more)

### Community 34 - "test_agent_state.py"
Cohesion: 0.13
Nodes (18): _action(), make_incident(), _result(), test_attempt_record_pairs_action_with_evidence(), test_hitl_choice_has_expired(), test_hitl_decision_validates(), test_incident_event_is_the_agent_input(), test_incident_report_v2_fields_default() (+10 more)

### Community 35 - "KubernetesApplier"
Cohesion: 0.14
Nodes (17): get_kubernetes_applier(), KubernetesActionPayload, KubernetesActionResult, KubernetesApplier, _exec(), _exec_rollback(), Any, BaseModel (+9 more)

### Community 36 - "HitlDecision"
Cohesion: 0.18
Nodes (11): HitlDecision, AutoApprover, Auto-approver stub: eval runs measure the apply path unattended (ADR-0005)., Records every request_approval call; returns a scripted decision., SpyGate, _patch_action(), DurableFixRegistry: file/list/promote roundtrip, refile guard, AutoApprover…, test_auto_approver_always_approves() (+3 more)

### Community 37 - "test_dynamic_topology_and_deployments_sprint2.py"
Cohesion: 0.13
Nodes (26): _format_telemetry(), _prompt(), DeploymentCorrelation, DeploymentEvent, DeploymentIntelligenceStore, DeploymentSource, DeploymentStatus, parse_argocd_webhook() (+18 more)

### Community 39 - "sanitizer.py"
Cohesion: 0.14
Nodes (15): contain_telemetry_boundary(), neutralize_prompt_injections(), LLM Prompt-Injection Defense & Telemetry Sanitizer (AegisOps Sprint 4). Shields…, Strip chat model control tokens and raw HTML scripts., Detect and neutralize prompt-injection phrases, preserving harmless diagnostic…, Enclose untrusted diagnostic text within explicit data boundaries., Full-pipeline sanitization for log lines, exception messages, and alerts., sanitize_text() (+7 more)

### Community 40 - "IncidentReport"
Cohesion: 0.26
Nodes (11): PostgresReportSink, PrintSink, Report sinks: stdout for demos, Postgres for the dashboard (spec section 12)., IncidentReport, conn_string(), docker, Report sink tests: PrintSink (stdout) and PostgresReportSink (dashboard…, _report() (+3 more)

### Community 41 - "hub.py"
Cohesion: 0.09
Nodes (31): httpx, networkx, Unified observability hub (AegisOps Sprint 2). Aggregates Prometheus RED…, JaegerClient, AsyncClient, Jaeger distributed trace client and correlator (AegisOps Slice 2). Extracts…, Dynamic Kubernetes & Service Mesh Topology Discovery Engine (AegisOps Sprint…, parse_prometheus_text() (+23 more)

### Community 42 - "ActionType"
Cohesion: 0.15
Nodes (23): ActionMetadata, ActionType, BaseModel, Enum, str, route_after_policy(), test_action_metadata_is_frozen(), test_catalog_covers_every_action_type() (+15 more)

### Community 43 - "executor.py"
Cohesion: 0.14
Nodes (18): Per-action live appliers: act on the running mock_app compose service., _tar_single_file(), Path, Shared patch rendering: containment guard + git apply in a temp tree. Used by…, Apply `patch` to repo_root/target_file in a temp tree; return the patched bytes., render_patched_file(), docker_errors, docker_types (+10 more)

### Community 44 - "test_crypto_ledger_sanitizer_and_slack_sprint4.py"
Cohesion: 0.14
Nodes (15): format_postmortem_for_jira_or_pagerduty(), Verify Slack HMAC-SHA256 request signature., Format an SRE post-mortem report for external ticketing sync (Jira / PagerDuty)., verify_slack_signature(), starlette_testclient, asyncio, Unit and integration tests for Sprint 4: - Cryptographic Merkle Audit Ledger…, Verify Criterion 3: SRE clicks 'Approve' in Slack -> action executes &… (+7 more)

### Community 71 - "test_model_tiering.py"
Cohesion: 0.18
Nodes (9): _case(), _FakeLLM, _FakeSearch, _FakeStructured, Each config keeps a diagnosable per-case `results` list, and `comparisons`…, Fast, offline test for the model-tiering experiment runner. No network, no…, Same real pricing-table model string used for both roles (triage and propose…, test_run_experiment_sonnet_triage_costs_more_than_haiku() (+1 more)

### Community 72 - "test_sandbox_recovery.py"
Cohesion: 0.22
Nodes (12): Live closed-loop telemetry verifier (AegisOps Slice 1). Monitors live…, check_degraded(), check_recovered(), Pure recovery-assertion rules for sandbox fault replay (ADR-0002). No Docker…, should_retrigger(), test_check_degraded_floors(), test_check_recovered_ceilings(), test_no_retrigger_for_non_restart_mitigations() (+4 more)

### Community 74 - "pytest"
Cohesion: 0.09
Nodes (32): get_llm(), with_structured_output(), get_propose_llm(), get_triage_llm(), Any, Chat models used by the agent graph. Triage is a bounded classification +…, DirectSearchAdapter, Wraps a sync psycopg connection as an async search tool `retrieve_node` accepts. (+24 more)

### Community 75 - "test_closed_loop_verify.py"
Cohesion: 0.20
Nodes (15): route_after_apply(), route_after_verify(), rollback_node(), LiveVerificationResult, Post-remediation live telemetry assertion (AegisOps Slice 1)., Enriched verification result with Phase 1 (Canary) and Phase 2 (Soak) telemetry., TwoPhaseVerificationResult, _make_incident() (+7 more)

### Community 76 - "DESIGN.md"
Cohesion: 0.15
Nodes (12): Badges, Status Dots & Indicators, Brand & Style, Buttons & Interactive Controls, Colors, Components, Elevation & Depth, HUD Metric Cards, Incident Audit Ledger & Data Tables (+4 more)

### Community 77 - "test_controls.py"
Cohesion: 0.17
Nodes (6): FeatureFlags, ScaleState, test_flag_set_and_unknown_flag_raises(), test_flags_default_off(), test_scale_defaults_and_bounds(), test_scale_env_misconfig_clamped_not_crashing()

### Community 78 - "get_incident_ledger"
Cohesion: 0.18
Nodes (11): apply_node(), Apply node: execute the policy-cleared mitigation on the live target (AegisOps…, Report node: emit the final IncidentReport; file the durable fix (ADR-0003)., Rollback node: automated rollback safeguard when live verification fails…, Verify node: live telemetry assertion for closed-loop recovery (AegisOps Slice…, Two-Phase Canary & Sustained Soak Verifier (AegisOps Sprint 3). Upgrades post-…, get_incident_ledger(), Immutable Incident Ledger with Cryptographic Hash Chaining (AegisOps Sprint 4).… (+3 more)

### Community 79 - "agent/main.py"
Cohesion: 0.07
Nodes (39): main(), _process_incident(), _process_promotion(), promoted_incident(), Redis, Demo entrypoint: run the full agent graph with HITL web UI., Derived identity for a promoted durable-fix run, so its report upserts a…, _read_latest_incidents() (+31 more)

### Community 81 - "test_traced_decorator_logs_the_node_with_incident_context"
Cohesion: 0.29
Nodes (5): fault_kind, _Incident, Each traced node emits one log line, so the lifecycle is visible in the…, test_traced_decorator_logs_the_node_with_incident_context(), test_traced_decorator_opens_span_with_incident_attrs()

### Community 82 - "TraceSummary"
Cohesion: 0.24
Nodes (6): Any, BaseModel, Fetch recent traces for a given service., Fetch a specific trace by trace_id., SpanSummary, TraceSummary

### Community 83 - "adaptive_sentinel.py"
Cohesion: 0.18
Nodes (10): collections, get_approval_gate(), math, Adaptive Statistical Telemetry Sentinel (Sprint 1: Dynamic Anomaly Detection).…, get_observability_hub(), ObservabilityHub, get_topology(), Live service dependency graph and node health statuses. (+2 more)

### Community 84 - "crypto_ledger.py"
Cohesion: 0.11
Nodes (18): compute_entry_hash(), compute_entry_signature(), CryptographicIncidentLedger, CryptographicLedgerEntry, get_crypto_ledger(), Any, BaseModel, Cryptographic Merkle Audit Ledger (AegisOps Sprint 4). Provides SOC2 / ISO… (+10 more)

### Community 85 - "actions.py"
Cohesion: 0.25
Nodes (13): Typed remediation action catalog: the agent's entire action space (ADR-0001)., Sandbox node: empirical fault replay of the plan's mitigation (ADR-0002)., sandbox_node(), AttemptRecord, One sandbox-verified attempt: what was tried, what the replay proved (ADR-0006)., FakeExecutor, Sandbox node: verify() wiring, attempt tracking, skip logic (ADR-0002/0006)., _result() (+5 more)

### Community 86 - "test_adaptive_sentinel_and_alerts_sprint1.py"
Cohesion: 0.19
Nodes (14): AdaptiveBaselineDetector, AnomalyDiagnosis, MetricSample, Computes rolling online EWMA, Z-Score, and IQR baselines across telemetry…, Calculate Q1, Q3, and upper fence Q3 + 1.5 * IQR., asyncio, Sprint 1 Unit Tests: Adaptive Statistical Sentinel & Multi-Source Alert…, Ensures low-traffic periods with high variance don't cause false positives. (+6 more)

### Community 87 - "test_apply_node.py"
Cohesion: 0.33
Nodes (5): SpyApplier, SpyEngine, _state(), test_apply_failure_is_caught_and_not_recorded(), test_apply_success_records_and_flags_applied()

### Community 88 - "ApprovalGate"
Cohesion: 0.11
Nodes (27): Future, ApprovalGate, build_brief(), Decision brief, not raw data: everything the approver needs on one card., DurableFixRegistry, Open durable fixes filed by the report node; promotable to their own run., create_hitl_app(), FastAPI (+19 more)

### Community 89 - "conftest.py"
Cohesion: 0.31
Nodes (8): fakeredis_aioredis, mock_app_faults, client(), fake_redis(), fixture, Snapshot + restore the global OTel tracer provider around every test.…, reset_faults(), reset_tracer_provider()

### Community 91 - "IncidentLedger"
Cohesion: 0.18
Nodes (9): IncidentLedger, LedgerEntry, Any, BaseModel, Verify the cryptographic hash-chain across all entries., Append an immutable, cryptographically chained event to the ledger., Fetch recent cryptographic audit entries across all incidents., Fetch the full sequential cryptographic audit trail for an incident. (+1 more)

### Community 92 - "SlackInteractionHandler"
Cohesion: 0.22
Nodes (7): build_slack_approval_card(), Any, Handles Slack Block Kit user clicks and unblocks LangGraph HITL approvals., Process interactive button click from Slack Block Kit., Generate Slack Block Kit interactive card JSON with operational action buttons., SlackInteractionHandler, test_slack_approval_card_builder()

### Community 93 - "_FakeStructuredResult"
Cohesion: 0.22
Nodes (4): FakeLLM, FakeRaw, _FakeStructuredResult, Backs FakeLLM.with_structured_output; keyed-by-type fake used by…

### Community 94 - "NodeUsage"
Cohesion: 0.51
Nodes (8): NodeUsage, cost_usd(), Static pricing table: NodeUsage tokens -> dollars (ADR-0010). Prices are $ per…, total_cost_usd(), test_known_model_cost_is_tokens_times_price(), test_total_sums_across_usages(), test_unknown_model_costs_zero(), _usage()

### Community 95 - "test_run_evals_tier4.py"
Cohesion: 0.15
Nodes (11): _expected_outcome(), _NoopApplier, _NoopRegistry, _NoopSink, Map ground-truth expected_policy -> the outcome the e2e run should land on…, Run each case through the WHOLE compiled graph with a real PolicyEngine and an…, run_tier4(), _tier4_metrics() (+3 more)

### Community 96 - "DbDeadlockFault"
Cohesion: 0.18
Nodes (5): app_version(), Deploy version this process simulates; 'previous' = the rollback target, i.e.…, DbDeadlockFault, Database Deadlock Runbook, test_db_deadlock_emits_on_alternate_ticks()

### Community 97 - "IncidentEvent"
Cohesion: 0.15
Nodes (10): AdaptiveTelemetrySentinel, Orchestrates telemetry ingestion from ObservabilityHub and evaluates adaptive…, AlertIngestionGateway, AlertRecord, Normalize Alertmanager v4 payload into IncidentEvents with deduplication., Normalize PagerDuty V2 messages into IncidentEvents., Async dequeue of incoming alerts for the LangGraph agent runner., Ingests multi-source webhooks, deduplicates firing alerts, and normalizes into… (+2 more)

### Community 98 - "HitlChoice"
Cohesion: 0.21
Nodes (15): _determine_outcome(), HitlChoice, Enum, str, _ask(), _passing_sandbox(), _plan_plain(), _plan_with_durable_fix() (+7 more)

### Community 99 - "app.py"
Cohesion: 0.24
Nodes (11): cache_data, _eval_runs(), _format_metric(), _incident_rows(), main(), Aegis dashboard (spec section 12, ADR-0011): Operations from Postgres,…, _render_evaluation(), fetch_incident_rows() (+3 more)

### Community 100 - "sandbox/demo.py"
Cohesion: 0.43
Nodes (6): docker, build_action(), ensure_images(), main(), Phase-2 demo CLI: inject a fault, apply an action, print verified before/after…, run_one()

### Community 101 - "postmortem.py"
Cohesion: 0.33
Nodes (6): generate_postmortem(), PostMortem, BaseModel, Automated SRE Post-Mortem Report Generator (AegisOps Slice 5). Generates…, Generate structured and Markdown post-mortem for a given incident., test_postmortem_generator_structure()

### Community 102 - "TwoPhaseVerifier"
Cohesion: 0.20
Nodes (7): get_two_phase_verifier(), Any, AsyncClient, Execute Phase 1 (Canary Probe) followed by Phase 2 (Sustained Soak Window)., Production 2-phase canary and sustained soak verification engine., Query real-time metrics directly from the live service., TwoPhaseVerifier

### Community 103 - "_generate.py"
Cohesion: 0.33
Nodes (4): _incident(), One-shot: emit schema-authentic IncidentEvent fixtures. Re-run to regenerate., _raw(), itertools

### Community 104 - "Incident Lifecycle Pipeline"
Cohesion: 0.40
Nodes (5): Incident Remediation Approval UI Walkthrough, HITL Approval Brief, Incident Lifecycle Pipeline, Deterministic Policy Gate, Sandbox Fault Replay

### Community 106 - "sanitize_telemetry_dict"
Cohesion: 0.50
Nodes (4): Any, Recursively sanitize dictionary values before feeding into LLM context., sanitize_telemetry_dict(), test_sanitize_telemetry_dict_recursive()

## Knowledge Gaps
- **29 isolated node(s):** `aegis`, `entrypoint.sh script`, `fault_kind`, `Brand & Style`, `Colors` (+24 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 633 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FaultKind` connect `FaultKind` to `test_auth_and_rbac_slice6.py`, `PolicyDecision`, `SandboxResult`, `mock_app/main.py`, `test_faults.py`, `alerts_gateway.py`, `SystemTelemetrySnapshot`, `schema.py`, `run_evals.py`, `test_sandbox_executor.py`, `make_incident`, `consumer.py`, `state.py`, `LiveVerifier`, `test_eval_driver.py`, `test_dashboard_operations_data.py`, `Severity`, `test_k8s_recovery_and_two_phase_verification_sprint3.py`, `test_agent_state.py`, `test_dynamic_topology_and_deployments_sprint2.py`, `SandboxExecutor`, `IncidentReport`, `executor.py`, `test_model_tiering.py`, `test_sandbox_recovery.py`, `pytest`, `test_closed_loop_verify.py`, `get_incident_ledger`, `adaptive_sentinel.py`, `actions.py`, `test_adaptive_sentinel_and_alerts_sprint1.py`, `DbDeadlockFault`, `IncidentEvent`, `sandbox/demo.py`, `TwoPhaseVerifier`, `_generate.py`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Why does `ProposedAction` connect `ProposedAction` to `test_auth_and_rbac_slice6.py`, `PolicyDecision`, `SandboxResult`, `run_evals.py`, `test_cockpit_and_postmortem_slice5.py`, `test_sandbox_executor.py`, `test_report_node.py`, `make_incident`, `test_agent_graph.py`, `state.py`, `FaultKind`, `test_eval_driver.py`, `test_dashboard_operations_data.py`, `test_k8s_recovery_and_two_phase_verification_sprint3.py`, `test_agent_state.py`, `KubernetesApplier`, `HitlDecision`, `SandboxExecutor`, `IncidentReport`, `ActionType`, `executor.py`, `test_model_tiering.py`, `pytest`, `test_closed_loop_verify.py`, `get_incident_ledger`, `agent/main.py`, `actions.py`, `test_apply_node.py`, `ApprovalGate`, `HitlChoice`, `sandbox/demo.py`, `TwoPhaseVerifier`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `ActionType` connect `ActionType` to `test_auth_and_rbac_slice6.py`, `graph.py`, `PolicyDecision`, `SandboxResult`, `test_cockpit_and_postmortem_slice5.py`, `test_sandbox_executor.py`, `test_report_node.py`, `make_incident`, `test_agent_graph.py`, `state.py`, `FaultKind`, `test_eval_driver.py`, `test_dashboard_operations_data.py`, `ProposedAction`, `test_k8s_recovery_and_two_phase_verification_sprint3.py`, `test_agent_state.py`, `KubernetesApplier`, `HitlDecision`, `SandboxExecutor`, `IncidentReport`, `executor.py`, `test_model_tiering.py`, `test_sandbox_recovery.py`, `pytest`, `test_closed_loop_verify.py`, `get_incident_ledger`, `actions.py`, `test_apply_node.py`, `ApprovalGate`, `HitlChoice`, `sandbox/demo.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 103 inferred relationships involving `FaultKind` (e.g. with `propose_node()` and `IncidentReport`) actually correct?**
  _`FaultKind` has 103 INFERRED edges - model-reasoned connections that need verification._
- **Are the 114 inferred relationships involving `ActionType` (e.g. with `route_after_policy()` and `propose_node()`) actually correct?**
  _`ActionType` has 114 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `ProposedAction` (e.g. with `propose_node()` and `AttemptRecord`) actually correct?**
  _`ProposedAction` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PolicyDecision` (e.g. with `route_after_policy()` and `_determine_outcome()`) actually correct?**
  _`PolicyDecision` has 54 INFERRED edges - model-reasoned connections that need verification._