from __future__ import annotations

import logging
from typing import Iterable

from neo4j import Driver

from gateway.ingest.artifacts import Artifact, ChunkEmbedding

logger = logging.getLogger(__name__)


class Neo4jWriter:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def ensure_constraints(self) -> None:
        cypher_statements = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:SourceFile) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:DesignDoc) REQUIRE d.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
        ]
        with self.driver.session(database="system") as session:
            for stmt in cypher_statements:
                session.run(stmt)

    def sync_artifact(self, artifact: Artifact) -> None:
        label = _artifact_label(artifact)
        with self.driver.session() as session:
            params = {
                "path": artifact.path.as_posix(),
                "artifact_type": artifact.artifact_type,
                "git_commit": artifact.git_commit,
                "git_timestamp": artifact.git_timestamp,
                "subsystem": artifact.subsystem,
            }
            session.run(
                f"MERGE (node:{label} {{path: $path}}) "
                "SET node.artifact_type = $artifact_type, "
                "    node.git_commit = $git_commit, "
                "    node.git_timestamp = $git_timestamp, "
                "    node.subsystem = $subsystem",
                **params,
            )
            if artifact.subsystem:
                rel = _relationship_for_label(label)
                if rel:
                    session.run(
                        "MERGE (s:Subsystem {name: $name})\n"
                        "WITH s\n"
                        f"MATCH (f:{label} {{path: $path}})\n"
                        f"MERGE (f)-[:{rel}]->(s)",
                        name=artifact.subsystem,
                        path=artifact.path.as_posix(),
                    )

    def sync_chunks(self, chunk_embeddings: Iterable[ChunkEmbedding]) -> None:
        with self.driver.session() as session:
            for item in chunk_embeddings:
                artifact_type = item.chunk.metadata.get("artifact_type", "code")
                label = _label_for_type(str(artifact_type))
                params = {
                    "chunk_id": item.chunk.chunk_id,
                    "path": item.chunk.metadata.get("path"),
                    "sequence": item.chunk.sequence,
                    "digest": item.chunk.content_digest,
                }
                session.run(
                    "MERGE (c:Chunk {chunk_id: $chunk_id})\n"
                    "SET c.sequence = $sequence, c.content_digest = $digest\n"
                    "WITH c\n"
                    f"MATCH (f:{label} {{path: $path}})\n"
                    "MERGE (f)-[:HAS_CHUNK]->(c)",
                    **params,
                )


def _artifact_label(artifact: Artifact) -> str:
    mapping = {
        "doc": "DesignDoc",
        "code": "SourceFile",
        "test": "TestCase",
        "proto": "SourceFile",
        "config": "ConfigFile",
    }
    return mapping.get(artifact.artifact_type, "Artifact")


def _label_for_type(artifact_type: str) -> str:
    return {
        "doc": "DesignDoc",
        "code": "SourceFile",
        "test": "TestCase",
        "proto": "SourceFile",
        "config": "ConfigFile",
    }.get(artifact_type, "Artifact")


def _relationship_for_label(label: str) -> str | None:
    return {
        "SourceFile": "BELONGS_TO",
        "DesignDoc": "DESCRIBES",
        "TestCase": "VALIDATES",
    }.get(label)
