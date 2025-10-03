
# Work Packages

## Summary Stats
- Total work packages: 9 (Security:1, Operational:3, Performance:1, Quality:1, BestPractice:1, Enhancement:1, TechnicalDebt:1)
- Priority distribution: High=0, Medium=5, Low=1
- Estimated effort by priority: High ≈ 0; Medium ≈ 3×S + 1×XS + 1×M; Low ≈ 1×M
- Quick-win candidates: None (all previously identified quick wins delivered)

## Priority: HIGH

## WP-201: Default To Authenticated Gateway Boots *(Completed)*

**Category**: Security
**Priority**: HIGH
**Effort**: S (2-8hrs)
**Risk Level**: High

### Description
Running the API outside the packaged container previously started with `KM_AUTH_ENABLED=false`, exposing every reader and maintainer endpoint without credentials if operators forgot to override the flag.

### Current State
`AppSettings.auth_enabled` now defaults to `True`, the scheduler/tests receive fixture-provided credentials, and startup logs emit a dedicated warning when operators deliberately disable auth. Documentation reflects the new default and discourages `KM_ALLOW_INSECURE_BOOT` outside isolated demos.

### Desired State
✔️ Achieved — gateway boots are secure-by-default and fail closed when credentials are missing.

### Impact if Not Addressed
Addressed; residual monitoring captured in RISK-001 (reduced to credential hygiene).

### Delivered Changes
1. Default `KM_AUTH_ENABLED` to `True` and log `auth_disabled` warnings in `gateway/api/app.py` when operators opt out.
2. Added autouse fixtures supplying test credentials, refreshed API smoke/security/UI tests to include tokens where required, and extended defaults coverage (`tests/test_settings_defaults.py`).
3. Updated configuration docs and changelog to highlight the secure default; `docs/UPGRADE_ROLLBACK.md` no longer instructs flipping the flag manually.

### Affected Components
- gateway/config/settings.py
- gateway/api/app.py
- tests/conftest.py
- tests/test_settings_defaults.py
- tests/test_app_smoke.py
- tests/test_api_security.py
- tests/test_ui_routes.py
- docs/CONFIG_REFERENCE.md
- docs/UPGRADE_ROLLBACK.md
- CHANGELOG.md

### Dependencies
- None

### Acceptance Criteria
- [x] Creating the app without explicit overrides enforces authentication and fails fast if tokens are missing.
- [x] Documentation explains how to opt into insecure dev-mode and calls out risks.
- [x] Security tests cover secure, insecure, and misconfigured credential scenarios.

### Related Issues
- RISK-001

## WP-202: Make Scheduled Backup Pruning Safe *(Completed)*

**Category**: Operational
**Priority**: HIGH
**Effort**: S (2-8hrs)
**Risk Level**: High

### Description
Backup retention deletes *every* item in the configured destination beyond the retention limit, even if the directory contains unrelated files.

### Current State
`gateway/backup/service.py` now defaults backups to `${KM_STATE_PATH}/backups/archives`, `km-backup-*.tgz` filenames, and exposes helper utilities (`default_backup_destination`, `is_backup_archive`). The scheduler (`gateway/scheduler.py`) prunes only managed archives, increments a new Prometheus metric (`km_backup_retention_deletes_total`), and leaves foreign files intact. `bin/km-backup` writes to the archival subdirectory by default, and documentation references have been updated.

### Desired State
✔️ Achieved — retention operates exclusively on managed archives inside a dedicated directory.

### Impact if Not Addressed
Resolved by the implemented changes; residual risk tracked in RISK-002 has been reduced to monitoring.

### Delivered Changes
1. Shared helpers (`default_backup_destination`, `is_backup_archive`) surfaced for schedulers and tooling.
2. Scheduler now records deletion metrics, updates health status with counts, and limits pruning to `km-backup-*` archives.
3. `bin/km-backup` defaults to `.duskmantle/backups/archives`; docs (`OPERATIONS.md`, `QUICK_START.md`, `UPGRADE_ROLLBACK.md`, `MCP_INTERFACE_SPEC.md`) reflect the new layout.
4. Regression tests added/updated (`tests/test_scheduler.py`, `tests/mcp/test_server_tools.py`) to cover safe pruning and path expectations.

### Affected Components
- gateway/scheduler.py
- gateway/backup/service.py
- gateway/backup/__init__.py
- gateway/observability/metrics.py
- bin/km-backup
- docs/OPERATIONS.md
- docs/QUICK_START.md
- docs/UPGRADE_ROLLBACK.md
- docs/MCP_INTERFACE_SPEC.md
- docs/ACCEPTANCE_DEMO_PLAYBOOK.md
- tests/test_scheduler.py
- tests/mcp/test_server_tools.py

