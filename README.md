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
3. Build and run the appliance, mounting your target repository and a persistent data directory (pass `--network=host` if your environment restricts DNS lookups during builds):
   ```bash
   docker build --network=host -t duskmantle/km:dev .
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
5. Query the API at `http://localhost:8000/search` (vector search with graph context per result) and explore graph endpoints under `/graph/...`.

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
6. Apply pending Neo4j migrations when graph schema changes:
   ```bash
   gateway-graph migrate
   ```
   The packaged container already exports `KM_GRAPH_AUTO_MIGRATE=true`, so migrations run automatically at API startup with detailed logging of pending/Applied IDs. For change-controlled environments, leave the variable unset and invoke the CLI (or a pipeline hook) as part of your deploy.

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
| `KM_NEO4J_USER`/`KM_NEO4J_PASSWORD` | `neo4j`/`neo4jadmin` | Neo4j authentication (override for production) |
| `KM_NEO4J_AUTH_ENABLED` | `false` | Enable to require credentials (`true` for secured deployments) |
| `KM_STATE_PATH` | `/opt/knowledge/var` | Base directory for audit and coverage artifacts |
| `KM_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model identifier |
| `KM_INGEST_WINDOW`/`KM_INGEST_OVERLAP` | `1000` / `200` | Chunking parameters |
| `KM_INGEST_DRY_RUN` | `false` | Disable writes for test runs |
| `KM_INGEST_USE_DUMMY` | `false` | Force deterministic embeddings (non-prod) |
| `KM_AUTH_ENABLED` | `false` | Toggle bearer-token checks on API routes |
| `KM_READER_TOKEN` / `KM_ADMIN_TOKEN` | _unset_ | Tokens for reader/maintainer scopes |
| `KM_RATE_LIMIT_REQUESTS` / `KM_RATE_LIMIT_WINDOW` | `120` / `60` | Rate limit budget (requests per seconds window) |
| `KM_SCHEDULER_ENABLED` | `false` | Enable APScheduler ingestion jobs |
| `KM_SCHEDULER_INTERVAL_MINUTES` | `30` | Interval for scheduled ingestion runs |
| `KM_COVERAGE_ENABLED` | `true` | Persist coverage reports after ingestion |
| `KM_GRAPH_AUTO_MIGRATE` | `false`¹ | Run Neo4j schema migrations automatically at startup |
| `KM_TRACING_ENABLED` | `false` | Enable OpenTelemetry tracing for the API and ingestion jobs |
| `KM_TRACING_ENDPOINT` | _unset_ | OTLP HTTP collector endpoint (e.g., `http://otel-collector:4318/v1/traces`) |
| `KM_TRACING_HEADERS` | _unset_ | Comma-separated `key=value` pairs forwarded to the OTLP exporter |
| `KM_TRACING_SAMPLE_RATIO` | `1.0` | Fraction of requests/jobs sampled into traces (0.0 – 1.0) |
| `KM_TRACING_SERVICE_NAME` | `duskmantle-knowledge-gateway` | Service name attached to exported spans |
| `KM_TRACING_CONSOLE_EXPORT` | `false` | Mirror spans to stdout alongside OTLP export (local debugging) |
| `KM_SEARCH_WEIGHT_PROFILE` | `default` | Named bundle of search weights (`default`, `analysis`, `operations`, `docs-heavy`) |
| `KM_SEARCH_W_SUBSYSTEM` | `0.28` | Weight applied to subsystem affinity boosts in `/search` scoring (overrides profile) |
| `KM_SEARCH_W_RELATIONSHIP` | `0.05` | Weight applied per relationship in `/search` scoring (capped at five, overrides profile) |
| `KM_SEARCH_W_SUPPORT` | `0.09` | Weight applied to supporting artifacts (design docs/tests, overrides profile) |
| `KM_SEARCH_W_COVERAGE_PENALTY` | `0.15` | Penalty applied in proportion to missing coverage (overrides profile) |
| `KM_SEARCH_W_CRITICALITY` | `0.12` | Weight applied to subsystem criticality score (graph fallback when chunk metadata absent) |
| `KM_SEARCH_SCORING_MODE` | `heuristic` | Choose `ml` to enable learned ranking coefficients (requires model artifact) |
| `KM_SEARCH_MODEL_PATH` | _unset_ | Absolute path to model JSON when `KM_SEARCH_SCORING_MODE=ml` (defaults to `state_path/feedback/models/model.json`) |
| `KM_SEARCH_WARN_GRAPH_MS` | `250` | Emit a warning log when a single graph enrichment exceeds this latency (milliseconds) |

