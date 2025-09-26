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