### Dependencies
- None

### Acceptance Criteria
- [x] Retention logic deletes only gateway-created archives.
- [x] Backup destination defaults to a safe, isolated directory.
- [x] Tests cover retention with extraneous files and verify no collateral deletions.

### Related Issues
- RISK-002

## WP-204: Bound Graph Enrichment Latency In Search *(Completed)*

**Category**: Performance
**Priority**: HIGH
**Effort**: M (1-3 days)
**Risk Level**: Medium

### Description
Hybrid search previously fetched graph context for every hit sequentially with no global budget, so slow Neo4j responses could stall the entire request.

### Current State
`SearchService.search` now enforces configurable result/time budgets (`KM_SEARCH_GRAPH_MAX_RESULTS`, `KM_SEARCH_GRAPH_TIME_BUDGET_MS`), skips additional graph lookups once exhausted, and emits Prometheus counters (`km_search_graph_skipped_total`) to monitor skipped enrichments. Warnings are surfaced in API metadata when limits trigger.

### Desired State
✔️ Achieved — graph enrichment respects per-request budgets and exposes telemetry for operators.

### Impact if Not Addressed
Resolved; residual monitoring covered by RISK-004 (now focused on tuning budgets rather than unbounded latency).

### Delivered Changes
1. Added configurable graph enrichment settings in `AppSettings` and propagated to `SearchOptions` for runtime tuning.
2. Updated `SearchService` to cap the number of enriched results, enforce a time budget, and record skip metrics/warnings.
3. Extended tests (`tests/test_search_service.py`) to cover limit/time-budget behaviour and metric increments.

### Affected Components
- gateway/config/settings.py
- gateway/search/service.py
- gateway/observability/metrics.py
- gateway/api/dependencies.py
- tests/test_search_service.py
- docs/CONFIG_REFERENCE.md
- CHANGELOG.md

### Dependencies
- None

### Acceptance Criteria
- [x] Search responses return within the configured graph budget even under Neo4j slowness.
- [x] Metrics report skipped/timeout graph lookups and concurrency usage.
- [x] Regression tests cover mixed fast/slow graph situations.

### Related Issues
- RISK-004

## Priority: MEDIUM

## WP-203: Rotate Search Feedback Event Logs *(Completed)*

**Category**: Operational
**Priority**: MEDIUM
**Effort**: S (2-8hrs)
**Risk Level**: Medium

### Description
The feedback store previously appended JSON lines indefinitely with no rotation or metrics, risking disk growth and silent data loss when logs were truncated.

### Current State
`SearchFeedbackStore` now enforces configurable size-based rotation (`KM_FEEDBACK_LOG_MAX_BYTES`, `KM_FEEDBACK_LOG_MAX_FILES`), exposes Prometheus metrics (`km_feedback_log_bytes`, `km_feedback_rotations_total`), and updates documentation/runbooks describing the behaviour.

### Desired State
✔️ Achieved — feedback logs rotate automatically with observable metrics and operator tuning knobs.

### Impact if Not Addressed
Resolved; residual monitoring captured in RISK-003 (reduced to ensuring operators keep retention defaults sensible).

### Delivered Changes
1. Added rotation controls to `AppSettings`, wired through `create_app`, and enhanced `SearchFeedbackStore` with rotation logic and metrics.
2. Introduced new Prometheus metrics for log size/rotations and default configuration entries in `docs/CONFIG_REFERENCE.md` / `docs/OPERATIONS.md`.
3. Added focused regression tests (`tests/test_search_feedback.py`) covering rotation and metric updates.

### Affected Components
- gateway/search/feedback.py
- gateway/observability/metrics.py
- gateway/config/settings.py
- gateway/api/app.py
- docs/CONFIG_REFERENCE.md
- docs/OPERATIONS.md
- CHANGELOG.md
- tests/test_search_feedback.py

### Dependencies
- None

### Acceptance Criteria
- [x] Feedback logs rotate automatically with configurable limits.
- [x] Metrics/health endpoints expose current file size and last rotation.
- [x] Tests verify rotation, retention, and corrupted-log recovery.

### Related Issues
- RISK-003

## WP-205: Make Artifact Ledger Updates Atomic *(Completed)*

**Category**: TechnicalDebt
**Priority**: MEDIUM
**Effort**: S (2-8hrs)
**Risk Level**: Medium

### Description
The incremental ingest ledger previously rewrote JSON without locking or atomic rename, risking corruption during concurrent runs or crashes.

