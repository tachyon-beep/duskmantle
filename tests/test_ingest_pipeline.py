from __future__ import annotations

from pathlib import Path

import pytest

from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline


class StubQdrantWriter:
    def __init__(self) -> None:
        self.collection_sizes: list[int] = []
        self.upsert_payloads: list[int] = []

    def ensure_collection(self, vector_size: int) -> None:
        self.collection_sizes.append(vector_size)

    def upsert_chunks(self, chunks) -> None:
        self.upsert_payloads.append(len(list(chunks)))


class StubNeo4jWriter:
    def __init__(self) -> None:
        self.artifacts: list[str] = []
        self.chunk_ids: list[str] = []

    def ensure_constraints(self) -> None:  # pragma: no cover - not used in unit test
        pass

    def sync_artifact(self, artifact) -> None:
        self.artifacts.append(artifact.path.as_posix())

    def sync_chunks(self, chunk_embeddings) -> None:
        for item in chunk_embeddings:
            self.chunk_ids.append(item.chunk.chunk_id)


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "src" / "esper" / "kasmina").mkdir(parents=True)
    (tmp_path / "tests").mkdir()

    (tmp_path / "docs" / "overview.md").write_text("Kasmina module design.\n")
    (tmp_path / "src" / "esper" / "kasmina" / "module.py").write_text("def run():\n    return 'ok'\n")
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
    pipeline.run()

    assert qdrant.collection_sizes, "collection should be ensured"
    assert sum(qdrant.upsert_payloads) > 0
    assert neo4j.artifacts
    assert neo4j.chunk_ids
