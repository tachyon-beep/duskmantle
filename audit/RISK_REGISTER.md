
# Risk Register

## RISK-001: Insecure Gateway Boots When Launched Manually
- **Category**: Security
- **Likelihood**: Medium
- **Impact**: High
- **Description**: Launching the API without the container entrypoint leaves `KM_AUTH_ENABLED` disabled by default (`gateway/config/settings.py:50`), exposing every route to unauthenticated callers.
- **Mitigation Strategy**: Implement WP-201 to default to secure boots, warn loudly when auth is disabled, and extend security tests.
- **Risk Owner**: Gateway maintainers
- **Monitoring & Review**: Add CI coverage in `tests/test_api_security.py`, include a release checklist item verifying auth defaults, and review at every minor release.

## RISK-002: Backup Retention Deletes Unrelated Files
- **Category**: Operational
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: Retention now targets `km-backup-*.tgz` archives inside `${KM_STATE_PATH}/backups/archives`, leaving foreign files untouched. Residual risk comes from operators manually placing sensitive data in the managed archive directory or renaming files to match the pattern.
- **Mitigation Strategy**: Completed via WP-202 — scheduler pruning is pattern scoped, `bin/km-backup` writes to the archival subdirectory by default, documentation highlights the layout, and `km_backup_retention_deletes_total` surfaces deletions.
- **Risk Owner**: Operations / SRE
- **Monitoring & Review**: Track `km_backup_retention_deletes_total` and `km_backup_runs_total`, audit the archive directory monthly, and keep backup destinations dedicated to gateway artifacts.

## RISK-003: Search Feedback Log Grows Without Bound
- **Category**: Operational
- **Likelihood**: High
- **Impact**: Medium
- **Description**: `SearchFeedbackStore` appends to `events.log` indefinitely (`gateway/search/feedback.py:29-66`) with no rotation or size monitoring.
- **Mitigation Strategy**: Execute WP-203 to add rotation, metrics, and health checks; consider archiving old logs.
- **Risk Owner**: Gateway maintainers
- **Monitoring & Review**: Track new metrics (`km_feedback_events_bytes_total`) once implemented; until then, include file size checks in weekly ops runbooks.

## RISK-004: Neo4j Tail Latency Stalls Search Responses
- **Category**: Performance
- **Likelihood**: Medium
- **Impact**: Medium-High
- **Description**: Search enrichment performs two sequential Cypher queries per hit (`gateway/search/service.py:150-430`), so a slow node degrades the entire response.
- **Mitigation Strategy**: Complete WP-204 (bounded graph budget) and WP-206 (refactor) to parallelise lookups, enforce timeouts, and improve observability.
- **Risk Owner**: Gateway maintainers / Performance engineer
- **Monitoring & Review**: Watch `SEARCH_GRAPH_LOOKUP_SECONDS` for P95 spikes; if over 500ms for two consecutive days, prioritise mitigation work.

## RISK-005: Artifact Ledger Corruption Breaks Incremental Ingest
- **Category**: Technical Debt
- **Likelihood**: Low-Medium
- **Impact**: Medium
- **Description**: Ledger writes are non-atomic (`gateway/ingest/pipeline.py:432-444`), so concurrent runs or crashes can corrupt incremental state.
- **Mitigation Strategy**: Implement WP-205 for atomic writes, locking, and validation; add recovery tooling.
- **Risk Owner**: Gateway maintainers
- **Monitoring & Review**: Run ingestion smoke tests after each release and check for ledger read warnings in logs.

## RISK-006: Lack Of API Versioning Breaks External Clients
- **Category**: Best Practice
- **Likelihood**: Medium
- **Impact**: Medium
- **Description**: REST routes live at the root (`gateway/api/routes/*.py`), so schema changes can break MCP clients and automation with no migration path.
- **Mitigation Strategy**: Deliver WP-207 to introduce `/api/v1` and document deprecation timelines.
- **Risk Owner**: Gateway maintainers / Developer relations
- **Monitoring & Review**: Track MCP smoke tests (`pytest -m mcp_smoke`) in CI; review compatibility before each minor release.

## RISK-007: Audit History Endpoint Can Exhaust Memory
- **Category**: Operational
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: `/audit/history` accepts arbitrary `limit` values (`gateway/api/routes/reporting.py:25-38`), allowing a single request to dump the full SQLite table.
- **Mitigation Strategy**: Apply WP-208 to clamp limits, validate inputs, and document ceilings.
- **Risk Owner**: Operations / API owners
- **Monitoring & Review**: Once limit clamping is in place, log when requests hit the ceiling; review monthly.

## RISK-008: Feedback Insights Never Reach ML Scoring
- **Category**: Enhancement Opportunity
- **Likelihood**: High
- **Impact**: Low
- **Description**: Feedback logs are not transformed into training datasets (`gateway/search/trainer.py`), so ML scoring mode stagnates.
- **Mitigation Strategy**: Implement WP-209 to export feedback, retrain models, and document the loop.
- **Risk Owner**: Search relevance team
- **Monitoring & Review**: Track model artifact freshness (timestamp in state directory) and schedule quarterly retraining reviews.
