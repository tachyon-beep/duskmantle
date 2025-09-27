from __future__ import annotations

import json
import time
from pathlib import Path

from gateway.ingest.pipeline import IngestionConfig, IngestionResult
from gateway.observability.metrics import (
    COVERAGE_LAST_RUN_STATUS,
    COVERAGE_LAST_RUN_TIMESTAMP,
    COVERAGE_MISSING_ARTIFACTS,
)


def write_coverage_report(
    result: IngestionResult,
    config: IngestionConfig,
    *,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [detail for detail in result.artifacts if detail.get("chunk_count", 0) == 0]
    generated_at = time.time()
    payload = {
        "generated_at": generated_at,
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
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    profile = result.profile
    COVERAGE_LAST_RUN_STATUS.labels(profile).set(1)
    COVERAGE_LAST_RUN_TIMESTAMP.labels(profile).set(generated_at)
    COVERAGE_MISSING_ARTIFACTS.labels(profile).set(len(missing))
