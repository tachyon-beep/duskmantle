# Duskmantle Knowledge Management Appliance

This repository packages a turnkey knowledge management stack that bundles the Knowledge Gateway, Qdrant, and Neo4j into a single container. It targets Esper-Lite engineers and power users who need deterministic retrieval-augmented answers and graph-backed reasoning over their own repositories without standing up infrastructure.

## Highlights
- **Single container delivery:** Supervisor launches the gateway, Qdrant, and Neo4j together with baked-in defaults.
- **Deterministic ingestion:** Periodic jobs index docs, source, tests, and protobufs with provenance and coverage reporting.
- **Graph-aware retrieval:** Combined vector search and Neo4j context power downstream LLM agents and humans alike.
- **Offline ready:** Embedding models and dependencies are vendored so the appliance runs in air-gapped environments.

## Quick Start
1. Clone this repository alongside the project you want to index.
2. Build the development image (requires Docker; Python 3.12 is only needed for local library development):
   ```bash
   docker build -t duskmantle/km:dev .
   ```
3. Build and run the appliance, mounting your target repository and a persistent data directory:
   ```bash
   docker build -t duskmantle/km:dev .
   docker run --rm \
     -p 8000:8000 \
     -v $(pwd)/data:/opt/knowledge/var \
     -v /path/to/your/repo:/workspace/repo \
     duskmantle/km:dev
   ```
4. Trigger a manual ingest (optional) in another terminal:
   ```bash
   docker exec $(docker ps -qf ancestor=duskmantle/km:dev) \
     gateway-ingest rebuild --profile local
   ```
5. Query the API at `http://localhost:8000/search` and explore graph endpoints under `/graph/...`.

## Repository Layout
- `docs/` — Specifications, architecture design, implementation plan, and risk mitigation playbook.
- `gateway/` — Python 3.12 application modules (API, ingestion, config, plugins).
- `infra/` — (Planned) Supervisor configs, resource profiles, helper scripts.
- `tests/` — Pytest suites and smoke tests for the turnkey appliance.
- `AGENTS.md` — Contributor guide tailored for coding agents and maintainers.

## Local Development
1. Ensure Python 3.12 is available on your workstation.
2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies (runtime + development extras):
   ```bash
   pip install -e .[dev]
   ```
4. (Optional) Install the slimmer runtime set used by the container build:
   ```bash
   pip install -r gateway/requirements.txt
   ```
5. Run the smoke tests:
   ```bash
   pytest
   ```

## Container Runtime
- Entrypoint script: `/opt/knowledge/docker-entrypoint.sh` (invoked automatically) validates the mounted volume and launches Supervisord.
- Process manager: `supervisord` starts Qdrant (`6333`/`6334`), Neo4j (`7474`/`7687`), and the gateway API (`8000`). Logs live under `/opt/knowledge/var/logs/`.
- Persistent state: mount a host directory to `/opt/knowledge/var` for Qdrant snapshots, Neo4j data/logs, and audit ledgers.
- Quick smoke check: `./infra/smoke-test.sh duskmantle/km:dev` builds the image, launches a disposable container, and polls `/readyz`.

## Configuration
Key environment variables (all prefixed with `KM_`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_REPO_PATH` | `/workspace/repo` | Mounted repository to ingest |
| `KM_QDRANT_URL` | `http://localhost:6333` | Qdrant API endpoint |
| `KM_QDRANT_COLLECTION` | `esper_knowledge_v1` | Collection name for embeddings |
| `KM_NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt URI |
| `KM_NEO4J_USER`/`KM_NEO4J_PASSWORD` | `neo4j`/`changeme` | Neo4j authentication |
| `KM_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model identifier |
| `KM_INGEST_WINDOW`/`KM_INGEST_OVERLAP` | `1000` / `200` | Chunking parameters |
| `KM_INGEST_DRY_RUN` | `false` | Disable writes for test runs |
| `KM_INGEST_USE_DUMMY` | `false` | Force deterministic embeddings (non-prod) |

Set these in your environment or an `.env` file before building/running the container.

## Getting Involved
- Review the core specification in `docs/KNOWLEDGE_MANAGEMENT.md` and the companion design and implementation plan documents.
- Follow the practices in `AGENTS.md` for coding style, testing, and workflow expectations.
- Open issues for questions or enhancements—target users are experienced operators, so include environment details and reproduction steps.

## Roadmap References
- Architecture decisions: `docs/KNOWLEDGE_MANAGEMENT_DESIGN.md`
- Implementation phases & milestones: `docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md`
- Risk tracking and mitigations: `docs/RISK_MITIGATION_PLAN.md`

A CHANGELOG and release notes will ship once the first containerized milestone lands.
