"""Read-only graph service utilities backed by Neo4j."""

from __future__ import annotations

import base64
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any, TypeVar, cast

from neo4j import Driver, ManagedTransaction, Session
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from neo4j.graph import Node, Relationship

from gateway.observability.metrics import GRAPH_CYPHER_DENIED_TOTAL

T = TypeVar("T")


class GraphServiceError(RuntimeError):
    """Base class for graph-related errors."""


class GraphNotFoundError(GraphServiceError):
    """Raised when a requested node cannot be found."""


class GraphQueryError(GraphServiceError):
    """Raised when a supplied query is invalid or unsafe."""


@dataclass(slots=True)
class SubsystemGraphSnapshot:
    """Snapshot of a subsystem node and its related graph context."""

    subsystem: dict[str, Any]
    related: list[dict[str, Any]]
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]


ORPHAN_DEFAULT_LABELS: tuple[str, ...] = (
    "DesignDoc",
    "SourceFile",
    "Chunk",
    "TestCase",
    "IntegrationMessage",
)


class SubsystemGraphCache:
    """Simple TTL cache for subsystem graph snapshots."""

    def __init__(self, ttl_seconds: float, max_entries: int) -> None:
        """Create a cache with an expiry window and bounded size."""
        self._ttl = max(0.0, ttl_seconds)
        self._max_entries = max(1, max_entries)
        self._entries: OrderedDict[tuple[str, int], tuple[float, SubsystemGraphSnapshot]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: tuple[str, int]) -> SubsystemGraphSnapshot | None:
        """Return a cached snapshot if it exists and has not expired."""
        if self._ttl <= 0:
            return None
        now = monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, snapshot = entry
            if expires_at <= now:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return snapshot

    def set(self, key: tuple[str, int], snapshot: SubsystemGraphSnapshot) -> None:
        """Cache a snapshot for the given key, evicting oldest entries if needed."""
        if self._ttl <= 0:
            return
        expires_at = monotonic() + self._ttl
        with self._lock:
            self._entries[key] = (expires_at, snapshot)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        """Remove all cached subsystem snapshots."""
        with self._lock:
            self._entries.clear()


