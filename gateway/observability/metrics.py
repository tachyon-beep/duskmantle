"""Prometheus metric definitions for the knowledge gateway."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

BACKUP_RUNS_TOTAL = Counter(
    "km_backup_runs_total",
    "Backup job outcomes partitioned by result",
    labelnames=["result"],
)

BACKUP_LAST_STATUS = Gauge(
    "km_backup_last_status",
    "Last backup status (1=success,0=failure)",
)

BACKUP_LAST_SUCCESS_TIMESTAMP = Gauge(
    "km_backup_last_success_timestamp",
    "Unix timestamp of the last successful backup run",
)

BACKUP_RETENTION_DELETES_TOTAL = Counter(
    "km_backup_retention_deletes_total",
    "Number of backup archives removed by retention pruning",
)

GRAPH_DEPENDENCY_STATUS = Gauge(
    "km_graph_dependency_status",
    "Neo4j connectivity status (1=healthy,0=unavailable)",
)

GRAPH_DEPENDENCY_LAST_SUCCESS = Gauge(
    "km_graph_dependency_last_success_timestamp",
    "Unix timestamp of the last successful Neo4j heartbeat",
)

QDRANT_DEPENDENCY_STATUS = Gauge(
    "km_qdrant_dependency_status",
    "Qdrant connectivity status (1=healthy,0=unavailable)",
)

QDRANT_DEPENDENCY_LAST_SUCCESS = Gauge(
    "km_qdrant_dependency_last_success_timestamp",
    "Unix timestamp of the last successful Qdrant heartbeat",
)

INGEST_DURATION_SECONDS = Histogram(
    "km_ingest_duration_seconds",
    "Duration of ingestion runs",
    labelnames=["profile", "status"],
)

INGEST_ARTIFACTS_TOTAL = Counter(
    "km_ingest_artifacts_total",
    "Number of artifacts processed",
    labelnames=["profile", "artifact_type"],
)

INGEST_CHUNKS_TOTAL = Counter(
    "km_ingest_chunks_total",
    "Number of chunks generated",
    labelnames=["profile"],
)

INGEST_LAST_RUN_STATUS = Gauge(
    "km_ingest_last_run_status",
    "Last ingestion status (1=success,0=failure)",
    labelnames=["profile"],
)

INGEST_LAST_RUN_TIMESTAMP = Gauge(
    "km_ingest_last_run_timestamp",
    "Unix timestamp of last ingestion run",
    labelnames=["profile"],
)

COVERAGE_LAST_RUN_STATUS = Gauge(
    "km_coverage_last_run_status",
    "Last coverage report generation status (1=success,0=failure)",
    labelnames=["profile"],
)

COVERAGE_LAST_RUN_TIMESTAMP = Gauge(
    "km_coverage_last_run_timestamp",
    "Unix timestamp of last coverage report",
    labelnames=["profile"],
)

COVERAGE_MISSING_ARTIFACTS = Gauge(
    "km_coverage_missing_artifacts_total",
    "Number of artifacts without chunks discovered in last coverage report",
    labelnames=["profile"],
)

COVERAGE_STALE_ARTIFACTS = Gauge(
    "km_coverage_stale_artifacts_total",
    "Number of stale or removed artifacts recorded in last coverage report",
    labelnames=["profile"],
)


INGEST_STALE_RESOLVED_TOTAL = Counter(
    "km_ingest_stale_resolved_total",
    "Count of stale artifacts removed from backends during ingestion",
    labelnames=["profile"],
)

INGEST_SKIPS_TOTAL = Counter(
    "km_ingest_skips_total",
    "Ingestion runs skipped partitioned by reason",
    labelnames=["reason"],
)

SEARCH_REQUESTS_TOTAL = Counter(
    "km_search_requests_total",
    "Search API requests partitioned by outcome",
    labelnames=["status"],
)

SEARCH_GRAPH_CACHE_EVENTS = Counter(
    "km_search_graph_cache_events_total",
    "Graph context cache events during search",
    labelnames=["status"],
)

SEARCH_GRAPH_SKIPPED_TOTAL = Counter(
    "km_search_graph_skipped_total",
    "Number of search results where graph enrichment was skipped",
    labelnames=["reason"],
)

SEARCH_FEEDBACK_ROTATIONS_TOTAL = Counter(
    "km_feedback_rotations_total",
    "Number of times the search feedback log rotated due to size limits",
)

SEARCH_FEEDBACK_LOG_BYTES = Gauge(
    "km_feedback_log_bytes",
    "Current size of the primary search feedback log in bytes",
)

SEARCH_GRAPH_LOOKUP_SECONDS = Histogram(
    "km_search_graph_lookup_seconds",
    "Latency of graph lookups for search enrichment",
)

SEARCH_SCORE_DELTA = Histogram(
    "km_search_adjusted_minus_vector",
    "Distribution of adjusted minus vector scores",
)

SEARCH_SYMBOL_FILTERS_TOTAL = Counter(
    "km_search_symbol_filters_total",
    "Search requests with symbol filters, partitioned by filter type",
    labelnames=["filter_type"],
)

GRAPH_CYPHER_DENIED_TOTAL = Counter(
    "km_graph_cypher_denied_total",
    "Maintainer Cypher requests blocked by read-only safeguards",
    labelnames=["reason"],
)

GRAPH_MIGRATION_LAST_STATUS = Gauge(
    "km_graph_migration_last_status",
    "Graph migration result (1=success, 0=failure, -1=skipped)",
)

GRAPH_MIGRATION_LAST_TIMESTAMP = Gauge(
    "km_graph_migration_last_timestamp",
    "Unix timestamp of the last graph migration attempt",
)

SCHEDULER_RUNS_TOTAL = Counter(
    "km_scheduler_runs_total",
    "Scheduled ingestion job outcomes partitioned by result",
    labelnames=["result"],
)

SCHEDULER_LAST_SUCCESS_TIMESTAMP = Gauge(
    "km_scheduler_last_success_timestamp",
    "Unix timestamp of the last successful scheduled ingestion run",
)

COVERAGE_HISTORY_SNAPSHOTS = Gauge(
    "km_coverage_history_snapshots",
    "Number of retained coverage history snapshots",
    labelnames=["profile"],
)

WATCH_RUNS_TOTAL = Counter(
    "km_watch_runs_total",
    "Watcher outcomes partitioned by result",
    labelnames=["result"],
)


LIFECYCLE_LAST_RUN_STATUS = Gauge(
    "km_lifecycle_last_run_status",
    "Lifecycle report generation status (1=success,0=failure)",
    labelnames=["profile"],
)

LIFECYCLE_LAST_RUN_TIMESTAMP = Gauge(
    "km_lifecycle_last_run_timestamp",
    "Unix timestamp of the last lifecycle report",
    labelnames=["profile"],
)

LIFECYCLE_STALE_DOCS_TOTAL = Gauge(
    "km_lifecycle_stale_docs_total",
    "Number of stale design docs in the latest lifecycle report",
    labelnames=["profile"],
)

LIFECYCLE_ISOLATED_NODES_TOTAL = Gauge(
    "km_lifecycle_isolated_nodes_total",
    "Number of isolated graph nodes recorded in the latest lifecycle report",
    labelnames=["profile"],
)

LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL = Gauge(
    "km_lifecycle_missing_test_subsystems_total",
    "Number of subsystems missing tests in the latest lifecycle report",
    labelnames=["profile"],
)

LIFECYCLE_REMOVED_ARTIFACTS_TOTAL = Gauge(
    "km_lifecycle_removed_artifacts_total",
    "Number of recently removed artifacts recorded in the latest lifecycle report",
    labelnames=["profile"],
)

LIFECYCLE_HISTORY_SNAPSHOTS = Gauge(
    "km_lifecycle_history_snapshots",
    "Number of retained lifecycle history snapshots",
    labelnames=["profile"],
)

MCP_REQUESTS_TOTAL = Counter(
    "km_mcp_requests_total",
    "MCP tool invocations partitioned by result",
    labelnames=["tool", "result"],
)

MCP_REQUEST_SECONDS = Histogram(
    "km_mcp_request_seconds",
    "Latency of MCP tool handlers",
    labelnames=["tool"],
)

MCP_FAILURES_TOTAL = Counter(
    "km_mcp_failures_total",
    "MCP tool failures partitioned by error type",
    labelnames=["tool", "error"],
)

MCP_UPLOAD_TOTAL = Counter(
    "km_mcp_upload_total",
    "MCP upload tool invocations partitioned by result",
    labelnames=["result"],
)

MCP_STORETEXT_TOTAL = Counter(
    "km_mcp_storetext_total",
    "MCP storetext tool invocations partitioned by result",
    labelnames=["result"],
)


UI_REQUESTS_TOTAL = Counter(
    "km_ui_requests_total",
    "Embedded UI visits partitioned by view",
    labelnames=["view"],
)


UI_EVENTS_TOTAL = Counter(
    "km_ui_events_total",
    "Embedded UI events partitioned by event label",
    labelnames=["event"],
)
