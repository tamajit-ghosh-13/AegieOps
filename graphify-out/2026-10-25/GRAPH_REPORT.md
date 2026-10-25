# Graph Report - Aegis  (2026-10-25)

## Corpus Check
- 197 files · ~373,605 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 7, .patch 2, .example 1)

## Summary
- 1855 nodes · 5564 edges · 113 communities (74 shown, 39 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 654 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9f0c8dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_auth_and_rbac_slice6.py
- state.py
- observability/router.py
- PolicyDecision
- pathlib
- SandboxResult
- mock_app/main.py
- test_faults.py
- model_tiering.py
- alerts_gateway.py
- hub.py
- schema.py
- run_evals.py
- DurableFixRegistry
- FakeContainer
- test_report_node.py
- test_run_evals_tier2.py
- test_dashboard_evals_data.py
- make_incident
- test_agent_graph.py
- test_eval_metrics.py
- Consumer
- _run_tier2_cli
- LiveVerifier
- FaultKind
- drivers.py
- test_dashboard_operations_data.py
- Correlator
- LiveApplier
- DynamicTopologyEngine
- test_k8s_recovery_and_two_phase_verification_sprint3.py
- score_root_cause
- logging.py
- web.py
- test_agent_state.py
- KubernetesApplier
- HitlChoice
- test_dynamic_topology_and_deployments_sprint2.py
- SandboxExecutor
- sanitizer.py
- IncidentReport
- test_observability_slice2.py
- ActionType
- render_patched_file
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
- _FakeLLM
- executor.py
- auth/__init__.py
- test_run_evals_tier3.py
- get_tracer
- DESIGN.md
- AntiFlapCircuitBreaker
- gate.py
- agent/main.py
- langchain_anthropic
- Part 2: Act-by-Act Synchronized Playbook (Screen Actions + Terminal Commands + Tagged Voiceover)
- JaegerClient
- circuit_breaker.py
- .record_event
- test_sandbox_node.py
- test_adaptive_sentinel_and_alerts_sprint1.py
- test_apply_node.py
- ApprovalGate
- CryptographicIncidentLedger
- audit/__init__.py
- IncidentLedger
- SlackInteractionHandler
- _FakeStructuredResult
- NodeUsage
- test_run_evals_tier4.py
- DbDeadlockFault
- IncidentEvent
- test_hitl_gate.py
- app.py
- sandbox/demo.py
- TwoPhaseVerifier
- MemoryLeakFault
- setup_tracing
- promoted_incident
- BoomContainer
- GoneContainer
- KubernetesActionPayload
- .__init__
- .clear
- .metric_snapshot
- .trigger
- .__init__

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
- `What Was Upgraded From Your Initial Script (From Inspecting the Aegis Repo)` --references--> `drain_connections()`  [INFERRED]
  AEGISOPS_PITCH_AND_TTS_PLAYBOOK.md → mock_app/main.py
- `What Was Upgraded From Your Initial Script (From Inspecting the Aegis Repo)` --references--> `run_config()`  [INFERRED]
  AEGISOPS_PITCH_AND_TTS_PLAYBOOK.md → observability/langsmith.py
- `Policy Test Cases Dataset` --references--> `PolicyEngine`  [INFERRED]
  evals/policy_cases.yaml → policy/engine.py
- `Deterministic Policy Gate` --conceptually_related_to--> `PolicyEngine`  [INFERRED]
  README.md → policy/engine.py
- `test_hitl_choice_has_expired()` --uses--> `HitlChoice`  [INFERRED]
  tests/test_agent_state.py → agent/state.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Incident Lifecycle Stages** — readme_incident_lifecycle, readme_sandbox_fault_replay, readme_policy_engine_gate, readme_hitl_approval_brief [EXTRACTED 1.00]
- **Incident Runbooks** — retrieval_runbooks_db_deadlock_runbook, retrieval_runbooks_error_spike_runbook, retrieval_runbooks_memory_leak_runbook, retrieval_runbooks_traffic_surge_runbook [EXTRACTED 1.00]

## Communities (113 total, 39 thin omitted)

### Community 0 - "test_auth_and_rbac_slice6.py"
Cohesion: 0.06
Nodes (53): alias, get_current_user(), FastAPI dependencies for JWT authentication and RBAC validation (AegisOps Slice…, Extract and validate bearer token from Header, Query, or Cookie., Enforce that the authenticated user possesses one of the allowed roles., require_role(), LoginRequest, BaseModel (+45 more)

### Community 1 - "state.py"
Cohesion: 0.06
Nodes (72): build_graph(), LangGraph state machine: Triage -> Retrieve -> Propose -> Sandbox -> Policy ->…, route_after_apply(), route_after_hitl(), route_after_verify(), route_entry(), apply_node(), Apply node: execute the policy-cleared mitigation on the live target (AegisOps… (+64 more)

### Community 2 - "observability/router.py"
Cohesion: 0.05
Nodes (66): LedgerEntry, delete, get_adaptive_sentinel(), get_alert_gateway(), get_deployment_store(), get_dynamic_topology_engine(), generate_postmortem(), PostMortem (+58 more)

### Community 3 - "PolicyDecision"
Cohesion: 0.14
Nodes (45): PolicyDecision, Incident Remediation Approval UI Walkthrough, Policy Test Cases Dataset, _seed_history(), PolicyEngine, Any, HITL Approval Brief, Incident Lifecycle Pipeline (+37 more)

### Community 4 - "pathlib"
Cohesion: 0.10
Nodes (34): dotenv, mcp, mcp_client_stdio, mcp_server_fastmcp, pathlib, pgvector, pgvector_psycopg, Postgres + pgvector connection and schema for the retrieval corpus. (+26 more)

### Community 5 - "SandboxResult"
Cohesion: 0.13
Nodes (23): BlastRadius, PolicyVerdict, BaseModel, SandboxResult, TriageResult, Deterministic, deny-by-default, stateful policy engine (ADR-0004). Seven…, FakeExecutor, Queue of sandbox results, one per verify() call (last one repeats). (+15 more)

### Community 6 - "mock_app/main.py"
Cohesion: 0.05
Nodes (41): contextlib, fakeredis_aioredis, FeatureFlags, Runtime controls the remediation actions manipulate: feature flags and worker…, ScaleState, mock_app_faults, clear_fault(), drain_connections() (+33 more)

### Community 7 - "test_faults.py"
Cohesion: 0.07
Nodes (21): ErrorSpikeFault, Called by GET /work; 500s only while the risky feature flag is on., Deterministic capacity model: latency grows with load per worker., TrafficSurgeFault, Error Spike Runbook, Traffic Surge Runbook, is_reproducible(), FakeProducer (+13 more)

### Community 8 - "model_tiering.py"
Cohesion: 0.16
Nodes (16): _case_record(), _compare(), main(), Path, Model-tiering experiment: compare per-node model choices on accuracy and cost…, Graceful skip (print + return, no write) if the API key is unset or Postgres is…, Trimmed per-case row for the artifact: enough to see WHICH incident's action…, Delta of a candidate config against the baseline. cost_delta is the… (+8 more)

### Community 9 - "alerts_gateway.py"
Cohesion: 0.36
Nodes (9): AlertmanagerAlertItem, AlertmanagerWebhookPayload, PagerDutyIncident, PagerDutyMessage, PagerDutyWebhookPayload, BaseModel, Multi-Source Alert Ingestion Gateway (Sprint 1: Alertmanager & PagerDuty…, test_alertmanager_ingestion_and_dedup() (+1 more)

### Community 10 - "hub.py"
Cohesion: 0.12
Nodes (26): get_approval_gate(), get_observability_hub(), ObservabilityHub, BaseModel, Unified observability hub (AegisOps Sprint 2). Aggregates Prometheus RED…, Fetch real-time unified telemetry snapshot across all observability signals., SystemTelemetrySnapshot, Synchronous topology evaluation (guarantees zero latency and backward… (+18 more)

### Community 11 - "schema.py"
Cohesion: 0.10
Nodes (34): ABC, datetime, _incident(), One-shot: emit schema-authentic IncidentEvent fixtures. Re-run to regenerate., _raw(), itertools, Fault, make_dedup_key() (+26 more)

### Community 12 - "run_evals.py"
Cohesion: 0.22
Nodes (15): Fraction of category='unsafe' cases NOT auto-allowed. Headline: must be 1.0., Fraction of all cases whose decision exactly matches ground truth., unsafe_blocked_rate(), verdict_accuracy(), load_cases(), Path, Tier-1/2/3/4 evals runner (ADR-0007). Tier 1: seeded safe/unsafe proposals ->…, Run tier 1 (pure Python, always runnable) and return its gate exit code: 0 iff… (+7 more)

### Community 13 - "DurableFixRegistry"
Cohesion: 0.10
Nodes (21): DurableFixRegistry, Durable-fix follow-up registry + promotion queue (ADR-0003/0005)., Open durable fixes filed by the report node; promotable to their own run., create_hitl_app(), FastAPI, test_api_alert_webhooks(), client_app(), fixture (+13 more)

### Community 14 - "FakeContainer"
Cohesion: 0.18
Nodes (5): FakeContainer, FakeContainers, FakeDocker, test_safe_remove_still_force_removes_live_container(), test_start_app_removes_container_when_never_ready()

### Community 15 - "test_report_node.py"
Cohesion: 0.28
Nodes (20): report_node(), _attempt(), FakeRegistry, FakeSink, _patch_action(), Report node v2 tests: outcome derivation, durable-fix filing, report…, _state(), test_applied_target_file_set_only_for_patch_code() (+12 more)

### Community 16 - "test_run_evals_tier2.py"
Cohesion: 0.09
Nodes (19): argparse, _apply_geval(), Shared results envelope for all tiers., Replay each case through triage->retrieve->propose, then override the retrieved…, Score G-Eval root-cause quality in the MAIN thread, AFTER the async graph…, First case per distinct fault_kind, preserving fixture order — the default…, _representative_cases(), run_tier2() (+11 more)

### Community 17 - "test_dashboard_evals_data.py"
Cohesion: 0.12
Nodes (35): EvalRun, headline_scorecard(), latest_per_tier(), load_eval_runs(), metric_series(), _normalize_tier(), Path, Evaluation-tab data access: timestamped eval-result JSONs (spec section 12,… (+27 more)

### Community 18 - "make_incident"
Cohesion: 0.17
Nodes (25): _attempts_block(), _prompt(), propose_node(), Propose node: emit a RemediationPlan — mitigate now, file the durable fix…, initial_state(), Seed a graph run. Promoted durable-fix runs preset `plan` (and reuse the…, Mitigate-first plan: mitigation executes now, durable_fix is filed as follow-up…, RemediationPlan (+17 more)

### Community 19 - "test_agent_graph.py"
Cohesion: 0.12
Nodes (32): route_after_policy(), route_after_sandbox(), Outcome, _Built, _graph(), _plan(), _policy_state(), RaisingGate (+24 more)

### Community 20 - "test_eval_metrics.py"
Cohesion: 0.19
Nodes (21): action_selection_accuracy(), durable_fix_valid_path_rate(), mean_confidence(), pct_below_confidence_floor(), Path, Deterministic Tier-1 metrics — owned plain functions, not framework-wrapped…, Of the drafted patch_code durable fixes, the fraction whose target_file…, remediation_success_rate() (+13 more)

### Community 21 - "Consumer"
Cohesion: 0.26
Nodes (5): Consumer, Redis, XREADGROUP loop with bounded in-flight processing (backpressure) feeding a…, One-time read of this consumer's previously-pending entries on startup., Process one poll cycle: drain backlog if high, read new entries, sweep…

### Community 22 - "_run_tier2_cli"
Cohesion: 0.21
Nodes (12): _dependency_status(), _dispatch(), main(), Cheap, exception-swallowing probes for the optional eval dependencies, used to…, Graceful skip if required dependencies are unavailable; never touches exit…, Route a parsed args namespace to the right tier(s). Tier 1 is the sole exit-…, _run_tier2_cli(), Tests for `--tier all` orchestration and the shared `_dependency_status` skip… (+4 more)

### Community 23 - "LiveVerifier"
Cohesion: 0.17
Nodes (11): LiveVerifier, AsyncClient, Samples live telemetry to assert that an applied operational fix actually cured…, Fetch real-time metrics directly from the live service., Polls live metrics until recovery is asserted or timeout expires., asyncio, Unit tests for LiveVerifier (AegisOps Slice 1)., test_get_live_metrics_returns_parsed_dict() (+3 more)

### Community 24 - "FaultKind"
Cohesion: 0.15
Nodes (22): FaultKind, str, app_image(), executor(), _patch_action(), fixture, Empirical fault-replay verification against real containers. Requires Docker…, sandbox_image() (+14 more)

### Community 25 - "drivers.py"
Cohesion: 0.16
Nodes (14): dataclasses, drive_propose(), Tier-2 offline driver: replay a fixture through triage -> retrieve -> propose…, Shared core: run triage -> retrieve -> propose and return the scorable tier-2…, run_propose(), EvalCase, Load the offline-replay incident corpus + ground truth (ADR-0007)., _case() (+6 more)

### Community 26 - "test_dashboard_operations_data.py"
Cohesion: 0.17
Nodes (27): _render_operations(), expired_approvals(), incident_cost_usd(), IncidentRow, node_usage_stats(), open_durable_fixes(), outcome_breakdown(), _percentile() (+19 more)

### Community 27 - "Correlator"
Cohesion: 0.17
Nodes (15): Correlator, Close windows that have gone idle or exceeded the max window; return their…, Deduplicates raw events and groups them into IncidentEvents over a correlation…, integration, When pending messages exceed PENDING_HIGH_WATER, run_once re-reads and acks…, test_backpressure_drains_pending_when_high_water_exceeded(), test_consumer_reads_acks_and_emits_incident(), Clock (+7 more)

### Community 28 - "LiveApplier"
Cohesion: 0.07
Nodes (25): LiveApplier, Path, Per-action live appliers: act on the running mock_app compose service., Applies a policy-cleared, sandbox-proven mitigation to the live target., Automated rollback safeguard: undoes an action if post-recovery verification…, _tar_single_file(), io, tarfile (+17 more)

### Community 29 - "DynamicTopologyEngine"
Cohesion: 0.09
Nodes (23): DynamicTopologyEngine, Synchronize NetworkX DiGraph representation., Register or update a dynamic microservice at runtime., Remove a dynamic microservice., Register a dynamic dependency edge between services., Query Jaeger REST API for runtime call dependency graphs., Discover live containerized services running on local host., Return all downstream dependencies for a service via NetworkX graph traversal. (+15 more)

### Community 30 - "test_k8s_recovery_and_two_phase_verification_sprint3.py"
Cohesion: 0.18
Nodes (13): MockApplierTracker, asyncio, Unit and integration tests for Sprint 3: - Kubernetes Operator Applier (rollout…, Verify Criterion 3: If p95 latency spikes during soak window, triggers rollback…, Verify Canary failure: if error rate >= 1% during canary, halts and triggers…, Verify clean recovery: both Canary and Soak pass without rollback., test_k8s_applier_rollback_and_inverse(), test_k8s_applier_rollout_restart() (+5 more)

### Community 31 - "score_root_cause"
Cohesion: 0.16
Nodes (8): _deepeval_available(), DeepEval G-Eval root-cause reasoning quality, judged by a custom Claude model.…, # NOTE: verified end-to-end against deepeval 4.1.3 + a live ANTHROPIC_API_KEY at, score_root_cause(), Defensive-wrapper proof: even if _deepeval_available() claims deepeval is…, test_score_is_none_when_deepeval_missing(), test_score_is_none_without_key(), test_scored_path_error_degrades_to_none()

### Community 32 - "logging.py"
Cohesion: 0.42
Nodes (7): add_trace_context(), structlog configuration: every line carries incident_id + trace_id (ADR-0009)., structlog processor: stamp the active span's trace_id/span_id onto the line., setup_logging(), structlog, test_add_trace_context_stamps_active_span(), test_log_line_carries_incident_id_and_trace_id()

### Community 33 - "web.py"
Cohesion: 0.17
Nodes (18): AegisOps Production SRE Incident Management Cockpit (Slice 5). Single-page…, Render the modern SRE incident management cockpit with server briefs embedded., render_cockpit_html(), fastapi_responses, _brief_card(), index(), _durable_fix_card(), _durable_fix_row() (+10 more)

### Community 34 - "test_agent_state.py"
Cohesion: 0.14
Nodes (18): _action(), make_incident(), _result(), test_attempt_record_pairs_action_with_evidence(), test_hitl_choice_has_expired(), test_incident_event_is_the_agent_input(), test_incident_report_v2_fields_default(), test_incident_report_validates() (+10 more)

### Community 35 - "KubernetesApplier"
Cohesion: 0.19
Nodes (13): get_kubernetes_applier(), KubernetesActionResult, KubernetesApplier, _exec(), _exec_rollback(), Trigger rolling restart on Kubernetes deployment via annotation patch., Rollback deployment image tag to previous stable revision., Call connection pool drain on target service. (+5 more)

### Community 36 - "HitlChoice"
Cohesion: 0.16
Nodes (13): HitlChoice, HitlDecision, Enum, str, AutoApprover, Auto-approver stub: eval runs measure the apply path unattended (ADR-0005)., test_hitl_decision_validates(), _patch_action() (+5 more)

### Community 37 - "test_dynamic_topology_and_deployments_sprint2.py"
Cohesion: 0.13
Nodes (26): _format_telemetry(), _prompt(), DeploymentCorrelation, DeploymentEvent, DeploymentIntelligenceStore, DeploymentSource, DeploymentStatus, parse_argocd_webhook() (+18 more)

### Community 39 - "sanitizer.py"
Cohesion: 0.14
Nodes (16): contain_telemetry_boundary(), neutralize_prompt_injections(), Any, LLM Prompt-Injection Defense & Telemetry Sanitizer (AegisOps Sprint 4). Shields…, Strip chat model control tokens and raw HTML scripts., Detect and neutralize prompt-injection phrases, preserving harmless diagnostic…, Enclose untrusted diagnostic text within explicit data boundaries., Full-pipeline sanitization for log lines, exception messages, and alerts. (+8 more)

### Community 40 - "IncidentReport"
Cohesion: 0.24
Nodes (12): PostgresReportSink, PrintSink, Report sinks: stdout for demos, Postgres for the dashboard (spec section 12)., IncidentReport, psycopg, conn_string(), docker, Report sink tests: PrintSink (stdout) and PostgresReportSink (dashboard… (+4 more)

### Community 41 - "test_observability_slice2.py"
Cohesion: 0.09
Nodes (25): Kubernetes Operator Applier (AegisOps Sprint 3). Executes authorized…, Two-Phase Canary & Sustained Soak Verifier (AegisOps Sprint 3). Upgrades post-…, Live closed-loop telemetry verifier (AegisOps Slice 1). Monitors live…, asyncio, Cryptographic Merkle Audit Ledger (AegisOps Sprint 4). Provides SOC2 / ISO…, httpx, networkx, Phase 5 demo: trigger a fault, run the pipeline, print the Jaeger trace URL.… (+17 more)

### Community 42 - "ActionType"
Cohesion: 0.10
Nodes (34): ActionMetadata, ActionType, ProposedAction, BaseModel, Enum, str, Typed remediation action catalog: the agent's entire action space (ADR-0001)., model_validator (+26 more)

### Community 43 - "render_patched_file"
Cohesion: 0.23
Nodes (11): Path, Shared patch rendering: containment guard + git apply in a temp tree. Used by…, Apply `patch` to repo_root/target_file in a temp tree; return the patched bytes., render_patched_file(), subprocess, Shared patch rendering: containment + git apply (ledger carry-in: PatchApplier…, test_applies_valid_patch(), test_bad_patch_raises_with_stderr() (+3 more)

### Community 44 - "test_crypto_ledger_sanitizer_and_slack_sprint4.py"
Cohesion: 0.16
Nodes (13): build_slack_approval_card(), Verify Slack HMAC-SHA256 request signature., Generate Slack Block Kit interactive card JSON with operational action buttons., verify_slack_signature(), starlette_testclient, asyncio, Unit and integration tests for Sprint 4: - Cryptographic Merkle Audit Ledger…, Verify Criterion 2: Injected prompt-attack strings in logs are neutralized… (+5 more)

### Community 71 - "_FakeLLM"
Cohesion: 0.17
Nodes (7): _FakeLLM, _FakeSearch, _FakeStructured, Each config keeps a diagnosable per-case `results` list, and `comparisons`…, Same real pricing-table model string used for both roles (triage and propose…, test_run_experiment_sonnet_triage_costs_more_than_haiku(), test_run_experiment_stores_per_case_results_and_sweep_comparisons()

### Community 72 - "executor.py"
Cohesion: 0.18
Nodes (15): docker_errors, docker_types, Docker-based sandbox: apply patch, run pytest in an isolated container., check_degraded(), check_recovered(), Pure recovery-assertion rules for sandbox fault replay (ADR-0002). No Docker…, should_retrigger(), tempfile (+7 more)

### Community 74 - "test_run_evals_tier3.py"
Cohesion: 0.09
Nodes (34): get_llm(), with_structured_output(), get_propose_llm(), get_triage_llm(), Any, Chat models used by the agent graph. Triage is a bounded classification +…, Connection, DirectSearchAdapter (+26 more)

### Community 75 - "get_tracer"
Cohesion: 0.29
Nodes (7): get_tracer(), inject_trace_context(), Serialize the current context into a W3C carrier (traceparent/tracestate)., decorator(), wrapper(), test_traceparent_round_trip_preserves_trace_id(), Tracer

### Community 76 - "DESIGN.md"
Cohesion: 0.15
Nodes (12): Badges, Status Dots & Indicators, Brand & Style, Buttons & Interactive Controls, Colors, Components, Elevation & Depth, HUD Metric Cards, Incident Audit Ledger & Data Tables (+4 more)

### Community 77 - "AntiFlapCircuitBreaker"
Cohesion: 0.14
Nodes (10): AntiFlapCircuitBreaker, Check if global cascading failure circuit breaker is open (>3 services in 5…, Comprehensive check before allowing automated remediation. Returns (allowed,…, Clear all active history., Return remaining cooldown seconds for services., Enterprise safety circuit breaker and anti-flap controller., Record an applied action on a service., Check if service is in cooldown (flapping protection: 1 action per 15 min). (+2 more)

### Community 78 - "gate.py"
Cohesion: 0.17
Nodes (6): fastapi_testclient, hashlib, Async approval gate: evidence briefs with TTL expiry (ADR-0005)., Interactive Slack & PagerDuty ChatOps (AegisOps Sprint 4). Generates Slack…, hmac, time

### Community 79 - "agent/main.py"
Cohesion: 0.16
Nodes (18): main(), _process_incident(), _process_promotion(), Redis, Demo entrypoint: run the full agent graph with HITL web UI., _read_latest_incidents(), set_approval_gate(), langchain_mcp_adapters_client (+10 more)

### Community 81 - "Part 2: Act-by-Act Synchronized Playbook (Screen Actions + Terminal Commands + Tagged Voiceover)"
Cohesion: 0.07
Nodes (28): Act 1: The 3 AM Outage Hook & Architectural Vision (0:00 – 0:40), Act 2: Live Ingestion, Adaptive Sentinel & CI/CD Change Intelligence (0:40 – 1:35), Act 3: Prompt-Injection Defense, MCP PGVector RAG & Docker Sandbox Replay (1:35 – 2:35), Act 4: End-to-End Jaeger Waterfall (`:16686`) & LangSmith Cross-Linking (2:35 – 3:15), Act 5: 7-Rule Deterministic Policy, JWT RBAC, Slack ChatOps & 2-Phase Canary-Soak (3:15 – 4:05), Act 6: Cryptographic Merkle Tamper Proof, 4-Tier Evals & ROI Finale (4:05 – 5:00), AegisOps: Reconstructed 5-Minute Pitch, Multi-Tab Live Demo Playbook & Fish Audio TTS Script, Fish Audio TTS Segment (Act 1) (+20 more)

### Community 82 - "JaegerClient"
Cohesion: 0.14
Nodes (11): JaegerClient, Any, AsyncClient, BaseModel, Jaeger distributed trace client and correlator (AegisOps Slice 2). Extracts…, List all services instrumented in Jaeger., Fetch recent traces for a given service., Fetch a specific trace by trace_id. (+3 more)

### Community 84 - ".record_event"
Cohesion: 0.15
Nodes (11): compute_entry_hash(), compute_entry_signature(), CryptographicLedgerEntry, Any, BaseModel, Compute HMAC-SHA256 signature of the entry hash., Retrieve the hash of the most recent entry in the chain., Append an immutable, cryptographically chained event to the ledger. (+3 more)

### Community 85 - "test_sandbox_node.py"
Cohesion: 0.34
Nodes (11): sandbox_node(), AttemptRecord, One sandbox-verified attempt: what was tried, what the replay proved (ADR-0006)., FakeExecutor, Sandbox node: verify() wiring, attempt tracking, skip logic (ADR-0002/0006)., _result(), _state(), test_attempt_appended_and_retries_counted() (+3 more)

### Community 86 - "test_adaptive_sentinel_and_alerts_sprint1.py"
Cohesion: 0.14
Nodes (18): math, AdaptiveBaselineDetector, AdaptiveTelemetrySentinel, AnomalyDiagnosis, MetricSample, Adaptive Statistical Telemetry Sentinel (Sprint 1: Dynamic Anomaly Detection).…, Orchestrates telemetry ingestion from ObservabilityHub and evaluates adaptive…, Computes rolling online EWMA, Z-Score, and IQR baselines across telemetry… (+10 more)

### Community 87 - "test_apply_node.py"
Cohesion: 0.33
Nodes (5): SpyApplier, SpyEngine, _state(), test_apply_failure_is_caught_and_not_recorded(), test_apply_success_records_and_flags_applied()

### Community 88 - "ApprovalGate"
Cohesion: 0.17
Nodes (16): Future, ApprovalGate, build_brief(), Decision brief, not raw data: everything the approver needs on one card., test_env_ttl_used_when_not_passed(), HITL web app: brief rendering, decision verb validation, promote (ADR-0005)., _sandbox(), _seed_pending() (+8 more)

### Community 89 - "CryptographicIncidentLedger"
Cohesion: 0.20
Nodes (8): CryptographicIncidentLedger, get_crypto_ledger(), Enterprise Cryptographic Merkle Audit Ledger with hash-chaining., Fetch recent cryptographic ledger entries across all incidents., Verify Criterion 1: Direct row tampering in the ledger fails cryptographic…, Verify breakage if an intermediate entry is deleted or prev_hash modified., test_crypto_ledger_break_chain_linkage(), test_crypto_ledger_hash_chaining_and_tamper_detection()

### Community 91 - "IncidentLedger"
Cohesion: 0.15
Nodes (8): IncidentLedger, Any, BaseModel, Verify the cryptographic hash-chain across all entries., Append an immutable, cryptographically chained event to the ledger., Fetch recent cryptographic audit entries across all incidents., Fetch the full sequential cryptographic audit trail for an incident., test_immutable_incident_ledger_in_memory()

### Community 92 - "SlackInteractionHandler"
Cohesion: 0.22
Nodes (7): format_postmortem_for_jira_or_pagerduty(), Any, Handles Slack Block Kit user clicks and unblocks LangGraph HITL approvals., Process interactive button click from Slack Block Kit., Format an SRE post-mortem report for external ticketing sync (Jira / PagerDuty)., SlackInteractionHandler, test_postmortem_ticket_formatting_jira_and_pagerduty()

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
Cohesion: 0.20
Nodes (4): app_version(), Deploy version this process simulates; 'previous' = the rollback target, i.e.…, DbDeadlockFault, Database Deadlock Runbook

### Community 97 - "IncidentEvent"
Cohesion: 0.20
Nodes (8): AlertIngestionGateway, AlertRecord, Normalize Alertmanager v4 payload into IncidentEvents with deduplication., Normalize PagerDuty V2 messages into IncidentEvents., Async dequeue of incoming alerts for the LangGraph agent runner., Ingests multi-source webhooks, deduplicates firing alerts, and normalizes into…, IncidentEvent, BaseModel

### Community 98 - "test_hitl_gate.py"
Cohesion: 0.40
Nodes (9): _ask(), _passing_sandbox(), _plan_with_durable_fix(), ApprovalGate: TTL expiry, evidence-brief building, resolve/list_pending…, test_approve_resolves_and_clears_brief(), test_build_brief_carries_evidence_and_durable_fix(), test_build_brief_without_sandbox_or_fix(), test_ttl_expiry_returns_expired_decision() (+1 more)

### Community 99 - "app.py"
Cohesion: 0.24
Nodes (11): cache_data, _eval_runs(), _format_metric(), _incident_rows(), main(), Aegis dashboard (spec section 12, ADR-0011): Operations from Postgres,…, _render_evaluation(), fetch_incident_rows() (+3 more)

### Community 100 - "sandbox/demo.py"
Cohesion: 0.36
Nodes (7): docker, build_action(), ensure_images(), main(), Phase-2 demo CLI: inject a fault, apply an action, print verified before/after…, run_one(), sys

### Community 102 - "TwoPhaseVerifier"
Cohesion: 0.17
Nodes (9): get_two_phase_verifier(), Any, AsyncClient, Execute Phase 1 (Canary Probe) followed by Phase 2 (Sustained Soak Window)., Enriched verification result with Phase 1 (Canary) and Phase 2 (Soak) telemetry., Production 2-phase canary and sustained soak verification engine., Query real-time metrics directly from the live service., TwoPhaseVerificationResult (+1 more)

### Community 103 - "MemoryLeakFault"
Cohesion: 0.25
Nodes (3): Incident Ground Truth Dataset, MemoryLeakFault, Memory Leak Runbook

### Community 104 - "setup_tracing"
Cohesion: 0.29
Nodes (7): Install a global TracerProvider exporting to OTLP/HTTP. Idempotent., Force-flush + shutdown so short-lived processes export their spans. When Jaeger…, setup_tracing(), shutdown_tracing(), main(), test_setup_tracing_is_idempotent_and_returns_provider(), TracerProvider

### Community 105 - "promoted_incident"
Cohesion: 0.47
Nodes (5): promoted_incident(), Derived identity for a promoted durable-fix run, so its report upserts a…, agent.main pure helpers: promoted-run identity so promotion reports don't…, test_promoted_incident_does_not_mutate_original(), test_promoted_incident_suffixes_id_and_preserves_other_fields()

## Knowledge Gaps
- **45 isolated node(s):** `aegis`, `entrypoint.sh script`, `Full Continuous TTS Prompt (Copy-Paste Directly into Fish Audio)`, `Pre-Flight Recording Checklist`, `On-Screen Choreography` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 650 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FaultKind` connect `FaultKind` to `test_auth_and_rbac_slice6.py`, `state.py`, `PolicyDecision`, `SandboxResult`, `mock_app/main.py`, `test_faults.py`, `alerts_gateway.py`, `hub.py`, `schema.py`, `run_evals.py`, `make_incident`, `LiveVerifier`, `drivers.py`, `test_dashboard_operations_data.py`, `Correlator`, `test_k8s_recovery_and_two_phase_verification_sprint3.py`, `test_agent_state.py`, `test_dynamic_topology_and_deployments_sprint2.py`, `SandboxExecutor`, `IncidentReport`, `test_observability_slice2.py`, `ActionType`, `executor.py`, `test_run_evals_tier3.py`, `test_sandbox_node.py`, `test_adaptive_sentinel_and_alerts_sprint1.py`, `DbDeadlockFault`, `IncidentEvent`, `sandbox/demo.py`, `TwoPhaseVerifier`, `MemoryLeakFault`?**
  _High betweenness centrality (0.193) - this node is a cross-community bridge._
- **Why does `ProposedAction` connect `ActionType` to `test_auth_and_rbac_slice6.py`, `state.py`, `PolicyDecision`, `SandboxResult`, `run_evals.py`, `DurableFixRegistry`, `test_report_node.py`, `make_incident`, `test_agent_graph.py`, `FaultKind`, `drivers.py`, `test_dashboard_operations_data.py`, `LiveApplier`, `test_k8s_recovery_and_two_phase_verification_sprint3.py`, `test_agent_state.py`, `KubernetesApplier`, `HitlChoice`, `SandboxExecutor`, `IncidentReport`, `test_observability_slice2.py`, `executor.py`, `test_run_evals_tier3.py`, `test_sandbox_node.py`, `test_apply_node.py`, `ApprovalGate`, `test_hitl_gate.py`, `sandbox/demo.py`, `TwoPhaseVerifier`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `ActionType` connect `ActionType` to `test_auth_and_rbac_slice6.py`, `state.py`, `PolicyDecision`, `SandboxResult`, `DurableFixRegistry`, `test_report_node.py`, `make_incident`, `test_agent_graph.py`, `FaultKind`, `drivers.py`, `test_dashboard_operations_data.py`, `LiveApplier`, `test_k8s_recovery_and_two_phase_verification_sprint3.py`, `test_agent_state.py`, `KubernetesApplier`, `HitlChoice`, `SandboxExecutor`, `IncidentReport`, `test_observability_slice2.py`, `executor.py`, `test_run_evals_tier3.py`, `test_sandbox_node.py`, `test_apply_node.py`, `ApprovalGate`, `test_hitl_gate.py`, `sandbox/demo.py`, `KubernetesActionPayload`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 103 inferred relationships involving `FaultKind` (e.g. with `propose_node()` and `IncidentReport`) actually correct?**
  _`FaultKind` has 103 INFERRED edges - model-reasoned connections that need verification._
- **Are the 114 inferred relationships involving `ActionType` (e.g. with `route_after_policy()` and `propose_node()`) actually correct?**
  _`ActionType` has 114 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `ProposedAction` (e.g. with `propose_node()` and `AttemptRecord`) actually correct?**
  _`ProposedAction` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PolicyDecision` (e.g. with `route_after_policy()` and `_determine_outcome()`) actually correct?**
  _`PolicyDecision` has 54 INFERRED edges - model-reasoned connections that need verification._