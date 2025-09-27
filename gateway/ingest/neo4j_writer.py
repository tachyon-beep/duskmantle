from __future__ import annotations

import logging
from typing import Iterable, Any

from neo4j import Driver

from gateway.ingest.artifacts import Artifact, ChunkEmbedding

logger = logging.getLogger(__name__)


class Neo4jWriter:
    def __init__(self, driver: Driver, database: str = "knowledge") -> None:
        self.driver = driver
        self.database = database

    def ensure_constraints(self) -> None:
        cypher_statements = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:SourceFile) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:DesignDoc) REQUIRE d.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:LeylineMessage) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (tc:TelemetryChannel) REQUIRE tc.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cfg:ConfigFile) REQUIRE cfg.path IS UNIQUE",
        ]
        with self.driver.session(database=self.database) as session:
            for stmt in cypher_statements:
                session.run(stmt)

    def sync_artifact(self, artifact: Artifact) -> None:
        label = _artifact_label(artifact)
        metadata = artifact.extra_metadata or {}
        subsystem_meta = metadata.get("subsystem_metadata")
        subsystem_properties = _subsystem_properties(subsystem_meta)
        leyline_entities = _clean_string_list(metadata.get("leyline_entities"))
        telemetry_signals = _clean_string_list(metadata.get("telemetry_signals"))
        dependencies = _extract_dependencies(subsystem_meta)

        with self.driver.session(database=self.database) as session:
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

            if artifact.subsystem:
                subsystem_name = artifact.subsystem
                session.run(
                    "MERGE (s:Subsystem {name: $name})\n"
                    "SET s += $properties",
                    name=subsystem_name,
                    properties=subsystem_properties,
                )

                rel = _relationship_for_label(label)
                if rel:
                    session.run(
                        f"MATCH (entity:{label} {{path: $path}})\n"
                        "MERGE (s:Subsystem {name: $name})\n"
                        f"MERGE (entity)-[:{rel}]->(s)",
                        name=subsystem_name,
                        path=artifact.path.as_posix(),
                    )

                if dependencies:
                    filtered_dependencies = [
                        dep for dep in dependencies if dep and dep != subsystem_name
                    ]
                    if filtered_dependencies:
                        session.run(
                            "MATCH (source:Subsystem {name: $name})\n"
                            "UNWIND $dependencies AS dep_name\n"
                            "MERGE (target:Subsystem {name: dep_name})\n"
                            "MERGE (source)-[:DEPENDS_ON]->(target)",
                            name=subsystem_name,
                            dependencies=filtered_dependencies,
                        )

                if leyline_entities:
                    session.run(
                        "MATCH (s:Subsystem {name: $name})\n"
                        "UNWIND $entities AS entity_name\n"
                        "MERGE (m:LeylineMessage {name: entity_name})\n"
                        "MERGE (s)-[:IMPLEMENTS]->(m)",
                        name=subsystem_name,
                        entities=leyline_entities,
                    )

                if telemetry_signals:
                    session.run(
                        "MATCH (s:Subsystem {name: $name})\n"
                        "UNWIND $signals AS signal_name\n"
                        "MERGE (t:TelemetryChannel {name: signal_name})\n"
                        "SET t.source_subsystem = $name\n"
                        "MERGE (s)-[:EMITS]->(t)",
                        name=subsystem_name,
                        signals=telemetry_signals,
                    )

            if label == "SourceFile" and leyline_entities:
                session.run(
                    "MATCH (f:SourceFile {path: $path})\n"
                    "UNWIND $entities AS entity_name\n"
                    "MERGE (m:LeylineMessage {name: entity_name})\n"
                    "MERGE (f)-[:DECLARES]->(m)",
                    path=artifact.path.as_posix(),
                    entities=leyline_entities,
                )

    def sync_chunks(self, chunk_embeddings: Iterable[ChunkEmbedding]) -> None:
        with self.driver.session(database=self.database) as session:
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


def _clean_string_list(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    seen: dict[str, None] = {}
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        seen.setdefault(text, None)
    return list(seen.keys())


def _normalize_subsystem_name(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.islower():
        return text.capitalize()
    return text


def _extract_dependencies(metadata: Any) -> list[str]:
    if not isinstance(metadata, dict):
        return []
    raw = metadata.get("dependencies") or metadata.get("depends_on") or metadata.get(
        "depends_on_subsystems"
    )
    dependencies = []
    if isinstance(raw, (list, tuple, set)):
        for value in raw:
            if not isinstance(value, str):
                continue
            normalized = _normalize_subsystem_name(value)
            if normalized:
                dependencies.append(normalized)
    elif isinstance(raw, str):
        normalized = _normalize_subsystem_name(raw)
        if normalized:
            dependencies.append(normalized)
    return list(dict.fromkeys(dependencies))


def _subsystem_properties(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    properties: dict[str, Any] = {}
    for key in ("description", "criticality", "owner", "domain"):
        value = metadata.get(key)
        if value:
            properties[key] = value
    for list_key in ("tags", "labels"):
        values = metadata.get(list_key)
        cleaned = _clean_string_list(values)
        if cleaned:
            properties[list_key] = cleaned
    return properties
