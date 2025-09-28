# Configuration Reference

The knowledge gateway reads its runtime configuration from environment variables (prefixed with `KM_`). This reference consolidates the most common options; consult module-specific docs for advanced flags.

## Core Paths & Identity

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_IMAGE` | (set by launcher) | Container image tag (e.g., `ghcr.io/tachyon-beep/duskmantle-km:latest`). |
| `KM_CONTAINER_NAME` | `duskmantle` | Docker container name used by helper scripts. |
| `KM_STATE_PATH` | `/opt/knowledge/var` | Gateway state root (Neo4j/Qdrant data, coverage, logs, watcher fingerprints). |
| `KM_REPO_PATH` | `/workspace/repo` | Repository location scanned by ingestion. |
| `KM_DATA_DIR` | `./.duskmantle/config` (host default) | Host directory mounted to `/opt/knowledge/var` when using `bin/km-run`. |
| `KM_REPO_DIR` | `./.duskmantle/data` (host default) | Host directory mounted to `/workspace/repo` when using `bin/km-run`. |
| `KM_CONTENT_ROOT` | `/workspace/repo` | Base directory used by MCP upload/storetext helpers (usually matches `KM_REPO_PATH`). |
| `KM_CONTENT_DOCS_SUBDIR` | `docs` | Relative subdirectory under `KM_CONTENT_ROOT` for authored documents. |
| `KM_UPLOAD_DEFAULT_OVERWRITE` | `false` | Allow MCP uploads to overwrite existing files by default. |
| `KM_UPLOAD_DEFAULT_INGEST` | `false` | Whether MCP uploads/storetext trigger an ingest run automatically. |

## Authentication & Security

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_AUTH_ENABLED` | `false` | Require bearer tokens on HTTP and CLI entry points. |
| `KM_READER_TOKEN` | _unset_ | Token granting read-only operations (search/graph). |
| `KM_ADMIN_TOKEN` | _unset_ | Token granting maintainer operations (ingest, coverage, backups). |
| `KM_RATE_LIMIT_REQUESTS` / `KM_RATE_LIMIT_WINDOW` | `120` / `60` | Requests allowed per window (seconds). |

## Ingestion & Search

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_INGEST_WINDOW` / `KM_INGEST_OVERLAP` | `1000` / `200` | Chunking size and overlap (characters). |
| `KM_INGEST_DRY_RUN` | `false` | Skip writes (plan the ingestion without mutating storage). |
| `KM_INGEST_USE_DUMMY` | `false` | Use deterministic embeddings for non-production runs. |
| `KM_SEARCH_WEIGHT_PROFILE` | `default` | Built-in weight bundle (`default`, `analysis`, `operations`, `docs-heavy`). |
| `KM_SEARCH_VECTOR_WEIGHT` / `KM_SEARCH_LEXICAL_WEIGHT` | `1.0` / `0.25` | Hybrid weighting multipliers. |
| `KM_SEARCH_HNSW_EF_SEARCH` | `128` | Recall tuning for Qdrant HNSW queries (increase for higher recall). |
| `KM_SEARCH_WARN_GRAPH_MS` | `250` | Log warning when graph enrichment exceeds this latency (milliseconds). |
| `KM_SEARCH_SCORING_MODE` | `heuristic` | Set to `ml` to load coefficients from `KM_SEARCH_MODEL_PATH`. |

## Scheduler & Automation

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_SCHEDULER_ENABLED` | `false` | Enable scheduled ingestion via APScheduler. |
| `KM_SCHEDULER_INTERVAL_MINUTES` | `30` | Interval-based schedule when cron is not specified. |
| `KM_SCHEDULER_CRON` | _unset_ | Cron expression (UTC) for scheduled ingestion. |
| `KM_WATCH_ENABLED` | `false` | When `true`, the container runs `bin/km-watch` internally. |
| `KM_WATCH_INTERVAL` | `60` | Polling interval (seconds) for the internal watcher. |
| `KM_WATCH_PROFILE` | `local` | Ingestion profile invoked by the watcher. |
| `KM_WATCH_USE_DUMMY` | `true` | Append `--dummy-embeddings` when the watcher triggers ingestion. |
| `KM_WATCH_ROOT` | `/workspace/repo` | Directory hashed by the watcher (override for subdirectories). |
| `KM_WATCH_FINGERPRINTS` | `/opt/knowledge/var/watch/fingerprints.json` | Fingerprint cache path inside the container. |
| `KM_WATCH_METRICS_PORT` | `9103` (container default) | Start an HTTP server on this port to expose watcher metrics. Set to `0` to disable. |

## Neo4j & Qdrant

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_NEO4J_URI` | `bolt://localhost:7687` | Bolt endpoint for Neo4j. |
| `KM_NEO4J_USER` / `KM_NEO4J_PASSWORD` | `neo4j` / `neo4jadmin` | Credentials for Neo4j. |
| `KM_NEO4J_DATABASE` | `neo4j` | Database name (container default is `knowledge`). |
| `KM_NEO4J_AUTH_ENABLED` | `false` | Toggle authentication for Neo4j access. |
| `KM_GRAPH_AUTO_MIGRATE` | `false` | Auto-run graph migrations at API startup (container default `true`). |
| `KM_QDRANT_URL` | `http://localhost:6333` | Qdrant API base URL. |
| `KM_QDRANT_COLLECTION` | `km_knowledge_v1` | Collection name used by ingestion. |

## Observability & Tracing

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_COVERAGE_ENABLED` | `true` | Store coverage reports after ingest. |
| `KM_COVERAGE_HISTORY_LIMIT` | `5` | Number of historical coverage snapshots kept. |
| `KM_TRACING_ENABLED` | `false` | Toggle OpenTelemetry tracing. |
| `KM_TRACING_ENDPOINT` | _unset_ | OTLP collector endpoint (e.g., `http://otel-collector:4318/v1/traces`). |
| `KM_TRACING_HEADERS` | _unset_ | Extra headers for the OTLP exporter (`key=value` pairs). |
| `KM_TRACING_SAMPLE_RATIO` | `1.0` | Fraction of requests sampled (0.0–1.0). |
| `KM_TRACING_SERVICE_NAME` | `duskmantle-knowledge-gateway` | Service name for exported spans. |
| `KM_TRACING_CONSOLE_EXPORT` | `false` | Mirror spans to stdout in addition to the OTLP exporter. |
| `KM_STATE_PATH/audit/mcp_actions.log` | _derived_ | JSONL audit log appended by MCP write tools (see MCP playbook). |

## CLI Helpers

| Command | Purpose |
|---------|---------|
| `bin/km-bootstrap` | Pull the image, generate credentials, and launch the stack with `.duskmantle` defaults. |
| `bin/km-run` | Start the container with configurable mounts/ports. |
| `bin/km-watch` | Host-side watcher that triggers `gateway-ingest` when `.duskmantle/data` changes. |
| `bin/km-backup` | Create tarball backups of `.duskmantle/config`. |
| `bin/km-make-tokens` | Generate UUID tokens for reader/maintainer scopes. |
| `bin/km-mcp` / `bin/km-mcp-container` | Launch the MCP surface (local or in-container). |

See `docs/QUICK_START.md` and `docs/UPGRADE_ROLLBACK.md` for usage patterns, and `docs/OBSERVABILITY_GUIDE.md` for monitoring details.
