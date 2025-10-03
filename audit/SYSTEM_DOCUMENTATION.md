# System Documentation

## Architecture Overview
- The appliance centres on a FastAPI application (`gateway/api/app.py`) that exposes REST routes for search, graph introspection, health, reporting, and static UI assets. Dependency wiring is handled at startup so Neo4j and Qdrant clients, scheduler, and search components share lifecycle hooks.
- Supporting subsystems include the ingestion pipeline (`gateway/ingest`), hybrid search layer (`gateway/search`), Neo4j graph access (`gateway/graph`), lifecycle/coverage reporters, and the FastMCP bridge (`gateway/mcp`).
- State is persisted across three domains: Neo4j holds the domain graph, Qdrant stores vector embeddings, and the filesystem (under `KM_STATE_PATH`) retains audit databases, coverage/lifecycle reports, feedback logs, and backups.
- Background processing is coordinated via APScheduler (`gateway/scheduler.py`) and CLI entry points (`gateway/ingest/cli.py`, `gateway/graph/cli.py`, `gateway/recipes/cli.py`).
- Runtime container topology: Docker Compose (see `.duskmantle/compose/docker-compose.yml`) launches three services on the `duskmantle-internal` network—`gateway` (this Python image), `neo4j` (official 5.x image), and `qdrant` (official 1.15.x image). Host volumes under `.duskmantle/config/` persist state, and only the API port `8000` is published by default.

```mermaid
graph TD
    subgraph Client Interfaces
        UI[Static UI]
        REST[FastAPI REST]
        MCP[FastMCP Server]
    end

    REST -->|Dependencies| APIDeps[Dependency Layer]
    REST -->|Routes| SearchRoute[/search]
    REST --> GraphRoute[/graph]
    REST --> ReportRoute[/coverage,/lifecycle]
    REST --> HealthRoute[/healthz,/metrics]

    MCP -->|HTTP calls| REST

    subgraph Services
        SearchSvc[SearchService]
        GraphSvc[GraphService]
        IngestSvc[IngestionPipeline]
        Scheduler[IngestionScheduler]
    end

    SearchRoute --> SearchSvc
    GraphRoute --> GraphSvc
    ReportRoute --> IngestReports[Coverage & Lifecycle readers]
    Scheduler --> IngestSvc

    SearchSvc --> Qdrant[(Qdrant)]
    SearchSvc --> Embedder[SentenceTransformers]
    SearchSvc -.optional.- GraphSvc

    GraphSvc --> Neo4j[(Neo4j)]

    IngestSvc --> Qdrant
    IngestSvc --> Neo4j
    IngestSvc --> StateFS[(State Files)]

    ReportRoute --> StateFS
    HealthRoute --> StateFS
```

- ## Technology Stack
- **FastAPI 0.110+ & Uvicorn 0.24+** – Serve REST endpoints, static UI assets, and manage dependency injection (`gateway/api`). Upgrade path: keep pace with FastAPI/Starlette releases and re-run regression tests for dependency injection wiring and SlowAPI middleware changes.
- **fastmcp 2.12+** – Exposes the gateway as an MCP toolset (`gateway/mcp/server.py`) with HTTPX client bindings to the REST API. Monitor MCP spec updates; adapter code already centralises schema definitions in `docs/MCP_INTERFACE_SPEC.md`.
- **Neo4j 5.26** – Primary graph store (Compose defaults to `neo4j:5.26.0`). Accessed via the official Bolt driver for schema migrations, query execution, and graph enrichment (`gateway/graph/service.py`, `gateway/ingest/neo4j_writer.py`). Upgrades require Cypher migration compatibility checks and driver pin updates in `pyproject.toml`.
- **Qdrant 1.15.4** – Vector database for chunk embeddings, accessed via `qdrant-client>=1.7`. Collection creation/upsert semantics are encapsulated in `gateway/ingest/qdrant_writer.py`; when upgrading ensure HNSW/optimizer defaults remain backward compatible.
- **SentenceTransformers (all-MiniLM-L6-v2 by default)** – Provides embedding models for ingestion and ad-hoc search scoring (`gateway/ingest/embedding.py`). Model path is configurable; upgrades should regenerate embeddings and validate cosine similarity consistency.
- **Prometheus client 0.20 + SlowAPI 0.1.7** – Surface metrics (`gateway/observability/metrics.py`) and enforce rate limits via middleware.
- **APScheduler 3.10 + FileLock** – Drive scheduled ingestion runs and guard concurrent executions (`gateway/scheduler.py`). Cron expression parsing remains server-side; upgrades must respect timezone defaults.
- **OpenTelemetry 1.24** – Wraps ingestion spans and captures pipeline metrics (`gateway/observability/tracing.py`). Exporter endpoints configured through environment variables for OTLP collectors.

