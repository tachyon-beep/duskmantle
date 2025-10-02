# Quick Start Guide

This guide walks through launching the Duskmantle knowledge gateway, running a smoke ingest, verifying health endpoints, and creating backups.
For detailed architecture and operational runbooks, see `docs/KNOWLEDGE_MANAGEMENT.md` and `docs/OBSERVABILITY_GUIDE.md`.

## What You Get

- **Turnkey ingest** that sweeps docs, source, and tests into Qdrant + Neo4j with coverage tracking and provenance logs.
- **Hybrid `/search` API** blending dense vectors with lexical overlap and graph signals, returning per-result scoring breakdowns.
- **Graph endpoints** (`/graph/subsystems`, `/graph/nodes`, `/graph/search`, `/graph/cypher`) for topology inspection and agent workflows.
- **Model Context Protocol (MCP) server** exposing search, graph, ingest, backup, and feedback tools so Codex CLI (and other agents) can
interact without raw HTTP calls.
- **Release and observability tooling**: smoke tests, health/metrics endpoints, backup helpers, and acceptance snapshot templates.

## 1. Prerequisites

- Docker 24+ with BuildKit enabled (default in recent releases).
- Python 3.12 (optional, for local development and CLI usage).
- At least 4 GB RAM and 5 GB free disk for Neo4j/Qdrant data.

## 2. Build or Pull the Container

To build from source:

```bash
scripts/build-image.sh duskmantle/km:dev
```

This script enables BuildKit, prints image metadata, and accepts optional args via `KM_BUILD_ARGS` or `KM_BUILD_PROGRESS`.

Alternatively, pull a published image (GitHub Container Registry):

```bash
docker pull ghcr.io/tachyon-beep/duskmantle-km:1.1.0
```

**Shortcut:** run `bin/km-bootstrap` (optionally `--image <tag>`). It pulls the latest image, prepares `.duskmantle/{config,data,backups}`,
generates secure tokens/passwords in `.duskmantle/secrets.env`, and launches the stack via `bin/km-run`.

## 3. Launch the Stack

Create working directories for state and content:

```bash
mkdir -p .duskmantle/{config,data}
```

Copy or symlink the material you want the gateway to index into `.duskmantle/data/`. That path becomes `/workspace/repo` inside the
container. Run `bin/km-sweep` whenever you add loose `*.md`, `*.docx`, `*.txt`, `*.doc`, or `*.pdf` files—the helper copies them into
`.duskmantle/data/docs/` so the next ingest picks them up.

Use the helper script for consistent mounts and ports:

```bash
bin/km-run
```

Prefer Compose? Copy `infra/examples/docker-compose.sample.yml` into your project,
adjust the volume paths/environment, and run `docker compose up -d` for the same
layout.

Defaults:

- Ports: API `8000`, Qdrant `6333`, Neo4j `7687`.
- State directory: `.duskmantle/config` mounted to `/opt/knowledge/var`.
- Repository mount: `.duskmantle/data` to `/workspace/repo` (read-only by default).

On first boot the container seeds `/workspace/repo` with a small sample repository
(docs plus `.metadata/subsystems.json`) so `/graph/subsystems` has data immediately.
Set `KM_SEED_SAMPLE_REPO=false` if you prefer a pristine volume. Replace the
seeded files with your real knowledge base before running a production ingest.

**Swap in your repo**

1. Set `KM_SEED_SAMPLE_REPO=false` (or delete the `.km-sample-repo` marker file inside the mounted repo directory).
2. Remove the seeded docs under your host mount (e.g., `.duskmantle/data/docs/*`).
3. Copy or sync your real documentation/code/test assets into the same directory.
4. Run `gateway-ingest rebuild --profile <name>` to index the new content.

Override with environment variables (examples):

```bash
KM_IMAGE=duskmantle/km:latest \
KM_DATA_DIR=/srv/km/config \
KM_REPO_DIR=/srv/km/content \
bin/km-run --detach
```

> **Networking tip:** prefer Docker's default bridge network so port publishing
> works without requiring extra privileges. When running on systems that block
> `iptables` (e.g. locked-down CI hosts), either enable rootless Docker or fall
> back to `--network host` and ensure ports 8000/6333/7687 are free.

Verify readiness:

```bash
curl http://localhost:8000/readyz
```

