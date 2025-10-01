# MCP Agent Playbook

A quick guide for LLM-based or automated agents that interact with the Duskmantle appliance exclusively through the Model Context Protocol (MCP).

## 1. Environment Setup

1. Ensure the gateway is running (`bin/km-bootstrap` or `bin/km-run`).
2. Export credentials for the MCP process:
   - `KM_GATEWAY_URL` (defaults to `http://localhost:8000`).
   - `KM_READER_TOKEN` for read operations (`km-search`, `km-graph-*`, `km-coverage-summary`).
   - `KM_ADMIN_TOKEN` for write/admin operations (`km-upload`, `km-storetext`, ingest/backup/feedback).
3. Launch the MCP server locally or inside the container: `./bin/km-mcp --transport stdio` (host) or `./bin/km-mcp-container` (container).
4. Register the server with your agent client (Codex CLI, Claude, Cursor). See `docs/MCP_INTEGRATION.md` for configuration snippets.

## 2. Quick Validation Checklist

Run these commands after startup to confirm connectivity and scope:

```bash
# List available tools and descriptions
km-help {}

# Check health and coverage
km-coverage-summary {}

# Perform a sample search
km-search '{"query": "knowledge gateway", "limit": 3}'
```

Expect `status: ok` responses and zeroed MCP telemetry counters (`km_mcp_requests_total`). If you receive `401/403`, verify tokens; if `503`, check the container logs for dependency issues.

## 3. Common Agent Flows

### 3.1 Add Existing Files and Re-ingest

```bash
# Copy a host-visible file into the workspace (no ingest yet)
km-upload '{"source_path": "./notes/design.md", "destination": "docs/uploads/"}'

# Trigger a rebuild once you've added all files
km-ingest-trigger '{"profile": "manual"}'

# Verify the new material is indexed
km-search '{"query": "design", "limit": 5}'
```

Tips:
- Omit `destination` to drop a file directly into the default docs directory.
- Supply `"ingest": true` to `km-upload` when you want ingestion to fire immediately (respects the default from `KM_UPLOAD_DEFAULT_INGEST`).

### 3.2 Capture Ad-hoc Notes

```bash
# Persist text with optional metadata and ingest immediately
km-storetext '{
  "title": "Daily Digest",
  "content": "## Summary\n- Investigated ingestion retry",
  "subsystem": "Operations",
  "tags": ["digest", "status"],
  "ingest": true
}'

# Confirm the note is searchable
km-search '{"query": "Daily Digest", "limit": 3}'
```

Notes:
- Metadata becomes YAML front matter above the stored markdown. This aids subsystem/tag discovery.
- Use `"destination"` to write under a custom folder (e.g., `docs/digests`).

### 3.3 Review Ingest Status & Coverage

```bash
km-ingest-status '{"profile": "manual"}'
km-coverage-summary {}
```

These endpoints report the latest run id, duration, and artifact/chunk counts. Pair with `/metrics` (requires maintainer token) to watch Prometheus counters such as `km_mcp_upload_total` or ingest throughput.

### 3.4 Provide Feedback for Ranking

```bash
# After a search, capture the request ID and chunk ID
km-feedback-submit '{
  "request_id": "<from km-search metadata>",
  "chunk_id": "docs/digests/daily-digest.md::0",
  "vote": 1,
  "note": "Relevant summary"
}'
```

Aim to provide balanced votes (-1 to 1) so search telemetry can train improved ranking weights. Use `km-help {"tool": "km-feedback-submit", "include_spec": true}` for full schema details.

### 3.5 Review Audit Trail

Every successful `km-upload` and `km-storetext` call appends a JSON line to `KM_STATE_PATH/audit/mcp_actions.log`. Inspect this file when reconciling changes or debugging ingest triggers. Pair it with `km-ingest-status` to correlate ingest runs and use future recipe support to automate audit triage.

### 3.6 Knowledge Recipes

Use `km-recipe-run <name>` (or `gateway-recipes run <name>`) to execute bundled workflows. The baseline recipes include:

- `stale-audit` – pull lifecycle signals for stale docs/isolated nodes.
- `subsystem-freshness` – inspect a subsystem graph and surface recent artefacts.
- `release-prep` – trigger ingest, wait for completion, capture coverage/lifecycle, then take a backup.

Example:

```bash
km-recipe-run release-prep --var profile=staging
```

Every execution writes to `/opt/knowledge/var/audit/recipes.log`; tail it to monitor automation runs or escalate failures.

More details live in `docs/MCP_RECIPES_DESIGN.md` and `docs/MCP_RECIPES.md`.

## 4. Troubleshooting

| Symptom | Likely Cause | Next Steps |
|---------|--------------|------------|
| `invalid_request` from `km-upload` | Path missing or outside content root | Double-check `source_path`; the MCP server forbids traversal outside `KM_CONTENT_ROOT`. |
| `upstream_error` after ingest trigger | Ingest run failed | Inspect gateway logs (`.duskmantle/config/logs/gateway.log`) and rerun with `"dry_run": true` for diagnostics. |
| `Forbidden` on write tools | Reader token used | Switch to the maintainer token (`KM_ADMIN_TOKEN`). |
| Search returns stale results | Ingest didn’t run | Trigger `km-ingest-trigger` (or use `"ingest": true` on uploads/storetext) and verify with `km-ingest-status`. |

## 5. Useful References

- `docs/MCP_INTERFACE_SPEC.md` – full contract and schema definitions.
- `docs/MCP_RECIPES.md` – step-by-step command snippets for common automation patterns.
- `docs/QUICK_START.md` – end-to-end container bootstrap and operational runbook.
- Prometheus metrics – `km_mcp_requests_total`, `km_mcp_upload_total`, `km_mcp_storetext_total` for MCP-side monitoring.

Keep this playbook alongside your agent configuration so new team members can bootstrap quickly.
