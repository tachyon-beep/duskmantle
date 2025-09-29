from __future__ import annotations

import json
import time
from contextlib import suppress
from pathlib import Path

from datetime import datetime, timezone
from typing import Iterable

from gateway.ingest.pipeline import IngestionConfig, IngestionResult
from gateway.observability.metrics import (
    COVERAGE_HISTORY_SNAPSHOTS,
    COVERAGE_LAST_RUN_STATUS,
    COVERAGE_LAST_RUN_TIMESTAMP,
    COVERAGE_MISSING_ARTIFACTS,
    COVERAGE_STALE_ARTIFACTS,
)


def write_coverage_report(
    result: IngestionResult,
    config: IngestionConfig,
    *,
    output_path: Path,
    history_limit: int | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [detail for detail in result.artifacts if detail.get("chunk_count", 0) == 0]
    removed = list(result.removed_artifacts)
    generated_at = time.time()
    generated_at_iso = datetime.fromtimestamp(generated_at, tz=timezone.utc).isoformat()
    payload = {
        "generated_at": generated_at,
        "generated_at_iso": generated_at_iso,
        "run": {
            "run_id": result.run_id,
            "profile": result.profile,
            "repo_head": result.repo_head,
        },
        "include_patterns": list(config.include_patterns),
        "summary": {
            "artifact_total": len(result.artifacts),
            "artifact_breakdown": result.artifact_counts,
            "chunk_count": result.chunk_count,
        },
        "artifacts": result.artifacts,
        "missing_artifacts": missing,
        "removed_artifacts": removed,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    snapshots = _write_history_snapshot(
        payload,
        output_path.parent,
        history_limit or config.coverage_history_limit,
    )
    profile = result.profile
    COVERAGE_LAST_RUN_STATUS.labels(profile).set(1)
    COVERAGE_LAST_RUN_TIMESTAMP.labels(profile).set(generated_at)
    COVERAGE_MISSING_ARTIFACTS.labels(profile).set(len(missing))
    COVERAGE_STALE_ARTIFACTS.labels(profile).set(len(removed))
    COVERAGE_HISTORY_SNAPSHOTS.labels(profile).set(len(snapshots))


def _write_history_snapshot(
    payload: dict[str, object], reports_dir: Path, history_limit: int
) -> list[Path]:
    history_dir = reports_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    history_path = history_dir / f"coverage_{timestamp}.json"
    history_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    snapshots = sorted(history_dir.glob("coverage_*.json"), key=lambda path: path.stat().st_mtime)
    if len(snapshots) <= history_limit:
        return snapshots
    for old_path in snapshots[0 : len(snapshots) - history_limit]:
        with suppress(FileNotFoundError):
            old_path.unlink()
    return sorted(history_dir.glob("coverage_*.json"), key=lambda path: path.stat().st_mtime)
