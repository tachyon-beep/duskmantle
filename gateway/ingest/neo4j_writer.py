"""Write ingestion artifacts and chunks into Neo4j."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence

from neo4j import Driver

from gateway.ingest.artifacts import Artifact, ChunkEmbedding

logger = logging.getLogger(__name__)


class Neo4jWriter:
    """Persist artifacts and derived data into a Neo4j database."""

    def __init__(self, driver: Driver, database: str = "knowledge") -> None:
        """Initialise the writer with a driver and target database."""
        self.driver = driver
        self.database = database

    def ensure_constraints(self) -> None:
        """Create required uniqueness constraints if they do not exist."""
        cypher_statements = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:SourceFile) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:DesignDoc) REQUIRE d.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:IntegrationMessage) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (tc:TelemetryChannel) REQUIRE tc.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cfg:ConfigFile) REQUIRE cfg.path IS UNIQUE",
        ]
        with self.driver.session(database=self.database) as session:
            for stmt in cypher_statements:
                session.run(stmt)

    def sync_artifact(self, artifact: Artifact) -> None:
        """Upsert the artifact node and related subsystem relationships."""
        label = _artifact_label(artifact)
        metadata = artifact.extra_metadata or {}
        subsystem_meta = metadata.get("subsystem_metadata")
        subsystem_properties = _subsystem_properties(subsystem_meta)
        message_entities = _clean_string_list(metadata.get("message_entities"))
        telemetry_signals = _clean_string_list(metadata.get("telemetry_signals"))
        dependencies = _extract_dependencies(subsystem_meta)

        with self.driver.session(database=self.database) as session:
            params: dict[str, object] = {
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
                parameters=params,
            )

            if artifact.subsystem:
                subsystem_name = artifact.subsystem
                session.run(
                    "MERGE (s:Subsystem {name: $name})\nSET s += $properties",
                    name=subsystem_name,
                    properties=subsystem_properties,
                )

                rel = _relationship_for_label(label)
                if rel:
                    session.run(
                        f"MATCH (entity:{label} {{path: $path}})\nMATCH (s:Subsystem {{name: $name}})\nMERGE (entity)-[:{rel}]->(s)",
                        name=subsystem_name,
                        path=artifact.path.as_posix(),
                    )

                if dependencies:
                    filtered_dependencies = [dep for dep in dependencies if dep and dep != subsystem_name]
                    if filtered_dependencies:
                        session.run(
                            "MATCH (source:Subsystem {name: $name})\n"
                            "UNWIND $dependencies AS dep_name\n"
                            "MERGE (target:Subsystem {name: dep_name})\n"
                            "MERGE (source)-[:DEPENDS_ON]->(target)",
                            name=subsystem_name,
                            dependencies=filtered_dependencies,
                        )

                if message_entities:
                    session.run(
                        "MATCH (s:Subsystem {name: $name})\n"
                        "UNWIND $entities AS entity_name\n"
                        "MERGE (m:IntegrationMessage {name: entity_name})\n"
                        "MERGE (s)-[:IMPLEMENTS]->(m)",
                        name=subsystem_name,
                        entities=message_entities,
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

            if label == "SourceFile" and message_entities:
                session.run(
                    "MATCH (f:SourceFile {path: $path})\n"
                    "UNWIND $entities AS entity_name\n"
                    "MERGE (m:IntegrationMessage {name: entity_name})\n"
                    "MERGE (f)-[:DECLARES]->(m)",
                    path=artifact.path.as_posix(),
                    entities=message_entities,
                )

    def sync_chunks(self, chunk_embeddings: Iterable[ChunkEmbedding]) -> None:
        """Upsert chunk nodes and connect them to their owning artifacts."""
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
                    parameters=params,
                )

    def delete_artifact(self, path: str) -> None:
        """Remove an artifact node and its chunks."""

        with self.driver.session(database=self.database) as session:
            session.run(
                "MATCH (n {path: $path})\n"
                "OPTIONAL MATCH (n)-[:HAS_CHUNK]->(c:Chunk)\n"
                "WITH n, collect(c) AS chunks\n"
                "FOREACH (chunk IN chunks | DETACH DELETE chunk)\n"
                "DETACH DELETE n",
                path=path,
            )


def _artifact_label(artifact: Artifact) -> str:
    """Map artifact types to Neo4j labels."""
    mapping = {
        "doc": "DesignDoc",
        "code": "SourceFile",
        "test": "TestCase",
        "proto": "SourceFile",
        "config": "ConfigFile",
    }
    return mapping.get(artifact.artifact_type, "Artifact")


def _label_for_type(artifact_type: str) -> str:
    """Return the default label for the given artifact type."""
    return {
        "doc": "DesignDoc",
        "code": "SourceFile",
        "test": "TestCase",
        "proto": "SourceFile",
        "config": "ConfigFile",
    }.get(artifact_type, "Artifact")


def _relationship_for_label(label: str) -> str | None:
    """Return the relationship used to link artifacts to subsystems."""
    return {
        "SourceFile": "BELONGS_TO",
        "DesignDoc": "DESCRIBES",
        "TestCase": "VALIDATES",
    }.get(label)


def _clean_string_list(values: object) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
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


def _extract_dependencies(metadata: Mapping[str, object] | None) -> list[str]:
    if not isinstance(metadata, Mapping):
        return []
    raw = metadata.get("dependencies") or metadata.get("depends_on") or metadata.get("depends_on_subsystems")
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


def _subsystem_properties(metadata: Mapping[str, object] | None) -> dict[str, object]:
    if not isinstance(metadata, Mapping):
        return {}
    properties: dict[str, object] = {}
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
