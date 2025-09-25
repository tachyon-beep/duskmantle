# Repository Guidelines

## Project Structure & Module Organization
Keep specifications in `docs/`, especially `docs/KNOWLEDGE_MANAGEMENT.md` (spec), `docs/KNOWLEDGE_MANAGEMENT_DESIGN.md` (architecture), and `docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md` (execution). Place runtime code under `gateway/` with clear subpackages (`gateway/api/`, `gateway/ingest/`, `gateway/config/`, `gateway/plugins/`). Use `tests/` to mirror runtime modules. Store container tooling and helper scripts under `infra/` (e.g., supervisor configs, build helpers).

## Build, Test, and Development Commands
Set up a Python 3.12 virtual env with `python3.12 -m venv .venv && source .venv/bin/activate`, then `pip install -r gateway/requirements.txt` for local hacking. Build the turnkey image via `docker build -t duskmantle/km:dev .`. Run it with `docker run --rm -p 8000:8000 -v $(pwd)/data:/opt/knowledge/var -v $(pwd):/workspace/repo duskmantle/km:dev`, which exposes the API at `http://localhost:8000`. Trigger a manual ingest inside the container with `docker exec <container> python -m gateway.ingest.cli rebuild --profile local`.

## Coding Style & Naming Conventions
Format Python with `black` (88 columns) and lint using `ruff`. Enforce type hints (PEP 484) across gateway modules. Modules remain `snake_case.py`; classes use `PascalCase`; CLI entry points adopt `snake_case` verbs (e.g., `rebuild`). YAML configs should be kebab-cased (e.g., `chunking.yaml`) and live under `gateway/config/`.

## Testing Guidelines
Use `pytest` with coverage: `pytest --cov=gateway --cov-report=term-missing`. Co-locate unit tests with mirror paths (e.g., `tests/ingest/test_discovery.py`). Add smoke tests that spin up the container, run a small ingest, and probe `/healthz`. Include contract tests that assert Qdrant payload schema and Neo4j relationships match the design docs.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `docs:`). PR descriptions should outline implementation scope, note schema or ingestion impacts, and list manual verification steps (`docker build`, `docker run`, `curl`). Reference any relevant design/plan sections and flag documentation updates required.

## Agent Workflow Tips
Before coding, confirm expectations in the design and implementation-plan docs. Keep changes scoped: update config defaults, ingestion logic, and docs in the same PR when they are materially linked. After each ingest-affecting change, rerun the turnkey smoke test and refresh any sample commands in this guide.
