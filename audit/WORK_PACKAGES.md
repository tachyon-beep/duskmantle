
# Work Packages

## Summary Stats
- Total work packages: 9 (Security:1, Operational:3, Performance:1, Quality:1, BestPractice:1, Enhancement:1, TechnicalDebt:1)
- Priority distribution: High=3, Medium=5, Low=1
- Estimated effort by priority: High ≈ 2×S + 1×M; Medium ≈ 4×S + 1×XS + 1×M; Low ≈ 1×M
- Quick-win candidates: WP-203, WP-208 (≤S effort with medium/high impact)

## Priority: HIGH

## WP-201: Default To Authenticated Gateway Boots

**Category**: Security
**Priority**: HIGH
**Effort**: S (2-8hrs)
**Risk Level**: High

### Description
Running the API outside the packaged container starts with `KM_AUTH_ENABLED` set to `False`, exposing every reader and maintainer endpoint without credentials.

### Current State
`AppSettings.auth_enabled` defaults to `False` (`gateway/config/settings.py:50`). The Docker entrypoint flips the flag to `True`, but developers or operators who launch `uvicorn gateway.api.app:create_app --factory` directly inherit the insecure default with no warning.

### Desired State
Gateway processes should fail closed unless `KM_AUTH_ENABLED=false` is explicitly provided. Local development remains possible via an explicit env override or a dedicated `--insecure` CLI flag.

### Impact if Not Addressed
An accidentally exposed gateway leaks graph/search data and permits destructive maintainer workflows to any network peer.

### Proposed Solution
1. Change the default to `True` and emit a loud log warning when auth is disabled. 2. Update CLI/docs to require `KM_ALLOW_INSECURE_BOOT=true` (or similar) for demo scenarios. 3. Extend tests (`tests/test_api_security.py`) to cover both secure and insecure boot paths.

### Affected Components
- gateway/config/settings.py
- gateway/api/app.py
- docs/QUICK_START.md
- tests/test_api_security.py

### Dependencies
- None

### Acceptance Criteria
- [ ] Creating the app without explicit overrides enforces authentication and fails fast if tokens are missing.
- [ ] Documentation explains how to opt into insecure dev-mode and calls out risks.
- [ ] Security tests cover secure, insecure, and misconfigured credential scenarios.

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

## WP-204: Bound Graph Enrichment Latency In Search

**Category**: Performance
**Priority**: HIGH
**Effort**: M (1-3 days)
**Risk Level**: Medium

### Description
Hybrid search performs two synchronous Cypher calls per hit (`get_node` + `shortest_path_depth`), causing tail-latency spikes when Neo4j is slow or results are numerous.

### Current State
`SearchService.search` / `_resolve_graph_context` (`gateway/search/service.py:150-430`) iterate results sequentially with no concurrency cap, timeout, or per-request budget. A single slow node can delay the entire response.

### Desired State
Graph enrichment should run within a bounded per-request budget, skip or degrade gracefully when Neo4j is slow, and ideally fetch results concurrently up to a small worker pool.

### Impact if Not Addressed
Search endpoints stall under load, Prometheus latency alerts fire, and MCP tools appear hung even though vector search completed.

### Proposed Solution
1. Introduce an async or thread-based worker pool with a configurable concurrency limit. 2. Apply per-hit timeouts and short-circuit once the graph budget is exhausted. 3. Emit metrics for skipped/slow enrichments and extend tests (`tests/test_search_service.py`) to cover degraded graph scenarios.

### Affected Components
- gateway/search/service.py
- gateway/graph/service.py
- gateway/observability/metrics.py
- tests/test_search_service.py

### Dependencies
- None

### Acceptance Criteria
- [ ] Search responses return within the configured graph budget even under Neo4j slowness.
- [ ] Metrics report skipped/timeout graph lookups and concurrency usage.
- [ ] Regression tests cover mixed fast/slow graph situations.

### Related Issues
- RISK-004

## Priority: MEDIUM

## WP-203: Rotate Search Feedback Event Logs

**Category**: Operational
**Priority**: MEDIUM
**Effort**: S (2-8hrs)
**Risk Level**: Medium

### Description
The feedback store appends JSON lines indefinitely with no size cap, rotation, or corruption handling.

### Current State
`SearchFeedbackStore` (`gateway/search/feedback.py:29-66`) writes to a single `events.log`. Long-running gateways accumulate unbounded state and have no metric indicating log health.

### Desired State
Feedback storage should rotate once a configurable size or age threshold is reached, with metrics and alerts when rotation occurs.

### Impact if Not Addressed
Disk fills compromise ingestion and backups, and truncated/corrupt logs silently drop training data.

### Proposed Solution
Implement rollover (size or time-based), optionally back by gzip, surface `km_feedback_events_bytes_total`, and add health checks for stale rotation. Update docs for retention tuning.

### Affected Components
- gateway/search/feedback.py
- gateway/observability/metrics.py
- docs/OPERATIONS.md
- tests/test_search_service.py

### Dependencies
- None

### Acceptance Criteria
- [ ] Feedback logs rotate automatically with configurable limits.
- [ ] Metrics/health endpoints expose current file size and last rotation.
- [ ] Tests verify rotation, retention, and corrupted-log recovery.

### Related Issues
- RISK-003

## WP-205: Make Artifact Ledger Updates Atomic

**Category**: TechnicalDebt
**Priority**: MEDIUM
**Effort**: S (2-8hrs)
**Risk Level**: Medium

