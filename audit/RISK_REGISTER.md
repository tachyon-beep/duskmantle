
# Risk Register

## RISK-001: Credential Hygiene After Secure Defaults
- **Category**: Security
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: Authentication now defaults to enabled, but operators can still disable it intentionally or reuse weak maintainer tokens/Neo4j passwords. Manual launches that unset tokens will fail, yet poor credential rotation remains a concern.
- **Mitigation Strategy**: Maintain WP-201 changes (secure default, disable warning) and enforce strong credential guidance in docs; consider telemetry on repeated `auth_disabled` warnings.
- **Risk Owner**: Gateway maintainers
- **Monitoring & Review**: Keep `tests/test_api_security.py` coverage, monitor logs for the `auth_disabled` warning, and review credential rotation guidance each release.

## RISK-002: Backup Retention Deletes Unrelated Files
- **Category**: Operational
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: Retention now targets `km-backup-*.tgz` archives inside `${KM_STATE_PATH}/backups/archives`, leaving foreign files untouched. Residual risk comes from operators manually placing sensitive data in the managed archive directory or renaming files to match the pattern.
- **Mitigation Strategy**: Completed via WP-202 — scheduler pruning is pattern scoped, `bin/km-backup` writes to the archival subdirectory by default, documentation highlights the layout, and `km_backup_retention_deletes_total` surfaces deletions.
- **Risk Owner**: Operations / SRE
- **Monitoring & Review**: Track `km_backup_retention_deletes_total` and `km_backup_runs_total`, audit the archive directory monthly, and keep backup destinations dedicated to gateway artifacts.

## RISK-003: Feedback Log Retention Tuning
- **Category**: Operational
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: Search feedback logs now rotate automatically, but misconfigured limits (large `KM_FEEDBACK_LOG_MAX_BYTES` / `KM_FEEDBACK_LOG_MAX_FILES`) can still grow disk usage over time.
- **Mitigation Strategy**: Keep default rotations from WP-203, monitor `km_feedback_log_bytes` / `km_feedback_rotations_total`, and document recommended settings for large deployments.
- **Risk Owner**: Gateway maintainers
- **Monitoring & Review**: Dashboard the new metrics, review retention settings quarterly, and archive rotated logs as part of backup routines.

## RISK-004: Neo4j Tail Latency Stalls Search Responses
- **Category**: Performance
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: Graph enrichment now enforces result/time budgets, but mis-tuned limits or persistent Neo4j slowness can still degrade relevance when many results skip graph context.
- **Mitigation Strategy**: Maintain WP-204 budgets and continue the planned WP-206 refactor to isolate enrichment. Tune `KM_SEARCH_GRAPH_MAX_RESULTS` / `KM_SEARCH_GRAPH_TIME_BUDGET_MS` based on telemetry and add dashboards for skip counters.
- **Risk Owner**: Gateway maintainers / Performance engineer
- **Monitoring & Review**: Track `km_search_graph_skipped_total` and `SEARCH_GRAPH_LOOKUP_SECONDS` for sustained increases; revisit settings quarterly or whenever Neo4j topology changes.

## RISK-005: Artifact Ledger Corruption Breaks Incremental Ingest
- **Category**: Technical Debt
- **Likelihood**: Low
- **Impact**: Medium
- **Description**: Ledger writes now use file locks and atomic rename; residual risk stems from operators overriding ledger paths or persistent lock contention.
- **Mitigation Strategy**: Maintain WP-205 changes, monitor ingest logs for lock timeout warnings, and include ledger validation in smoke tests.
- **Risk Owner**: Gateway maintainers
- **Monitoring & Review**: Run ingestion smoke tests after each release, audit logs for `Timed out waiting for ledger lock`, and review retention policies quarterly.

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
- **Likelihood**: Very Low
- **Impact**: Low
- **Description**: `/api/v1/audit/history` now clamps requests to `KM_AUDIT_HISTORY_MAX_LIMIT` (default 100) and emits warning headers when the cap is exceeded, significantly reducing the chance of accidental large dumps.
- **Mitigation Strategy**: WP-208 completed — maintain sensible defaults, expose the limit in docs, and keep warning headers so operators can tune the cap consciously.
- **Risk Owner**: Operations / API owners
- **Monitoring & Review**: Track occurrences of the warning header in access logs and revisit the configured limit quarterly or when workloads change.

## RISK-008: Feedback Insights Never Reach ML Scoring
- **Category**: Enhancement Opportunity
- **Likelihood**: High
- **Impact**: Low
- **Description**: Feedback logs are not transformed into training datasets (`gateway/search/trainer.py`), so ML scoring mode stagnates.
- **Mitigation Strategy**: Implement WP-209 to export feedback, retrain models, and document the loop.
- **Risk Owner**: Search relevance team
- **Monitoring & Review**: Track model artifact freshness (timestamp in state directory) and schedule quarterly retraining reviews.
