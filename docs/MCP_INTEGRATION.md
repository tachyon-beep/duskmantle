# MCP Integration Guide

The Duskmantle gateway now exposes a first-class Model Context Protocol (MCP) surface so tools such as Codex CLI, Claude Desktop, and Cursor can interact with search, graph, ingest, backup, and feedback workflows without touching the raw HTTP API. This document covers installation, configuration, validation, and troubleshooting.

## 1. Prerequisites
- Python 3.12 with the project installed locally (`pip install -e .[dev]`). The dev extras bring in FastMCP and `pytest-asyncio` for smoke tests.
- A running gateway instance (local container via `bin/km-run` or remote deployment) reachable at the URL you provide to the MCP adapter.
- Tokens if authentication is enabled:
  - `KM_READER_TOKEN` for read-only operations (search/graph/coverage).
  - `KM_ADMIN_TOKEN` for maintainer operations (ingest trigger, backups, feedback submission).

## 2. Launch the MCP Server
`gateway-mcp` is an entry point exposed by this repository.

```bash
# Install dev dependencies if needed
pip install -e .[dev]

# Start the MCP server with stdio transport (ideal for Codex CLI)
KM_GATEWAY_URL=http://localhost:8000 \
KM_READER_TOKEN=$KM_READER_TOKEN \
gateway-mcp --transport stdio
```

- Omit `KM_READER_TOKEN` only when the gateway is running without auth. Add `KM_ADMIN_TOKEN` when you intend to trigger ingest or backups through MCP tools.
- To expose the adapter over HTTP/SSE instead of stdio, choose a different transport:
  ```bash
  gateway-mcp --transport http --host 127.0.0.1 --port 8822
  ```
  Agents such as Claude Desktop can then connect using the declared host/port.
- All tools are documented in `docs/MCP_INTERFACE_SPEC.md`. The IDs align with the following command names:
  - `km-search`
  - `km-graph-node`
  - `km-graph-subsystem`
  - `km-graph-search`
  - `km-coverage-summary`
  - `km-ingest-status`
  - `km-ingest-trigger`
  - `km-backup-trigger`
  - `km-feedback-submit`

## 3. Configure Codex CLI (Example)
Add a stanza to `~/.codex/config.toml` that points at the local adapter. Codex CLI will spawn `gateway-mcp` on demand when tools require it.

```toml
# ~/.codex/config.toml
[mcp_servers.duskmantle]
command = "gateway-mcp"
args = ["--transport", "stdio"]
# Provide tokens/endpoints when auth is enabled
env = { "KM_GATEWAY_URL" = "http://localhost:8000", "KM_READER_TOKEN" = "maintainer-token", "KM_ADMIN_TOKEN" = "maintainer-token" }
```

Restart Codex CLI after editing the config. List available MCP servers with `/sys mcp list` and invoke tools via `/sys mcp run duskmantle km-search --query "ingestion pipeline"`.

#### FastMCP manifest example

Some tools prefer a manifest file instead of CLI arguments. Save the following as `fastmcp.json` to expose the adapter over HTTP/SSE:

```json
{
  "entrypoint": "gateway.mcp.cli:main",
  "args": ["--transport", "http", "--host", "127.0.0.1", "--port", "8822"],
  "environment": {
    "KM_GATEWAY_URL": "http://localhost:8000",
    "KM_READER_TOKEN": "maintainer-token",
    "KM_ADMIN_TOKEN": "maintainer-token"
  }
}
```

Run `fastmcp serve fastmcp.json` (or point an IDE at the file) to launch the adapter. To use stdio instead, change the arguments to `["--transport", "stdio"]` and omit the host/port flags.

## 4. Validate Locally
Use the dedicated Pytest marker to confirm the adapter works end-to-end:

```bash
pytest -m mcp_smoke --maxfail=1 --disable-warnings
```

This smoke slice exercises `km-search`, `km-coverage-summary`, and `km-backup-trigger`, recording metrics under:
- `km_mcp_requests_total{tool,result}`
- `km_mcp_request_seconds_bucket{tool}`
- `km_mcp_failures_total{tool,error}`

For full coverage (including error paths) run `pytest tests/mcp/test_server_tools.py`.

## 5. Observability & Operations
- Metrics for MCP usage are exported alongside the existing Prometheus registry (see `/metrics`). Add `km_mcp_requests_total` and `km_mcp_request_seconds` to dashboards to monitor latency and error rates.
- Logs include tool names, duration, and structured error details when upstream requests fail.
- When running the adapter over HTTP, protect it with the same bearer tokens used by the gateway or place it behind a trusted reverse proxy.

## 6. Troubleshooting
| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `RuntimeError: No active context found` | Tool invoked without MCP context (e.g., calling `.run()` without passing `context`) | Use the adapter directly (`gateway-mcp`) or supply `{"context": null}` when invoking tools manually in tests. |
| `Gateway request failed with status 401/403` | Missing or incorrect token | Set `KM_READER_TOKEN` / `KM_ADMIN_TOKEN` before launching the adapter. |
| `Gateway request failed with status 503` | Gateway not ready or dependencies offline (Qdrant/Neo4j) | Confirm the API is reachable (`curl http://localhost:8000/readyz`) and retry after ingestion completes. |
| MCP metrics absent | Adapter never executed or metrics registry not scraped | Run `pytest -m mcp_smoke` or execute any MCP command; verify `/metrics` includes `km_mcp_requests_total`. |

## 7. Release Integration
- GitHub Actions (`release.yml`) executes the MCP smoke marker on every tagged build.
- The Neo4j integration workflow also runs the MCP smoke slice after graph tests to ensure the adapter remains healthy.

Refer to `docs/MCP_INTERFACE_SPEC.md` for schema-level details and error models.
