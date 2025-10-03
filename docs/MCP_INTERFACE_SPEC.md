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
| `km-lifecycle-report` | maintainer | Summarise isolated graph nodes, stale design docs, and subsystems missing tests. |
| `km-ingest-status` | maintainer | Report last ingest run (run ID, success, counts, timestamp). |
| `km-ingest-trigger` | maintainer | Force an ingest run using the configured profile. |
| `km-feedback-submit` | maintainer | Record feedback on search results (vote, note, context). |
| `km-backup-trigger` | maintainer | Trigger a backup (invokes `bin/km-backup` or equivalent API). |
| `km-recipe-run` | maintainer | Execute a named recipe (daily health, release prep, stale audit). |
| `km-upload` | maintainer | Copy an existing file into the knowledge workspace and optionally trigger ingest. |
| `km-storetext` | maintainer | Persist ad-hoc text as a document within the knowledge workspace. |

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
  - No parameters. Mirrors `/api/v1/coverage` and returns artifact/chunk counts plus freshness stats.
  - Example: `/sys mcp run duskmantle km-coverage-summary`.
- `km-lifecycle-report`
  - No parameters. Mirrors `/api/v1/lifecycle` and lists isolated graph nodes, stale design docs (by age threshold), and subsystems missing tests.
  - Example: `/sys mcp run duskmantle km-lifecycle-report`.
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
- `km-recipe-run`
  - Required: `recipe` name. Optional: `vars` object mapping overrides. Executes the YAML recipe and returns the final outputs transcript.
  - Example: `/sys mcp run duskmantle km-recipe-run --recipe release-prep --vars {"profile":"release"}`.
- `km-feedback-submit`
  - Required: `request_id` and `chunk_id` (use the IDs from search responses).
  - Optional: `vote` (-1.0 to 1.0) and `note`.
  - Example: `/sys mcp run duskmantle km-feedback-submit --request-id req123 --chunk-id chunk456 --vote 1`.
- `km-upload`
  - Required: `source_path` (must be readable by the MCP host).
  - Optional: `destination` (relative to `KM_CONTENT_ROOT`), `overwrite`, `ingest`.
  - Example: `/sys mcp run duskmantle km-upload --source-path ./notes/design.md --destination docs/uploads/`.
- `km-storetext`
  - Required: `content` (text body).
  - Optional: `title`, `destination`, `subsystem`, `tags`, `metadata`, `overwrite`, `ingest`.
  - Example: `/sys mcp run duskmantle km-storetext --title "Release Notes" --content "## Summary"`.

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
    "tags": ["Integration"],
    "symbols": ["Example.method"],
    "symbol_kinds": ["method"],
    "symbol_languages": ["python"],
    "updated_after": "2024-01-01T00:00:00Z",
    "max_age_days": 30
  },
  "sort_by_vector": false
}
```

- `filters.symbols`: array of qualified symbol names (case-insensitive).
- `filters.symbol_kinds`: array of symbol kinds (`class`, `function`, `method`, `interface`, `type`, `module`).
- `filters.symbol_languages`: array of languages (`python`, `typescript`, `tsx`, `javascript`, `go`).
- **Response:** hybrid search results (chunk, graph context, scoring). Include `metadata.request_id` for follow-up feedback. Each chunk now includes a `symbols` array when symbol indexing is enabled; entries contain `id`, `qualified_name`, span details, and an `editor_uri` when `KM_EDITOR_URI_TEMPLATE` is configured.
- **CLI shortcut:** When invoking via FastMCP or Codex CLI, use `--symbol`, `--kind`, or `--lang` flags (repeatable/comma-separated) to append filter terms without hand-crafting the `filters` payload.

### 3.2 `km-graph-node`
- **Request:** `{ "node_id": "DesignDoc:docs/archive/WORK_PACKAGES.md", "relationships": "all", "limit": 25 }`
- **Response:** node serialization plus relationship list. Errors: `not_found`, `invalid_identifier`.

### 3.3 `km-graph-subsystem`
- **Request:** `{ "name": "Kasmina", "depth": 2, "limit": 25, "cursor": null, "include_artifacts": true }`
- **Response:** subsystem node, related nodes (now including `hops`, `path`, `cursor`, `total`), artifacts array.

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
### 3.10 `km-recipe-run`
- **Request:** `{ "recipe": "release-prep", "vars": {"profile": "release"} }`
- **Response:** `{ "status": "success", "outputs": {...}, "steps": [...] }` where `steps` describes each tool invocation.
- **Errors:** `recipe_not_found`, `tool_failed`, `assert_failed`, `timeout`.

- **Request:** `{ "destination": null }`
- **Response:** `{ "archive": "backups/archives/km-backup-20250927T195120.tgz" }`

### 3.10 `km-upload`
- **Request:**
```json
{
  "source_path": "./notes/design.md",
  "destination": "docs/uploads/",
  "overwrite": false,
  "ingest": false
}
```
  - `source_path`: required path to a file accessible by the MCP host/container.
  - `destination`: optional relative path under the content root. When omitted, the file is copied to `<docs_subdir>/<filename>`.
  - `overwrite`: allow replacing an existing file (default: `KM_UPLOAD_DEFAULT_OVERWRITE`).
  - `ingest`: trigger an ingest run after the copy (default: `KM_UPLOAD_DEFAULT_INGEST`).
- **Response:**
```json
{
  "status": "success",
  "stored_path": "/workspace/repo/docs/uploads/design.md",
  "relative_path": "docs/uploads/design.md",
  "overwritten": false,
  "ingest_triggered": false,
  "ingest_run": null
}
```
- **Errors:** `invalid_request` (missing/invalid path), `forbidden` (insufficient scope), `upstream_error` (ingest failure).

### 3.11 `km-storetext`
- **Request:**
```json
{
  "content": "## Body\nDetails\n",
  "title": "Release Notes",
  "destination": "docs/uploads/",
  "subsystem": "Deployment",
  "tags": ["release", "notes"],
  "metadata": {"author": "agent"},
  "overwrite": false,
  "ingest": true
}
```
  - `content`: required text body (UTF-8); a trailing newline is added automatically.
  - `title`: optional; used for slug generation and stored in front matter.
  - `destination`: optional relative path (defaults to the docs subdirectory).
  - `subsystem`, `tags`, `metadata`: captured in YAML front matter to aid classification.
  - `overwrite` / `ingest`: same defaults as `km-upload`.
- **Response:**
```json
{
  "status": "success",
  "stored_path": "/workspace/repo/docs/uploads/release-notes.md",
  "relative_path": "docs/uploads/release-notes.md",
  "ingest_triggered": true,
  "ingest_run": {"success": true, "run_id": "abc", "profile": "manual"}
}
```
- **Errors:** `invalid_request` (empty content), `forbidden`, `upstream_error` (ingest failure).

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
