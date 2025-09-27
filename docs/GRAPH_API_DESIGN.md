# Graph API Surface Design

This document specifies the read-only HTTP interface that exposes graph insights derived from the ingestion pipeline. It expands the outline in `docs/KNOWLEDGE_MANAGEMENT_DESIGN.md §6.3` with precise routes, payloads, and authorization requirements.

## 1. Design Principles
- **Read-only:** Graph APIs never mutate Neo4j data. Writes remain confined to ingestion jobs.
- **Scoped access:** Reader tokens may fetch subsystem/asset context; maintainer tokens are required for raw Cypher execution and debugging utilities.
- **Deterministic payloads:** Responses always include node identifiers, human-readable labels, and provenance references (source file path, commit hash) where applicable.
- **Pagination:** Endpoints that can return large edge sets support cursor-based pagination to avoid overwhelming clients.
- **Error transparency:** All endpoints surface precise error codes (`404` for missing nodes, `400` for invalid parameters, `429` for rate limits, `503` for backend unavailability).

## 2. Authentication & Rate Limits
- Routes inherit bearer-token enforcement (`KM_AUTH_ENABLED=true`).
- Default rate limit: `60 requests / 60 seconds` shared with other reader endpoints; maintainer-only routes retain the stricter `30/minute` throttle.
- When auth is disabled (`KM_AUTH_MODE=insecure`), endpoints remain accessible for local testing but log warnings.

## 3. Endpoints

### 3.1 `GET /graph/subsystems/{name}` *(Reader scope)*
Returns rich context for a named subsystem.

**Query Parameters**
- `depth` (int, default `1`): how many hops to traverse for related subsystems.
- `includeArtifacts` (bool, default `true`): whether to embed associated documents/tests within the response.
- `cursor` (string, optional): pagination cursor for large neighbor sets.
- `limit` (int, 1-100, default `25`): page size for related nodes/edges.

**Response**
```json
{
  "subsystem": {
    "id": "Subsystem:telemetry",
    "name": "telemetry",
    "description": "Streams sensor data to processing cluster",
    "repo_head": "a1b2c3",
    "metadata": {"owner": "observability"}
  },
  "related": {
    "nodes": [
      {"id": "Subsystem:analytics", "name": "analytics", "relationship": "DEPENDS_ON"}
    ],
    "cursor": "opaque-cursor-or-null"
  },
  "artifacts": [
    {
      "id": "SourceFile:src/telemetry/ingest.py",
      "path": "src/telemetry/ingest.py",
      "repo_head": "a1b2c3",
      "chunk_ids": ["chunk:abc"],
      "doc_refs": ["docs/design/telemetry.md"],
      "last_updated": "2025-09-12T15:03:00Z"
    }
  ]
}
```

**Errors**
- `404` when subsystem not found.
- `400` when `depth` exceeds configured maximum (default `3`).

### 3.2 `GET /graph/nodes/{nodeId}` *(Reader scope)*
Fetches a single node by compound identifier (`Label:identifier`). Supports generic inspection of files, tests, design docs, etc.

**Query Parameters**
- `relationships` (`incoming|outgoing|all`, default `outgoing`): which edges to return.
- `limit` (int, default `50`): maximum edges per direction.

**Response**
```json
{
  "node": {
    "id": "SourceFile:src/telemetry/ingest.py",
    "labels": ["SourceFile"],
    "properties": {"path": "src/telemetry/ingest.py", "subsystem": "telemetry"}
  },
  "relationships": [
    {
      "type": "BELONGS_TO",
      "direction": "OUT",
      "target": {
        "id": "Subsystem:telemetry",
        "labels": ["Subsystem"],
        "properties": {"name": "telemetry"}
      }
    }
  ]
}
```

**Errors**
- `404` when node cannot be resolved.

### 3.3 `GET /graph/search`
Lightweight search across graph entities, intended for UI autocomplete.

**Query Parameters**
- `q` (string, required): case-insensitive term matched against node names, aliases, or file paths.
- `limit` (int, default `20`)

**Response**
```json
{
  "results": [
    {"id": "Subsystem:telemetry", "label": "Subsystem", "score": 0.92, "snippet": "Telemetry processing subsystem"},
    {"id": "DesignDoc:docs/design/telemetry.md", "label": "DesignDoc", "score": 0.88, "snippet": "Design overview for telemetry"}
  ]
}
```

### 3.4 `POST /graph/cypher` *(Maintainer scope)*
Executes read-only Cypher queries for power users and troubleshooting.

**Request Body**
```json
{
  "query": "MATCH (n:Subsystem)-[r:DEPENDS_ON]->(m) RETURN n, r, m LIMIT 10",
  "parameters": {"limit": 10}
}
```

