# Duskmantle Knowledge Management Appliance

This repository packages a turnkey knowledge management stack that bundles the Knowledge Gateway, Qdrant, and Neo4j into a single container. It targets engineering teams and power users who need deterministic retrieval-augmented answers and graph-backed reasoning over their own repositories without standing up infrastructure.

## Highlights

- **Single container delivery:** Supervisor launches the gateway, Qdrant, and Neo4j together with baked-in defaults.
- **Deterministic ingestion:** Periodic jobs index docs, source, tests, and protobufs with provenance and coverage reporting.
- **Hybrid search + graph context:** Vector similarity fused with lexical overlap and live graph lookups for every result.
- **Embedded preview UI:** Visit `/ui/` for a bundled console shell; future sprints will light up search, subsystems, and lifecycle dashboards.
- **MCP-native interface:** Codex CLI (and other MCP clients) can call search, graph, ingest, backup, and feedback tools without touching raw HTTP APIs.
- **Offline ready:** Embedding models and dependencies are vendored so the appliance runs in air-gapped environments.

## LLM Agent Workflow

1. Run `bin/km-bootstrap`. It pulls the latest `ghcr.io/tachyon-beep/duskmantle-km` image, provisions `.duskmantle/{config,data,backups}`, and generates fresh credentials.
2. Drop or symlink the repositories, docs, or transcripts you want indexed into `.duskmantle/data/`. The container mounts this directory at `/workspace/repo` and the watcher fingerprints files so edits trigger delta ingests automatically.
3. Monitor ingest state. Leave `bin/km-watch` running for host-side polling, or hit `/metrics` and `/healthz` (with maintainer token if auth is enabled) to verify coverage and scheduler status.
   Visit `/ui/search` after bootstrap to issue hybrid queries through the bundled console (supply your reader token via the Tokens menu). Switch to `/ui/subsystems` to explore dependency chains and linked artifacts. The `/ui/lifecycle` tab plots spark lines once a few lifecycle snapshots exist, making stale docs and isolation trends easy to spot.
   Use the action buttons to copy ready-to-run MCP commands (`km-search`, `km-graph-subsystem`, recipes) or download JSON exports for issue triage.
   Tokens entered via the console are stored for the current browser session only; clear them anytime with the Tokens dialog when you step away from the machine.
4. Import the Codex MCP snippet from `docs/MCP_INTEGRATION.md` (or the per-tool recipes in `docs/MCP_RECIPES.md`). Any MCP-capable agent can now call `km-search`, `km-graph-*`, `km-ingest-*`, and `km-feedback-submit` without bespoke glue code.
5. Exercise the surface using the MCP smoke recipe (`docs/MCP_RECIPES.md` section 3) or run `pytest -m mcp_smoke`. Start with `km-upload`/`km-storetext` to add material, then query via `km-search`; `/search` responses include a `metadata.feedback_prompt`, so keep submitting feedback with `km-feedback-submit` until ranking telemetry stabilises.

## Core Capabilities

- **End-to-end ingestion** – discovers repository artifacts, normalises metadata, and writes to Qdrant and Neo4j with constraint enforcement.
- **Search with explainability** – `/search` returns scoring breakdowns (vector, lexical, subsystem signals) plus graph context for every hit.
- **Graph exploration** – `/graph/subsystems`, `/graph/nodes`, `/graph/search`, and `/graph/cypher` expose the knowledge graph for diagnostics and agents.
- **Operational tooling** – `/metrics`, `/healthz`, `/coverage`, `gateway-ingest`, `gateway-search`, `gateway-graph`, and backup helpers cover daily operations.
- **Release automation** – reproducible wheel/image pipelines, checksum generation, and smoke tests capture every acceptance run in `docs/ACCEPTANCE_DEMO_SNAPSHOT.md`.

## Quick Start

Prefer the detailed walkthrough in `docs/QUICK_START.md`. Agents should follow the **LLM Agent Workflow** above; dive into the manual steps below only when customising the container build, mounts, or runtime settings.

Summary (or simply run `bin/km-bootstrap` to let the repo pull the latest image, generate credentials, and start the container automatically):

1. Prepare working directories: `mkdir -p .duskmantle/{config,data}`. Copy or symlink the content you want indexed into `.duskmantle/data/` (this path is mounted at `/workspace/repo`). Use `bin/km-sweep` anytime to copy loose `*.md`, `*.docx`, `*.txt`, `*.doc`, or `*.pdf` files into `.duskmantle/data/docs/` so they’re picked up on the next ingest.
2. Build the container with `scripts/build-image.sh duskmantle/km:dev` (BuildKit enabled by default).
3. Launch it via `bin/km-run` (default container name `duskmantle`, mounts `.duskmantle/config` and `.duskmantle/data`). Override `KM_DATA_DIR`, `KM_REPO_DIR`, or `KM_IMAGE` as needed.
4. Kick off an ingest inside the container: `docker exec duskmantle gateway-ingest rebuild --profile local --dummy-embeddings`.
5. Verify `http://localhost:8000/readyz`, `/healthz`, and `/coverage`; inspect Prometheus metrics at `/metrics` (requires maintainer token if auth enabled).
6. Use `bin/km-backup` to snapshot `.duskmantle/config` before upgrades; restore with a simple `tar -xzf` into that directory.
7. Run `./infra/smoke-test.sh duskmantle/km:dev` to build, launch, ingest, and validate coverage end-to-end.
8. (Optional) Leave `bin/km-watch` running to detect file changes under `.duskmantle/data` and trigger ingestion automatically (pass `--metrics-port` to expose watcher metrics; the in-container watcher uses `KM_WATCH_METRICS_PORT`, default `9103`).

