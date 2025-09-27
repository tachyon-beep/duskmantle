# Project Status Summary

## Overview
- **Container Runtime (WP1):** Completed. Docker image bundles Python 3.12 (bookworm), Qdrant 1.15.4, Neo4j 5.26.0, supervisord orchestration, volume guards, and smoke-test harness.
- **Gateway Core (WP2):** Completed. FastAPI app exposes `/healthz`, `/readyz`, `/metrics`, `/audit/history`; structured JSON logging; rate limiting; bearer-token auth; scheduler hooks.
- **Ingestion Pipeline (WP3):** Functional but pending provenance/coverage polish. Discovery, chunking, embedding, Qdrant/Neo4j sync and coverage report implemented; ingestion returns rich metadata.
- **Graph Integration (WP4):** Partial. Neo4j writer adds nodes/edges/constraints; ingestion populates graph. Missing Graph API endpoints, migration tooling, and validation tests.
- **Observability & Security (WP5):** Partially complete. Metrics/logging/auth/coverage/scheduler guardrails delivered; remaining tasks documented below.
- **Release Tooling (WP6):** Not started.
- **Autonomous Analysis Interface (WP7):** Not started.

## Work Package Breakdown

### WP1 — Container Runtime Foundation *(Completed)*
Nothing outstanding.

### WP2 — Gateway Core Skeleton *(Completed)*
Nothing outstanding.

### WP3 — Ingestion Pipeline MVP *(In Progress)*
- ✅ Discovery, chunking, embeddings, Qdrant/Neo4j integration, coverage report, metrics instrumentation.
- 🔸 Outstanding: Persist provenance/audit ledger exposure (API/CLI readout) and finalize coverage reporting for non-dummy embeddings when model bundled. Ensure design spec’s audit logger expectations are fully met.

### WP4 — Graph Model Integration *(In Progress)*
- ✅ Neo4j writer ensures constraints, BELONGS_TO/DESCRIBES/VALIDATES/HAS_CHUNK edges populated during ingestion; `/graph/subsystems`, `/graph/nodes`, `/graph/search`, maintainer-only `/graph/cypher`, schema migration runner/CLI, and `/search` graph-context enrichment are live with tests and dependency overrides.
- 🔸 Outstanding: Add optional auto-migration hooks and expand validation against live Neo4j instances.

### WP5 — Observability & Security Hardening *(In Progress)*
- ✅ Metrics (`/metrics`), structured logging, rate limiting, bearer-token auth, audit history endpoint, coverage report, scheduler with repo-head gating & locking, documentation updates, OpenTelemetry tracing toggle (`KM_TRACING_ENABLED`), and operator runbook (`docs/OBSERVABILITY_GUIDE.md`).
- 🔸 Outstanding:
  - Monitor metric names/log format in docs and consider additional ingestion health checks.

### WP6 — Release Tooling & Documentation *(Not Started)*
- Docker CI pipeline, backup/restore helpers, checksum generation, troubleshooting guide, release notes.

### WP7 — Autonomous Analysis Interface *(Not Started)*
- OpenAI client integration, MCP command, prompt orchestration, retrieval quality/groundedness reporting.

## Recent Highlights
- Added UUID-based Qdrant IDs, audit logging, coverage reports.
- Metrics, auth, rate limiting, scheduler guardrails, and OpenTelemetry tracing toggle implemented with tests.
- Published `docs/OBSERVABILITY_GUIDE.md` with metrics, tracing, and troubleshooting playbooks.
- `/coverage` endpoint now serves the persisted report with maintainer auth plus integration coverage tests.
- `/healthz` now reports coverage freshness, audit ledger accessibility, and scheduler status with supporting metrics gauges.
- Graph endpoints (`/graph/subsystems`, `/graph/nodes`, `/graph/search`, `/graph/cypher`) now available with read-only Cypher support.
- `/search` now returns enriched graph context per result, publishes the active weight profile + resolved weights, and supports preset bundles via `KM_SEARCH_WEIGHT_PROFILE` alongside existing overrides.
- Graph-derived signals now include shortest-path depth (computed via Neo4j and cached per request) and improved freshness fallbacks, reducing duplicate graph queries during high-volume searches.
- Graph auto-migration instrumentation exposes `km_graph_migration_last_status` and `km_graph_migration_last_timestamp` to catch failed or stale migrations instantly.
- Neo4j validation harness grew assertions for constraints/relationships and now runs nightly via CI (`Neo4j Integration Tests`) to exercise end-to-end ingest + search replay against a live database.
- Search scoring now incorporates coverage ratio and subsystem criticality weights (configurable via `KM_SEARCH_W_*`), with refreshed defaults, a `/search/weights` endpoint, and `gateway-search show-weights` CLI for quick introspection.
- `/search` supports optional filters (`subsystems`, `artifact_types`, `namespaces`, `tags`, `updated_after`, `max_age_days`) with graph-aware fallback, recency-aware pruning, new logs for slow graph lookups, and metadata (`filters_applied`) so agents and dashboards can reason about constrained result sets.
- Prometheus now exposes search-specific observability: cache hit/miss/error counts (`km_search_graph_cache_events_total`), lookup latency histograms (`km_search_graph_lookup_seconds`), and ranking delta distribution (`km_search_adjusted_minus_vector`) to monitor Neo4j health and scoring drift.
- Packaged runtimes now default `KM_GRAPH_AUTO_MIGRATE` to true (with detailed startup logging), while `gateway-graph migrate` remains for manual runs and dry-run previews.
- `/search` requests emit JSONL telemetry (`/opt/knowledge/var/feedback/events.log`) capturing per-result scoring breakdown and agent feedback votes for future ranking models.
- Phase 2 tooling `gateway-search export-training-data` converts accumulated telemetry into CSV/JSONL datasets ready for modelling.
- Phase 3 trainer `gateway-search train-model` fits a linear regression over exported features and outputs versionable JSON artifacts with basic metrics.
- Retention utilities (`gateway-search prune-feedback` and `gateway-search redact-dataset`) keep telemetry lean and allow sensitive fields to be scrubbed before sharing datasets.
- Evaluation harness (`gateway-search evaluate-model`) benchmarks trained ranking models (MSE/R²/NDCG/Spearman) prior to inference rollout.
- Release tooling plan published at `docs/WP6_RELEASE_TOOLING_PLAN.md`; initial scripts (`scripts/build-wheel.sh`, `scripts/checksums.sh`) and `CHANGELOG.md`/`RELEASE.md` skeletons are in place with automated tests.
- Observability CI workflow (`.github/workflows/observability.yml`) runs nightly to assert `/readyz`, `/healthz`, `/metrics`, and `/coverage` remain healthy.
- Manual auth-enabled smoke test succeeded with password `tRusKAxG2fQKmP-ik3Y0`.

## Next Priorities
- WP5: finalize documentation/tracing decisions, optional CLI exposure, ensure metrics/logging guidance complete.
- WP4: deliver schema migrations and search enrichment leveraging the new graph service.
- WP6: begin release tooling once WP5 wraps.
- WP7: plan OpenAI integration after core hardening.
