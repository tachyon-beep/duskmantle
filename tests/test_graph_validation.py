"""End-to-end validation of ingestion and graph-backed search."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence, cast

import pytest
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

from gateway.graph.migrations.runner import MigrationRunner
from gateway.graph.service import get_graph_service
from gateway.ingest.embedding import Embedder
from gateway.ingest.neo4j_writer import Neo4jWriter
from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline
from gateway.search import SearchService


@pytest.mark.neo4j
def test_ingestion_populates_graph(tmp_path: Path) -> None:
    """Run ingestion and verify graph nodes, edges, and metadata."""
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "neo4jadmin")
    database = os.getenv("NEO4J_TEST_DATABASE", "knowledge")

    if not uri:
        pytest.skip("Set NEO4J_TEST_URI to run Neo4j integration tests")

    repo_root = tmp_path / "repo"
    (repo_root / "docs").mkdir(parents=True)
    (repo_root / "src" / "project" / "telemetry").mkdir(parents=True)

    sample_doc = repo_root / "docs" / "sample.md"
    sample_doc.write_text("# Sample\nGraph validation doc.\n")

    sample_code = repo_root / "src" / "project" / "telemetry" / "module.py"
    sample_code.write_text("def handler():\n    return 'ok'\n")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session(database=database) as session:
            session.run("MATCH (n) DETACH DELETE n")

        MigrationRunner(driver=driver, database=database).run()

        neo4j_writer = Neo4jWriter(driver, database=database)
        neo4j_writer.ensure_constraints()

        config = IngestionConfig(
            repo_root=repo_root,
            dry_run=False,
            use_dummy_embeddings=True,
        )

        pipeline = IngestionPipeline(
            qdrant_writer=None,
            neo4j_writer=neo4j_writer,
            config=config,
        )

        result = pipeline.run()
        assert result.success

        with driver.session(database=database) as session:
            doc_record = session.run(
                "MATCH (d:DesignDoc {path: $path}) RETURN d",
                path=sample_doc.relative_to(repo_root).as_posix(),
            ).single()
            assert doc_record is not None

            constraints = session.run("SHOW CONSTRAINTS").data()
            seen = {(tuple(record.get("labelsOrTypes", [])), tuple(record.get("properties", []))) for record in constraints}
            expected = {
                (("Subsystem",), ("name",)),
                (("SourceFile",), ("path",)),
                (("DesignDoc",), ("path",)),
                (("TestCase",), ("path",)),
                (("Chunk",), ("chunk_id",)),
            }
            assert expected.issubset(seen)

            chunk_record = session.run(
                "MATCH (:DesignDoc {path: $path})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) AS chunks",
                path=sample_doc.relative_to(repo_root).as_posix(),
            ).single()
            assert chunk_record is not None and chunk_record["chunks"] >= 1

            code_record = session.run(
                "MATCH (f:SourceFile {path: $path})-[:BELONGS_TO]->(s:Subsystem) RETURN f, s",
                path=sample_code.relative_to(repo_root).as_posix(),
            ).single()
            assert code_record is not None
            assert code_record["s"]["name"] == "Telemetry"

            rel_counts = {
                record["type"]: record["count"] for record in session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count")
            }
            assert rel_counts.get("BELONGS_TO", 0) >= 1
            assert rel_counts.get("HAS_CHUNK", 0) >= 1

            graph_service = get_graph_service(driver, database)
            node_data = graph_service.get_node(
                f"SourceFile:{sample_code.relative_to(repo_root).as_posix()}",
                relationships="outgoing",
                limit=10,
            )
            assert any(
                rel["type"] == "BELONGS_TO" and rel["target"]["properties"].get("name") == "Telemetry" for rel in node_data["relationships"]
            )
            subsystem_search = graph_service.search("telemetry", limit=5)
            assert any(result["label"] == "Subsystem" for result in subsystem_search["results"])
    finally:
        driver.close()


class _DummyEmbedder(Embedder):
    """Minimal embedder returning deterministic vectors for tests."""

    def __init__(self) -> None:
        self.model_name = "test"

    @property
    def dimension(self) -> int:
        return 3

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class _FakePoint:
    def __init__(self, payload: dict[str, object], score: float) -> None:
        self.payload = payload
        self.score = score


class _DummyQdrantClient:
    """Stub Qdrant client that returns pre-seeded points."""

    def __init__(self, points: list[_FakePoint]) -> None:
        self._points = points

    def search(self, **_kwargs: Any) -> list[_FakePoint]:
        return self._points


@pytest.mark.neo4j
def test_search_replay_against_real_graph(tmp_path: Path) -> None:
    """Replay saved search results against the populated knowledge graph."""
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "neo4jadmin")
    database = os.getenv("NEO4J_TEST_DATABASE", "knowledge")

    if not uri:
        pytest.skip("Set NEO4J_TEST_URI to run Neo4j integration tests")

    repo_root = tmp_path / "repo"
    (repo_root / "docs").mkdir(parents=True)
    (repo_root / "src" / "project" / "telemetry").mkdir(parents=True)

    doc_path = repo_root / "docs" / "sample.md"
    doc_path.write_text("# Sample\nGraph validation doc.\n")

    code_path = repo_root / "src" / "project" / "telemetry" / "module.py"
    code_path.write_text("def handler():\n    return 'ok'\n")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session(database=database) as session:
            session.run("MATCH (n) DETACH DELETE n")

        MigrationRunner(driver=driver, database=database).run()
        neo4j_writer = Neo4jWriter(driver, database=database)
        neo4j_writer.ensure_constraints()

        config = IngestionConfig(
            repo_root=repo_root,
            dry_run=False,
            use_dummy_embeddings=True,
        )

        pipeline = IngestionPipeline(
            qdrant_writer=None,
            neo4j_writer=neo4j_writer,
            config=config,
        )
        result = pipeline.run()
        assert result.success

        graph_service = get_graph_service(driver, database)

        relative_code = code_path.relative_to(repo_root).as_posix()
        relative_doc = doc_path.relative_to(repo_root).as_posix()

        qdrant_points = [
            _FakePoint(
                {
                    "chunk_id": f"{relative_code}::0",
                    "path": relative_code,
                    "artifact_type": "code",
                    "subsystem": "Telemetry",
                    "text": "code chunk",
                    "coverage_missing": False,
                },
                0.90,
            ),
            _FakePoint(
                {
                    "chunk_id": f"{relative_doc}::0",
                    "path": relative_doc,
                    "artifact_type": "doc",
                    "subsystem": "Telemetry",
                    "text": "doc chunk",
                    "coverage_missing": False,
                },
                0.85,
            ),
        ]

        search_service = SearchService(
            qdrant_client=cast(QdrantClient, _DummyQdrantClient(qdrant_points)),
            collection_name="collection",
            embedder=_DummyEmbedder(),
        )

        response = search_service.search(
            query="telemetry handler",
            limit=2,
            include_graph=True,
            graph_service=graph_service,
        )

        assert response.metadata["graph_context_included"] is True
        assert response.results
        for result_item in response.results:
            assert result_item.graph_context is not None
            signals = result_item.scoring["signals"]
            assert "path_depth" in signals
            assert signals.get("subsystem_criticality", 0.0) >= 0.0

        # Ensure ranking favours the higher vector score but still exposes metadata
        assert response.results[0].chunk["artifact_type"] == "code"
    finally:
        driver.close()