## Key Features & Capabilities
- Hybrid search combining vector similarity with graph-derived heuristics, optional machine-learned reranking, and subsystem filters (`gateway/search/service.py`).
- Graph introspection APIs that paginate subsystem neighbourhoods, fetch node detail, list orphans, and run read-only Cypher (`gateway/api/routes/graph.py`).
- Reporting endpoints for coverage and lifecycle health, backed by offline JSON reports generated during ingestion (`gateway/ingest/coverage.py`, `gateway/ingest/lifecycle.py`).
- Ingestion pipeline that discovers repository artifacts, chunks content, produces embeddings, and persists to both stores with incremental update support (`gateway/ingest/pipeline.py`).
- MCP tool suite enabling search, graph inspection, ingest triggering, feedback capture, file uploads, and state backups for MCP-compatible agents (`gateway/mcp/server.py`).
- Observability via Prometheus metrics, structured logging, OpenTelemetry traces, and granular health endpoints (`gateway/observability`).

## Data Architecture
### Neo4j Graph Schema
- **Node Labels:** `Subsystem`, `SourceFile`, `DesignDoc`, `TestCase`, `Chunk`, `IntegrationMessage`, `TelemetryChannel`, `ConfigFile`. Uniqueness constraints enforced via migrations (`gateway/graph/migrations/runner.py`).
- **Relationships:**
  - `BELONGS_TO`, `DESCRIBES`, `VALIDATES` connect artifacts to subsystems.
  - `HAS_CHUNK` links artifacts to chunk nodes.
  - `DEPENDS_ON` captures subsystem dependencies.
  - `IMPLEMENTS` and `EMITS` relate subsystems to integration messages and telemetry channels.
  - `DECLARES` links source files to integration messages.
- **Properties:** Artifacts store `path`, `artifact_type`, `git_commit`, `git_timestamp`, `subsystem`. Subsystems carry metadata such as `description`, `criticality`, `owner`, `tags`/`labels` via ingestion metadata.
- **Access Patterns:**
  - Graph snapshots for subsystems (`GraphService.get_subsystem`) gather related nodes/edges with caching.
  - Node lookup and relationship pagination (`GraphService.get_node`).
  - Graph search via case-insensitive term matching (`GraphService.search`).
  - Read-only Cypher execution for maintainers with lightweight validation (`GraphService.run_cypher`).

### Qdrant Collections
- **Collection:** Single default `km_knowledge_v1` configured with cosine distance and dynamic segment optimisers (`QdrantWriter.ensure_collection`).
- **Vector Size:** Determined by selected SentenceTransformer model; persisted before upsert operations.
- **Payload Schema:** Includes chunk metadata (`chunk_id`, `path`, `artifact_type`, `subsystem`, textual content, scoring context) mirroring ingestion artifacts.
- **Operations:**
  - Batch upsert of embeddings with deterministic UUID based on chunk digest (`QdrantWriter.upsert_chunks`).
  - Deletion by artifact path to remove stale content (`QdrantWriter.delete_artifact`).
  - Search queries with optional HNSW tuning and filters for subsystems, artifact types, namespaces, tags, and recency (`SearchService.search`).

