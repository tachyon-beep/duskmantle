# Work Packages

## Summary Statistics
- High priority: 4 items (Effort mix: 3×S, 1×M)
- Medium priority: 4 items (Effort mix: 2×S, 1×M, 1×L)
- Low priority: 2 items (Effort mix: 1×XS, 1×S)
- Estimated effort by priority:
  - High: ≈ 2–3 developer weeks (assuming S≈1–2 days, M≈3–5 days)
  - Medium: ≈ 3–4 developer weeks (two S, one M, one L)
  - Low: <1 developer week combined

## High Priority

## WP-001: Enforce UI Auth on Sensitive Observability Views
**Category**: Security  
**Priority**: HIGH  
**Effort**: S  
**Risk Level**: High

### Description
Unauthenticated UI endpoints (`/ui/lifecycle`, `/ui/lifecycle/report`, `/ui/events`) expose operational data and accept event writes even when `KM_AUTH_ENABLED=true`.

### Current State
- `gateway/ui/routes.py` serves lifecycle JSON and event logging without authentication or rate limits beyond metrics counters.  
- Tests (`tests/test_ui_routes.py`) only cover unauthenticated mode.

### Desired State
- UI endpoints require reader or maintainer token when auth is enabled, mirroring REST surface behaviour.  
- Anonymous access remains optional when `KM_AUTH_ENABLED=false`.

### Impact if Not Addressed
Lifecycle reports and telemetry can leak ingest details, coverage gaps, and host metadata to unauthenticated users; endpoint can be abused for event flooding.

### Proposed Solution
- Introduce FastAPI dependencies wrapping `require_reader` / `require_maintainer` for UI routers.  
- Respect settings toggle to allow anonymous previews if explicitly configured (e.g., new `KM_UI_PUBLIC` flag).  
- Update tests to cover both authenticated and unauthenticated modes.

### Affected Components
- `gateway/ui/routes.py`
- `gateway/api/auth.py`
- `tests/test_ui_routes.py`

### Dependencies
- None.

### Acceptance Criteria
- [ ] UI JSON and event endpoints respond 401/403 when tokens missing and auth enabled.  
- [ ] Happy-path UI responses succeed with valid reader token.  
- [ ] Tests cover secured mode.  
- [ ] Documentation updated to describe UI auth behaviour.

### Related Issues
- Risk register item R1.

---

## WP-002: Externalise Rate Limiter Storage
**Category**: Operational  
**Priority**: HIGH  
**Effort**: M  
**Risk Level**: Medium

### Description
Rate limiting relies on an in-memory SlowAPI store initialised with `memory://<uuid4>`; limits reset per process and are ineffective across multiple workers or nodes.

### Current State
- `_configure_rate_limits` in `gateway/api/app.py` hard-codes `Limiter(storage_uri=f"memory://{uuid4()}")`.  
- No configuration to supply Redis/Memcached backend; documentation implies production use.

### Desired State
- Operators can configure persistent or centralised storage (Redis, Memcached, database).  
- Default remains in-memory for development but documented as non-production.

### Impact if Not Addressed
Multi-process deployments bypass limits, enabling DoS on expensive endpoints (search, graph cypher, metrics) and invalidating throttle guarantees.

### Proposed Solution
- Add settings (e.g., `KM_RATE_LIMIT_STORAGE_URI`) and validate on startup.  
- Document deployment guidance and provide example redis configuration.  
- Update tests to ensure fallback to memory when unset.

### Affected Components
- `gateway/api/app.py`
- `gateway/config/settings.py`
- `docs/` deployment guidance

### Dependencies
- None.

### Acceptance Criteria
- [ ] Storage backend configurable via settings with sane default.  
- [ ] Failing to connect to configured backend raises startup error.  
- [ ] Documentation updated with redis example.  
- [ ] Tests cover memory and dummy backend configuration.

### Related Issues
- Risk register item R2.

---

## WP-003: Fail Fast on Critical Dependency Outages
**Category**: Operational  
**Priority**: HIGH  
**Effort**: S  
**Risk Level**: High

### Description
Gateway reports ready even when Neo4j or Qdrant are unreachable; `_initialise_*` warn but service starts and `/readyz` returns success.

### Current State
- `create_app` logs warnings, sets metrics, but leaves app running.  
- Clients receive 5xx on first request; deployment automation may mark service healthy prematurely.

### Desired State
- Optional fail-fast mode (default on for production) aborts startup when dependencies unavailable or misconfigured.  
- Readiness endpoint reflects dependency status when fail-fast disabled.

### Impact if Not Addressed
Leads to brown-out windows, failed ingestion, and confusing health signals during deploy/rollout.

### Proposed Solution
- Add setting `KM_STRICT_DEPENDENCY_STARTUP` (default true in secure mode) enforcing successful handshake.  
- Update readiness handler to surface degraded status when strict mode disabled.  
- Extend tests to cover fail-fast and tolerant modes.