### Current State
`IngestionPipeline` now guards ledger reads/writes with `FileLock`, validates schema on load, and performs atomic `os.replace` writes via temporary files. Rotating artifacts are covered by new unit tests.

### Desired State
✔️ Achieved — ledger updates are atomic, protected by locks, and corruption falls back to safe defaults with logging.

### Impact if Not Addressed
Addressed; residual monitoring lives in RISK-005 (reduced to ensuring lock timeouts don’t fire under heavy contention).

### Delivered Changes
1. Added ledger lock handling and atomic rename logic in `gateway/ingest/pipeline.py`.
2. Enhanced ledger loading with validation/logging and ensured temporary files are cleaned up.
3. Added regression tests for atomic writes and corrupt ledger recovery (`tests/test_ingest_pipeline.py`).

### Affected Components
- gateway/ingest/pipeline.py
- tests/test_ingest_pipeline.py
- CHANGELOG.md

### Dependencies
- None

### Acceptance Criteria
- [x] Ledger updates are atomic and concurrent ingestion attempts block gracefully.
- [x] Corrupt ledgers are detected with a clear error and recovery instructions.
- [x] Tests cover crash/retry scenarios.

### Related Issues
- RISK-005

## WP-206: Refactor SearchService For Maintainability *(Completed)*

**Category**: Quality
**Priority**: MEDIUM
**Effort**: M (1-3 days)
**Risk Level**: Low

### Description
`SearchService` previously bundled vector retrieval, graph enrichment, heuristic scoring, and ML reranking into a 1k+ LOC module. The coupling slowed reviews and made new signals risky.

### Current State
`SearchService` now orchestrates dedicated collaborators: `VectorRetriever`, `GraphEnricher`, `HeuristicScorer`, and `ModelScorer`. Filters and DTOs live in `gateway/search/filtering.py` and `gateway/search/models.py`, while unit suites cover each collaborator. Documentation (`docs/SEARCH_SCORING_PLAN.md`, audit set) reflects the new layout.

### Desired State
✔️ Achieved — responsibilities are split into reusable modules with targeted tests and updated docs.

### Impact if Not Addressed
Resolved; future relevance work can evolve each component independently.

### Delivered Changes
1. Introduced collaborator modules (`vector_retriever`, `filtering`, `graph_enricher`, `scoring`, `ml`, `models`) and rewired `SearchService` to compose them.
2. Added focused unit suites in `tests/search/test_*.py` and refreshed integration tests to cover the new architecture.
3. Updated scoring documentation and audit artefacts to describe the modular search pipeline.

### Affected Components
- gateway/search/service.py
- gateway/search/vector_retriever.py
- gateway/search/filtering.py
- gateway/search/graph_enricher.py
- gateway/search/scoring.py
- gateway/search/ml.py
- gateway/search/models.py
- docs/SEARCH_SCORING_PLAN.md
- audit/MODULE_DOCUMENTATION.md
- tests/search/test_vector_retriever.py
- tests/search/test_filtering.py
- tests/search/test_graph_enricher.py
- tests/search/test_scoring.py
- tests/search/test_ml_scorer.py
- tests/test_search_service.py

### Dependencies
- None

### Acceptance Criteria
- [x] Search code is decomposed into well-documented modules with focused tests.
- [x] High-complexity helpers removed from `SearchService`, reducing its cyclomatic score.
- [x] Documentation reflects the new architecture.

### Related Issues
- RISK-004

## WP-207: Introduce Versioned REST Surface *(Completed)*

**Category**: BestPractice
**Priority**: MEDIUM
**Effort**: S (2-8hrs)
**Risk Level**: Medium

### Description
All FastAPI routes were previously mounted at the root (e.g., `/search`, `/graph/...`) with no versioning or compatibility contract.

### Current State
The API now serves all maintainer/reader operations exclusively via `/api/v1/*`, and tests/docs reference the versioned paths by default.

### Desired State
✔️ Achieved — `/api/v1` is the canonical surface and clients default to it; no fallback routes remain.

### Impact if Not Addressed
Resolved; external integrations can upgrade independently without coordinating URL changes.

### Delivered Changes
1. Added shared API constants and updated `gateway/api/app.py` to mount search/graph/reporting routers under `/api/v1`.
2. Switched MCP/recipe clients and pytest suites to the versioned paths and refreshed CLI/security/graph tests accordingly.
3. Updated documentation and audit artefacts (README, CONFIG_REFERENCE, OBSERVABILITY_GUIDE, system docs, changelog) to highlight the new prefix as the canonical surface.

