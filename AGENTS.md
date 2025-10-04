# Repository Guidelines

## Project Structure & Module Organization
Core services live in `gateway/`, organized by concern: `api/` for FastAPI surfaces, `ingest/` for graph loaders, `config/` for runtime settings, `plugins/` for optional adapters, and `mcp/` for MCP tool glue. Shared utilities sit in `gateway/common/`. Tests mirror this layout under `tests/`, so new modules should ship with peers like `tests/ingest/test_<feature>.py`. Docs that inform implementation choices are in `docs/`, with specs and design notes that must guide any code updates.

## Development Environment & Core Commands
Create a dev shell with `python3.12 -m venv .venv && source .venv/bin/activate`, followed by `pip install -e .[dev]` for editable installs. Use `pytest --cov=gateway --cov-report=term-missing` before pushing, and narrow to `pytest tests/ingest/` or `pytest tests/mcp/` while iterating. When modifying MCP integrations, also run `pytest -m mcp_smoke`. Execute `ruff check .` and `black .` to satisfy linting and formatting gates. For end-to-end verification tied to code changes, prefer `bin/km-run` (local services) and `./infra/smoke-test.sh` once features stabilize. If you need the password-protected UI locally, set `KM_UI_LOGIN_ENABLED=true`, choose a `KM_UI_PASSWORD`, and optionally disable secure cookies for HTTP testing with `KM_UI_SESSION_SECURE_COOKIE=false` before restarting the stack.

## Coding Style & Naming Conventions
Python uses 4-space indentation, `snake_case` modules, and exhaustive type hints (mypy clean). Keep classes in `PascalCase`, exception classes ending with `Error`, and constants in `UPPER_SNAKE_CASE`. Run `black` with the repo default (88 columns) and `ruff --fix` for lint autofixes. Keep comments surgical—explain intent behind complex flows rather than restating code.

## Testing Guidelines
Test files follow `test_*.py` naming, with fixtures consolidated in `tests/conftest.py`. Write unit coverage for new graph walkers, API handlers, and plugin hooks; extend integration coverage when touching cross-module boundaries. UI contract smoke tests live in `playwright/`; use `npm install` once, then `npm run test:ui` for regressions that impact front-end clients. Document any temporary exclusions in the PR body.

## Commit & Pull Request Guidelines
Commits should be scoped and labeled with Conventional Commit prefixes (`feat:`, `fix:`, `docs:`, etc.). PRs must summarize behavior changes, cite relevant spec or design paragraphs, list verification commands, and call out risk mitigations. Include before/after traces, sample API payloads, or schema diffs when altering graph or ingest logic. Coordinate doc updates in `docs/` within the same PR to keep guidance current.

## Architecture Extension Tips
Reuse existing service boundaries: new ingest pipelines should plug into the abstractions in `gateway/ingest/pipelines/`, and additional tool endpoints should extend FastAPI routers under `gateway/api/routes/`. Use feature flags or config toggles in `gateway/config/models.py` when introducing optional behavior, and surface new knobs in the documentation to aid future contributors.