**Response**
```json
{
  "data": [
    {
      "row": [
        {"id": "Subsystem:telemetry", "labels": ["Subsystem"], "properties": {...}},
        {"type": "DEPENDS_ON", "properties": {}},
        {"id": "Subsystem:analytics", "labels": ["Subsystem"], "properties": {...}}
      ]
    }
  ],
  "summary": {
    "resultConsumedAfterMs": 5,
    "database": "knowledge"
  }
}
```

**Constraints**
- Only `MATCH`, `RETURN`, `WITH`, `UNWIND`, `ORDER BY`, `LIMIT` clauses allowed (enforced with allowlist regex).
- `LIMIT` is required and clamped to `100` to protect the database.
- `400` when query fails validation; `500` when Neo4j raises runtime errors.

### 3.5 Future (Deferred) Endpoint Ideas
- `GET /graph/coverage/{subsystem}`: overlay coverage stats per subsystem.
- `POST /graph/path`: compute shortest path between two nodes.
- `GET /graph/stats`: expose summary counts for dashboards.

## 4. Pagination Format
Cursor responses follow the pattern:
```json
{
  "cursor": "base64-encoded-state",
  "hasMore": true
}
```
Clients pass the opaque `cursor` query parameter to fetch the next page. The server encodes last seen node id + depth to avoid duplicates. If `hasMore=false`, omit `cursor`.

## 5. Error Model
All graph endpoints return:
```json
{
  "detail": "Human readable message",
  "error_code": "GRAPH_NODE_NOT_FOUND"
}
```
`error_code` values are stable strings (e.g., `GRAPH_NODE_NOT_FOUND`, `GRAPH_QUERY_INVALID`, `GRAPH_SEARCH_TOO_BROAD`).

## 6. Logging & Metrics
- Each endpoint increments `km_graph_requests_total{route="...",status="success|failure"}` (new counter added in implementation phase).
- For Cypher executions, log query hashes (not full text) to avoid leaking sensitive data while maintaining traceability.

## 7. Security Considerations
- Sanitize user-controlled values before injecting into Cypher (parameterized queries).
- Enforce maximum depth and limit to mitigate query explosion.
- Ensure responses redact Neo4j internal identifiers, only exposing canonical IDs derived from ingestion metadata.
- Include rate-limit headers to help clients back off when necessary.

## 8. Implementation Notes
- Reuse existing Neo4j driver sessions within request lifespan (FastAPI dependency).
- Add helper in `gateway/graph/service.py` to centralize query building and pagination.
- Unit test with Neo4j test double (e.g., `neo4j.fake_graph` or custom stub) to avoid integration test flakiness.
- For integration tests, use temporary Neo4j container or in-memory driver configured via `neo4j.testkit` (if available); otherwise, mark as optional pending test infrastructure.

## 9. Schema Migrations & Tooling
- Migrations live under `gateway/graph/migrations/` and are executed by `MigrationRunner` using Cypher statements.
- Applied migrations are tracked in Neo4j via `(:MigrationHistory {id, applied_at})` nodes to ensure idempotency. Each migration ID is stored once, so history growth is bounded; if a rollback removes a migration from the codebase, delete the corresponding history node via `MATCH (m:MigrationHistory {id: 'xyz'}) DETACH DELETE m` to keep the ledger tidy (record the decision in release notes).
- Run `gateway-graph migrate` to apply pending migrations (supports `--dry-run` to list operations).
- The packaged container exports `KM_GRAPH_AUTO_MIGRATE=true`, so API startup performs a preflight (`pending_ids`) summary, logs IDs to be applied, and reports completion (or no-op) results. Failures emit stack traces but do not block the service from serving requests.
- Production deployments may prefer to leave `KM_GRAPH_AUTO_MIGRATE` unset/`false` and invoke `gateway-graph migrate` as an explicit pipeline step to retain change-control windows.
- Observability: the API now emits `km_graph_migration_last_status` (1=success, 0=failure, -1=skipped) and `km_graph_migration_last_timestamp` gauges so dashboards can track migration health.

### Rollback Procedure
When a migration must be reversed after deployment:
1. **Freeze Auto-Migrate:** Set `KM_GRAPH_AUTO_MIGRATE=false` (or remove it) on all running instances to prevent reapplication during rollback.
2. **Revert Domain Changes:** Apply the inverse Cypher statements for the migration (drop constraints/indices, delete relationships, etc.). Store rollback scripts alongside the original migration file for traceability.
3. **Prune History Node:** Remove the applied marker so future deploys can run the migration again once fixed: `MATCH (m:MigrationHistory {id: '002_new_edges'}) DETACH DELETE m`.
4. **Validate:** Execute the Neo4j validation harness (`pytest -m neo4j`) and run `gateway-graph migrate --dry-run` to ensure the migration reappears as pending.
5. **Re-enable Auto-Migrate (Optional):** Once stable, reintroduce `KM_GRAPH_AUTO_MIGRATE=true` for turnkey environments.