class GraphService:
    """Service layer for read-only graph queries."""

    __slots__ = (
        "_driver_provider",
        "_readonly_provider",
        "_failure_callback",
        "database",
        "subsystem_cache",
    )

    def __init__(
        self,
        driver_provider: Callable[[], Driver],
        database: str,
        *,
        cache_ttl: float | None = None,
        cache_max_entries: int = 128,
        readonly_provider: Callable[[], Driver] | None = None,
        failure_callback: Callable[[Exception], None] | None = None,
    ) -> None:
        self._driver_provider = driver_provider
        self._readonly_provider = readonly_provider
        self._failure_callback = failure_callback
        self.database = database
        self.subsystem_cache = SubsystemGraphCache(cache_ttl, cache_max_entries) if cache_ttl is not None and cache_ttl > 0 else None

    def clear_cache(self) -> None:
        """Wipe the subsystem snapshot cache if caching is enabled."""
        if self.subsystem_cache is not None:
            self.subsystem_cache.clear()

    def _get_driver(self, *, readonly: bool = False) -> Driver:
        if readonly and self._readonly_provider is not None:
            return self._readonly_provider()
        return self._driver_provider()

    def _execute(self, operation: Callable[[Driver], T], *, readonly: bool = False) -> T:
        attempts = 2 if self._failure_callback is not None else 1
        for attempt in range(attempts):
            driver = self._get_driver(readonly=readonly)
            try:
                return operation(driver)
            except GraphServiceError:
                raise
            except (Neo4jError, ServiceUnavailable, OSError) as exc:
                if self._failure_callback is not None:
                    self._failure_callback(exc)
                if attempt == attempts - 1:
                    raise
        raise RuntimeError("unreachable")

    def _run_with_session(
        self,
        operation: Callable[[Session], T],
        *,
        readonly: bool = False,
        **session_kwargs: object,
    ) -> T:
        def _invoke(driver: Driver) -> T:
            kwargs = {"database": self.database}
            kwargs.update(session_kwargs)
            with driver.session(**kwargs) as session:
                return operation(session)

        return self._execute(_invoke, readonly=readonly)

    def get_subsystem(
        self,
        name: str,
        *,
        depth: int,
        limit: int,
        cursor: str | None,
        include_artifacts: bool,
    ) -> dict[str, Any]:
        """Return a windowed view of related nodes for the requested subsystem."""
        offset = max(0, _decode_cursor(cursor))
        limit = max(1, limit)
        snapshot = self._load_subsystem_snapshot(name, depth)

        related = snapshot.related
        total = len(related)
        window = related[offset : offset + limit]
        next_cursor = None
        if offset + limit < total:
            next_cursor = _encode_cursor(offset + limit)

        artifacts = snapshot.artifacts if include_artifacts else []

        return {
            "subsystem": snapshot.subsystem,
            "related": {
                "nodes": window,
                "cursor": next_cursor,
                "total": total,
            },
            "artifacts": artifacts,
        }

    def get_subsystem_graph(self, name: str, *, depth: int) -> dict[str, Any]:
        """Return the full node/edge snapshot for a subsystem."""
        snapshot = self._load_subsystem_snapshot(name, depth)
        return {
            "subsystem": snapshot.subsystem,
            "nodes": snapshot.nodes,
            "edges": snapshot.edges,
            "artifacts": snapshot.artifacts,
        }

    def list_orphan_nodes(
        self,
        *,
        label: str | None,
        cursor: str | None,
        limit: int,
    ) -> dict[str, Any]:
        """List nodes that have no relationships of the allowed labels."""
        if label and label not in ORPHAN_DEFAULT_LABELS:
            raise GraphQueryError(f"Unsupported orphan label '{label}'")
        offset = max(0, _decode_cursor(cursor))
        limit = max(1, limit)

        records = self._run_with_session(
            lambda session: session.execute_read(
                _fetch_orphan_nodes,
                label,
                offset,
                limit,
            ),
            readonly=True,
        )
        nodes = [_serialize_node(record) for record in records]
        next_cursor = None
        if len(nodes) == limit:
            next_cursor = _encode_cursor(offset + limit)
        return {"nodes": nodes, "cursor": next_cursor}

    def _load_subsystem_snapshot(self, name: str, depth: int) -> SubsystemGraphSnapshot:
        depth = max(1, depth)
        cache_key = (name, depth)
        if self.subsystem_cache is not None:
            cached = self.subsystem_cache.get(cache_key)
            if cached is not None:
                return cached
        snapshot = self._build_subsystem_snapshot(name, depth)
        if self.subsystem_cache is not None:
            self.subsystem_cache.set(cache_key, snapshot)
        return snapshot

    def _build_subsystem_snapshot(self, name: str, depth: int) -> SubsystemGraphSnapshot:
        def _op(session: Session) -> tuple[Node, Sequence[Mapping[str, Any]], Sequence[Node]]:
            subsystem_node = session.execute_read(_fetch_subsystem_node, name)
            if subsystem_node is None:
                raise GraphNotFoundError(f"Subsystem '{name}' not found")
            resolved_node = _ensure_node(subsystem_node)
            path_records = session.execute_read(
                _fetch_subsystem_paths,
                name,
                depth,
            )
            artifact_records = session.execute_read(_fetch_artifacts_for_subsystem, name)
            return resolved_node, path_records, artifact_records

        subsystem_node, path_records, artifact_records = self._run_with_session(
            _op,
            readonly=True,
        )

        subsystem_serialized = _serialize_node(subsystem_node)
        nodes_by_id: OrderedDict[str, dict[str, Any]] = OrderedDict()
        nodes_by_id[subsystem_serialized["id"]] = subsystem_serialized
        edges_by_key: OrderedDict[tuple[str, str, str], dict[str, Any]] = OrderedDict()
        related_entries: list[dict[str, Any]] = []
        related_order: list[str] = []

        for record in path_records:
            components = _extract_path_components(record)
            if components is None:
                continue
            target_node_obj, path_nodes, relationships = components

            path_edges = _record_path_edges(path_nodes, relationships, nodes_by_id, edges_by_key)
            if not path_edges:
                continue

            target_serialized = _ensure_serialized_node(target_node_obj, nodes_by_id)
            entry = _build_related_entry(target_serialized, relationships, path_edges)
            _append_related_entry(entry, target_serialized["id"], related_entries, related_order)

        artifacts = [_serialize_node(_ensure_node(node)) for node in artifact_records]

        return SubsystemGraphSnapshot(
            subsystem=subsystem_serialized,
            related=related_entries,
            nodes=list(nodes_by_id.values()),
            edges=list(edges_by_key.values()),
            artifacts=artifacts,
        )

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:
        """Return a node and a limited set of relationships using Cypher lookups."""
        label, key, value = _parse_node_id(node_id)

        def _op(session: Session) -> tuple[Node, list[dict[str, Any]]]:
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
            return node, rels

        node, rels = self._run_with_session(_op, readonly=True)

        return {
            "node": _serialize_node(node),
            "relationships": rels,
        }

    def search(self, term: str, *, limit: int) -> dict[str, Any]:
        """Search the graph for nodes matching the provided term."""
        if not term.strip():
            return {"results": []}
        lower_term = term.lower()
        records = self._run_with_session(
            lambda session: session.execute_read(_search_entities, lower_term, limit),
            readonly=True,
        )
        results = [
            {
                "id": _canonical_node_id(_ensure_node(record["node"])),
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
            record = self._run_with_session(
                lambda session: session.run(query, value=value).single(),
                readonly=True,
            )
        except (Neo4jError, ServiceUnavailable, OSError) as exc:  # pragma: no cover - driver failure
            raise GraphServiceError(str(exc)) from exc
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
        parameters: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an arbitrary Cypher query and serialize the response."""
        _validate_cypher(query)
        params = parameters or {}
        try:
            result = self._execute(
                lambda driver: driver.execute_query(
                    query,
                    parameters=params,
                    database_=self.database,
                ),
                readonly=True,
            )
        except (Neo4jError, ServiceUnavailable, OSError) as exc:  # pragma: no cover - driver errors wrapped
            raise GraphQueryError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive guard
            raise GraphQueryError(str(exc)) from exc

        summary = result.summary
        if summary is not None:
            counters = getattr(summary, "counters", None)
            if counters:
                contains_updates = getattr(counters, "contains_updates", None)
                if callable(contains_updates):
                    has_updates = bool(contains_updates())
                elif isinstance(contains_updates, bool):
                    has_updates = contains_updates
                else:  # pragma: no cover - fallback for older driver variants
                    update_fields = [
                        "nodes_created",
                        "nodes_deleted",
                        "relationships_created",
                        "relationships_deleted",
                        "properties_set",
                        "labels_added",
                        "labels_removed",
                        "indexes_added",
                        "indexes_removed",
                        "constraints_added",
                        "constraints_removed",
                    ]
                    has_updates = any(getattr(counters, field, 0) for field in update_fields)
                if has_updates:
                    _deny_cypher("mutation", "Only read-only Cypher queries are permitted")

        data = [
            {
                "row": [_serialize_value(value) for value in record.values()],
            }
            for record in result.records
        ]
        consumed_ms = None
        if summary and summary.result_available_after is not None:
            consumed_ms = summary.result_available_after

        database_name = self.database
        if summary is not None:
            db_info = getattr(summary, "database", None)
            db_name = getattr(db_info, "name", None)
            if isinstance(db_name, str):
                database_name = db_name

        return {
            "data": data,
            "summary": {
                "resultConsumedAfterMs": consumed_ms,
                "database": database_name,
            },
        }


def get_graph_service(
    driver: Driver | Callable[[], Driver],
    database: str,
    *,
    cache_ttl: float | None = None,
    cache_max_entries: int = 128,
    readonly_driver: Driver | Callable[[], Driver] | None = None,
    failure_callback: Callable[[Exception], None] | None = None,
) -> GraphService:
    """Factory helper that constructs a `GraphService` with optional caching."""

    def _ensure_provider(candidate: Driver | Callable[[], Driver]) -> Callable[[], Driver]:
        if callable(candidate):
            return cast(Callable[[], Driver], candidate)
        driver_obj = candidate
        return lambda: driver_obj

    driver_provider = _ensure_provider(driver)
    readonly_provider = None
    if readonly_driver is not None:
        readonly_provider = _ensure_provider(readonly_driver)

    return GraphService(
        driver_provider=driver_provider,
        database=database,
        cache_ttl=cache_ttl,
        cache_max_entries=cache_max_entries,
        readonly_provider=readonly_provider,
        failure_callback=failure_callback,
    )


def _extract_path_components(
    record: Mapping[str, Any],
) -> tuple[Node, Sequence[Node], Sequence[Relationship]] | None:
    target_node = record.get("node")
    if not isinstance(target_node, Node):
        return None

    path_nodes_raw = record.get("nodes")
    if not isinstance(path_nodes_raw, list):
        return None
    path_nodes: list[Node] = [node for node in path_nodes_raw if isinstance(node, Node)]
    if len(path_nodes) != len(path_nodes_raw) or len(path_nodes) < 2:
        return None

    relationships_raw = record.get("relationships")
    if not isinstance(relationships_raw, list):
        return None
    relationships: list[Relationship] = [rel for rel in relationships_raw if isinstance(rel, Relationship)]
    if len(relationships) != len(relationships_raw) or not relationships:
        return None
    if len(path_nodes) != len(relationships) + 1:
        return None

    return target_node, path_nodes, relationships


def _record_path_edges(
    path_nodes: Sequence[Node],
    relationships: Sequence[Relationship],
    nodes_by_id: OrderedDict[str, dict[str, Any]],
    edges_by_key: OrderedDict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    path_edges: list[dict[str, Any]] = []
    for idx, relationship in enumerate(relationships):
        source_node = path_nodes[idx]
        target_node = path_nodes[idx + 1]
        source_serialized = _ensure_serialized_node(source_node, nodes_by_id)
        target_serialized = _ensure_serialized_node(target_node, nodes_by_id)
        direction = _relationship_direction(relationship, source_node)
        edge_payload = {
            "type": relationship.type,
            "direction": direction,
            "source": source_serialized["id"],
            "target": target_serialized["id"],
        }
        edge_key = (
            source_serialized["id"],
            target_serialized["id"],
            relationship.type,
        )
        if edge_key not in edges_by_key:
            edges_by_key[edge_key] = edge_payload
        path_edges.append(edge_payload)
    return path_edges


def _ensure_serialized_node(
    node: Node,
    nodes_by_id: OrderedDict[str, dict[str, Any]],
) -> dict[str, Any]:
    node_id = _canonical_node_id(node)
    if node_id not in nodes_by_id:
        nodes_by_id[node_id] = _serialize_node(node)
    return nodes_by_id[node_id]


def _relationship_direction(relationship: Relationship, source_node: Node) -> str:
    start_element = _node_element_id(relationship.start_node)
    return "OUT" if start_element == source_node.element_id else "IN"


def _build_related_entry(
    target_serialized: dict[str, Any],
    relationships: Sequence[Relationship],
    path_edges: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "target": target_serialized,
        "hops": len(relationships),
        "path": list(path_edges),
        "relationship": path_edges[0]["type"],
        "direction": path_edges[0]["direction"],
    }


def _append_related_entry(
    entry: dict[str, Any],
    target_id: str,
    related_entries: list[dict[str, Any]],
    related_order: list[str],
) -> None:
    if target_id in related_order:
        return
    related_entries.append(entry)
    related_order.append(target_id)


# --- Neo4j read helpers ----------------------------------------------------


def _fetch_subsystem_node(tx: ManagedTransaction, /, name: str) -> Node | None:
    result = tx.run("MATCH (s:Subsystem {name: $name}) RETURN s LIMIT 1", name=name)
    record = result.single()
    return record["s"] if record else None


def _fetch_subsystem_paths(
    tx: ManagedTransaction,
    /,
    name: str,
    depth: int,
) -> list[dict[str, Any]]:
    bounded_depth = max(1, int(depth))
    depth_clause = f"[rel*1..{bounded_depth}]"
    query = (
        "MATCH p=(s:Subsystem {name: $name})-"
        f"{depth_clause}"
        "-(n) "
        "WHERE n <> s "
        "WITH n, p "
        "ORDER BY length(p) ASC "
        "WITH n, collect(p) AS paths "
        "WITH n, head(paths) AS path "
        "RETURN n AS node, nodes(path) AS nodes, relationships(path) AS relationships "
        "ORDER BY coalesce(n.name, n.title, n.path, elementId(n))"
    )
    result = tx.run(query, name=name)
    return [
        {
            "node": record["node"],
            "nodes": record["nodes"],
            "relationships": record["relationships"],
        }
        for record in result
    ]


def _fetch_artifacts_for_subsystem(tx: ManagedTransaction, /, name: str) -> list[Node]:
    query = (
        "MATCH (artifact)-[rel]->(s:Subsystem {name: $name}) "
        "WHERE type(rel) IN ['BELONGS_TO', 'DESCRIBES', 'VALIDATES'] "
        "RETURN artifact ORDER BY artifact.path LIMIT 200"
    )
    result = tx.run(query, name=name)
    return [record["artifact"] for record in result]


def _fetch_orphan_nodes(
    tx: ManagedTransaction,
    /,
    label: str | None,
    skip: int,
    limit: int,
) -> list[Node]:
    params: dict[str, Any] = {
        "allowed": ORPHAN_DEFAULT_LABELS,
        "skip": max(0, int(skip)),
        "limit": max(1, int(limit)),
    }
    clauses = [
        "MATCH (n)",
        "WHERE any(l IN labels(n) WHERE l IN $allowed)",
        "  AND NOT (n)-[:BELONGS_TO|DESCRIBES|VALIDATES]->(:Subsystem)",
    ]
    if label:
        params["label"] = label
        clauses.append("  AND $label IN labels(n)")
    clauses.append("RETURN n ORDER BY coalesce(n.name, n.title, n.path, elementId(n)) SKIP $skip LIMIT $limit")
    query = " ".join(clauses)
    result = tx.run(query, parameters=params)
    return [record["n"] for record in result]


def _fetch_node_by_id(tx: ManagedTransaction, /, label: str, key: str, value: object) -> Node | None:
    query = f"MATCH (n:{label} {{{key}: $value}}) RETURN n LIMIT 1"
    record = tx.run(query, value=value).single()
    return record["n"] if record else None


def _fetch_node_relationships(
    tx: ManagedTransaction,
    /,
    label: str,
    key: str,
    value: object,
    direction: str,
    limit: int,
) -> list[dict[str, Any]]:
    if direction == "incoming":
        query = f"MATCH (n:{label} {{{key}: $value}})<-[rel]-(other) RETURN rel AS relationship, other AS node LIMIT $limit"
    elif direction == "all":
        query = f"MATCH (n:{label} {{{key}: $value}})-[rel]-(other) RETURN rel AS relationship, other AS node LIMIT $limit"
    else:  # outgoing
        query = f"MATCH (n:{label} {{{key}: $value}})-[rel]->(other) RETURN rel AS relationship, other AS node LIMIT $limit"
    result = tx.run(query, parameters={"value": value, "limit": limit})
    return [{"relationship": record["relationship"], "node": record["node"]} for record in result]


def _search_entities(tx: ManagedTransaction, /, term: str, limit: int) -> list[dict[str, Any]]:
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
    result = tx.run(query, parameters={"term": term, "limit": limit})
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
    relationship = record["relationship"]
    node = _ensure_node(record["node"])
    if isinstance(relationship, Relationship):
        start_element = _node_element_id(relationship.start_node)
        subsystem_element = subsystem_node.element_id
        direction = "OUT" if start_element == subsystem_element else "IN"
        rel_type = relationship.type
    else:  # tolerate legacy tuple/dict encodings emitted by Neo4j drivers
        direction = "OUT"
        rel_type = getattr(relationship, "type", "UNKNOWN")
    return {
        "relationship": rel_type,
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
    relationship = record["relationship"]
    node = _ensure_node(record["node"])
    if isinstance(relationship, Relationship):
        end_element = _node_element_id(relationship.end_node)
        start_element = _node_element_id(relationship.start_node)
        node_element = node.element_id
        if end_element == node_element:
            direction = "OUT"
        elif start_element == node_element:
            direction = "IN"
        else:  # pragma: no cover - fallback for undirected or unexpected shapes
            direction = "BOTH"
        rel_type = relationship.type
    else:  # pragma: no cover - defensive against legacy tuple encodings
        direction = "OUT"
        rel_type = getattr(relationship, "type", "UNKNOWN")
    return {
        "type": rel_type,
        "direction": direction,
        "target": _serialize_node(node),
    }


def _serialize_value(value: object) -> object:
    if isinstance(value, Node):
        return _serialize_node(value)
    if isinstance(value, Relationship):
        return {
            "type": value.type,
            "start": _canonical_node_id(_ensure_node(value.start_node)),
            "end": _canonical_node_id(_ensure_node(value.end_node)),
            "properties": dict(value),
        }
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _ensure_node(value: object) -> Node:
    if not isinstance(value, Node):
        raise GraphServiceError("Expected Neo4j node from query result")
    return value


def _node_element_id(node: Node | None) -> str:
    if node is None:
        raise GraphServiceError("Neo4j relationship missing node reference")
    return node.element_id


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
    sanitized = _strip_literals_and_comments(query)
    upper_query = " ".join(sanitized.upper().split())
    tokens = _tokenize_query(upper_query)

    forbidden_tokens = {
        "CREATE",
        "MERGE",
        "DELETE",
        "DETACH",
        "SET",
        "DROP",
        "REMOVE",
        "ALTER",
        "GRANT",
        "REVOKE",
        "LOAD",
        "CSV",
    }
    if any(token in forbidden_tokens for token in tokens):
        _deny_cypher("keyword", "Only read-only Cypher is permitted")

    for procedure in _extract_procedure_calls(tokens):
        if not any(procedure.startswith(prefix) for prefix in _ALLOWED_PROCEDURE_PREFIXES):
            _deny_cypher("procedure", "CALL to procedure is not permitted in this context")

    normalized = f" {upper_query} "
    if " RETURN " not in normalized:
        _deny_cypher("structure", "Cypher query must include RETURN")
    if " LIMIT " not in normalized:
        _deny_cypher("structure", "Cypher query must include LIMIT")


def _strip_literals_and_comments(query: str) -> str:
    result: list[str] = []
    length = len(query)
    i = 0
    while i < length:
        ch = query[i]
        if ch in {'"', "'", "`"}:
            quote = ch
            result.append(" ")
            i += 1
            while i < length:
                current = query[i]
                if current == "\\" and i + 1 < length:
                    i += 2
                    continue
                if current == quote:
                    i += 1
                    break
                i += 1
            continue
        if ch == "/" and i + 1 < length:
            nxt = query[i + 1]
            if nxt == "/":
                result.append(" ")
                i += 2
                while i < length and query[i] not in {"\n", "\r"}:
                    i += 1
                continue
            if nxt == "*":
                result.append(" ")
                i += 2
                while i + 1 < length and not (query[i] == "*" and query[i + 1] == "/"):
                    i += 1
                i = min(length, i + 2)
                continue
        if ch == "-" and i + 1 < length and query[i + 1] == "-":
            result.append(" ")
            i += 2
            while i < length and query[i] not in {"\n", "\r"}:
                i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _tokenize_query(upper_query: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    for ch in upper_query:
        if ch.isalpha():
            current.append(ch)
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    return tokens


def _extract_procedure_calls(tokens: list[str]) -> list[str]:
    procedures: list[str] = []
    total = len(tokens)
    i = 0
    while i < total:
        if tokens[i] == "CALL":
            proc_tokens: list[str] = []
            j = i + 1
            while j < total:
                token = tokens[j]
                if token in {"YIELD", "RETURN", "WITH", "WHERE"}:
                    break
                proc_tokens.append(token)
                j += 1
            if not proc_tokens:
                _deny_cypher("procedure", "Procedure name missing after CALL")
            procedures.append(".".join(proc_tokens))
            i = j
        else:
            i += 1
    return procedures


_ALLOWED_PROCEDURE_PREFIXES = (
    "DB.SCHEMA.",
    "DB.LABELS",
    "DB.RELATIONSHIPTYPES",
    "DB.INDEXES",
    "DB.CONSTRAINTS",
    "DB.PROPERTYKEYS",
)


def _deny_cypher(reason: str, message: str) -> None:
    try:
        GRAPH_CYPHER_DENIED_TOTAL.labels(reason=reason).inc()
    except Exception:  # pragma: no cover - metric updates should not mask errors
        pass
    raise GraphQueryError(message)
