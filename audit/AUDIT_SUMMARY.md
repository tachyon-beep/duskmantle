
# Audit Summary

## Executive Summary
The Duskmantle gateway remains a well-structured platform with clear service boundaries, strong test coverage, and solid observability hooks. Search, graph, and ingest workflows share a consistent dependency layer, and every FastAPI route is guarded by rate limiting and scope checks. Recent hardening of backup retention removes the highest operational risk; remaining gaps focus on configuration defaults, long-running telemetry storage, and the monolithic search service. Addressing the highlighted work packages will harden day-to-day operations without disrupting the existing architecture, while a modest refactor of the monolithic search service will unlock faster iteration on relevance improvements.

## Key Metrics
- Python modules analysed: 111 (production 71, tests 39, scripts 1)
- Total Python LOC: 18,720 (production 11,623; tests 7,014)
- Test focus: extensive pytest suite covering API, ingest, graph, MCP, and scheduler paths (`pytest.ini`)
- Observability: Prometheus metrics, structured logging, SlowAPI limits, optional OTLP tracing
- Deployment: Docker Compose with `gateway`, `neo4j:5.26.0`, and `qdrant/qdrant:1.15.4`; backups managed via `bin/km-backup`

## Findings By Category
- **Security** – Auth defaults rely on the container entrypoint; running `uvicorn` directly leaves the API wide open (`gateway/config/settings.py:50`). (WP-201)
- **Operational** – Feedback logs never rotate (`gateway/search/feedback.py:29-66`) and `/audit/history` accepts unbounded limits. (WP-203, WP-208)
- **Performance** – Search graph enrichment executes two serial Cypher calls per result with no timeout budget, creating tail-latency spikes under Neo4j load (`gateway/search/service.py:150-430`). (WP-204)
- **Code Quality** – `SearchService` has grown past 1k LOC combining vector search, graph enrichment, and ML ranking, complicating reviews and targeted testing. (WP-206)
- **Best Practice** – REST routes lack versioning, so protocol changes break MCP clients with no migration path (`gateway/api/routes/*.py`). (WP-207)
- **Enhancement** – Collected feedback never feeds the ML scoring pipeline; no tooling exports datasets for `gateway/search/trainer.py`. (WP-209)
- **Technical Debt** – Artifact ledger writes are non-atomic and risk corruption on crashes or concurrent ingest runs (`gateway/ingest/pipeline.py:432-444`). (WP-205)

## Top Priority Actions
1. **WP-201** – Flip auth defaults to secure mode and warn loudly when exposed.
2. **WP-204** – Bound graph enrichment latency with concurrency limits and timeouts.
3. **WP-203** – Rotate and monitor search feedback logs before disks fill.
4. **WP-205** – Make artifact ledger updates atomic with locking and temp files.
5. **WP-207** – Introduce a versioned REST prefix to stabilise external integrations.
6. **WP-206** – Decompose `SearchService` for maintainability and clearer extensibility.
7. **WP-208** – Clamp `/audit/history` limits to prevent accidental DoS.
8. **WP-209** – Export feedback logs into the training pipeline to revive ML scoring.

## Overall System Health
- **Score**: 7/10 (Amber) – Core functionality is dependable and well tested, but tightening auth defaults, backup safety, and graph/search performance is necessary before scaling to less supervised environments.

## Recommended Immediate Actions
- Prioritise WP-201 in the next sprint to eliminate the top security gap; ensure unit coverage for secure/insecure boots.
- Schedule WP-204 alongside telemetry review to stabilise search latency under Neo4j drift; run `pytest tests/test_search_service.py` after changes.
