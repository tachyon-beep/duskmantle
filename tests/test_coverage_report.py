from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from gateway.ingest.coverage import write_coverage_report
from gateway.ingest.pipeline import IngestionConfig, IngestionResult


def test_write_coverage_report(tmp_path: Path) -> None:
    config = IngestionConfig(repo_root=tmp_path)
    result = IngestionResult(
        run_id="run123",
        profile="local",
        started_at=0.0,
        duration_seconds=1.0,
        artifact_counts={"doc": 1, "code": 2},
        chunk_count=3,
        repo_head="abc",
        success=True,
        artifacts=[
            {"path": "docs/a.md", "artifact_type": "doc", "chunk_count": 1, "subsystem": None},
            {"path": "src/x.py", "artifact_type": "code", "chunk_count": 0, "subsystem": "X"},
        ],
    )

    out = tmp_path / "coverage.json"
    write_coverage_report(result, config, output_path=out)

    data = json.loads(out.read_text())
    assert data["run"]["run_id"] == "run123"
    assert data["summary"]["artifact_total"] == 2
    assert data["summary"]["chunk_count"] == 3
    assert len(data["artifacts"]) == 2
    assert len(data["missing_artifacts"]) == 1
