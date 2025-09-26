# Knowledge Management System Design

## 1. Executive Summary
This design delivers a turnkey knowledge management appliance for Esper-Lite engineers and a small circle of power users. A single Docker image bundles the Python Knowledge Gateway, embedded Qdrant vector store, and Neo4j graph database, preconfigured for one-command startup. Users mount a host directory for persistent data, run the container, and immediately gain retrieval-augmented answers and graph-aware insights over repository artifacts without assembling infrastructure themselves.

## 2. Architectural Overview
The runtime is a trio of co-located services managed inside the container by a lightweight supervisor. The gateway orchestrates ingestion and exposes APIs, while Qdrant and Neo4j handle vector similarity and relationship reasoning. Scheduled ingestion tasks run within the same process space.

### 2.1 Component Diagram
```
+-----------------------------------------------------------+
|                Single Knowledge Management Container      |
|                                                           |
|  +--------------+    upsert/search    +-----------+       |
|  | Knowledge    |<------------------->|  Qdrant   |       |
|  | Gateway API  |                    /| Vector DB |\      |
|  +------+-------+   graph sync      / +-----------+ \     |
|         | REST + Cypher            /                \     |
|         v                         v                  v    |
|  +------+-------+        +-----------+     +----------------+
|  | Ingestion    |------->|  Neo4j    |<----| Supervisor/Init |
|  | Scheduler    |        |  Graph DB |     +----------------+
|  +--------------+        +-----------+                        |
|                                                           |
+-----------------------------------------------------------+
```

### 2.2 Runtime Topology
- **Distribution:** Single Docker image published via container registry. Includes all binaries, configuration defaults, and entrypoint supervisor (e.g., s6-overlay or supervisord).
- **Execution:** `docker run --rm -p 8000:8000 -v $(pwd)/data:/opt/knowledge/var duskmantle/km:latest` spins up the full stack. The supervisor launches Qdrant, Neo4j, then the gateway.
- **Persistence:** Host-mounted volume `/opt/knowledge/var` stores Qdrant snapshots, Neo4j data/logs, and audit ledger. Optional secondary mounts supply repository contents for ingestion.
- **Offline Operation:** All dependencies (embedding model, Python wheels) are baked into the image to support air-gapped users.

## 3. Core Services

### 3.1 Knowledge Gateway
- FastAPI app with APScheduler, Pydantic models, and CLI entry points.
- Supervises ingestion lifecycle, exposes REST API on port 8000, and surfaces admin endpoints.
- Communicates with Qdrant via localhost gRPC/HTTP; connects to Neo4j bolt://localhost:7687.
- Ships with plugin registry so adopters can drop in additional artifact readers under `gateway/plugins/`.

### 3.2 Qdrant Vector Store
- Runs using the official Qdrant binary inside the container.
- Collection `esper_knowledge_v1` sized for MiniLM (384 dimensions). Uses on-disk storage rooted at `/opt/knowledge/var/qdrant`.
- HNSW parameters preset for balanced recall/latency given modest corpus (<5M chunks).

### 3.3 Neo4j Graph Database
- Community edition packaged in the container with APOC plugin.
- Data directory `/opt/knowledge/var/neo4j/data` persisted via host volume.
- Authentication enabled with default credentials overridden through environment variables (e.g., `KM_NEO4J_PASS`).

## 4. Data & Schema Design

### 4.1 Vector Payload Model
| Field | Purpose |
|-------|---------|
| `path` | Relative file path of source artifact |
| `artifact_type` | Enum: `doc`, `code`, `test`, `proto`, `config` |
| `subsystem` | Derived domain (e.g., `Kasmina`) |
| `leyline_entities` | Array of detected message names |
| `telemetry_signals` | Array of detected channel IDs |
| `git_commit` | Last indexed commit SHA |
| `git_timestamp` | Last modified epoch seconds |
| `content_digest` | SHA256 for dedupe |
| `chunk_id` | `${path}::${chunk_index}` |
| `environment` | Label (default `local`) |
| `provenance` | JSON blob with model + ingest run metadata |

### 4.2 Graph Schema
- Nodes: `Subsystem`, `SourceFile`, `DesignDoc`, `TestCase`, `LeylineMessage`, `TelemetryChannel`, optional `Chunk` nodes.
- Relationships: `BELONGS_TO`, `DESCRIBES`, `VALIDATES`, `IMPLEMENTS`, `EMITS`, `DEPENDS_ON`, `HAS_CHUNK`.
- Constraints and indexes are applied at container startup via Cypher migrations embedded in the gateway image.

### 4.3 Metadata & Provenance
- Provenance tracked per chunk and persisted in an append-only SQLite ledger at `/opt/knowledge/var/audit/audit.db`.
- Each ingestion run logs configuration snapshot (model version, chunk parameters) and repository HEAD for reproducibility.

## 5. Ingestion Pipeline