-## API & Interface Layer
- **POST /search** – Reader scope. Request body includes `query: str`, optional `filters` (`subsystems`, `artifact_types`, `namespaces`, `tags`, `after_commit`), `include_graph: bool`, and tuning knobs (`limit`, `graph_limit`, `score_debug`). Response contains `results` with `chunk`, `scores` (vector, lexical, heuristics), optional `graph` context, and `metadata.feedback_prompt` for MCP feedback tools. SlowAPI rate limiting enforces defaults (120 req/minute).
- **GET /search/weights** – Maintainer scope. Returns resolved weight profile name, overrides, and applied numeric values so operators can verify heuristics and UI visualisations.
- **Graph suite** –
  - `GET /graph/subsystem` with `name`, `depth`, pagination (`cursor`, `limit`, `include_artifacts`). Returns cached `related` nodes, `artifacts`, `subsystem` metadata.
  - `GET /graph/subsystem/graph` returns full node/edge snapshot for visualisation tools.
  - `GET /graph/node` fetches node detail plus relationships filtered by type/direction with pagination.
  - `GET /graph/orphans` enumerates nodes lacking relationships (label filter optional).
  - `POST /graph/search` performs term search across subsystems, nodes, and artifacts; returns summary hits.
  - `POST /graph/cypher` (maintainer scope) executes read-only Cypher after validation (procedure whitelist, summary counters). Optional read-only driver ensures server-side enforcement.
- **Reporting** – `GET /coverage`, `/lifecycle`, `/lifecycle/history`, `/audit/history` serve JSON documents from `KM_STATE_PATH/reports` and the ingest audit SQLite ledger. Maintainer scope required.
- **Operations** – `GET /healthz` exposes dependency heartbeat gauge (last success/failure, revisions), `GET /readyz` checks scheduler and model load, `/metrics` exports Prometheus registry. Static assets under `/ui/*` host the preview console and documentation.
- **FastMCP Surface** – Tools defined in `gateway/mcp/server.py` provide equivalent operations over MCP transport: `km-search`, `km-graph-*`, `km-ingest-*`, `km-backup-trigger`, `km-feedback-submit`, `km-upload`, `km-storetext`. Requests are proxied through `GatewayClient` using scoped bearer tokens and consistent output schemas (documented in `docs/MCP_INTERFACE_SPEC.md`).

## Configuration & Deployment
- **Runtime Settings:** Centralised in `gateway/config/settings.py` using Pydantic `AppSettings`. Environment variables prefixed with `KM_` control auth, data stores, scheduler, search weights, tracing, and ingest behaviour. Optional `KM_NEO4J_READONLY_{URI,USER,PASSWORD}` credentials force `/graph/cypher` traffic through a read-only Neo4j account. Helper methods clamp values and derive scheduler triggers and weight profiles.
- **Startup Sequence:** `docker-entrypoint.sh` seeds sample repo content on first boot, generates reader/maintainer tokens when absent (unless `KM_ALLOW_INSECURE_BOOT=true`), verifies `KM_NEO4J_PASSWORD`, exports default service URLs (`KM_QDRANT_URL=http://qdrant:6333`, `KM_NEO4J_URI=bolt://neo4j:7687`), and finally execs the configured command (default `uvicorn`).
- **Docker Image:** Builds a Python 3.12 slim runtime containing the gateway application plus CLI tooling (`Dockerfile`, `infra/docker-entrypoint.sh`). It expects Qdrant and Neo4j to run as sibling containers (Compose brings official images) and only exposes port 8000 from the gateway container.
- **Compose Scaffold:** `.duskmantle/compose/docker-compose.yml` (mirrors `infra/examples/docker-compose.sample.yml`) launches `gateway`, `neo4j`, and `qdrant` services on a private bridge network, mounts `.duskmantle/{config,repo}` volumes, and surfaces core env vars (`KM_ADMIN_TOKEN`, `KM_NEO4J_PASSWORD`, seed toggles). Only the gateway's 8000/tcp is published by default.
- **State Directories:** `KM_STATE_PATH` (default `/opt/knowledge/var`) stores audit SQLite DBs, coverage/lifecycle reports, scheduler locks, managed backups under `backups/archives/km-backup-*.tgz`, and search feedback logs.
- **CLI Entry Points:**
  - `knowledge-gateway` – start API via Uvicorn.
  - `gateway-ingest` – run ingestion interactively (`gateway/ingest/cli.py`).
  - `gateway-graph` – inspect migrations (`gateway/graph/cli.py`).
  - `gateway-search`, `gateway-recipes`, `gateway-lifecycle` – support maintenance workflows.

