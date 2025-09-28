# MCP Interface Specification

This specification defines the Model Context Protocol (MCP) surface for the Duskmantle knowledge gateway. Agents (e.g., Codex CLI) interact solely via MCP tools; they never call the HTTP API directly.

## 1. Scope & Authentication
- **Reader operations** (search, graph, coverage) require `KM_READER_TOKEN` or higher.
- **Maintainer operations** (feedback submission, backups, ingest controls) require `KM_ADMIN_TOKEN`.
- The MCP server manages tokens via environment variables (`KM_GATEWAY_URL`, `KM_READER_TOKEN`, `KM_ADMIN_TOKEN`). It attaches the correct bearer token to each gateway call.

## 2. Tool Catalogue

| Tool ID | Scope | Purpose |
|---------|-------|---------|
| `km-help` | reader | Return usage notes for any tool (optionally include the full specification). |
| `km-search` | reader | Hybrid search returning vector hits with scoring/graph context. |
| `km-graph-node` | reader | Fetch a graph node and relationships by canonical ID (e.g., `DesignDoc:docs/README.md`). |
| `km-graph-subsystem` | reader | Inspect subsystem details, related nodes, and artifacts. |
| `km-graph-search` | reader | Search graph entities by term (subsystems, design docs, source files). |
| `km-coverage-summary` | reader | Retrieve latest coverage summary (artifacts, chunks, missing list). |
| `km-ingest-status` | maintainer | Report last ingest run (run ID, success, counts, timestamp). |
| `km-ingest-trigger` | maintainer | Force an ingest run using the configured profile. |
| `km-feedback-submit` | maintainer | Record feedback on search results (vote, note, context). |
| `km-backup-trigger` | maintainer | Trigger a backup (invokes `bin/km-backup` or equivalent API). |

### 2.1 Usage Cheat Sheet

The MCP server exposes the following helper summaries. These mirror the metadata surfaced at runtime (see `km-help`).

- `km-help`
  - Returns usage for all tools, or pass `tool="km-search"` for a specific tool. Set `include_spec=true` to embed this document.
- `km-search`
  - Required: `query` text.
  - Optional: `limit` (default 10, max 25), `include_graph`, structured `filters`, `sort_by_vector`.
  - Example: `/sys mcp run duskmantle km-search --query "ingest pipeline" --limit 5`.
- `km-graph-node`
  - Required: `node_id` such as `DesignDoc:docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md`.
  - Optional: `relationships` (`outgoing`, `incoming`, `all`, `none`), `limit` (default 50, max 200).
  - Example: `/sys mcp run duskmantle km-graph-node --node-id "Code:gateway/mcp/server.py"`.
- `km-graph-subsystem`
  - Required: subsystem `name`.
  - Optional: `depth` (default 1, max 5), `include_artifacts`, pagination `cursor`, `limit` (default 25, max 100).
  - Example: `/sys mcp run duskmantle km-graph-subsystem --name Kasmina --depth 2`.
- `km-graph-search`
  - Required: `term`.
  - Optional: `limit` (default 20, max 50).
  - Example: `/sys mcp run duskmantle km-graph-search --term coverage`.
- `km-coverage-summary`
  - No parameters. Mirrors `/coverage` and returns artifact/chunk counts plus freshness stats.
  - Example: `/sys mcp run duskmantle km-coverage-summary`.
- `km-ingest-status`
  - Optional: `profile` filter (default: latest run regardless of profile).
  - Example: `/sys mcp run duskmantle km-ingest-status --profile demo`.
- `km-ingest-trigger`
  - Optional: `profile` (defaults to MCP settings), `dry_run`, `use_dummy_embeddings`.
  - Note: targeted path ingest is not yet supported; providing `paths` results in an error.
  - Example: `/sys mcp run duskmantle km-ingest-trigger --profile local --dry-run true`.
- `km-backup-trigger`
  - No parameters. Requires maintainer token and returns backup archive metadata.
  - Example: `/sys mcp run duskmantle km-backup-trigger`.
