"""Unit tests for the lightweight Neo4j writer integration layer."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace, TracebackType
from typing import Any, cast

from neo4j import Driver

from gateway.ingest.artifacts import Artifact, Chunk, ChunkEmbedding
from gateway.ingest.neo4j_writer import Neo4jWriter


class RecordingSession:
    """Stubbed session that records Cypher queries for assertions."""

    def __init__(self) -> None:
        self.queries: list[tuple[str, dict[str, object]]] = []

    def run(self, query: str, **params: object) -> SimpleNamespace:
        self.queries.append((query, params))
        return SimpleNamespace(single=lambda: None)

    def __enter__(self) -> RecordingSession:  # pragma: no cover - trivial
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # pragma: no cover - trivial
        return None


class RecordingDriver:
    """Stubbed driver that yields recording sessions."""

    def __init__(self) -> None:
        self.sessions: list[RecordingSession] = []

    def session(self, *, database: str | None = None) -> RecordingSession:
        """Return a new recording session; database name is ignored."""
        _ = database  # pragma: no cover - value unused in stub
        session = RecordingSession()
        self.sessions.append(session)
        return session


def _make_writer() -> tuple[Neo4jWriter, RecordingDriver]:
    """Create a writer bound to a recording driver for inspection."""

    driver = RecordingDriver()
    return Neo4jWriter(driver=cast(Driver, driver), database="knowledge"), driver


def test_sync_artifact_creates_domain_relationships() -> None:
    """Artifacts trigger the expected Cypher commands and relationships."""
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("src/project/nissa/handler.py"),
        artifact_type="code",
        subsystem="Nissa",
        content="",
        git_commit="abc123",
        git_timestamp=1700000000,
        extra_metadata={
            "message_entities": ["IntegrationSync"],
            "telemetry_signals": ["TelemetryEvent"],
            "subsystem_metadata": {
                "description": "Runtime orchestrator",
                "criticality": "high",
                "dependencies": ["Kasmina"],
                "tags": ["runtime"],
            },
            "symbols": [
                {
                    "id": "src/project/nissa/handler.py::Example",
                    "name": "Example",
                    "kind": "class",
                    "language": "python",
                    "line_start": 1,
                    "line_end": 10,
                    "qualified_name": "Example",
                },
                {
                    "id": "src/project/nissa/handler.py::Example.method",
                    "name": "method",
                    "kind": "method",
                    "language": "python",
                    "line_start": 2,
                    "line_end": 3,
                    "qualified_name": "Example.method",
                },
            ],
        },
    )

    writer.sync_artifact(artifact)

    assert driver.sessions, "expected at least one Neo4j session"
    queries = driver.sessions[0].queries
    cypher_text = "\n".join(query for query, _ in queries)

    # Artifact node persisted
    assert any("MERGE (node:SourceFile" in query for query, _ in queries)

    # Subsystem metadata applied
    subsystem_updates = [params for query, params in queries if "SET s += $properties" in query]
    assert subsystem_updates
    properties = subsystem_updates[0].get("properties")
    assert isinstance(properties, dict)
    description = cast(Any, properties.get("description"))
    assert description == "Runtime orchestrator"

    # Dependency edge
    assert any("DEPENDS_ON" in query for query, _ in queries)

    # Integration message relationships
    assert "IntegrationMessage" in cypher_text and "IMPLEMENTS" in cypher_text
    assert "DECLARES" in cypher_text
    assert "DECLARES_SYMBOL" in cypher_text

    # Telemetry channel relationship
    assert "TelemetryChannel" in cypher_text and "EMITS" in cypher_text


def test_sync_artifact_merges_subsystem_edge_once() -> None:
    """Syncing an artifact does not duplicate the subsystem relationship."""
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("src/project/nissa/handler.py"),
        artifact_type="code",
        subsystem="Nissa",
        content="",
        git_commit="abc123",
        git_timestamp=1700000000,
    )

    writer.sync_artifact(artifact)

    queries = driver.sessions[0].queries
    subsystem_edge_queries = [query for query, _ in queries if "BELONGS_TO" in query]

    assert len(subsystem_edge_queries) == 1
    assert "MERGE (entity" in subsystem_edge_queries[0]


def test_sync_chunks_links_chunk_to_artifact() -> None:
    """Chunk synchronization creates chunk nodes and linking edges."""
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("src/project/nissa/handler.py"),
        artifact_type="code",
        subsystem="Nissa",
        content="",
        git_commit=None,
        git_timestamp=None,
    )
    chunk = Chunk(
        artifact=artifact,
        chunk_id="src/project/nissa/handler.py::0",
        text="example",
        sequence=0,
        content_digest="digest",
        metadata={
            "artifact_type": "code",
            "path": artifact.path.as_posix(),
        },
    )
    embedding = ChunkEmbedding(chunk=chunk, vector=[0.1] * 8)

    writer.sync_chunks([embedding])

    queries = driver.sessions[0].queries
    cypher_text = "\n".join(query for query, _ in queries)
    assert "MERGE (c:Chunk" in cypher_text
    assert "HAS_CHUNK" in cypher_text


def test_sync_artifact_ignores_missing_symbols() -> None:
    """Artifacts without symbol metadata should not emit symbol queries."""
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("src/no/symbols.py"),
        artifact_type="code",
        subsystem=None,
        content="",
        git_commit=None,
        git_timestamp=None,
        extra_metadata={
            "symbols": [],
        },
    )

    writer.sync_artifact(artifact)

    queries = driver.sessions[0].queries
    assert all("DECLARES_SYMBOL" not in query for query, _ in queries)


def test_delete_artifact_removes_declared_symbols() -> None:
    """Deleting an artifact also removes its declared symbol nodes."""
    writer, driver = _make_writer()
    writer.delete_artifact("src/project/nissa/handler.py")

    queries = driver.sessions[0].queries
    delete_query = "\n".join(q for q, _ in queries)
    assert "DECLARES_SYMBOL" in delete_query


def test_sync_artifact_creates_exercises_relationships() -> None:
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("tests/test_example.py"),
        artifact_type="test",
        subsystem=None,
        content="",
        git_commit=None,
        git_timestamp=None,
        extra_metadata={
            "exercises_symbols": ["src/project/module.py::Example.method"],
        },
    )

    writer.sync_artifact(artifact)

    queries = driver.sessions[0].queries
    assert any("EXERCISES" in query for query, _ in queries)
    delete_queries = [query for query, _ in queries if "DELETE r" in query]
    assert delete_queries, "expected existing EXERCISES edges to be cleared before insertion"
