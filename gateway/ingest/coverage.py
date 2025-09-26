from __future__ import annotations

import json
import time
from pathlib import Path

from gateway.ingest.pipeline import IngestionResult


def write_coverage_report(result: IngestionResult, artifacts_total: int, *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.time(),
        "run_id": result.run_id,
        "profile": result.profile,
        "repo_head": result.repo_head,
        "artifacts_total": artifacts_total,
        "artifact_breakdown": result.artifact_counts,
        "chunk_count": result.chunk_count,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