- `km-feedback-submit`
  - Required: `request_id` and `chunk_id` (use the IDs from search responses).
  - Optional: `vote` (-1.0 to 1.0) and `note`.
  - Example: `/sys mcp run duskmantle km-feedback-submit --request-id req123 --chunk-id chunk456 --vote 1`.

## 3. Request & Response Schemas

### 3.1 `km-search`
- **Request:**
```json
{
  "query": "ingestion pipeline",
  "limit": 10,
  "include_graph": true,
  "filters": {
    "subsystems": ["Kasmina"],
    "artifact_types": ["doc", "code"],
    "namespaces": ["docs"],
    "tags": ["Leyline"],
    "updated_after": "2024-01-01T00:00:00Z",
    "max_age_days": 30
  },
  "sort_by_vector": false
}
```
- **Response:** hybrid search results (chunk, graph context, scoring). Include `metadata.request_id` for follow-up feedback.

### 3.2 `km-graph-node`
- **Request:** `{ "node_id": "DesignDoc:docs/archive/WORK_PACKAGES.md", "relationships": "all", "limit": 25 }`
- **Response:** node serialization plus relationship list. Errors: `not_found`, `invalid_identifier`.

### 3.3 `km-graph-subsystem`
- **Request:** `{ "name": "Kasmina", "depth": 1, "limit": 25, "cursor": null, "include_artifacts": true }`
- **Response:** subsystem node, related nodes (with cursor), artifacts array.

### 3.4 `km-graph-search`
- **Request:** `{ "term": "ingest", "limit": 10 }`
- **Response:** `results` array with `id`, `label`, `score`, `snippet`.

### 3.5 `km-coverage-summary`
- **Request:** `{}`
- **Response:** coverage summary (artifact totals, chunk count, missing artifacts).

### 3.6 `km-ingest-status`
- **Request:** `{ "profile": "scheduled" }` (default `"scheduled"`; allow `"demo"`, `"local"`, or custom).
- **Response:** `{ "run_id": "...", "profile": "demo", "started_at": 1699999999.0, "success": true, "artifact_counts": {...}, "chunk_count": 320 }` plus `duration_seconds` and optional `repo_head`.

### 3.7 `km-ingest-trigger`
- **Request:**
```json
{
  "profile": "manual",
  "dry_run": false,
  "use_dummy_embeddings": false
}
```
  - `profile`: label recorded with the ingest run (defaults to the MCP server setting when omitted).
  - `dry_run`: skip writes (useful for validation).
  - `use_dummy_embeddings`: optional flag for smoke testing.
  - `paths`: **not currently supported**; calls fail with `unsupported_operation` when provided.
- **Response:** accepts once the job is queued/completed. For synchronous call, return the resulting `km-ingest-status` payload; for async call (future enhancement), return a job ID.
- **Errors:** `upstream_error`, `unsupported_operation` (if incremental ingest not supported), `unauthorized`.

### 3.8 `km-feedback-submit`
- **Request:** `{ "request_id": "uuid", "chunk_id": "docs/README.md::3", "vote": 1, "note": "useful", "context": {"task": "demo"} }`
- **Response:** acknowledgement with timestamp.

### 3.9 `km-backup-trigger`
- **Request:** `{ "destination": null }`
- **Response:** `{ "archive": "backups/km-backup-20250927T195120.tgz" }`

## 4. Error Model
- All responses include `status` and optionally `error`.
- Standard error codes: `invalid_request`, `not_found`, `unauthorized`, `forbidden`, `upstream_error`, `unsupported_operation`.

## 5. Telemetry
- Metrics: `km_mcp_requests_total{tool,result}`, `km_mcp_request_seconds_bucket{tool}`, `km_mcp_failures_total{tool,error}`.
- Logs: Structured entries per MCP invocation with tool, parameters summary (sanitized), duration, and warnings.

## 6. Security
- Store tokens in secrets/env variables; avoid logging them.
- Optionally enforce rate limiting for MCP commands (mirror gateway limiter).
- Validate inputs defensively (paths, node IDs) to prevent injection or excessive workload.

## 7. Future Enhancements
- Additional tools: `km-ingest-list`, `km-scheduler-status`, `km-health-summary`, custom Cypher (maintainer-only).
- Batch operations for feedback or search.