Set these in your environment or an `.env` file before building/running the container.

¹ The bundled container runtime exports `KM_GRAPH_AUTO_MIGRATE=true`. Production templates should set it to `false` and call `gateway-graph migrate` (or an equivalent pipeline step) during deployment. See `infra/examples/production.env` for a starter override file.

### Observability & Security
- Metrics exposed at `/metrics` (Prometheus format); audit history available at `/audit/history` (maintainer scope).
- Coverage reports downloadable via `/coverage` (maintainer scope) or from `/opt/knowledge/var/reports/coverage_report.json`.
- Logs emitted as JSON with `ingest_run_id`, artifact counts, and timing metadata.
- Distributed tracing (FastAPI + ingestion pipeline) is available when `KM_TRACING_ENABLED=true`; point `KM_TRACING_ENDPOINT` at your OTLP collector or enable console export for local inspection.
- Use the bundled CLI to review recent runs: `gateway-ingest audit-history --limit 10` (add `--json` for machine parsing).
- Search telemetry and MCP feedback are persisted under `/opt/knowledge/var/feedback/events.log` for ranking model training; each entry records query text, scoring breakdown, optional context, and vote captured from the requesting agent.
- Inspect the active search weighting with `gateway-search show-weights` or `GET /search/weights` (maintainer scope); slow graph lookups generate `graph_lookup_slow` warnings when they exceed `KM_SEARCH_WARN_GRAPH_MS`.
- Export training datasets from accumulated feedback with `gateway-search export-training-data` (choose CSV or JSONL, optionally require explicit votes). Outputs land in `/opt/knowledge/var/feedback/datasets/` by default.
- Fit a first-pass ranking model with `gateway-search train-model <dataset.csv>` to produce JSON artifacts under `/opt/knowledge/var/feedback/models/`. The trainer solves a linear regression across captured signals and reports simple metrics (MSE, R²).
- Apply retention or sanitisation with `gateway-search prune-feedback --max-age-days 30` before exporting, and redact sensitive columns via `gateway-search redact-dataset datasets/training.csv --drop-query --drop-context`.
- Benchmark trained models using `gateway-search evaluate-model datasets/validation.csv model.json` to generate MSE/R²/NDCG metrics before promoting to inference.
- Run `gateway-graph migrate` after schema changes or rely on the bundled default (`KM_GRAPH_AUTO_MIGRATE=true`) to apply migrations automatically. Startup logs now report pending IDs before execution and completion status afterwards; failures are emitted with stack traces but do not block boot.
- `/healthz` surfaces coverage freshness, audit ledger status, and scheduler state alongside the overall result; `/readyz` remains a simple readiness probe.
- Graph context is exposed via `/graph/subsystems/{name}`, `/graph/nodes/{id}`, `/graph/search`, and maintainer-only `/graph/cypher` (read-only Cypher) for deeper analysis.
- `/search` responses include a `scoring` breakdown (`vector_score`, `adjusted_score`, per-signal contributions such as `path_depth`, `subsystem_criticality`, and `freshness_days`). Set `KM_SEARCH_WEIGHT_PROFILE` (`default`, `analysis`, `operations`, `docs-heavy`) to load preset weighting bundles; any `KM_SEARCH_W_*` variables override the bundle. Use `KM_SEARCH_SORT_BY_VECTOR=true` to bypass graph boosts during troubleshooting.
- Observability includes search-specific metrics: `km_search_graph_cache_events_total` (cache hits/misses/errors), `km_search_graph_lookup_seconds` (Neo4j lookup latency), and `km_search_adjusted_minus_vector` (ranking deltas). Add these to dashboards to spot graph regressions or ranking drift.
- To enable learned ranking, set `KM_SEARCH_SCORING_MODE=ml` and point `KM_SEARCH_MODEL_PATH` at a JSON artifact produced by `gateway-search train-model`; responses will include per-feature contributions under `scoring.model` along with the active `metadata.scoring_mode`.
- Optional subsystem metadata: provide `docs/subsystems.json` (e.g., `{ "Kasmina": { "criticality": "high" } }`) or `.metadata/subsystems.json` to annotate criticality used by scoring heuristics.
- Rate limiting and bearer-token auth are optional but recommended for multi-user deployments.
- Optional APScheduler can be enabled via `KM_SCHEDULER_ENABLED=true`; jobs skip automatically when the repository HEAD has not changed or another run is in progress.
- See `docs/OBSERVABILITY_GUIDE.md` for detailed dashboards, alerting examples, and troubleshooting playbooks covering the full telemetry stack.
- Integration validation: run `pytest -m neo4j` with `NEO4J_TEST_URI`/credentials set to confirm graph topology against a live Neo4j instance.
  ```bash
  docker run -d --rm --name neo4j-test -p 7687:7687 -e NEO4J_AUTH=neo4j/secret neo4j:5
  NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=secret pytest -m neo4j
  ```