### 5.1 Discovery & Classification
- The container expects the repository to be mounted at `/workspace/repo`. Discovery is implemented in `gateway/ingest/discovery.py` and walks `docs/`, `src/esper/`, `tests/`, `src/esper/leyline/_generated/`, and optional `.codacy/` paths.
- Subsystem inference is derived from path prefixes (e.g., `src/esper/kasmina/` → `Kasmina`) with regex fallbacks for Leyline messages and telemetry tags inside the file content.
- Git metadata (last commit hash/timestamp) is captured via lightweight `git log` calls when available; failures degrade gracefully to `None`.

### 5.2 Chunking & Embedding
- 1,000-character windows with 200-character overlap by default; runtime chunker implemented in `gateway/ingest/chunking.py` with environment-tunable window/overlap values.
- Uses `sentence-transformers/all-MiniLM-L6-v2` shipped offline. Batched inference (batch=64) via CPU; togglable GPU support if container launched with `--gpus`. A deterministic dummy embedder supports dry runs and tests.

### 5.3 Index & Graph Upserts
- Gateway mediates Qdrant and Neo4j writes sequentially to avoid cross-process coordination complexity. `gateway/ingest/qdrant_writer.py` ensures the collection exists and upserts chunk payloads; `gateway/ingest/neo4j_writer.py` maps artifacts to `SourceFile`, `DesignDoc`, and `TestCase` nodes with `HAS_CHUNK`, `BELONGS_TO`, `DESCRIBES`, and `VALIDATES` relationships.
- Upserts are idempotent; stale entries detected via digest comparison and removed during cleanup sweeps.
- Optional `--dry-run` flag allows users to preview ingestion without mutating stores.

### 5.4 Scheduling Strategy
- APScheduler triggers default ingestion every 30 minutes from within the container, gating runs on repository HEAD changes.
- Manual triggers: `gateway-ingest rebuild --profile local` (optionally with `--dry-run` or `--dummy-embeddings` for testing).
- Coverage report generated nightly and stored under `/opt/knowledge/var/reports/coverage_report.json`.

## 6. Query & Retrieval Workflows

### 6.1 RAG Query Flow
1. Client calls `POST /search` on the container’s exposed API.
2. Gateway queries Qdrant for top-k vectors, blending dense similarity with optional BM25 keyword scoring.
3. For each chunk, the gateway resolves graph context from Neo4j, bundling subsystem dependencies and related documents.
4. Response returned as JSON for downstream LLM prompting or manual inspection.

### 6.2 Graph Reasoning Use Cases
- `GET /graph/subsystem/{name}` surfaces connected subsystems, telemetry channels, and docs.
- `GET /graph/leyline/{message}` reveals implementers and source definitions.
- `POST /graph/cypher` (maintainer scope) executes read-only Cypher queries to support advanced users.

### 6.3 API Surface
- `GET /healthz`, `/readyz`, `/metrics`, `/coverage`, `/audit/history`.
- `POST /ingest/run` for ad-hoc ingestion (maintainer scope).
- JSON schemas published under `/openapi.json` for client generation.

## 7. Operational Considerations

### 7.1 Observability & Diagnostics
- Prometheus-compatible metrics endpoint on `/metrics` covering ingestion durations, queue sizes, Qdrant latency, Neo4j query counts.
- Structured logs emitted to stdout with ingest run IDs; users can redirect container logs to files if desired.
- Minimal OpenTelemetry traces recorded locally and optionally exported by mounting a collector configuration.

### 7.2 Security & Access Control
- Local deployments default to static credentials defined via environment variables (`KM_ADMIN_TOKEN`, `KM_READER_TOKEN`).
- HTTPS termination left to the host environment; documentation provides reverse proxy examples (Caddy, Nginx).
- Secrets stored in mounted config files; no external secret manager dependency to keep turnkey footprint low.

### 7.3 Resilience & Maintenance
- Persistence handled by host volume backups (rsync or snapshot tooling).
- Supervisor (`supervisord`) monitors Qdrant, Neo4j, and the FastAPI gateway; automatic restart on crash with exponential backoff.
- For upgrades, users pull the new image, stop existing container, back up `/opt/knowledge/var`, and redeploy. Migration scripts run automatically on startup.
- Risk mitigations for image footprint, persistence checks, resource tuning, and observability are expanded in `docs/RISK_MITIGATION_PLAN.md`.

## 8. Implementation Roadmap

### 8.1 Milestones
1. **Container Foundation:** Scaffold gateway, integrate supervisor, ship compose/dev scripts, ingest docs.
2. **Full Indexing:** Expand ingestion to code/tests, populate Neo4j, finalize API responses.
3. **Turnkey Hardening:** Add security toggles, metrics, nightly scheduler, offline asset bundling.
4. **Release Packaging:** Produce reference `docker run` instructions, smoke tests, and publish image/Tarball.

### 8.2 Open Questions
- What minimum host resources should we document (CPU/RAM/disk) for smooth operation?
- Which optional repositories or additional mounts should the turnkey release support by default?
- How frequently do target users expect to refresh indexes in air-gapped scenarios?
