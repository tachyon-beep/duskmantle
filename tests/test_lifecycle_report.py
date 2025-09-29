from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from gateway.ingest.lifecycle import LifecycleConfig, write_lifecycle_report
from gateway.ingest.pipeline import IngestionResult


class DummyGraphService:
    def __init__(self, pages: dict[str, list[list[dict[str, object]]]]) -> None:
        self._pages = pages

    def list_orphan_nodes(self, *, label: str | None, cursor: str | None, limit: int) -> dict[str, object]:
        label = label or "unknown"
        batches = self._pages.get(label, [])
        if not batches:
            return {"nodes": [], "cursor": None}
        index = int(cursor or 0)
        if index >= len(batches):
            return {"nodes": [], "cursor": None}
        next_index = index + 1 if index + 1 < len(batches) else None
        return {"nodes": batches[index], "cursor": str(next_index) if next_index is not None else None}


@pytest.fixture()
def ingestion_result() -> IngestionResult:
    now = datetime.now(tz=UTC).timestamp()
    old = now - 60 * 60 * 24 * 40
    artifacts = [
        {
            "path": "docs/current.md",
            "artifact_type": "DesignDoc",
            "subsystem": "Kasmina",
            "git_timestamp": now,
            "chunk_count": 3,
        },
        {
            "path": "docs/old.md",
            "artifact_type": "DesignDoc",
            "subsystem": "Kasmina",
            "git_timestamp": old,
            "chunk_count": 2,
        },
        {
            "path": "src/service.py",
            "artifact_type": "SourceFile",
            "subsystem": "Kasmina",
            "git_timestamp": now,
            "chunk_count": 5,
        },
    ]
    result = IngestionResult(
        run_id="test",
        profile="local",
        started_at=now,
        duration_seconds=1.0,
        artifact_counts={"DesignDoc": 2, "SourceFile": 1},
        chunk_count=7,
        repo_head="abc123",
        success=True,
        artifacts=artifacts,
    )
    return result


def test_write_lifecycle_report_without_graph(tmp_path: Path, ingestion_result: IngestionResult) -> None:
    output_path = tmp_path / "reports" / "lifecycle_report.json"
    config = LifecycleConfig(output_path=output_path, stale_days=30, graph_enabled=False)

    write_lifecycle_report(ingestion_result, config=config, graph_service=None)

    payload = json.loads(output_path.read_text())
    assert payload["run"]["run_id"] == "test"
    stale_docs = payload["stale_docs"]
    assert any(entry["path"] == "docs/old.md" for entry in stale_docs)
    assert payload["missing_tests"][0]["subsystem"] == "Kasmina"
    assert payload["isolated"] == {}


def test_write_lifecycle_report_with_graph(tmp_path: Path, ingestion_result: IngestionResult) -> None:
    output_path = tmp_path / "reports" / "lifecycle_report.json"
    graph_nodes = {
        "DesignDoc": [[{"id": "DesignDoc:docs/orphan.md", "properties": {"path": "docs/orphan.md"}}]],
        "SourceFile": [],
    }
    config = LifecycleConfig(output_path=output_path, stale_days=30, graph_enabled=True)
    graph_service = DummyGraphService(graph_nodes)

    write_lifecycle_report(ingestion_result, config=config, graph_service=graph_service)

    payload = json.loads(output_path.read_text())
    assert "DesignDoc" in payload["isolated"]
    assert payload["isolated"]["DesignDoc"][0]["path"] == "docs/orphan.md"
