from __future__ import annotations

from pathlib import Path

import pytest
from prometheus_client import REGISTRY

from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline


class StubQdrantWriter:
    def __init__(self) -> None:
        self.collection_sizes: list[int] = []
        self.upsert_payloads: list[int] = []
        self.deleted_paths: list[str] = []

    def ensure_collection(self, vector_size: int) -> None:
        self.collection_sizes.append(vector_size)

    def upsert_chunks(self, chunks) -> None:
        self.upsert_payloads.append(len(list(chunks)))

    def delete_artifact(self, artifact_path: str) -> None:
        self.deleted_paths.append(artifact_path)


def _metric_value(name: str, labels: dict[str, str]) -> float:
    value = REGISTRY.get_sample_value(name, labels)
    return float(value) if value is not None else 0.0


class StubNeo4jWriter:
    def __init__(self) -> None:
        self.artifacts: list[str] = []
        self.chunk_ids: list[str] = []
        self.deleted_paths: list[str] = []

    def ensure_constraints(self) -> None:  # pragma: no cover - not used in unit test
        pass

    def sync_artifact(self, artifact) -> None:
        self.artifacts.append(artifact.path.as_posix())

    def sync_chunks(self, chunk_embeddings) -> None:
        for item in chunk_embeddings:
            self.chunk_ids.append(item.chunk.chunk_id)

    def delete_artifact(self, path: str) -> None:
        self.deleted_paths.append(path)


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "src" / "project" / "kasmina").mkdir(parents=True)
    (tmp_path / "tests").mkdir()

    (tmp_path / "docs" / "overview.md").write_text("Kasmina module design.\n")
    (tmp_path / "src" / "project" / "kasmina" / "module.py").write_text("def run():\n    return 'ok'\n")
    (tmp_path / "tests" / "test_module.py").write_text("def test_run():\n    assert True\n")
    return tmp_path


def test_pipeline_generates_chunks(sample_repo: Path) -> None:
    qdrant = StubQdrantWriter()
    neo4j = StubNeo4jWriter()
    config = IngestionConfig(
        repo_root=sample_repo,
        dry_run=False,
        use_dummy_embeddings=True,
        chunk_window=64,
        chunk_overlap=10,
    )
    pipeline = IngestionPipeline(qdrant_writer=qdrant, neo4j_writer=neo4j, config=config)
    result = pipeline.run()

    assert qdrant.collection_sizes, "collection should be ensured"
    assert sum(qdrant.upsert_payloads) > 0
    assert neo4j.artifacts
    assert neo4j.chunk_ids
    assert result.chunk_count == len(neo4j.chunk_ids)
    assert result.artifact_counts["doc"] >= 1


def test_pipeline_removes_stale_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "src" / "project" / "kasmina").mkdir(parents=True)

    kept_path = repo / "docs" / "overview.md"
    stale_path = repo / "docs" / "obsolete.md"
    kept_path.write_text("Kasmina module design.\n")
    stale_path.write_text("Legacy overview\n")
    (repo / "src" / "project" / "kasmina" / "module.py").write_text("def run():\n    return 'ok'\n")

    ledger_path = tmp_path / "state" / "reports" / "artifact_ledger.json"

    def _run_pipeline() -> tuple[StubQdrantWriter, StubNeo4jWriter, IngestionPipeline]:
        qdrant = StubQdrantWriter()
        neo4j = StubNeo4jWriter()
        config = IngestionConfig(
            repo_root=repo,
            dry_run=False,
            use_dummy_embeddings=True,
            chunk_window=64,
            chunk_overlap=10,
            ledger_path=ledger_path,
        )
        pipeline = IngestionPipeline(qdrant_writer=qdrant, neo4j_writer=neo4j, config=config)
        return qdrant, neo4j, pipeline

    qdrant1, neo4j1, pipeline1 = _run_pipeline()
    result_first = pipeline1.run()
    assert not result_first.removed_artifacts
    assert ledger_path.exists()

    stale_path.unlink()

    qdrant2, neo4j2, pipeline2 = _run_pipeline()
    metric_before = _metric_value("km_ingest_stale_resolved_total", {"profile": "local"})
    result_second = pipeline2.run()
    metric_after = _metric_value("km_ingest_stale_resolved_total", {"profile": "local"})

    assert result_second.removed_artifacts
    removed_entry = result_second.removed_artifacts[0]
    assert removed_entry["path"] == "docs/obsolete.md"
    assert removed_entry["status"] == "deleted"
    assert "digest" in removed_entry
    assert "artifact_type" in removed_entry
    assert "docs/obsolete.md" in neo4j2.deleted_paths
    assert "docs/obsolete.md" in qdrant2.deleted_paths
    assert metric_after == metric_before + 1
