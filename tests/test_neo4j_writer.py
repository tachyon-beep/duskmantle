from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from gateway.ingest.artifacts import Artifact, Chunk, ChunkEmbedding
from gateway.ingest.neo4j_writer import Neo4jWriter


class RecordingSession:
    def __init__(self) -> None:
        self.queries: list[tuple[str, dict[str, object]]] = []

    def run(self, query: str, **params):
        self.queries.append((query, params))
        return SimpleNamespace(single=lambda: None)

    def __enter__(self) -> "RecordingSession":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None


class RecordingDriver:
    def __init__(self) -> None:
        self.sessions: list[RecordingSession] = []

    def session(self, database: str):  # noqa: ARG002 - database unused
        session = RecordingSession()
        self.sessions.append(session)
        return session


def _make_writer() -> tuple[Neo4jWriter, RecordingDriver]:
    driver = RecordingDriver()
    return Neo4jWriter(driver=driver, database="knowledge"), driver


def test_sync_artifact_creates_domain_relationships():
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("src/esper/nissa/handler.py"),
        artifact_type="code",
        subsystem="Nissa",
        content="",
        git_commit="abc123",
        git_timestamp=1700000000,
        extra_metadata={
            "leyline_entities": ["LeylineSync"],
            "telemetry_signals": ["TelemetryEvent"],
            "subsystem_metadata": {
                "description": "Runtime orchestrator",
                "criticality": "high",
                "dependencies": ["Kasmina"],
                "tags": ["runtime"],
            },
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
    assert subsystem_updates and subsystem_updates[0]["properties"]["description"] == "Runtime orchestrator"

    # Dependency edge
    assert any("DEPENDS_ON" in query for query, _ in queries)

    # Leyline message relationships
    assert "LeylineMessage" in cypher_text and "IMPLEMENTS" in cypher_text
    assert "DECLARES" in cypher_text

    # Telemetry channel relationship
    assert "TelemetryChannel" in cypher_text and "EMITS" in cypher_text


def test_sync_chunks_links_chunk_to_artifact():
    writer, driver = _make_writer()
    artifact = Artifact(
        path=Path("src/esper/nissa/handler.py"),
        artifact_type="code",
        subsystem="Nissa",
        content="",
        git_commit=None,
        git_timestamp=None,
    )
    chunk = Chunk(
        artifact=artifact,
        chunk_id="src/esper/nissa/handler.py::0",
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