### Affected Components
- `gateway/api/app.py`
- `gateway/api/routes/health.py`
- `tests/test_app_smoke.py`

### Dependencies
- None.

### Acceptance Criteria
- [ ] App exits with non-zero when strict mode enabled and dependencies unavailable.  
- [ ] `/readyz` reflects dependency degradation when strict mode disabled.  
- [ ] Tests simulate dependency outage.  
- [ ] Release notes mention behaviour change.

### Related Issues
- Risk register item R3.

---

## WP-004: Cap Maintainer Cypher Query Resource Usage
**Category**: Performance  
**Priority**: HIGH  
**Effort**: S  
**Risk Level**: Medium

### Description
Maintainer-only `/api/v1/graph/cypher` endpoint requires a `LIMIT` clause but does not bound the value; callers can request millions of rows, starving Neo4j.

### Current State
- `_validate_cypher` in `gateway/graph/service.py` only checks presence of `LIMIT`.  
- No server-side clamp or safety net beyond SlowAPI rate limits.

### Desired State
- Enforce maximum row count (configurable) and optionally enforce timeout.  
- Return 422 when LIMIT exceeds threshold.

### Impact if Not Addressed
Large queries can block graph workloads, cause ingestion slowdowns, and raise memory pressure.

### Proposed Solution
- Parse LIMIT value post-validation; reject values above e.g. 10k by default (configurable via settings).  
- Add metric for blocked queries.  
- Document safe Cypher usage for maintainers.

### Affected Components
- `gateway/graph/service.py`
- `gateway/config/settings.py`
- `gateway/api/routes/graph.py`
- `tests/test_graph_api.py`

### Dependencies
- None.

### Acceptance Criteria
- [ ] LIMIT above configured maximum returns 422 with helpful message.  
- [ ] Tests cover allowed vs blocked queries.  
- [ ] Metrics updated when requests denied.  
- [ ] Documentation warns about capped limits.

### Related Issues
- Risk register item R4.

---

## Medium Priority

## WP-005: Parallelise Graph Enrichment for Search Results
**Category**: Performance  
**Priority**: MEDIUM  
**Effort**: M  
**Risk Level**: Medium

### Description
`GraphEnricher.resolve` fetches graph context sequentially for each candidate hit; under high result counts, queries run serially and may exceed time budget.

### Current State
- Search pipeline iterates hits one-by-one (`gateway/search/service.py`).  
- Time budget partially mitigates but increases warning frequency and reduces enrichment quality.

### Desired State
- Batch or parallel graph lookups (async or threadpool) respecting same budget.  
- Metrics reflect enrichment latency distribution.

### Impact if Not Addressed
Search latency spikes for graph-heavy queries; warnings degrade user trust and reduce context coverage.

### Proposed Solution
- Implement async enrichment tasks or prefetch using `asyncio.gather`/`ThreadPoolExecutor`.  
- Preserve ordering and caching semantics.  
- Update metrics to capture enrichment concurrency success.

### Affected Components
- `gateway/search/graph_enricher.py`
- `gateway/search/service.py`
- `tests/test_search_service.py`

### Dependencies
- WP-004 (since both touch graph pipelines) optional but not blocker.

### Acceptance Criteria
- [ ] Median search latency reduced in performance tests vs baseline.  
- [ ] Graph warnings for timeouts decrease.  
- [ ] Tests updated to cover concurrent path.  
- [ ] Documentation mentions concurrency controls.

### Related Issues
- Risk register item R5.

---

## WP-006: Decompose `gateway/graph/service.py` for Maintainability
**Category**: Quality  
**Priority**: MEDIUM  
**Effort**: L  
**Risk Level**: Medium

### Description
Graph service spans ~1k lines covering caching, serialisation, query validation, Cypher execution, and helper utilities, making it difficult to test and evolve.

### Current State
- Monolithic module with mixed responsibilities and extensive helper functions.  
- Tests focus on high-level behaviours; refactors risky.

### Desired State
- Split into cohesive modules (e.g., cache, transformers, validators, Cypher guard).  
- Shared utilities exposed via internal package for MCP and API.

### Impact if Not Addressed
Increases risk of regression, slows onboarding, and discourages enhancements (e.g., future graph Analytics, batching).

### Proposed Solution
- Introduce subpackage `gateway/graph/core/` with focused modules.  
- Add targeted unit tests for utilities.  
- Update imports across API/MCP.

### Affected Components
- `gateway/graph/service.py`
- `gateway/mcp/server.py`
- `tests/test_graph_service_unit.py`

### Dependencies
- Coordinate with WP-004 (limit enforcement) to avoid merge conflicts.