> Maintainer operations (uploads, text capture, ingest and backup triggers) append audit lines to `KM_STATE_PATH/audit/mcp_actions.log`. Include the file in your log rotation policy whenever MCP workflows are part of your day-to-day usage.

### UI Smoke Tests (Playwright)

- Run `bin/km-playwright` to install Node dependencies (`npm ci`) and execute the smoke suite. Pass additional arguments to forward them to `npx playwright test` (e.g., `bin/km-playwright -- --trace on`).
- Use `bin/km-playwright --no-install` when you want to reuse an existing `node_modules/` directory without reinstalling packages.
- The Playwright config boots `tests/playwright_server.py`, which seeds lifecycle history, disables schedulers, and serves the embedded UI at `http://127.0.0.1:8765` for the tests.

### Security Defaults

The appliance ships with permissive defaults so local demos start without extra configuration (Neo4j user/password `neo4j` / `neo4jadmin`, API auth disabled, no maintainer tokens). Before handling anything beyond disposable test data, rotate those credentials—set `KM_NEO4J_PASSWORD` to a non-default value, enable `KM_AUTH_ENABLED=true`, and supply reader/maintainer tokens ahead of launch. The gateway now exits on startup if auth is enabled without a maintainer token or a custom Neo4j password.

**Quick hardening checklist**

1. Generate fresh tokens (`./bin/km-make-tokens` prints ready-to-paste export lines) and pick a new Neo4j password. For example:

   ```bash
   ./bin/km-make-tokens
   export KM_NEO4J_PASSWORD='s3cure-pass'
   export KM_AUTH_ENABLED='true'
   # Paste the reader/admin exports emitted above, for example:
   export KM_READER_TOKEN='5f9f3c8f-0c1e-4e7f-9dd0-6a6c2fef71fb'
   export KM_ADMIN_TOKEN='de0b36ba-27b2-4b0d-a01f-5bb00e2fd940'
   ```

   The entrypoint automatically configures Neo4j with the values from `KM_NEO4J_USER`/`KM_NEO4J_PASSWORD`, so no manual `cypher-shell` work is required.

2. If a container is already running with the defaults, stop it, remove the old state (Neo4j stores the password hash on disk), re-export the environment variables above, and restart with `bin/km-run`. The new password will be applied as Neo4j initialises on boot.

3. Update any CLI or MCP clients to pass the new maintainer token when invoking admin endpoints (`KM_AUTH_ENABLED=true` enforces bearer tokens for `/graph/cypher`, `/metrics`, `/coverage`, ingest/backup triggers, etc.).

## Repository Layout

- `docs/` — Specifications, architecture design, implementation plan, and risk mitigation playbook.
- `docs/archive/` — Completed work-package plans and historical artefacts preserved for reference.
- `gateway/` — Python 3.12 application modules (API, ingestion, config, plugins).
- `infra/` — (Planned) Supervisor configs, resource profiles, helper scripts.
- `tests/` — Pytest suites and smoke tests for the turnkey appliance.
- `docs/MCP_RECIPES.md` — Practical MCP usage examples and automation patterns.
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
- Quick smoke check: `./infra/smoke-test.sh duskmantle/km:dev` builds the image, launches a disposable container, runs a smoke ingest, and verifies `/coverage`.
- Helper scripts live in `bin/`:
- `bin/km-run [--detach]` starts the container with sensible defaults; by default it mounts `.duskmantle/config` to `/opt/knowledge/var` and `.duskmantle/data` to `/workspace/repo`. Override via `KM_IMAGE`, `KM_DATA_DIR`, `KM_REPO_DIR`, or `KM_DOCKER_RUN_ARGS`.
- `bin/km-backup [archive.tgz]` archives the mounted state directory (default `.duskmantle/config`) into `.duskmantle/backups` with a timestamped filename.
- See `docs/ACCEPTANCE_DEMO_PLAYBOOK.md` for an end-to-end demo checklist that combines build, ingest, search/graph verification, backup/restore, and smoke testing.

## MCP Integration

The bundled `gateway-mcp` server mirrors gateway functionality into the Model Context Protocol so agents never need direct HTTP access. Install the project with dev extras (`pip install -e .[dev]`) and launch:

```bash
KM_GATEWAY_URL=http://localhost:8000 \
KM_ADMIN_TOKEN=${KM_ADMIN_TOKEN:-maintainer-token} \
gateway-mcp --transport stdio
```