### Description
The incremental ingest ledger is rewritten wholesale without locking or atomic rename, so concurrent runs or crashes can corrupt it.

### Current State
`IngestionPipeline._write_artifact_ledger` (`gateway/ingest/pipeline.py:432-444`) writes JSON directly to disk. There is no locking, validation, or recovery path for partial writes.

### Desired State
Ledger writes should use `NamedTemporaryFile` + atomic rename, file locks to block concurrent writers, and schema validation to quarantine corrupt entries.

### Impact if Not Addressed
Incremental ingest can revert to full reprocessing or produce inconsistent coverage metrics after a crash.

### Proposed Solution
1. Introduce `filelock` around ledger writes. 2. Write to `*.tmp` and rename on success. 3. Validate schema before loading, with automatic backup/repair. Extend tests to simulate partial writes.

### Affected Components
- gateway/ingest/pipeline.py
- tests/test_ingest_pipeline.py
- tests/test_coverage_report.py

### Dependencies
- None

### Acceptance Criteria
- [ ] Ledger updates are atomic and concurrent ingestion attempts block gracefully.
- [ ] Corrupt ledgers are detected with a clear error and recovery instructions.
- [ ] Tests cover crash/retry scenarios.

### Related Issues
- RISK-005

## WP-206: Refactor SearchService For Maintainability

**Category**: Quality
**Priority**: MEDIUM
**Effort**: M (1-3 days)
**Risk Level**: Low

### Description
`gateway/search/service.py` exceeds 1k LOC and mixes vector retrieval, scoring, graph enrichment, and ML reranking in a single class, raising the maintenance burden.

### Current State
Complex helper functions (`_resolve_graph_context`, `_compute_scoring`, `_build_model_features`, etc.) interleave concerns, and tests rely on large fixtures (`tests/test_search_service.py`, `tests/test_search_maintenance.py`).

### Desired State
Separate modules or dataclasses for vector search, scoring heuristics, graph enrichment, and ML reranking with targeted unit tests and docstrings.

### Impact if Not Addressed
Future changes (e.g., new signals or models) risk regressions and slow review cycles.

### Proposed Solution
1. Split `SearchService` into smaller collaborators (e.g., `GraphEnricher`, `ScoreCombiner`). 2. Add docstrings and type aliases. 3. Expand unit tests for each component. 4. Update public API documentation to reflect new structure.

### Affected Components
- gateway/search/service.py
- gateway/search/maintenance.py
- tests/test_search_service.py
- docs/SEARCH_SCORING_PLAN.md

### Dependencies
- None

### Acceptance Criteria
- [ ] Search code is decomposed into well-documented modules with focused tests.
- [ ] Cyclomatic complexity metrics drop significantly (target <15 per function).
- [ ] Documentation reflects the new architecture.

### Related Issues
- RISK-004

## WP-207: Introduce Versioned REST Surface

**Category**: BestPractice
**Priority**: MEDIUM
**Effort**: S (2-8hrs)
**Risk Level**: Medium

### Description
All FastAPI routes are mounted at the root (e.g., `/search`, `/graph/...`) with no versioning or compatibility contract.

### Current State
Routers in `gateway/api/routes/*.py` expose bare paths, and clients (MCP, UI, scripts) couple to them directly. Breaking changes require lockstep upgrades.

### Desired State
Expose a versioned prefix (e.g., `/api/v1/`) with backward-compatible aliases and document deprecation timelines.

### Impact if Not Addressed
Future schema changes or refactors risk breaking MCP tools and external automation.

### Proposed Solution
1. Introduce a versioned APIRouter (`/api/v1`) and maintain legacy aliases behind a feature flag. 2. Update MCP client defaults and docs. 3. Add contract tests ensuring both paths stay in sync until the legacy surface is retired.

### Affected Components
- gateway/api/app.py
- gateway/api/routes/*
- gateway/mcp/client.py
- docs/API_APP_REFACTOR_PLAN.md

### Dependencies
- WP-201 (ensures consistent auth handling during migration)

### Acceptance Criteria
- [ ] `/api/v1/*` endpoints mirror existing behaviour with automated contract tests.
- [ ] Legacy routes emit deprecation warnings with a removal schedule.
- [ ] Client libraries and docs reference the versioned paths by default.

### Related Issues
- RISK-006

## WP-208: Clamp Audit History Window

**Category**: Operational
**Priority**: MEDIUM
**Effort**: XS (<2hrs)
**Risk Level**: Low

### Description
Maintainer users can request an unbounded number of audit entries, loading the entire SQLite table into memory.

### Current State
`/audit/history` passes the query `limit` straight to `AuditLogger.recent` (`gateway/api/routes/reporting.py:25-38`) without validation.

### Desired State
Clamp the limit to a sensible maximum (e.g., 100), validate inputs, and document the ceiling.

### Impact if Not Addressed
Large requests can impact latency and memory usage on modest hardware.

### Proposed Solution
1. Normalise the limit parameter with min/max bounds. 2. Add tests covering invalid/large limits. 3. Surface the configured limit via docs or response metadata.

### Affected Components
- gateway/api/routes/reporting.py
- tests/test_coverage_report.py

### Dependencies
- None

### Acceptance Criteria
- [ ] Requests exceeding the configured limit are clamped and return a warning.
- [ ] Unit tests cover boundary and invalid values.
- [ ] Documentation lists the maximum retrievable audit history span.

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
