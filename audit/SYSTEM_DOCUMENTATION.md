# System Documentation

## Architecture Overview
- The gateway centres on a FastAPI application (`gateway/api/app.py`) that exposes REST routes for search, graph introspection, health, and reporting while serving the static UI.
- Supporting subsystems include the ingestion pipeline (`gateway/ingest`), hybrid search services (`gateway/search`), Neo4j graph access (`gateway/graph`), and the FastMCP bridge (`gateway/mcp`).
- State is persisted across three domains: Neo4j holds the domain graph, Qdrant stores vector embeddings, and the filesystem (under `KM_STATE_PATH`) retains audit databases, coverage/lifecycle reports, and feedback logs.
- Background processing is coordinated via APScheduler (`gateway/scheduler.py`) and optional CLI invocations (`gateway/ingest/cli.py`, `gateway/graph/cli.py`).

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

## Technology Stack
- **FastAPI & Uvicorn:** Serve REST endpoints, static UI assets, and manage dependency injection (`gateway/api`).
- **fastmcp:** Exposes the gateway as an MCP toolset (`gateway/mcp/server.py`) with HTTPX client bindings to the REST API.
- **Neo4j 5.x:** Primary graph store. Accessed via the official Bolt driver for schema migrations, query execution, and graph enrichment (`gateway/graph/service.py`, `gateway/ingest/neo4j_writer.py`).
- **Qdrant 1.15:** Vector database for chunk embeddings, accessed via `qdrant-client` for upserts, deletes, and hybrid search (`gateway/ingest/qdrant_writer.py`, `gateway/search/service.py`).
- **SentenceTransformers:** Provides embedding models for ingestion and ad-hoc search scoring (`gateway/ingest/embedding.py`).
- **Prometheus client + SlowAPI:** Surface metrics (`gateway/observability/metrics.py`) and enforce rate limits.
- **APScheduler & FileLock:** Drive scheduled ingestion runs and guard concurrent executions (`gateway/scheduler.py`).
- **OpenTelemetry:** Wraps ingestion spans and captures pipeline metrics (`gateway/ingest/pipeline.py`, `gateway/observability/tracing.py`).

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

## API & Interface Layer
- **/search** (POST): Authenticated reader endpoint accepting query, filters, and graph inclusion flags; returns ranked chunks with optional graph context and feedback hints.
- **/search/weights** (GET): Maintainer endpoint exposing resolved weight profile and thresholds.
- **/graph** (GET/POST): Reader endpoints for subsystems, nodes, orphans, and search; maintainer-only `/graph/cypher` for read-only Cypher queries.
- **/coverage**, **/lifecycle**, **/lifecycle/history**, **/audit/history**: Maintainer reporting endpoints sourcing JSON assets and SQLite audit logs.
- **/healthz**, **/readyz**, **/metrics**: Operational status, readiness, and Prometheus metrics surfaces.
- **Static UI**: Served from `gateway/ui` providing basic navigation and documentation.
- **FastMCP Tools:** `km-search`, `km-graph-*`, `km-ingest-*`, `km-feedback-submit`, `km-upload`, `km-storetext`, etc. (`gateway/mcp/server.py`). They proxy to REST endpoints via `GatewayClient` with token management.

## Configuration & Deployment
- **Runtime Settings:** Centralised in `gateway/config/settings.py` using Pydantic `AppSettings`. Environment variables prefixed with `KM_` control auth, data stores, scheduler, search weights, tracing, and ingest behaviour. Helper methods clamp values and derive scheduler triggers and weight profiles.
- **Docker Image:** Builds a Python 3.12 environment bundling Qdrant and Neo4j binaries (`Dockerfile`, `infra/docker-entrypoint.sh`). Supervisord orchestrates all processes. Exposes ports 8000 (API), 6333/6334 (Qdrant), and 7474/7687 (Neo4j).
- **Compose Scaffold:** `infra/examples/docker-compose.sample.yml` mounts repo content and state directories, surfaces core env vars, and demonstrates minimal configuration.
- **State Directories:** `KM_STATE_PATH` (default `/opt/knowledge/var`) stores audit SQLite DBs, coverage/lifecycle reports, scheduler locks, backups, and search feedback logs.
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
- **Observability:** Structured logging initialised in `gateway/observability/logging.py`, OpenTelemetry tracing optional via env toggles, Prometheus metrics exposed on `/metrics` and enriched during ingestion/search/MCP flows.
- **Operational Playbooks:** Ingestion orchestrated via CLI or scheduler; backups triggered through MCP tool; lifecycle and coverage reports read from `KM_STATE_PATH/reports`.
- **Deployment Considerations:** Ensure secrets supplied through environment or secret management, mount persistent volumes for state, configure TLS/ingress for API and Qdrant, and monitor metrics for ingestion/scheduler health.