### Acceptance Criteria
- [ ] Graph service split into logical modules with ≤300 lines each.  
- [ ] Existing tests pass; new unit tests cover validators/serialisers.  
- [ ] Developer documentation updated describing new structure.

### Related Issues
- Risk register item R6.

---

## WP-007: Validate Backup Script Availability at Startup
**Category**: Operational  
**Priority**: MEDIUM  
**Effort**: S  
**Risk Level**: Medium

### Description
Backup scheduler defers failures until first run; missing or non-executable `km-backup` script silently sets status to error later.

### Current State
- `IngestionScheduler` initialises `_backup_status` but does not verify script path.  
- Operators discover misconfiguration only after scheduled job fails.

### Desired State
- Startup diagnostics verify script presence/executable and destination directory writability.  
- Health check surfaces actionable error immediately.

### Impact if Not Addressed
Backups silently absent, increasing RPO in production.

### Proposed Solution
- Add validation in `IngestionScheduler.start` (and CLI) to check script path and destination.  
- Fail startup in strict mode or surface degraded health with reason.  
- Update docs to highlight requirement.

### Affected Components
- `gateway/scheduler.py`
- `gateway/config/settings.py`
- `tests/test_scheduler.py`

### Dependencies
- Complements WP-003 fail-fast work.

### Acceptance Criteria
- [ ] Misconfigured backup script surfaces before scheduler start.  
- [ ] Health endpoint reports degraded status with clear message.  
- [ ] Tests cover missing/invalid script.  
- [ ] Docs updated.

### Related Issues
- Risk register item R7.

---

## WP-008: Surface Search ML Mode Telemetry
**Category**: Enhancement  
**Priority**: MEDIUM  
**Effort**: S  
**Risk Level**: Medium

### Description
When `KM_SEARCH_SCORING_MODE=ml` but model missing or errors occur, service falls back silently except for logs.

### Current State
- `SearchService` logs warning; metadata warnings not surfaced in metrics or `/healthz`.

### Desired State
- Metrics and API metadata clearly indicate heuristic fallback and alert operators.

### Impact if Not Addressed
Operators assume ML ranking active while system reverts to heuristic, degrading relevance without visibility.

### Proposed Solution
- Add Prometheus gauge (e.g., `km_search_ml_enabled`) and warning counter.  
- Embed flag in search response metadata and `/healthz` coverage.  
- Extend unit tests to assert metadata flag.

### Affected Components
- `gateway/search/service.py`
- `gateway/observability/metrics.py`
- `tests/test_search_service.py`

### Dependencies
- None.

### Acceptance Criteria
- [ ] Metrics expose ML availability.  
- [ ] Search metadata contains boolean `ml_active`.  
- [ ] Tests verify fallback path updates metric.  
- [ ] Documentation updated.

### Related Issues
- Risk register item R8.

---

## Low Priority

## WP-009: Document Coverage & Lifecycle History Retention Controls
**Category**: BestPractice  
**Priority**: LOW  
**Effort**: XS  
**Risk Level**: Low

### Description
Retention knobs (`KM_COVERAGE_HISTORY_LIMIT`, `KM_LIFECYCLE_HISTORY_LIMIT`) exist but are undocumented; history directories can grow unexpectedly.

### Current State
- Code enforces limits, but README/docs omit guidance and operations procedures.

### Desired State
- Documentation and operational runbooks explain retention knobs and pruning commands.

### Impact if Not Addressed
Teams may leave defaults, leading to storage sprawl or confusion when history pruned automatically.

### Proposed Solution
- Update README / docs with retention explanation and recommended values.  
- Add note to CLI output when exports occur.

### Affected Components
- `docs/` (Quick Start, Operations)  
- `README.md`

### Dependencies
- None.

### Acceptance Criteria
- [ ] Docs mention both env vars with defaults and guidance.  
- [ ] Release notes summarise doc addition.

### Related Issues
- None.

---

## WP-010: Add Auth-Aware UI Integration Tests
**Category**: Quality  
**Priority**: LOW  
**Effort**: S  
**Risk Level**: Low

### Description
Test suite covers unauthenticated UI flows only; once WP-001 lands, regressions could slip in without coverage.

### Current State
- `tests/test_ui_routes.py` hardcodes `KM_AUTH_ENABLED=false`.

### Desired State
- Tests assert 401/403 when auth enabled and success when token supplied.

### Impact if Not Addressed
Future changes may break UI auth without detection.

### Proposed Solution
- Parameterize existing tests for auth/no-auth scenarios.  
- Reuse helper fixtures to set tokens.

### Affected Components
- `tests/test_ui_routes.py`

### Dependencies
- Requires WP-001 changes.

### Acceptance Criteria
- [ ] Tests fail if UI endpoints ignore auth when enabled.  
- [ ] CI reflects new coverage.

### Related Issues
- Supports WP-001.

