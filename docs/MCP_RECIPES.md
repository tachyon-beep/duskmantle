# MCP Recipes

Practical examples for calling the gateway’s MCP tools. Assumptions:

- Gateway is reachable at `http://localhost:8000`.
- Tokens are available via `KM_READER_TOKEN` / `KM_ADMIN_TOKEN`.
- `gateway-mcp` (or `bin/km-mcp-container`) is installed.

## 1. Quickstart Sessions

### Codex CLI

```bash
KM_GATEWAY_URL=http://localhost:8000 \
KM_READER_TOKEN=$KM_READER_TOKEN \
KM_ADMIN_TOKEN=$KM_ADMIN_TOKEN \
./bin/km-mcp --transport stdio
```

Sample interaction:

```
> km-search {"query": "ingest pipeline", "limit": 2}
{"request_id":"4b0d...","results":[{"id":"DesignDoc:docs/QUICK_START.md","label":"DesignDoc","score":0.87,"graph_context":{"subsystem":"Ingestion"}}, {"id":"SourceFile:gateway/ingest/pipeline.py","label":"SourceFile","score":0.82}]}

> km-graph-node {"node_id": "DesignDoc:docs/QUICK_START.md"}
{"node":{"id":"DesignDoc:docs/QUICK_START.md","labels":["DesignDoc"],"properties":{"path":"docs/QUICK_START.md","title":"Quick Start Guide"}},"relationships":[{"type":"HAS_CHUNK","target":{"id":"Chunk:docs/QUICK_START.md::0"}}]}

> km-coverage-summary {}
{"profile":"local","timestamp":"2025-09-28T09:12:44Z","artifacts":46,"chunks":360,"missing":0}
```

### Claude Desktop / Cursor

Register the server in your MCP config:

```json
{
  "mcpServers": {
    "duskmantle": {
      "command": "./bin/km-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "KM_GATEWAY_URL": "http://localhost:8000",
        "KM_READER_TOKEN": "${KM_READER_TOKEN}",
        "KM_ADMIN_TOKEN": "${KM_ADMIN_TOKEN}"
      }
    }
  }
}
```

Typical command flow after connecting:

```
> km-graph-subsystem {"name":"ReleaseTooling","depth":1}
< subsystem: ReleaseTooling
  artifacts: docs/WP6_RELEASE_TOOLING_PLAN.md, docs/ACCEPTANCE_DEMO_PLAYBOOK.md

> km-ingest-trigger {"profile":"local","dry_run":true}
< ingest job scheduled (dry run)

> km-ingest-status {"profile":"local"}
< status: ok, last_run: 2025-09-28T09:20:11Z, artifacts: 46
```

## 2. Common Workflows

| Task | Tool & Params | Typical Output |
|------|---------------|----------------|
| Find scheduler docs | `km-search {"query": "scheduler", "limit": 5}` | Top chunks with subsystem context. |
| Inspect a subsystem | `km-graph-subsystem {"name": "Ingestion", "depth": 1}` | Core node plus neighbors/artifacts. Increase `depth` for more hops. |
| Fetch a design doc node | `km-graph-node {"node_id": "DesignDoc:docs/KNOWLEDGE_MANAGEMENT.md"}` | Node properties + relationships (`HAS_CHUNK`, `REFERENCES`, …). |
| Check ingest health | `km-coverage-summary {}` | Artifact/chunk totals, missing artifacts, last run details. |
| Trigger a rebuild | `km-ingest-trigger {"profile": "local", "dry_run": true}` | Schedules an ingest after editing `.duskmantle/data`. Drop `dry_run` for production. |
| Submit feedback | `km-feedback-submit {"request_id": "…", "chunk_id": "…", "vote": 1}` | Records a positive relevance vote. |
| Upload an existing file | `km-upload {"source_path": "./notes/design.md", "destination": "docs/uploads/"}` | Copies the file into the workspace and reports the stored path. |
| Capture ad-hoc notes | `km-storetext {"title": "Daily Notes", "content": "- Action items"}` | Persists text as markdown with optional metadata. |

## 3. Automation Patterns

### Refresh Ingest After Repo Changes

```bash
# Host-side: watch .duskmantle/data and trigger ingest
bin/km-watch --interval 15 \
  --command "gateway-ingest rebuild --profile local --dummy-embeddings" \
  --shell --metrics-port 9301
```

### Summarise Recent Changes

```bash
km-coverage-summary {}
# Optionally pretty-print (run as a separate command):
# km-coverage-summary {} | jq '{artifacts, chunks, missing, timestamp}'

km-search {"query":"release checklist","limit":3}
# Optional jq filter:
# km-search {"query":"release checklist","limit":3} | jq '.results[] | {id, score}'
```

### Upload Files and Capture Notes

```bash
# Copy an existing file into the workspace (no ingest by default)
km-upload {"source_path": "./notes/design.md", "destination": "docs/uploads/"}

# Store fresh text with metadata and trigger ingest immediately
km-storetext {"title": "Daily Digest", "content": "## Summary\n- Fixed ingestion retries", "destination": "docs/digests", "tags": ["digest", "status"], "ingest": true}

# Check the resulting ingest status
km-ingest-status {"profile": "manual"}
```

### Smoke-Test the MCP Surface

```bash
KM_GATEWAY_URL=http://localhost:8000 \
KM_READER_TOKEN=$KM_READER_TOKEN \
KM_ADMIN_TOKEN=$KM_ADMIN_TOKEN \
pytest -m mcp_smoke --maxfail=1 --disable-warnings
```

## 4. Error Handling Cheatsheet

| Error | Meaning | What to do |
|-------|---------|------------|
| `401 Unauthorized` | Missing `Authorization` header | Add `-H "Authorization: Bearer $KM_READER_TOKEN"` (or admin token for maintainer tools). |
| `403 Forbidden` | Token lacks scope | Use the maintainer token for ingest/backup/coverage operations. |
| `429 Too Many Requests` | Rate limit exceeded | Back off or tune `KM_RATE_LIMIT_WINDOW` / `KM_RATE_LIMIT_REQUESTS`. |
| `503 Service Unavailable` | Graph/search dependency offline | Check container logs, `km_ingest_last_run_status`, Neo4j/Qdrant reachability. |

Track MCP activity via Prometheus:

- `km_mcp_requests_total{tool="km-search"}` – call volume by tool.
- `km_mcp_request_seconds` – latency histogram.
- `km_mcp_failures_total` – non-2xx responses.

## 5. Extensibility Checklist

1. Add a CLI wrapper under `bin/` (e.g., `bin/km-graph-export`).
2. Register it in `gateway/mcp/tools.py`.
3. Document usage here and extend `pytest -m mcp_smoke` coverage.
4. Update `docs/MCP_INTERFACE_SPEC.md` with the tool contract.
5. Share ready-to-import MCP configuration snippets for popular clients.
