from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

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

SEARCH_GRAPH_LOOKUP_SECONDS = Histogram(
    "km_search_graph_lookup_seconds",
    "Latency of graph lookups for search enrichment",
)

SEARCH_SCORE_DELTA = Histogram(
    "km_search_adjusted_minus_vector",
    "Distribution of adjusted minus vector scores",
)

GRAPH_MIGRATION_LAST_STATUS = Gauge(
    "km_graph_migration_last_status",
    "Graph migration result (1=success, 0=failure, -1=skipped)",
)

GRAPH_MIGRATION_LAST_TIMESTAMP = Gauge(
    "km_graph_migration_last_timestamp",
    "Unix timestamp of the last graph migration attempt",
)