Key tools (see `docs/MCP_INTERFACE_SPEC.md` for full schemas):

| Tool ID | Scope | Description |
|---------|-------|-------------|
| `km-search` | reader | Hybrid search returning chunks, scoring metadata, and optional graph context. |
| `km-graph-node` | reader | Fetch a node plus relationships by ID (e.g., `DesignDoc:docs/...`). |
| `km-graph-subsystem` | reader | Inspect subsystem details, related nodes, and artifacts. |
| `km-graph-search` | reader | Search graph entities by term (subsystems, design docs, source files). |
| `km-coverage-summary` | reader | Retrieve the latest coverage snapshot. |
| `km-lifecycle-report` | maintainer | Summarise isolated graph nodes, stale design docs, and subsystems missing tests. |
| `km-ingest-status` / `km-ingest-trigger` | maintainer | Inspect or trigger ingestion runs. |
| `km-recipe-run` | maintainer | Execute multi-step knowledge recipes (health checks, release prep). |
| `km-backup-trigger` | maintainer | Create a compressed state backup mirroring `bin/km-backup`. |
| `km-feedback-submit` | maintainer | Record relevance votes for training datasets. |

All MCP usage is mirrored to Prometheus (`km_mcp_requests_total`, `km_mcp_request_seconds`, `km_mcp_failures_total`) so dashboards can track agent activity. Use `pytest -m mcp_smoke` to validate the adapter end-to-end.

## Release Artifacts

- GitHub Actions `release.yml` builds wheels, Docker images, pushes the image to GitHub Container Registry (GHCR), runs smoke tests, and drafts a tagged release with artifacts (wheels, tarballs, checksums).
- `dist/SHA256SUMS` and `dist/IMAGE_SHA256SUMS` contain SHA256 hashes generated by `scripts/checksums.sh`.
- Container images are tagged `duskmantle/km:<version>` locally and published as `ghcr.io/<owner>/duskmantle-km:<version>` on GHCR. For this repository you can pull with `docker pull ghcr.io/tachyon-beep/duskmantle-km:1.0.1` (adjust owner/tag as needed).
- For air-gapped installs, download the image tarball from the release artifacts, load via `docker load -i duskmantle-km.tar`, and follow `docs/QUICK_START.md`.


## Configuration

- Full environment-variable reference: see [`docs/CONFIG_REFERENCE.md`](docs/CONFIG_REFERENCE.md).
- Quick tips:
  - Set `KM_AUTH_ENABLED=true` with new reader/maintainer tokens for any non-demo usage.
  - `KM_WATCH_ENABLED=true` makes the container hash `/workspace/repo` every `KM_WATCH_INTERVAL` seconds and run `gateway-ingest` automatically.
  - Scheduler (`KM_SCHEDULER_ENABLED=true`) and watcher can run together; both require maintainer tokens when auth is enabled.
  - Use `bin/km-watch` host-side if you prefer to keep automation outside the container.

### Observability & Automation

- Metrics exposed at `/metrics` (Prometheus format); audit history available at `/audit/history` (maintainer scope).
- Coverage reports downloadable via `/coverage` or from `/opt/knowledge/var/reports/coverage_report.json`. Lifecycle summaries live at `/lifecycle` and the matching JSON under `/opt/knowledge/var/reports/lifecycle_report.json`.
- Run `gateway-recipes list` (or `bin/km-recipe-run --help`) to discover automation bundles such as `release-prep` or `stale-audit`.
- `bin/km-watch` (host) or the internal watcher provides continuous ingestion; adjust cadence with `KM_WATCH_INTERVAL` / `--interval`, and expose metrics via `KM_WATCH_METRICS_PORT` or `--metrics-port`.
- Enable OpenTelemetry tracing with `KM_TRACING_ENABLED=true`; set `KM_TRACING_ENDPOINT` for remote collectors.
- `gateway-ingest audit-history --limit 10` summarises the last runs; add `--json` for machine output.
- Expose the MCP surface with `gateway-mcp` (local) or `bin/km-mcp-container` (inside the running container). MCP requests emit metrics (`km_mcp_requests_total`, etc.).
- Import `docs/dashboards/gateway_overview.json` into Grafana for an out-of-the-box metrics view (ingest status, latency, search vs graph throughput).
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
- Optional APScheduler can be enabled via `KM_SCHEDULER_ENABLED=true`. Configure interval mode via `KM_SCHEDULER_INTERVAL_MINUTES` or supply a cron schedule with `KM_SCHEDULER_CRON` (UTC). Jobs skip automatically when the repository HEAD has not changed or another run is in progress.
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

## Support & Community

- Support is community-driven and limited to GitHub Issues; no email, chat, or commercial channels are offered.
- Before filing, review `FAQ.md` and search existing issues. Choose the appropriate template (bug or feature) so triage stays consistent.
- Every bug report should include `/healthz`, relevant `/metrics`, recent logs, MCP smoke output, and (when available) your latest `docs/ACCEPTANCE_DEMO_SNAPSHOT.md`.
- Feature requests should be scoped, actionable, and linked to design docs or roadmap entries when possible.

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