### Affected Components
- gateway/api/constants.py
- gateway/api/app.py
- gateway/mcp/client.py
- tests/test_api_security.py
- tests/test_search_api.py
- tests/test_graph_api.py
- tests/test_app_smoke.py
- tests/test_coverage_report.py
- tests/test_graph_service_startup.py
- docs/CONFIG_REFERENCE.md
- docs/OBSERVABILITY_GUIDE.md
- docs/KNOWLEDGE_MANAGEMENT*.md
- README.md, CHANGELOG.md
- audit documentation set (summary, system, risks, quick wins, work packages, module doc)

### Dependencies
- WP-201 (ensures consistent auth handling during migration)

### Acceptance Criteria
- [x] `/api/v1/*` endpoints mirror existing behaviour with automated contract tests.
- [x] Legacy routes emit deprecation warnings with a removal schedule.
- [x] Client libraries and docs reference the versioned paths by default.

### Related Issues
- RISK-006

## WP-208: Clamp Audit History Window *(Completed)*

**Category**: Operational
**Priority**: MEDIUM
**Effort**: XS (<2hrs)
**Risk Level**: Low

### Description
Maintainer users can request an unbounded number of audit entries, loading the entire SQLite table into memory.

### Current State
`/audit/history` clamps requests to `KM_AUDIT_HISTORY_MAX_LIMIT` (default 100), emits a warning header when the cap is hit, and includes the effective limit in the `X-KM-Audit-Limit` response header. The ingestion CLI mirrors the same cap and announces adjustments to operators, while `AuditLogger.recent` guards against zero/negative limits directly.

### Desired State
✔️ Achieved — audit history reads are bounded and surface clear operator feedback when requests are normalised.

### Impact if Not Addressed
Resolved; residual risk tracked in RISK-007 has been downgraded now that large pulls are clamped and observable.

### Delivered Changes
1. Added `KM_AUDIT_HISTORY_MAX_LIMIT` to `AppSettings` and validated bounds (`gateway/config/settings.py`).
2. Normalised `/api/v1/audit/history` limits, emitted warning/limit headers when clamps trigger, and logged adjustments (`gateway/api/routes/reporting.py`).
3. Mirrored the cap in `gateway-ingest audit-history`, updated `AuditLogger.recent` to sanitise limits, and extended pytest coverage for API/CLI behaviours (`tests/test_api_security.py`, `tests/test_ingest_cli.py`).
4. Documented the new setting and behaviour across configuration, observability, README, changelog, and audit artefacts.

### Affected Components
- gateway/config/settings.py
- gateway/api/routes/reporting.py
- gateway/ingest/cli.py
- gateway/ingest/audit.py
- tests/test_api_security.py
- tests/test_ingest_cli.py
- docs/CONFIG_REFERENCE.md
- docs/OBSERVABILITY_GUIDE.md
- README.md
- CHANGELOG.md
- audit documentation set (summary, system, risks, quick wins, work packages, module doc)

### Dependencies
- None

### Acceptance Criteria
- [x] Requests exceeding the configured limit are clamped and return a warning.
- [x] Unit tests cover boundary and invalid values.
- [x] Documentation lists the maximum retrievable audit history span.

### Related Issues
- RISK-007

## Priority: LOW

## WP-209: Promote Feedback Events Into Training Pipeline

**Category**: Enhancement
**Priority**: LOW
**Effort**: M (1-3 days)
**Risk Level**: Low

### Description
Collected feedback is never transformed into structured datasets for `gateway/search/trainer.py`, limiting the value of ML scoring mode.

### Current State
`search/trainer.py` expects curated training files, but the system only stores append-only logs (`gateway/search/feedback.py`). No tooling automates aggregation or model retraining.

### Desired State
Provide a CLI or scheduled job that rolls feedback logs into training datasets, retrains/validates models, and publishes artifacts for deployment.

### Impact if Not Addressed
The ML scoring mode stays stale and operators cannot incorporate collected ratings.

### Proposed Solution
1. Add a `gateway-search export-feedback` command that aggregates events into the trainer format. 2. Offer optional auto-training via scheduler or makefile. 3. Document the workflow in `docs/MCP_RECIPES.md` and add tests covering export edge cases.

### Affected Components
- gateway/search/feedback.py
- gateway/search/trainer.py
- gateway/search/cli.py
- docs/MCP_RECIPES.md

### Dependencies
- WP-203 (ensures feedback logs are well-behaved and rotated)

### Acceptance Criteria
- [ ] CLI command exports validated datasets ready for `gateway/search/trainer.py`.
- [ ] Documentation walks through feedback-driven retraining.
- [ ] Tests cover aggregation and malformed log handling.

### Related Issues
- RISK-008
