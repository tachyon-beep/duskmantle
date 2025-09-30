# Project Status Summary

## Overview

- **Container Runtime (WP1):** ✅ Completed (image build, supervisor orchestration, smoke harness).
- **Gateway Core (WP2):** ✅ Completed (health endpoints, auth/rate limiting, scheduler, logging).
- **Ingestion Pipeline (WP3):** ✅ Core ingestion/coverage complete; hybrid search tuning remains (see outstanding list).
- **Graph Integration (WP4):** ✅ Graph APIs, migrations runner, MCP coverage, and live `/graph/*` tests delivered.
- **Observability & Security (WP5):** ✅ Metrics/logging/auth/scheduler hardening done; keep monitoring doc polish.
- **Release Tooling (WP6):** ✅ Completed for 1.1.0 (pipeline, docs, acceptance playbook/snapshot). Continue maintaining support artefacts alongside future releases.
- **Autonomous Analysis Interface (WP7):** ⚙️ MCP server shipped; broader agent interface backlog remains.

## Work Package Breakdown

### WP1 — Container Runtime Foundation *(Completed)*

Nothing outstanding.

### WP2 — Gateway Core Skeleton *(Completed)*

Nothing outstanding.

### WP3 — Ingestion Pipeline MVP *(Complete with minor follow-up)*

- ✅ Discovery, chunking, embeddings, Qdrant/Neo4j integration, coverage report, metrics instrumentation.
- 🔸 Follow-up: provenance CLI polish/audit report formatting (optional) and ongoing evaluation of hybrid search defaults in production telemetry.

### WP4 — Graph Model Integration *(Complete)*

- ✅ Ingestion populates Neo4j with constraints/edges; `/graph/subsystems`, `/graph/nodes`, `/graph/search`, `/graph/cypher`, and `/search` graph-context enrichment are live with contract tests and live `pytest -m neo4j` coverage (container optional in CI via `RUN_NEO4J_SLICE`).
- 🔸 Follow-up: monitor auto-migration logs; schedule periodic live graph checks in CI when feasible.

### WP5 — Observability & Security Hardening *(Complete)*

- ✅ Metrics (`/metrics`), structured logging, rate limiting, bearer-token auth, audit history endpoint, coverage report, scheduler with repo-head gating/locking, OTel toggle, and observability runbooks.
- 🔸 Follow-up: continue documentation polish as new metrics are added.

### WP6 — Release Tooling & Documentation *(Completed)*

- ✅ Build/checksum scripts, release workflow (`release.yml`), Quick Start + troubleshooting updates, acceptance demo playbook/snapshot.
- ✅ Observability + release workflows now run Playwright UI suite and MCP smoke slice; docs refreshed for KM 1.1.0 release.
- 🔸 Ongoing: keep upgrade/rollback guidance and FAQ/support artefacts current as new releases ship.

### WP7 — Autonomous Analysis Interface *(Deferred to post-1.0)*

- ✅ MCP server/CLI/tests/telemetry/docs completed (ship-ready as tooling).
- 🔸 Deferred: full agent automation stack (prompt orchestration, OpenAI client flows, retrieval QA). Revisit after 1.0 release.

## Recent Highlights

- Added UUID-based Qdrant IDs, audit logging, coverage reports.
- Metrics, auth, rate limiting, scheduler guardrails, and OpenTelemetry tracing toggle implemented with tests.
- Published `docs/OBSERVABILITY_GUIDE.md` with metrics, tracing, and troubleshooting playbooks.
- `/coverage` endpoint now serves the persisted report with maintainer auth plus integration coverage tests.
- `/healthz` now reports coverage freshness, audit ledger accessibility, and scheduler status with supporting metrics gauges.
- Graph endpoints (`/graph/subsystems`, `/graph/nodes`, `/graph/search`, `/graph/cypher`) now available with read-only Cypher support.
- `/search` now returns enriched graph context per result, publishes the active weight profile + resolved weights, and supports preset bundles via `KM_SEARCH_WEIGHT_PROFILE` alongside existing overrides.
- Hybrid search combines dense embeddings with lexical overlap; tune via `KM_SEARCH_VECTOR_WEIGHT` / `KM_SEARCH_LEXICAL_WEIGHT` and `KM_SEARCH_HNSW_EF_SEARCH`.
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
- Final acceptance ingest (`c821eb34956345bc8ef7cb3765b4ab63`) refreshed Qdrant/Neo4j after archiving docs; `/search` now resolves to `docs/archive/*` paths and the 1.1.0 image will be validated via the updated acceptance playbook before release.
- Release tooling plan (archived) recorded in `docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md`; initial scripts (`scripts/build-wheel.sh`, `scripts/checksums.sh`) and `CHANGELOG.md`/`RELEASE.md` skeletons are in place with automated tests.
- Observability CI workflow (`.github/workflows/observability.yml`) runs nightly to assert `/readyz`, `/healthz`, `/metrics`, and `/coverage` remain healthy.
- Manual auth-enabled smoke test succeeded with password `tRusKAxG2fQKmP-ik3Y0`.

## Next Priorities

- Finalise WP6 deliverables: upgrade/rollback guide, support/FAQ artifacts, dry-run tagged release.
- Monitor hybrid search performance (baseline 2025-09-27 queries show vector/lexical mix 0.46 vs 0.24; continue gathering production telemetry before tuning) and continue provenance tooling polish.
- Plan WP7 agent enhancements (OpenAI/client orchestration) after release tooling closes.
