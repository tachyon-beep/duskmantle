from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from gateway.ingest.pipeline import IngestionResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    profile TEXT,
    started_at REAL,
    duration_seconds REAL,
    artifact_count INTEGER,
    chunk_count INTEGER,
    repo_head TEXT,
    success INTEGER,
    created_at REAL
)
"""

_SELECT_RECENT = """
SELECT run_id, profile, started_at, duration_seconds, artifact_count, chunk_count, repo_head, success, created_at
FROM ingestion_runs
ORDER BY created_at DESC
LIMIT ?
"""

_INSERT_RUN = """
INSERT INTO ingestion_runs (
    run_id,
    profile,
    started_at,
    duration_seconds,
    artifact_count,
    chunk_count,
    repo_head,
    success,
    created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class AuditLogger:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(_SCHEMA)

    def record(self, result: IngestionResult) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                _INSERT_RUN,
                (
                    result.run_id,
                    result.profile,
                    result.started_at,
                    result.duration_seconds,
                    sum(result.artifact_counts.values()),
                    result.chunk_count,
                    result.repo_head,
                    1 if result.success else 0,
                    time.time(),
                ),
            )
            conn.commit()

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(_SELECT_RECENT, (limit,)).fetchall()
        columns = [
            "run_id",
            "profile",
            "started_at",
            "duration_seconds",
            "artifact_count",
            "chunk_count",
            "repo_head",
            "success",
            "created_at",
        ]
        return [dict(zip(columns, row, strict=False)) for row in rows]
