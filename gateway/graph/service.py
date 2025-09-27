from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from neo4j import Driver, Transaction
from neo4j.graph import Node, Relationship


class GraphServiceError(RuntimeError):
    """Base class for graph-related errors."""


class GraphNotFoundError(GraphServiceError):
    """Raised when a requested node cannot be found."""


class GraphQueryError(GraphServiceError):
    """Raised when a supplied query is invalid or unsafe."""


@dataclass(slots=True)
class GraphService:
    """Service layer for read-only graph queries."""

    driver: Driver
    database: str

    def get_subsystem(
        self,
        name: str,
        *,
        depth: int,
        limit: int,
        cursor: str | None,
        include_artifacts: bool,
    ) -> dict[str, Any]:
        offset = _decode_cursor(cursor)
        with self.driver.session(database=self.database) as session:
            subsystem_node = session.execute_read(_fetch_subsystem_node, name)
            if subsystem_node is None:
                raise GraphNotFoundError(f"Subsystem '{name}' not found")

            related_records = session.execute_read(
                _fetch_related_nodes,
                name,
                depth,
                offset,
                limit,
            )
            related = [_serialize_related(record, subsystem_node) for record in related_records]

            next_cursor = None
            if len(related) == limit:
                next_cursor = _encode_cursor(offset + limit)

            artifacts: list[dict[str, Any]] = []
            if include_artifacts:
                artifact_records = session.execute_read(_fetch_artifacts_for_subsystem, name)
                artifacts = [_serialize_node(node) for node in artifact_records]

        return {
            "subsystem": _serialize_node(subsystem_node),
            "related": {
                "nodes": related,
                "cursor": next_cursor,
            },
            "artifacts": artifacts,
        }

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:
        label, key, value = _parse_node_id(node_id)
        with self.driver.session(database=self.database) as session:
            node = session.execute_read(_fetch_node_by_id, label, key, value)
            if node is None:
                raise GraphNotFoundError(f"Node '{node_id}' not found")

            rels: list[dict[str, Any]] = []
            if relationships != "none":
                direction = relationships
                rel_records = session.execute_read(
                    _fetch_node_relationships,
                    label,
                    key,
                    value,
                    direction,
                    limit,
                )
                rels = [_serialize_relationship(record) for record in rel_records]

        return {
            "node": _serialize_node(node),
            "relationships": rels,
        }

    def search(self, term: str, *, limit: int) -> dict[str, Any]:
        if not term.strip():
            return {"results": []}
        lower_term = term.lower()
        with self.driver.session(database=self.database) as session:
            records = session.execute_read(_search_entities, lower_term, limit)
        results = [
            {
                "id": _canonical_node_id(record["node"]),
                "label": record["label"],
                "score": record["score"],
                "snippet": record.get("snippet"),
            }
            for record in records
        ]
        return {"results": results}

    def shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:
        """Return the length of the shortest path from the node to any subsystem.

        The search is bounded by ``max_depth`` hops across the knowledge graph
        relationship types used by ingestion. ``None`` is returned when no
        subsystem can be reached within the given depth limit.
        """

        if max_depth < 1:
            max_depth = 1
        label, key, value = _parse_node_id(node_id)
        relationship_pattern = "BELONGS_TO|DESCRIBES|VALIDATES|HAS_CHUNK"
        depth_limit = int(max_depth)
        query = (
            f"MATCH (start:{label} {{{key}: $value}}) "
            f"MATCH p = shortestPath((start)-[:{relationship_pattern}*1..{depth_limit}]-(sub:Subsystem)) "
            "RETURN length(p) AS depth"
        )

        try:
            with self.driver.session(database=self.database) as session:
                record = session.run(query, value=value).single()
        except Exception as exc:  # pragma: no cover - defensive guard
            raise GraphServiceError(str(exc)) from exc
        if record is None:
            return None
        depth = record.get("depth")
        if depth is None:
            return None
        try:
            return int(depth)
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            return None

    def run_cypher(
        self,
        query: str,
        parameters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        _validate_cypher(query)
        params = parameters or {}
        try:
            result = self.driver.execute_query(
                query,
                parameters=params,
                database_=self.database,
            )
        except Exception as exc:  # pragma: no cover - driver errors wrapped for clients
            raise GraphQueryError(str(exc)) from exc

        data = [
            {
                "row": [_serialize_value(value) for value in record.values()],
            }
            for record in result.records
        ]
        summary = result.summary
        consumed_ms = None
        if summary and summary.result_available_after is not None:
            consumed_ms = summary.result_available_after

        return {
            "data": data,
            "summary": {
                "resultConsumedAfterMs": consumed_ms,
                "database": summary.database.name if summary and summary.database else self.database,
            },
        }


def get_graph_service(driver: Driver, database: str) -> GraphService:
    return GraphService(driver=driver, database=database)


# --- Neo4j read helpers ----------------------------------------------------


def _fetch_subsystem_node(tx: Transaction, name: str) -> Node | None:
    result = tx.run("MATCH (s:Subsystem {name: $name}) RETURN s LIMIT 1", name=name)
    record = result.single()
    return record["s"] if record else None


def _fetch_related_nodes(
    tx: Transaction,
    name: str,
    depth: int,
    skip: int,
    limit: int,
) -> list[dict[str, Any]]:
    _ = depth  # reserved for future expansion; currently depth=1
    query = (
        "MATCH (s:Subsystem {name: $name})-[rel]-(n) "
        "WHERE n <> s "
        "RETURN rel AS relationship, n AS node "
        "ORDER BY n.name "
        "SKIP $skip LIMIT $limit"
    )
    result = tx.run(query, name=name, skip=skip, limit=limit)
    return [{"relationship": record["relationship"], "node": record["node"]} for record in result]


def _fetch_artifacts_for_subsystem(tx: Transaction, name: str) -> list[Node]:
    query = (
        "MATCH (artifact)-[rel]->(s:Subsystem {name: $name}) "
        "WHERE type(rel) IN ['BELONGS_TO', 'DESCRIBES', 'VALIDATES'] "
        "RETURN artifact ORDER BY artifact.path LIMIT 200"
    )
    result = tx.run(query, name=name)
    return [record["artifact"] for record in result]


def _fetch_node_by_id(tx: Transaction, label: str, key: str, value: Any) -> Node | None:
    query = f"MATCH (n:{label} {{{key}: $value}}) RETURN n LIMIT 1"
    record = tx.run(query, value=value).single()
    return record["n"] if record else None


def _fetch_node_relationships(
    tx: Transaction,
    label: str,
    key: str,
    value: Any,
    direction: str,
    limit: int,
) -> list[dict[str, Any]]:
    if direction == "incoming":
        query = (
            f"MATCH (n:{label} {{{key}: $value}})<-[rel]-(other) "
            "RETURN rel AS relationship, other AS node "
            "LIMIT $limit"
        )
    elif direction == "all":
        query = (
            f"MATCH (n:{label} {{{key}: $value}})-[rel]-(other) "
            "RETURN rel AS relationship, other AS node "
            "LIMIT $limit"
        )
    else:  # outgoing
        query = (
            f"MATCH (n:{label} {{{key}: $value}})-[rel]->(other) "
            "RETURN rel AS relationship, other AS node "
            "LIMIT $limit"
        )
    result = tx.run(query, value=value, limit=limit)
    return [{"relationship": record["relationship"], "node": record["node"]} for record in result]


def _search_entities(tx: Transaction, term: str, limit: int) -> list[dict[str, Any]]:
    query = (
        "CALL {"
        "  MATCH (s:Subsystem)"
        "  WHERE toLower(s.name) CONTAINS $term"
        "  RETURN s AS node, 'Subsystem' AS label, 0.95 AS score, s.description AS snippet"
        "  UNION"
        "  MATCH (d:DesignDoc)"
        "  WHERE toLower(d.path) CONTAINS $term"
        "  RETURN d AS node, 'DesignDoc' AS label, 0.85 AS score, d.path AS snippet"
        "  UNION"
        "  MATCH (f:SourceFile)"
        "  WHERE toLower(f.path) CONTAINS $term"
        "  RETURN f AS node, 'SourceFile' AS label, 0.80 AS score, f.path AS snippet"
        "}"
        "RETURN node, label, score, snippet "
        "LIMIT $limit"
    )
    result = tx.run(query, term=term, limit=limit)
    return [
        {
            "node": record["node"],
            "label": record["label"],
            "score": record["score"],
            "snippet": record.get("snippet"),
        }
        for record in result
    ]


# --- Serialization helpers -------------------------------------------------


def _serialize_related(record: dict[str, Any], subsystem_node: Node) -> dict[str, Any]:
    relationship: Relationship = record["relationship"]
    node: Node = record["node"]
    direction = (
        "OUT"
        if relationship.start_node.element_id == subsystem_node.element_id
        else "IN"
    )
    return {
        "relationship": relationship.type,
        "direction": direction,
        "target": _serialize_node(node),
    }


def _serialize_node(node: Node) -> dict[str, Any]:
    return {
        "id": _canonical_node_id(node),
        "labels": list(node.labels),
        "properties": dict(node),
    }


def _serialize_relationship(record: dict[str, Any]) -> dict[str, Any]:
    relationship: Relationship = record["relationship"]
    node: Node = record["node"]
    if relationship.end_node.element_id == node.element_id:
        direction = "OUT"
    elif relationship.start_node.element_id == node.element_id:
        direction = "IN"
    else:  # pragma: no cover - fallback for undirected or unexpected shapes
        direction = "BOTH"
    return {
        "type": relationship.type,
        "direction": direction,
        "target": _serialize_node(node),
    }


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Node):
        return _serialize_node(value)
    if isinstance(value, Relationship):
        return {
            "type": value.type,
            "start": _canonical_node_id(value.start_node),
            "end": _canonical_node_id(value.end_node),
            "properties": dict(value),
        }
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _canonical_node_id(node: Node) -> str:
    labels = list(node.labels)
    props = dict(node)
    if "Subsystem" in labels and "name" in props:
        return f"Subsystem:{props['name']}"
    if "DesignDoc" in labels and "path" in props:
        return f"DesignDoc:{props['path']}"
    if "SourceFile" in labels and "path" in props:
        return f"SourceFile:{props['path']}"
    if "TestCase" in labels and "path" in props:
        return f"TestCase:{props['path']}"
    if "Chunk" in labels and "chunk_id" in props:
        return f"Chunk:{props['chunk_id']}"
    return node.element_id


def _parse_node_id(node_id: str) -> tuple[str, str, str]:
    if ":" not in node_id:
        raise GraphQueryError("Invalid node identifier")
    label, value = node_id.split(":", 1)
    label = label.strip()
    value = value.strip()
    key_map = {
        "Subsystem": "name",
        "DesignDoc": "path",
        "SourceFile": "path",
        "TestCase": "path",
        "Chunk": "chunk_id",
    }
    key = key_map.get(label)
    if key is None:
        raise GraphQueryError(f"Unsupported node label '{label}'")
    return label, key, value


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:  # pragma: no cover - invalid cursor falls back to 0
        return 0


def _validate_cypher(query: str) -> None:
    forbidden = {"CREATE", "MERGE", "DELETE", "SET", "DROP", "REMOVE"}
    normalized = query.upper()
    if any(keyword in normalized for keyword in forbidden):
        raise GraphQueryError("Only read-only Cypher is permitted")
    if "RETURN" not in normalized:
        raise GraphQueryError("Cypher query must include RETURN")
    if "LIMIT" not in normalized:
        raise GraphQueryError("Cypher query must include LIMIT")
