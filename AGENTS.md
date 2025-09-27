# Repository Guidelines

## Project Structure & Module Organization
Keep specifications in `docs/`, especially `docs/KNOWLEDGE_MANAGEMENT.md` (spec), `docs/KNOWLEDGE_MANAGEMENT_DESIGN.md` (architecture), and `docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md` (execution). Place runtime code under `gateway/` with clear subpackages (`gateway/api/`, `gateway/ingest/`, `gateway/config/`, `gateway/plugins/`). Use `tests/` to mirror runtime modules. Store container tooling and helper scripts under `infra/` (e.g., supervisor configs, build helpers).

## Build, Test, and Development Commands
Set up a Python 3.12 virtual env with `python3.12 -m venv .venv && source .venv/bin/activate`, then install tooling with `pip install -e .[dev]` (optionally also `pip install -r gateway/requirements.txt` to mirror container deps). Build the turnkey image via `docker build --network=host -t duskmantle/km:dev .`. Run it with `docker run --rm -p 8000:8000 -p 6333:6333 -p 7687:7687 -v $(pwd)/data:/opt/knowledge/var -v $(pwd):/workspace/repo duskmantle/km:dev`, which exposes the API at `http://localhost:8000`. Trigger a manual ingest inside the container with `docker exec <container> gateway-ingest rebuild --profile local --dry-run --dummy-embeddings` (drop the flags for production). Use `./infra/smoke-test.sh` for automated container verification during reviews.

## Coding Style & Naming Conventions
Format Python with `black` (88 columns) and lint using `ruff`. Enforce type hints (PEP 484) across gateway modules. Modules remain `snake_case.py`; classes use `PascalCase`; CLI entry points adopt `snake_case` verbs (e.g., `rebuild`). YAML configs should be kebab-cased (e.g., `chunking.yaml`) and live under `gateway/config/`.

## Testing Guidelines
Use `pytest` with coverage: `pytest --cov=gateway --cov-report=term-missing`. Co-locate unit tests with mirror paths (e.g., `tests/ingest/test_discovery.py`). Add smoke tests that spin up the container, run a small ingest, and probe `/healthz`. Include contract tests that assert Qdrant payload schema and Neo4j relationships match the design docs.

Neo4j auth is disabled by default for local development. Set `KM_NEO4J_AUTH_ENABLED=true` and provide credentials (`KM_NEO4J_USER`/`KM_NEO4J_PASSWORD`) when hardening a deployment.
- Use `/metrics` and `/audit/history` to validate ingestion health; remember to pass maintainer tokens when auth is enabled.
- Distributed tracing is available by setting `KM_TRACING_ENABLED=true`; point `KM_TRACING_ENDPOINT` at your OTLP collector or enable console export for local spans.
- Prefer `gateway-ingest audit-history --limit 10` for quick provenance checks; fall back to the API when scripting.
- Consult `docs/OBSERVABILITY_GUIDE.md` for runbooks, alert thresholds, and troubleshooting sequences before escalating production issues.
- Verify `/healthz` reports `status: ok` (coverage fresh, audit ledger readable, scheduler running if enabled) before promoting builds.
- Exercise `/graph/subsystems/{name}`, `/graph/nodes/{id}`, and `/graph/search` after ingestion changes; maintainer workflows may hit `/graph/cypher` for diagnostics.
- Run `gateway-graph migrate` when adjusting graph schema (constraints/relationships) to keep Neo4j in sync; use `--dry-run` to preview pending migrations during review.
- Bundled container images export `KM_GRAPH_AUTO_MIGRATE=true`, so migrations run automatically during API startup with detailed logging. For CI or production workflows that require explicit approval windows, unset the variable and run `gateway-graph migrate` (or equivalent pipeline step) instead.
- Validate `/search` responses include `graph_context` and refreshed `scoring.signals` (e.g., `path_depth`, `coverage_ratio`, `criticality_score`, `freshness_days`) after changes to ingestion or graph logic; override `app.state.search_service_dependency` in tests when stubbing results.
- Monitor `km_search_graph_cache_events_total` and `km_search_graph_lookup_seconds` in dashboards after code changes that touch Neo4j or search scoring; spikes in `status="error"` or latency regressions usually indicate graph connectivity issues.
- Integration harness: `pytest -m neo4j` will exercise ingestion against a real Neo4j instance (requires `NEO4J_TEST_URI`, user, password); skip or mark as optional in CI if a database is unavailable.
- Tune `/search` ranking via `KM_SEARCH_WEIGHT_PROFILE` (`default`, `analysis`, `operations`, `docs-heavy`) and, if needed, the granular `KM_SEARCH_W_*` overrides (subsystem, relationship, support, coverage penalty, criticality); include updated `scoring_breakdown` output in review notes for clarity. Use `gateway-search show-weights` or `/search/weights` to confirm runtime configuration.
- Set `KM_SEARCH_SORT_BY_VECTOR=true` when you need to disable graph boosts and inspect raw vector ordering during debugging sessions.
- Use `gateway-search export-training-data --require-vote` when preparing datasets for ranking experiments; outputs land in `state_path/feedback/datasets/` and reuse the JSONL telemetry emitted by `/search`.
- Fit baseline ranking coefficients with `gateway-search train-model datasets/training.csv`; inspect the resulting JSON artifact before enabling in production.
- Keep telemetry manageable with `gateway-search prune-feedback --max-age-days 30` and redact sensitive columns before sharing via `gateway-search redact-dataset --drop-query --drop-context`.
- Benchmark candidate models with `gateway-search evaluate-model datasets/validation.csv models/model.json` and include the reported metrics in review notes before promoting weights.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `docs:`). PR descriptions should outline implementation scope, note schema or ingestion impacts, and list manual verification steps (`docker build`, `docker run`, `curl`). Reference any relevant design/plan sections and flag documentation updates required.

## Agent Workflow Tips
Before coding, confirm expectations in the design and implementation-plan docs. Keep changes scoped: update config defaults, ingestion logic, and docs in the same PR when they are materially linked. After each ingest-affecting change, rerun the turnkey smoke test and refresh any sample commands in this guide.
- When enabling the scheduler, prefer interval tuning for local dev (`KM_SCHEDULER_INTERVAL_MINUTES`) and cron expressions (`KM_SCHEDULER_CRON`) for predictable pipelines; remember runs are skipped when another job holds the ingest lock or the repo HEAD is unchanged.
- CLI ingestion commands now enforce maintainer scope when auth is enabled—export `KM_ADMIN_TOKEN` before running `gateway-ingest` locally or from automation.
- Use `bin/km-run` for the canonical container launch command and `bin/km-backup` to snapshot `/opt/knowledge/var` before upgrades or experiments.