### Machine-Learned Ranking Workflow
1. **Collect feedback:** ensure MCP-driven searches supply a `feedback` payload; inspect `/opt/knowledge/var/feedback/events.log` for JSONL events (each row includes `request_id`, `scoring`, and votes).
2. **Prune & redact (optional):** limit history with `gateway-search prune-feedback --max-age-days 30` and scrub sensitive fields using `gateway-search redact-dataset <dataset> --drop-query --drop-context --drop-note`.
3. **Export training/validation sets:** `gateway-search export-training-data --require-vote --output feedback/datasets/training.csv` (repeat for a holdout dataset if desired).
4. **Train coefficients:** `gateway-search train-model feedback/datasets/training.csv --output feedback/models/model.json` stores weights and intercept alongside training metrics.
5. **Evaluate before rollout:** `gateway-search evaluate-model feedback/datasets/validation.csv feedback/models/model.json` prints MSE/R²/NDCG/Spearman so you can compare against heuristics.
6. **Enable in runtime:** set `KM_SEARCH_SCORING_MODE=ml` and (optionally) `KM_SEARCH_MODEL_PATH` to the artifact path. Restart the gateway; `/search` responses now report the active mode and feature contributions under `scoring.model`. Failures to load the artifact automatically fall back to heuristic scoring with a warning in logs.

## Getting Involved
- Review the core specification in `docs/KNOWLEDGE_MANAGEMENT.md` and the companion design and implementation plan documents.
- Follow the practices in `AGENTS.md` for coding style, testing, and workflow expectations.
- Open issues for questions or enhancements—target users are experienced operators, so include environment details and reproduction steps.

## Roadmap References
- Architecture decisions: `docs/KNOWLEDGE_MANAGEMENT_DESIGN.md`
- Graph API surface: `docs/GRAPH_API_DESIGN.md`
- Implementation phases & milestones: `docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md`
- Risk tracking and mitigations: `docs/RISK_MITIGATION_PLAN.md`
- Search ranking roadmap: `docs/SEARCH_SCORING_PLAN.md`

A CHANGELOG and release notes will ship once the first containerized milestone lands.
