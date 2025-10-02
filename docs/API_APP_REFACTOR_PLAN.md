# FastAPI App Factory Refactor Plan

## Context
- `gateway/api/app.py` currently embeds router registration, dependency factories, and endpoint implementations inside `create_app()`.
- The function spans more than 500 lines, making feature work and code review difficult.
- Inline closures hide dependencies on configuration and app state, preventing reuse across modules and unit tests.

## Target Architecture
- Keep `create_app()` focused on application assembly: logging, settings resolution, dependency wiring, router inclusion.
- Move shared dependency providers (Neo4j, Qdrant, search) into `gateway/api/dependencies.py` so they can be imported independently.
- Split endpoint implementations into dedicated routers under `gateway/api/routes/`:
  - `health.py` for `/healthz`, `/readyz`, `/metrics`.
  - `reporting.py` for lifecycle, audit, and coverage endpoints.
  - `search.py` for search submission, weights, and feedback hooks.
  - `graph.py` for subsystem, node, and Cypher endpoints.
- Each router module exports a configured `APIRouter` and any helper functions or dependencies it needs.
- Routers consume configuration and shared resources through FastAPI dependency injection and `app.state` handles, not closure variables.
- Rate limiting is centralised in a small helper that runs during app creation and attaches the resulting limiter to routers through dependencies.

## Step-By-Step Execution
1. **Bootstrap modules**
   - Introduce `gateway/api/dependencies.py` with typed accessors for settings, graph driver/service, search client/service, and limiter.
   - Ensure dependencies read from `Request.app.state` and raise clear HTTP errors when resources are missing.
2. **Extract routers**
   - Create router modules (`health`, `reporting`, `search`, `graph`) with the existing endpoint logic migrated verbatim where practical.
   - Replace closure usage with imports from `dependencies.py`; keep behavioural parity with current routes.
3. **Slim `create_app()`**
   - Leave lifecycle setup (logging, tracing, models, clients, limiter) in `create_app()`.
   - Store constructed resources on `app.state` for dependency modules to read.
   - Include the new routers via `app.include_router(...)` calls.
   - Remove nested route definitions and redundant state attributes.
4. **Documentation and testing**
   - Update existing docs or READMEs if startup behaviour or diagnostics logging changes.
   - Run `pytest` and `ruff` to ensure the refactor is safe.

## Non-Goals
- Changing business logic for search, graph, or reporting endpoints.
- Renaming request/response payloads or altering authentication requirements.

## Verification
- Unit test suite continues to pass (`pytest`).
- Manual smoke via `bin/km-run` still succeeds (optional for this refactor but recommended).
- Linting (`ruff`, `black`) remains clean.