## 10. Search Response Enrichment
- `/search` results (vector or hybrid) attach a `graph_context` block per hit when graph data is available.
- Response shape:
  ```json
  {
    "query": "telemetry ingest latency",
    "results": [
      {
        "chunk": {
          "id": "chunk:abc123",
          "text": "...",
          "artifact_path": "src/telemetry/ingest.py",
          "artifact_type": "code",
          "score": 0.87
        },
        "graph_context": {
          "primary_node": {
            "id": "SourceFile:src/telemetry/ingest.py",
            "labels": ["SourceFile"],
            "properties": {"subsystem": "telemetry"}
          },
          "relationships": [
            {
              "type": "BELONGS_TO",
              "direction": "OUT",
              "target": {
                "id": "Subsystem:telemetry",
                "labels": ["Subsystem"],
                "properties": {"name": "telemetry"}
              }
            }
          ],
          "neighbor_subsystems": ["analytics", "alerting"],
          "related_artifacts": [
            {
              "id": "DesignDoc:docs/design/telemetry.md",
              "relationship": "DESCRIBES"
            }
          ]
        }
      }
    ],
    "metadata": {
      "result_count": 1,
      "graph_context_included": true,
      "warnings": [],
      "scoring_mode": "ml"
    }
  }
  ```
- Filters appear in `metadata.filters_applied` so downstream agents can reason about constrained result sets.

## 11. Search Filters
- Optional filters narrow the candidate set before scoring while preserving graph-based enrichment.
- Request payload additions:
  ```json
  {
    "query": "telemetry latency",
    "limit": 10,
    "filters": {
      "subsystems": ["Telemetry", "Analytics"],
      "artifact_types": ["code", "doc"],
      "namespaces": ["src", "docs"],
      "tags": ["LeylineAlpha", "TelemetrySignal"],
      "updated_after": "2024-09-01T00:00:00Z",
      "max_age_days": 45
    }
  }
  ```
- Validation rules:
  - `filters` must be an object. Unknown keys are ignored for forward compatibility.
  - `subsystems` is an array of strings (case-insensitive). If chunk metadata lacks a subsystem match, the service falls back to graph context (primary node + neighbour subsystems) when available; otherwise the chunk is excluded.
  - `artifact_types` is an array of strings drawn from the ingestion taxonomy (`code`, `doc`, `test`, `proto`, `config`). Invalid entries result in `422`.
  - `namespaces` is an array of strings matched against each chunk’s derived namespace (top-level directory, with `src/<name>` collapsing to `<name>`). Comparisons are case-insensitive.
  - `tags` is an array of strings. Each chunk exposes a normalised tag set combining Leyline entities, telemetry signals, and optional subsystem metadata tags; at least one overlap (case-insensitive) is required when the filter is present.
  - `updated_after` accepts an ISO-8601 timestamp (string). Only artifacts whose git or graph timestamp is on/after the supplied value are returned. Timestamps are normalised to UTC internally.
  - `max_age_days` accepts a positive integer. Results older than the specified number of days relative to the request time are dropped. When both `updated_after` and `max_age_days` are provided, the stricter (most recent) cutoff wins.
  - Filters combine via logical AND. Absence of `filters` preserves existing behaviour.
- Response metadata includes `filters_applied` with the resolved subsets so dashboards and logs can correlate behaviour.
- When recency filters exclude chunks that lack timestamps, the response carries a warning (`"recency filter skipped results lacking timestamps"`) so MCP clients can trace why candidates disappeared.
- Retrieval flow per result:
  1. Use chunk metadata (`artifact_path`) to derive canonical node id (e.g., `SourceFile:{path}`).
  2. Call `GraphService.get_node(..., relationships="outgoing", limit=10)` to fetch the primary node and neighbours.
  3. Summarise related subsystems (`neighbor_subsystems` set) and design/test artifacts linked via DESCRIBES/VALIDATES edges.
  4. If graph connectivity fails (driver unavailable or node missing), set `graph_context=null` and append a warning explaining the omission.
- Pagination/limit controls for `/search` remain unchanged. Graph lookups should honour a configurable timeout (default 250 ms per chunk) to avoid delaying responses.
- Future enhancement: include shortest path snippets when users request `mode=explain` (deferred).

## 11. Validation Harness
- An integration test (`tests/test_graph_validation.py`) exercises ingestion against a live Neo4j instance. It is marked with `@pytest.mark.neo4j` and skipped unless `NEO4J_TEST_URI` (and optional user/password/database env vars) are defined.
- Run locally with:
  ```bash
  NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=yourpass pytest -m neo4j
  ```
- CI jobs may opt in by enabling the `neo4j` marker; the test clears the database, runs migrations, executes ingestion with dummy embeddings, and asserts design documents and chunks are persisted.

