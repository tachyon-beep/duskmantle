# System Documentation

## Architecture Overview
- The Duskmantle Knowledge Gateway is a FastAPI application (`gateway/api/app.py`) that brokers requests between clients, the Neo4j knowledge graph, and the Qdrant vector store.
- Core subsystems: API layer (`gateway/api`), ingestion pipeline (`gateway/ingest`), search stack (`gateway/search`), graph service (`gateway/graph`), Model Context Protocol adapter (`gateway/mcp`), observability utilities (`gateway/observability`), and CLI tools (`gateway/graph/cli.py`, `gateway/ingest/cli.py`, etc.).
- Background scheduler (`gateway/scheduler.py`) orchestrates periodic ingestion and backups using APScheduler jobs.
- Static UI hosted under `/ui` serves dashboards and configuration readouts via Jinja templates (`gateway/ui`).
- Stateful data persists under the configured `KM_STATE_PATH` (defaults to `/opt/knowledge/var`) and includes audit SQLite databases, coverage snapshots, lifecycle reports, and backups.

```mermaid
graph TD
  subgraph API
    A[FastAPI app]\n(gateway/api/app.py)
  end
  subgraph Ingestion
    I1[Discovery]\n(gateway/ingest/discovery.py)
    I2[Chunking]\n(gateway/ingest/chunking.py)
    I3[Embedding]\n(gateway/ingest/embedding.py)
    I4[Writers]\n(gateway/ingest/qdrant_writer.py, neo4j_writer.py)
  end
  subgraph Search
    S1[VectorRetriever]
    S2[GraphEnricher]
    S3[Scoring]
  end
  subgraph Storage
    N[(Neo4j)]
    Q[(Qdrant)]
    FS[State FS]
  end
  subgraph MCP
    M1[FastMCP server]
    M2[GatewayClient]
  end
  A -->|REST / MCP| Clients
  A --> N
  A --> Q
  A --> FS
  A -.-> M1
  M1 --> A
  I1 --> I2 --> I3 --> I4
  I4 --> N
  I4 --> Q
  S1 --> Q
  S2 --> N
  S1 --> S3
  S2 --> S3
  S3 --> A
```

