# WP4 Working Notes — Graph Model Integration

## Current State
- Schema migrations implemented via `gateway/graph/migrations/runner.py`; manual CLI (`gateway-graph migrate`) remains available, and packaged runtimes now default to auto-migration (`KM_GRAPH_AUTO_MIGRATE=true`) with startup logs summarizing pending/applied IDs.
- Startup instrumentation now publishes `km_graph_migration_last_status` / `_timestamp` so failed or skipped auto-migrations are visible in dashboards and can trigger alerts.
- Graph API endpoints live: `/graph/subsystems/{name}`, `/graph/nodes/{id}`, `/graph/search`, `/graph/cypher` with maintainer gating for Cypher. Dependency overrides stored on `app.state` for testing.
- Search enrichment: `/search` now returns `graph_context` and `scoring` metadata. Scoring includes vector score, adjusted score, and per-signal contributions (subsystem affinity, relationship count, supporting artifacts, coverage penalty). We added weights (`KM_SEARCH_W_*`) and optional pure-vector sorting (`KM_SEARCH_SORT_BY_VECTOR=true`).
- Search weighting now supports curated profiles (`KM_SEARCH_WEIGHT_PROFILE` with `default`, `analysis`, `operations`, `docs-heavy`) while preserving granular overrides via `KM_SEARCH_W_*`; responses include the active profile and resolved weights for transparency.
- Advanced signals enriched: path depth now leverages a Neo4j shortest-path query (cached per request) instead of heuristics, freshness falls back to graph timestamps when chunk metadata is missing, and repeated hits reuse memoised graph context to cut duplicate Cypher calls.
- Search telemetry phase 1 delivered: each `/search` call appends JSONL feedback under `/opt/knowledge/var/feedback/events.log` (with `metadata.request_id` for correlation) capturing per-result scoring and optional MCP votes. Phase 2 exporter (`gateway-search export-training-data`) converts the log into CSV/JSONL datasets for modelling. Phase 3 trainer (`gateway-search train-model`) now fits linear regression coefficients and writes JSON artifacts for later inference integration. Retention/redaction utilities (`gateway-search prune-feedback`, `gateway-search redact-dataset`) manage log growth and scrub sensitive fields before sharing datasets. Evaluation CLI (`gateway-search evaluate-model`) reports MSE/R²/NDCG/Spearman using holdout datasets before rollout.
- `/search` filters now accept namespaces, normalised tags, and recency guards (`updated_after`, `max_age_days`); ingestion derives namespaces from artifact paths and normalises tags across Leyline/Telemetry metadata so agents can combine structural and temporal slices without ad-hoc post-processing. Response metadata echoes the applied filters and warns when recency filters drop chunks that lack timestamps.
- Search inference: `SearchService` respects `KM_SEARCH_SCORING_MODE` (`heuristic` vs `ml`) and loads model artifacts automatically, exposing `scoring.model` contributions and surfacing the active mode in response metadata.
- Neo4j validation harness (`tests/test_graph_validation.py`) behind `pytest -m neo4j`; GitHub workflow `.github/workflows/neo4j-integration.yml` spins up Neo4j and runs the marker on demand.
- Validation harness now asserts constraint coverage, relationship counts, and replayed search scoring against a live Neo4j instance. The GitHub workflow runs nightly (03:30 UTC) to catch regressions early while retaining manual dispatch for ad-hoc checks.
- Runbooks updated with a dedicated graph-health checklist and documented rollback procedure for failed migrations (see `docs/OBSERVABILITY_GUIDE.md` §9 and `docs/GRAPH_API_DESIGN.md` §9).
- Documentation updates: `docs/GRAPH_API_DESIGN.md` details API, scoring signals, migration tooling, validation harness. README/AGENTS include new env vars and workflows. STATUS/WORK_PACKAGES adjusted.

## Open Work (WP4)
1. **Schema/Migration Ops**
   - Hybrid default chosen: packaged runtime keeps auto-migrate enabled, production templates disable it and rely on explicit `gateway-graph migrate` runs. Continue to ensure deployment docs/helpers mirror that split.
   - Monitor migration history growth; consider TTL/cleanup approach later.

