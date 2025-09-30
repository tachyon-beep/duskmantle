# Agent Playbook

This guide orientates coding agents and maintainers who interact with the Duskmantle Knowledge Management appliance. Use it alongside the specification (`docs/KNOWLEDGE_MANAGEMENT.md`), design (`docs/KNOWLEDGE_MANAGEMENT_DESIGN.md`), and implementation plan (`docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md`).

## Instruction Hierarchy & Working Agreements

- Follow instructions in priority order: system → developer → user → repository docs → this playbook.
- Always read linked specs before editing code or docs touching that area; confirm assumptions with the implementation plan.
- Scope work tightly. If a task spans code, config, and docs, update them in the same change.
- Use the planning tool for multi-step work (never single-step plans). Update the plan as you finish steps.
- Prefer `rg`/`rg --files` for repo searches. Avoid destructive commands unless explicitly requested.
- Do not revert or overwrite user-owned changes outside your scope; ask the user if unexpected deltas appear.

## Repository Layout & Key References

- Runtime code: `gateway/` with subpackages `api/`, `ingest/`, `config/`, `plugins/`, `mcp/`.
- Tests mirror runtime modules under `tests/` (e.g., `tests/ingest/`, `tests/mcp/`).
- Docs live in `docs/` (`KNOWLEDGE_MANAGEMENT*.md`, `MCP_INTERFACE_SPEC.md`, `OBSERVABILITY_GUIDE.md`, etc.).
- Container and helper scripts: `infra/`, `bin/`, `scripts/`.
- Release notes & changelog: `RELEASE.md`, `CHANGELOG.md`, `dist/` checksums.

## Environment Setup & Tooling

1. Create a Python 3.12 virtual environment: `python3.12 -m venv .venv && source .venv/bin/activate`.
2. Install dependencies for development: `pip install -e .[dev]` (optionally also `pip install -r gateway/requirements.txt` to mirror container deps).
3. Format with `black` (88 columns) and lint with `ruff`. Type hints (PEP 484) are mandatory in gateway modules.
4. Keep modules `snake_case.py`, classes `PascalCase`, CLI entry points `snake_case` verbs. YAML configs live under `gateway/config/` with kebab-case filenames.

## Development Workflow

- Confirm the change against design docs and open TODOs before editing.
- Use focused branches and Conventional Commit messages (`feat:`, `fix:`, `docs:`...).
- When touching ingestion or graph logic, update related docs and configs together.
- After coding, run targeted tests plus `pytest --cov=gateway --cov-report=term-missing` when feasible.
- For container-affecting changes, run `./infra/smoke-test.sh` or the turnkey workflow described in `docs/QUICK_START.md`.

## Runtime Operations & Scheduling

- Build the development image: `docker build --network=host -t duskmantle/km:dev .` (or `scripts/build-image.sh` for tagged builds).
- Run the container: `docker run --rm -p 8000:8000 -p 6333:6333 -p 7687:7687 -v $(pwd)/.duskmantle/config:/opt/knowledge/var -v $(pwd)/.duskmantle/data:/workspace/repo duskmantle/km:dev` (prefer `bin/km-run` and `bin/km-bootstrap` for scripted setups).
- Trigger ingest inside the container: `docker exec <container> gateway-ingest rebuild --profile local --dry-run --dummy-embeddings` (drop flags in production).
- Scheduler knobs: `KM_SCHEDULER_ENABLED=true`, `KM_SCHEDULER_INTERVAL_MINUTES=<mins>` or `KM_SCHEDULER_CRON=<expr>`. Watcher knobs: `KM_WATCH_ENABLED=true`, `KM_WATCH_INTERVAL=<secs>`.
- Auth defaults to disabled; enable with `KM_AUTH_ENABLED=true`, provide `KM_READER_TOKEN`/`KM_ADMIN_TOKEN`, and (optionally) set `KM_NEO4J_AUTH_ENABLED=true` with `KM_NEO4J_USER`/`KM_NEO4J_PASSWORD`.
- Neo4j migrations: run `gateway-graph migrate` for manual control or rely on `KM_GRAPH_AUTO_MIGRATE=true` (default) during startup.

## Observability & Troubleshooting

- Health: `/readyz` (readiness), `/healthz` (includes coverage freshness, audit ledger, scheduler state).
- Metrics: `/metrics` exposes Prometheus counters/histograms (`km_search_graph_cache_events_total`, `km_search_graph_lookup_seconds`, `km_mcp_requests_total`, etc.).
- Audit: `/audit/history`, `gateway-ingest audit-history --limit 10`, or `/metrics` maintainer slices for ingest provenance.
- Graph & search validation: `/graph/subsystems/{name}`, `/graph/nodes/{id}`, `/graph/search`, `/graph/cypher` (maintainer); `/search` responses should include `graph_context` and `scoring.signals` (`path_depth`, `coverage_ratio`, `criticality_score`, `freshness_days`).
- Tracing: set `KM_TRACING_ENABLED=true`, `KM_TRACING_ENDPOINT=<otlp>` for remote collectors, or enable console export for local spans.

## Release & Artifact Checklist

- Build images and wheels with `scripts/build-image.sh` or CI workflows; verify SHA256 hashes with `scripts/checksums.sh` and the contents of `dist/IMAGE_SHA256SUMS`.
- Container tags follow `duskmantle/km:<version>` locally; published images live at `ghcr.io/<owner>/duskmantle-km:<version>`.
- For air-gapped installs, export via `docker save` and distribute alongside checksum files; document upgrade paths in `docs/QUICK_START.md` and `RELEASE.md`.
- Acceptance runs should exercise search, graph queries, ingest rebuilds, and backup/restore per `docs/ACCEPTANCE_DEMO_PLAYBOOK.md`.

## MCP & Agent Integrations

- MCP server entry point: `gateway-mcp` (Python console script) or `bin/km-mcp`. Configure with `KM_GATEWAY_URL`, `KM_READER_TOKEN`, `KM_ADMIN_TOKEN`, etc.
- Tool surface (see `docs/MCP_INTERFACE_SPEC.md` & `docs/MCP_RECIPES.md`): `km-search`, `km-graph-node`, `km-graph-subsystem`, `km-graph-search`, `km-coverage-summary`, `km-ingest-status`, `km-backup-trigger`, `km-feedback-submit`.
- Run MCP smoke tests with `pytest -m mcp_smoke` or follow the scripted recipe in `docs/MCP_RECIPES.md` §3.
- Telemetry: MCP invocations emit metrics (`km_mcp_requests_total`, latency histograms) and structured logs; ensure dashboards include MCP panels when shipping changes that touch the interface.

## Checklist Before Exiting a Task

- Changes align with the spec/design/plan documents and this playbook.
- Code formatted (`black`), linted (`ruff`), and typed.
- Tests updated/executed; smoke tests run when runtime or ingestion logic changes.
- Documentation and configs updated together; instructions for operators remain accurate.
- For release-affecting changes, note artifact updates, checksum verification, and manual steps in PR descriptions.
- Summarize results clearly for the user and suggest relevant next actions (tests, builds, deploys) if not already completed.

Refer back to this playbook whenever you need a reminder of expected workflows or validation gates.