## Technology Stack
- **Language**: Python 3.12 (type-annotated, Pydantic v2).
- **Web Framework**: FastAPI 0.110+ with SlowAPI for rate limiting, Uvicorn server (scripts expose console entry point).
- **Scheduler**: APScheduler 3.10 for ingestion/backup automation.
- **Vector Store**: Qdrant 1.7+ (HTTP client, HNSW retrieval).
- **Graph Database**: Neo4j 5.14+ via official Python driver.
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` by default (configurable).
- **Observability**: Prometheus client metrics, python-json-logger for structured logs, OpenTelemetry exporters (`otlp`, console debugging).
- **MCP Adapter**: FastMCP 2.12 bridging Codex CLI tools to gateway services.
- **UI**: Jinja2 templates + static assets bundled under `gateway/ui` served by FastAPI.
- **Testing/Linting**: pytest, pytest-asyncio, pytest-cov, Ruff, Black, mypy, Pylint (dev extras).

Upgrade notes: Align on latest stable FastAPI/Uvicorn, Neo4j driver, and Qdrant client; monitor sentence-transformers releases for embedding quality, and keep OpenTelemetry exporters in lockstep (OTLP 1.24 currently).

## Key Features & Capabilities
- Hybrid search API combines dense vector retrieval (Qdrant) with graph-aware enrichment (Neo4j) and supports heuristic or ML-based ranking.
- Graph exploration endpoints expose subsystem topology, arbitrary Cypher queries (read-only), orphan detection, and graph search.
- Operational reporting: coverage snapshots, lifecycle reports, audit history, backup status, Prometheus metrics, and structured logging.
- Ingestion pipeline discovers repo artifacts, chunks content, embeds text, syncs graph relationships, and prunes stale data. Supports incremental mode with artifact ledger tracking.
- MCP tool suite (search, ingest trigger, backup trigger, upload/storetext, feedback) enables Codex agents to interact without HTTP credentials.
- Embedded UI surfaces search weight profiles, subsystem explorer, lifecycle dashboard, and JSON report download endpoints.

## Data Architecture
- **Neo4j** stores subsystem, artifact, chunk, integration message, telemetry channel, and migration history nodes. Relationships such as `BELONGS_TO`, `DESCRIBES`, `VALIDATES`, `HAS_CHUNK`, `DEPENDS_ON`, `IMPLEMENTS`, `EMITS` capture topology.
- **Qdrant** stores chunk embeddings keyed by chunk digests; payload metadata mirrors artifact path, subsystem assignment, coverage stats, and search scoring hints.
- **Filesystem state (`KM_STATE_PATH`)** retains ingestion audit SQLite DB, coverage reports, lifecycle reports/history, search feedback logs and models, backup archives, scheduler locks, and MCP audit trails.
- **MCP uploads/documents** written into `KM_CONTENT_ROOT` (default `/workspace/repo`) under the configured docs subdirectory.

## API & Interface Layer
- REST API versioned under `/api/v1`; routers grouped into search, graph, reporting, and health modules. Dependencies enforce authentication scopes via bearer tokens and limiters throttle high-cost routes.
- Health endpoints expose `/healthz`, `/readyz`, `/metrics` with component-level status (coverage, audit DB, scheduler, Neo4j, Qdrant, backup).
- Search endpoint `POST /api/v1/search` accepts filters (subsystems, artifact types, namespaces, tags, recency) and optional graph context toggle.
- Graph endpoints `GET /graph/subsystems/{name}`, `/graph/nodes/{node_id}`, `/graph/orphans`, POST `/graph/cypher` (read-only enforcement) support graph diagnostics.
- Reporting endpoints `/coverage`, `/lifecycle`, `/lifecycle/history`, `/audit/history` are maintainer-scoped.
- UI routes hosted under `/ui` render HTML or expose JSON for lifecycle reports; event telemetry POST `/ui/events` increments Prometheus counters.
- System CLIs (`gateway-ingest`, `gateway-graph`, `gateway-recipes`, `gateway-mcp`, etc.) wrap the same internal services for operators.

## Configuration & Deployment
- Settings via environment variables prefixed `KM_` (Pydantic `AppSettings`): API host/port, auth toggle and tokens, Neo4j/Qdrant endpoints & credentials, embedding model, chunking parameters, scheduler/backup triggers, search weight profile overrides, tracing endpoints, lifecycle thresholds.
- Auth modes: `KM_AUTH_ENABLED` toggles dependency enforcement; missing maintainer token blocks scheduler/backups; read-only graph queries enforced by sanitiser.
- Deployment packaging: `pyproject.toml` builds wheel, `Dockerfile` (root) for container image, scripts under `bin/` scaffolding docker-compose assets (see `docs` for specs). `.duskmantle/compose` used by bootstrap scripts.
- Backups: `KM_BACKUP_ENABLED`, `KM_BACKUP_DEST_PATH`, `KM_BACKUP_RETENTION_LIMIT` tune scheduler-managed archives; scripts expect `bin/km-backup` or override.
- Tracing: `KM_TRACING_ENABLED` and OTLP endpoint/headers; optional console exporter for debugging.

## Data Flow Diagrams
- **Ingestion**: `gateway.ingest.discovery` enumerates repo -> `Chunker` splits files -> `Embedder` encodes -> `QdrantWriter.upsert_chunks` & `Neo4jWriter.sync_chunks` persist -> coverage/lifecycle writers emit JSON -> audit logger records run (SQLite). Incremental ledger bypasses unchanged artifacts; stale artifacts deleted from both stores.
- **Search**: Request enters FastAPI -> embeddings generated using configured model -> Qdrant HNSW search -> payload filtered -> optional graph enrichment via `GraphService` (Neo4j) within latency budget -> heuristic or ML scoring -> sorted response payload -> optional feedback logging for retraining.
- **Lifecycle**: After ingest run, lifecycle writer collates stale docs, isolated nodes (Neo4j orphans), missing tests, removed artifacts -> metrics updated -> history snapshots rotated.
- **Backups**: Scheduler triggers `run_backup` -> external script packages state -> retention pruning removes old archives -> Prometheus gauges updated.

## Dependencies & Integration
- **External services**: Neo4j bolt endpoint (read/write URIs, optional read-only replica), Qdrant HTTP endpoint (API key optional), optional OTLP tracing endpoint, Prometheus scrape target for `/metrics`.
- **Python packages**: fastapi, httpx, qdrant-client, neo4j, sentence-transformers, apscheduler, opentelemetry stack, fastmcp, rich, prometheus-client, python-json-logger, slowapi, filelock.
- **Inter-service communication**: API dependencies share connection managers through FastAPI `state`. Scheduler reuses managers when provided; MCP server reuses HTTP client wrapper.

## Development & Operations
- **Environment setup**: `python3.12 -m venv .venv`, `pip install -e .[dev]`. Run `ruff check .`, `black .`, `pytest --cov=gateway --cov-report=term-missing` before publishing. Optional `pytest tests/mcp/` and `pytest -m mcp_smoke` for MCP changes.
- **Local services**: `bin/km-bootstrap` to pull container stack; `bin/km-watch` for host-side monitoring; `bin/km-run` orchestrates local environment (see `infra/` configs for Neo4j/Qdrant).
- **Testing**: Extensive pytest suite under `tests/` covering API security, search heuristics, graph migrations, scheduler behaviour, MCP smoke flows, CLI utilities. Playwright UI smoke tests under `playwright/`.
- **Observability**: Structured JSON logs, Prometheus counters/gauges/histograms, optional tracing instrumentation. Search and MCP modules instrument warnings and latencies. UI events recorded via `/ui/events`.
- **Deployment**: Docker image built via `scripts/build-image.sh` (`duskmantle/km:dev`), Compose assets under `.duskmantle/compose`. `infra/smoke-test.sh` for acceptance-run; release automation summarised in `README`/`docs`.