2. **Search Scoring Enhancements**
   - **2.1 Advanced Signals**
     - ✅ Coverage ratio and freshness now flow from ingestion to scoring to API responses; subsystem criticality weighting added with graph fallback and tunable `KM_SEARCH_W_CRITICALITY`.
   - **2.2 Weight Profiles**
     - ✅ Bundles (`default`, `analysis`, `operations`, `docs-heavy`) documented with use cases; defaults recalibrated after synthetic benchmarks.
     - ✅ CLI (`gateway-search show-weights`) and `/search/weights` endpoint expose active profile + resolved weights.
   - **2.3 Performance & Observability**
     - ✅ Instrument cache hit-rate/latency metrics (`km_search_graph_cache_events_total`, `km_search_graph_lookup_seconds`) and expose ranking deltas via `km_search_adjusted_minus_vector`.
     - ✅ Slow graph lookups emit structured warnings with `request_id` for correlation; dashboards/alerts implemented per `docs/DASHBOARD_SEARCH_HEALTH.md`.
   - Retention/redaction utilities reduce operational risk; next steps hinge on evaluation harness and inference integration defined in `docs/SEARCH_SCORING_PLAN.md`.

3. **Validation Harness Expansion**
   - **3.1 Graph Assertions** — extend `tests/test_graph_validation.py` to verify relationship counts, edge types, and constraint presence.
   - **3.2 Search Replay** — add a `pytest.mark.neo4j` scenario that runs sample queries and checks ranked outputs (heuristic & ML modes).
   - **3.3 CI Enablement** — revisit `.github/workflows/neo4j-integration.yml` to run on a schedule or as part of release candidates.

4. **Integration with `/search` filters**
   - **4.1 API Contract** — design payload support for subsystem/type filters plus documentation.
   - **4.2 Test Coverage** — tighten unit/API tests ensuring filters interact correctly with graph scoring and ML ranking.

5. **Documentation/Operational Guides**
   - **5.1 Operator Guide** — expand `docs/SEARCH_SCORING_PLAN.md` / README with tuning & troubleshooting steps for both heuristic and ML modes.
   - **5.2 Runbooks** — add graph-health checklist (migrations CLI, validation harness execution) to `docs/OBSERVABILITY_GUIDE.md`.

## Quick Reference
- **Key Flags**
  - `KM_GRAPH_AUTO_MIGRATE` — auto-run migrations at API startup.
  - `KM_SEARCH_W_SUBSYSTEM`, `KM_SEARCH_W_RELATIONSHIP`, `KM_SEARCH_W_SUPPORT`, `KM_SEARCH_W_COVERAGE_PENALTY` — scoring weights.
  - `KM_SEARCH_SORT_BY_VECTOR` — bypass graph scoring for pure vector order.
- **Manual Workflows**
  ```bash
  # Manual Neo4j migration
  gateway-graph migrate --dry-run
  gateway-graph migrate

  # Run integration harness (Neo4j required)
  docker run -d --rm --name neo4j-test -p 7687:7687 -e NEO4J_AUTH=neo4j/secret neo4j:5
  NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=secret pytest -m neo4j
  ```
- **Key Tests**
  - `tests/test_graph_api.py` — API contract.
  - `tests/test_graph_migrations.py`, `tests/test_graph_auto_migrate.py`, `tests/test_graph_cli.py` — migrations tooling.
  - `tests/test_search_service.py`, `tests/test_search_api.py` — scoring/endpoint behavior.
  - `tests/test_graph_validation.py` (`-m neo4j`) — end-to-end ingestion validation.

## Next Steps Queue
- Evaluate adding graph-scoring metrics or logs (e.g., histogram of adjusted minus vector score) for observability.
- Consider caching strategy for graph context (avoid redundant driver calls under heavy load).
- Investigate advanced ranking (learning-to-rank or dynamic weighting) once baseline heuristics are validated.