Then open `http://localhost:8000/ui/` in a browser to explore the embedded console preview (search, subsystem, and lifecycle panels arrive
in later iterations).
Head to the Search tab to issue hybrid queries without leaving the container, supplying your reader token when prompted.
Review dependencies from the Subsystems tab — start with `ReleaseTooling` or any subsystem defined in your ingest.
Spark lines on the Lifecycle tab appear after at least one completed ingest so you can visualise stale docs and isolated nodes over time.
Use the console actions to copy MCP commands or download JSON snapshots when filing issues.
Tokens entered via the Tokens menu are stored only for the current browser session; clear them after use.

## 4. Run an Ingest

Inside the container:

```bash
docker exec duskmantle gateway-ingest rebuild --profile local --dummy-embeddings
# Incremental ingest runs by default; add `--full-rebuild` to force reprocessing all artifacts.
```

For production, omit `--dummy-embeddings` (requires model download).

**Automatic ingestion (optional):** set `KM_WATCH_ENABLED=true` (and optionally adjust `KM_WATCH_INTERVAL`, `KM_WATCH_PROFILE`,
`KM_WATCH_USE_DUMMY`, `KM_WATCH_METRICS_PORT`) before launching `bin/km-run`. The container’s supervisor will run `bin/km-watch` internally,
hashing `/workspace/repo` every interval and triggering `gateway-ingest` whenever files change. Fingerprints persist under
`/opt/knowledge/var/watch/fingerprints.json`, and metrics are exposed on `KM_WATCH_METRICS_PORT` (default `9103`).

## 5. Health Checks & Observability

- `curl http://localhost:8000/healthz` — overall status plus coverage/audit/scheduler details.
- `curl http://localhost:8000/metrics` — Prometheus metrics (requires `KM_ADMIN_TOKEN` if auth enabled).
- `curl http://localhost:8000/coverage` — latest coverage report (maintainer scope).
- `curl http://localhost:8000/lifecycle` — lifecycle snapshot (isolated nodes, stale docs, missing tests; maintainer scope).
- `gateway-recipes list` — enumerate available automation recipes (use `km-recipe-run <name>` to execute).

Refer to `docs/OBSERVABILITY_GUIDE.md` for alerting thresholds and troubleshooting (e.g., auth 401/403 diagnostics, scheduler skews).

## 6. Smoke Test Script

Run the full pipeline locally before publishing:

```bash
./infra/smoke-test.sh duskmantle/km:dev
```

or simply `make smoke` (uses the same script with the default image tag).

The script builds the image, launches a disposable container, triggers a smoke ingest, validates `/coverage`, and tears down resources.
Pair it with `bin/km-watch` if you want continuous ingestion whenever `.duskmantle/data` changes.

## 7. Backups & Restore

Create a backup (tar.gz) of `/opt/knowledge/var`:

```bash
bin/km-backup
```

The archive lands in `.duskmantle/backups/km-backup-<timestamp>.tgz`. To restore:

```bash
tar -xzf .duskmantle/backups/km-backup-<timestamp>.tgz -C .duskmantle/config
```

Restart the container to pick up restored state.

## 8. Environment & Authentication

- Authentication is enabled by default. On first boot the container writes random tokens and a Neo4j password to `.duskmantle/config/secrets.env`
  (inside the container this is `${KM_VAR}/secrets.env`). Override any value by exporting your own before launch, or run `bin/km-bootstrap`
  to regenerate everything. Maintainer tokens satisfy reader endpoints; reader tokens cannot invoke admin operations. MCP write helpers
  (`km-upload`, `km-storetext`) append JSON lines to `KM_STATE_PATH/audit/mcp_actions.log`, so include that file in your log rotation strategy.
- Neo4j authentication is enabled by default. Use the generated `KM_NEO4J_PASSWORD` for `cypher-shell`/backups and only set
  `KM_NEO4J_AUTH_ENABLED=false` for isolated development environments—the gateway logs a warning when you do.
- Rotate credentials later with `bin/km-rotate-neo4j-password`; it stops the container, updates `.duskmantle/secrets.env`, and relaunches
  the stack with the new Neo4j password.
- Scheduler and `gateway-ingest` refuse to run without `KM_ADMIN_TOKEN` when auth is enabled.

## 9. Troubleshooting Highlights