## 12. Graph-Aware Search Signals (Phase 1)
Upcoming scoring enhancements will combine vector similarity with graph-derived signals. The initial signal inventory includes:

- **Subsystem affinity** – boost when the chunk’s owning subsystem matches an explicit query filter or appears in the free-text query (detected via simple keyword heuristics).
- **Relationship richness** – count of outgoing edges (DESCRIBES, VALIDATES, BELONGS_TO) attached to the primary node; higher connectivity indicates authoritative artifacts.
- **Cross-artifact support** – presence of linked design docs or test cases referencing the chunk (e.g., DESCRIBES/VALIDATES edges) yields additional confidence.
- **Graph proximity to critical nodes** – distance (1 hop vs >1) to flagged subsystems (e.g., safety-critical components) can apply additive boosts or penalties.
- **Coverage status** – if the coverage report marks the artifact as missing/unparsed, apply a slight penalty to surface better-covered results first.
- **Graph availability flag** – if graph context is unavailable (driver offline, node missing), retain baseline vector score and annotate metadata so downstream consumers can react.

The scoring specification will combine these signals into an `adjusted_score` alongside the raw vector similarity. Subsequent phases will tune coefficients, add configuration knobs, and expose debug metadata. This section captures the agreed signal set so implementation work can proceed without ambiguity.

### Scoring Model (LLM-Friendly Design)

Because the senior operator is an MCP-connected LLM, the ranking heuristic must be deterministic, auditable, and accompanied by machine-readable explanations. We will compute:

    adjusted_score = vector_score
                   + w_subsystem      * subsystem_affinity
                   + w_relationship   * min(relationship_count, 5)
                   + w_support        * supporting_artifact_bonus
                   - w_coverage_penalty * uncovered_flag

- `vector_score` — normalized similarity returned by Qdrant.
- `subsystem_affinity` — `1.0` when the query explicitly references the subsystem (filter or keyword), `0.5` for implicit matches inferred via heuristics, `0` otherwise.
- `relationship_count` — number of BELONGS_TO/DESCRIBES/VALIDATES edges from the primary node, capped at 5 to prevent runaway boosts.
- `supporting_artifact_bonus` — `0.2` for each linked design doc and `0.1` for each linked test case (capped at two of each to maintain balance).
- `uncovered_flag` — `1` when coverage reports mark the artifact as missing/unparsed, otherwise `0`.
- `path_depth` — heuristic distance from chunk node to subsystem root (0 when depth is unknown).
- `subsystem_criticality` — normalised value (0–1) derived from optional subsystem metadata (e.g., `docs/subsystems.json`).
- `freshness_days` — derived from git timestamps, indicating how long ago the source artifact changed.
- `coverage_ratio` — percentage of coverage surfaced for the artifact (defaults to 1.0 when chunks exist, 0.0 otherwise).
- Default weights: `w_subsystem=0.30`, `w_relationship=0.05`, `w_support=0.10`, `w_coverage_penalty=0.15`. Operators can switch among curated bundles (`default`, `analysis`, `operations`, `docs-heavy`) with `KM_SEARCH_WEIGHT_PROFILE`; individual overrides remain available via the `KM_SEARCH_W_*` variables and should stay within `[0, 1]` for predictability.

Implementation guidance:

- Include `vector_score`, `adjusted_score`, and a `scoring_breakdown` object in each `/search` result so LLM agents can reason about and explain the ranking. When ML mode is active (`KM_SEARCH_SCORING_MODE=ml`), expose `scoring.mode="ml"` and add `scoring.model` with per-feature contributions and the intercept.
- Set `metadata.scoring_mode` to the active mode (`heuristic` or `ml`) so downstream agents can select the appropriate reconciliation strategy.
- When graph context is unavailable the service must fall back to `adjusted_score = vector_score` while logging a warning and setting `graph_context_included=false` for transparency.
- Cache graph lookups per artifact during a single search request to limit Cypher calls.
- Expose a feature flag to disable graph boosts if operators need pure vector ranking for debugging.
- When `KM_SEARCH_SCORING_MODE=ml` is configured but the model file is missing or incompatible, the service logs a warning and continues in heuristic mode to avoid outages.
- Future iterations may incorporate path-based boosts or learned ranking, but this initial heuristic prioritizes interpretability for agentic consumers.

This design will guide the upcoming WP4 implementation tasks.

### Telemetry Hooks

- Each `/search` request now seeds a JSONL event in `/opt/knowledge/var/feedback/events.log` capturing the request identifier, query, per-result scoring breakdown, and any MCP-provided relevance vote or context payload.
- The API response exposes `metadata.request_id` so downstream agents can correlate subsequent feedback or audit trails with the recorded event.
- Operators can tail this file to inspect scoring behaviour, bootstrap training datasets, or debug agent dissatisfaction (combine with the forthcoming Phase 2 export tooling).
