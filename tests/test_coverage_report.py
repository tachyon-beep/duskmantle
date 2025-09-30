from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from gateway.api.app import create_app
from gateway.ingest.coverage import write_coverage_report
from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline, IngestionResult
from gateway.observability.metrics import (
    COVERAGE_HISTORY_SNAPSHOTS,
    COVERAGE_LAST_RUN_STATUS,
    COVERAGE_LAST_RUN_TIMESTAMP,
    COVERAGE_MISSING_ARTIFACTS,
    COVERAGE_STALE_ARTIFACTS,
)


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
        removed_artifacts=[{"path": "docs/old.md", "artifact_type": "doc", "status": "deleted"}],
    )

    out = tmp_path / "coverage.json"
    COVERAGE_LAST_RUN_STATUS.labels("local").set(0)
    COVERAGE_MISSING_ARTIFACTS.labels("local").set(0)
    COVERAGE_LAST_RUN_TIMESTAMP.labels("local").set(0)
    COVERAGE_STALE_ARTIFACTS.labels("local").set(0)
    write_coverage_report(result, config, output_path=out)

    data = json.loads(out.read_text())
    assert data["run"]["run_id"] == "run123"
    assert data["summary"]["artifact_total"] == 2
    assert data["summary"]["chunk_count"] == 3
    assert len(data["artifacts"]) == 2
    assert len(data["missing_artifacts"]) == 1
    assert data["removed_artifacts"]
    assert data["removed_artifacts"][0]["path"] == "docs/old.md"

    assert COVERAGE_LAST_RUN_STATUS.labels("local")._value.get() == 1
    assert COVERAGE_MISSING_ARTIFACTS.labels("local")._value.get() == 1
    assert COVERAGE_LAST_RUN_TIMESTAMP.labels("local")._value.get() > 0
    assert COVERAGE_HISTORY_SNAPSHOTS.labels("local")._value.get() == 1
    assert COVERAGE_STALE_ARTIFACTS.labels("local")._value.get() == 1


class StubQdrantWriter:
    def ensure_collection(self, vector_size: int) -> None:  # pragma: no cover - not used
        return None

    def upsert_chunks(self, chunks) -> None:  # pragma: no cover - not used
        list(chunks)


class StubNeo4jWriter:
    def ensure_constraints(self) -> None:  # pragma: no cover - not used
        return None

    def sync_artifact(self, artifact) -> None:
        return None

    def sync_chunks(self, chunk_embeddings) -> None:
        return None


def test_coverage_endpoint_after_report_generation(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "overview.md").write_text("IntegrationSync telemetry doc")
    # empty file to register as missing coverage
    (repo / "tests").mkdir()
    (repo / "tests" / "empty_test.py").write_text("")

    config = IngestionConfig(
        repo_root=repo,
        dry_run=True,
        use_dummy_embeddings=True,
        chunk_window=64,
        chunk_overlap=16,
        coverage_history_limit=2,
    )
    pipeline = IngestionPipeline(
        qdrant_writer=StubQdrantWriter(),
        neo4j_writer=StubNeo4jWriter(),
        config=config,
    )
    result = pipeline.run()

    state_path = tmp_path / "state"
    report_path = state_path / "reports" / "coverage_report.json"
    write_coverage_report(result, config, output_path=report_path)

    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    resp = client.get(
        "/coverage",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["summary"]["artifact_total"] >= 2
    assert any(item["chunk_count"] == 0 for item in payload["artifacts"])


def test_coverage_history_rotation(tmp_path: Path) -> None:
    config = IngestionConfig(repo_root=tmp_path, coverage_history_limit=2)
    out = tmp_path / "reports" / "coverage_report.json"

    for idx in range(4):
        result = IngestionResult(
            run_id=f"run{idx}",
            profile="local",
            started_at=0.0,
            duration_seconds=1.0,
            artifact_counts={},
            chunk_count=0,
            repo_head=f"sha{idx}",
            success=True,
        )
        write_coverage_report(result, config, output_path=out)

    history_dir = out.parent / "history"
    snapshots = sorted(history_dir.glob("coverage_*.json"))
    assert len(snapshots) == config.coverage_history_limit
    gauge_value = REGISTRY.get_sample_value(
        "km_coverage_history_snapshots",
        {"profile": "local"},
    )
    assert gauge_value == float(config.coverage_history_limit)