## Data Flow Diagrams (Text)
- **Ingestion Flow:**
  1. Discovery scans repository roots and infers artifact metadata (`gateway/ingest/discovery.py`).
  2. Chunking splits textual artifacts with configurable window/overlap (`gateway/ingest/chunking.py`).
  3. Embedding pool encodes chunks via SentenceTransformers, optionally in parallel batches.
  4. QdrantWriter ensures collection and upserts embeddings; Neo4jWriter syncs artifacts, subgraph relationships, and chunk nodes.
  5. Ledger/history updated for incremental runs, stale artifacts removed, audit entry persisted, coverage/lifecycle reports regenerated when enabled, metrics emitted.

- **Search Flow:**
  1. API validates payload, resolves filters, and fetches SearchService dependency.
  2. Query vector computed using shared embedder; Qdrant search executed with optional HNSW parameters.
  3. Payload filters, lexical scoring, and coverage heuristics applied; optional ML model adjusts ranking.
  4. Graph context fetched per result (subject to timeout); metadata assembled; feedback optionally logged.

- **MCP Interaction:**
  1. FastMCP loads `GatewayClient` within lifespan to reuse HTTP connections.
  2. Tools gather parameters, enforce limit clamps, and call REST endpoints with scope-specific bearer tokens.
  3. Metrics record tool latency and failures; rich feedback surfaced back to MCP host.

## Dependencies & Integration
- **External Services:** Neo4j (Bolt protocol), Qdrant HTTP API, SentenceTransformer model downloads (PyTorch CPU wheels), optional OTLP collector.
- **Python Libraries:** FastAPI, httpx, apscheduler, qdrant-client, neo4j-driver, sentence-transformers, slowapi, prometheus-client, pydantic v2, opentelemetry.*.
- **Inter-service Communication:**
  - REST API <-> Neo4j via Bolt sessions.
  - REST API <-> Qdrant via HTTP.
  - MCP server <-> REST API via HTTPX.
  - Scheduler invokes ingestion pipeline in-process.

## Development & Operations
- **Environment Setup:** `python3.12 -m venv .venv`, `pip install -e .[dev]`. Lint with `ruff` and format via `black`. Type checking through `mypy` (plugins enabled for Pydantic).
- **Testing:** Primary suite under `tests/` with pytest markers for Neo4j (`-m neo4j`) and MCP smoke tests (`-m mcp_smoke`). Coverage via `pytest --cov=gateway --cov-report=term-missing`.
- **Observability:** Structured logging initialised in `gateway/observability/logging.py`, OpenTelemetry tracing optional via env toggles, Prometheus metrics exposed on `/metrics` (including backup gauges/counters such as `km_backup_runs_total`, `km_backup_last_status`, `km_backup_retention_deletes_total`) and enriched during ingestion/search/MCP flows.
- **Operational Playbooks:** Ingestion orchestrated via CLI or scheduler; backups triggered through MCP tool; lifecycle and coverage reports read from `KM_STATE_PATH/reports`.
- **Deployment Considerations:** Ensure secrets supplied through environment or secret management, mount persistent volumes for state, configure TLS/ingress for API and Qdrant, and monitor metrics for ingestion/scheduler health.