- **401 Unauthorized**: Missing bearer token. Add `-H "Authorization: Bearer $KM_READER_TOKEN"` to requests.
- **403 Forbidden**: Invalid token or insufficient scope. Use the maintainer token for ingestion, coverage, and `/graph/cypher`.
- **Scheduler Skips**: Inspect `km_scheduler_runs_total` metrics (`skipped_head`, `skipped_lock`, `skipped_auth`) for root cause.
- **Tracing**: Enable with `KM_TRACING_ENABLED=true`. Set `KM_TRACING_ENDPOINT` for OTLP export; use `KM_TRACING_CONSOLE_EXPORT=true` to
mirror spans locally.
- **Hybrid search tuning**: Adjust dense vs. lexical weighting with `KM_SEARCH_VECTOR_WEIGHT` / `KM_SEARCH_LEXICAL_WEIGHT` (defaults 1.0 /
0.25). Increase `KM_SEARCH_HNSW_EF_SEARCH` for higher recall at the cost of latency.

For more detail, consult `docs/OBSERVABILITY_GUIDE.md` and the release playbook in `RELEASE.md`.

## 11. Upgrades & Rollback

1. Review the release changelog for schema/config changes.
2. Back up `/opt/knowledge/var` (`bin/km-backup`). Copy `.duskmantle/backups/km-backup-*.tgz` off-host.
3. Stop the running container (`docker rm -f duskmantle`).
4. Pull or build the new image (`docker pull duskmantle/km:<tag>` or `scripts/build-image.sh`). Relaunch with the same env vars
(`KM_NEO4J_DATABASE=knowledge`, tokens, mounts).
5. Run ingest if needed (`docker exec duskmantle gateway-ingest rebuild --profile production`).
6. Validate `/healthz`, `/coverage`, the smoke script, and `pytest -m mcp_smoke`.
7. For rollback: stop the container, restore the archived backup to `.duskmantle/config/`, and start the previous image tag.

See `docs/UPGRADE_ROLLBACK.md` for the detailed checklist.

## 10. Run the MCP Server

Launch `gateway-mcp` to expose the gateway over the Model Context Protocol so agents can call search/graph/ingest/backups without raw HTTP requests.

1 Install the project with dev extras if you have not already:

   ```bash
   pip install -e .[dev]
   ```

2 Start the MCP server (stdio transport works well with Codex CLI):

   ```bash
   KM_GATEWAY_URL=http://localhost:8000 \
   KM_READER_TOKEN=${KM_READER_TOKEN:-maintainer-token} \
   KM_ADMIN_TOKEN=${KM_ADMIN_TOKEN:-maintainer-token} \
   ./bin/km-mcp --transport stdio
   ```

- Drop `KM_READER_TOKEN` only if auth is disabled. Provide `KM_ADMIN_TOKEN` whenever you need maintainer tools (`km-ingest-*`,
   `km-backup-trigger`, `km-feedback-submit`).
- Use `--transport http --port 8822` for HTTP/SSE instead of stdio.
- To run inside the container, call `./bin/km-mcp-container`; it inherits the gateway environment and helper paths.

   | Tool | Scope | Purpose |
   |------|-------|---------|
   | `km-search` | reader | Hybrid search with scoring breakdown and optional graph context. |
   | `km-graph-node` | reader | Fetch a node and relationships by ID (`DesignDoc:docs/...`). |
   | `km-graph-subsystem` | reader | Inspect subsystem metadata, related nodes, and artifacts. |
   | `km-graph-search` | reader | Term search across graph entities. |
   | `km-coverage-summary` | reader | Retrieve the latest ingestion coverage snapshot. |

| `km-lifecycle-report` | maintainer | Summarise isolated graph nodes, stale docs, and subsystems missing tests. |
   | `km-ingest-status` / `km-ingest-trigger` | maintainer | Inspect or run ingestion profiles. |
| `km-recipe-run` | maintainer | Execute predefined automation workflows (e.g., release-prep). |
   | `km-backup-trigger` | maintainer | Invoke the backup helper to create a state archive. |
   | `km-feedback-submit` | maintainer | Record relevance votes for ranking telemetry. |

3 In another terminal, validate the surface:

   ```bash
   pytest -m mcp_smoke --maxfail=1 --disable-warnings
   ```

   The smoke slice exercises the core tools above and increments MCP metrics (`km_mcp_requests_total`, `km_mcp_request_seconds`,
   `km_mcp_failures_total`) exposed at `/metrics`.

For Codex CLI configuration (including container-scoped tips and token handling), see `docs/MCP_INTEGRATION.md`.
