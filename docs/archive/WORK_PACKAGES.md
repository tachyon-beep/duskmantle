# Work Packages & Implementation Order

This document distills the design and implementation plans into focused work packages. Each package summarizes scope, prerequisites, key deliverables, and the ideal sequencing to reach a turnkey single-container release.

## Work Package 1 — Container Runtime Foundation *(Completed)*
- **Scope:** Build the base Docker image (Python 3.12 slim), embed supervisor (s6 or equivalent), bundle Qdrant/Neo4j binaries, define entrypoint orchestration, and set up persistent volume paths.
- **Prerequisites:** None (starting point).
- **Deliverables:** `Dockerfile`, supervisor configs under `infra/`, entrypoint script with health checks, initial container smoke test.
- **Early Close Items:**
  - Base Python project scaffolding and tests complete (pyproject, gateway package, pytest smoke).
  - Documentation structure established for referencing container commands (README, AGENTS).
- **Outcome:** Docker image ships with Qdrant 1.15.4, Neo4j 5.26.0, supervisord, entrypoint volume guards, and automated smoke test script.

## Work Package 2 — Gateway Core Skeleton *(Completed)*
- **Scope:** Flesh out the FastAPI app factory, Uvicorn server harness, configuration loading, and basic routing (`/healthz`, `/readyz`). Wire CLI commands into the container runtime.
- **Prerequisites:** WP1 (container scaffolding to run the app).
- **Deliverables:** Functional gateway service inside the container, CLI hooks accessible via `docker exec`, updated tests covering API startup.
- **Early Close Items:**
  - FastAPI app factory with `/healthz` and CLI scaffolding already implemented and tested.
- **Outcome:** `/healthz` and `/readyz` live behind supervisord; configuration loader drives CLI, and container smoke tests rely on the readiness endpoint.

## Work Package 3 — Ingestion Pipeline MVP *(Completed)*
- **Scope:** Implement repository discovery, chunking, embedding via sentence-transformers, and Qdrant upserts for documentation-only ingestion. Persist provenance/audit ledgers.
- **Prerequisites:** WP2 (gateway runtime) and access to mounted repository on host.
- **Deliverables:** `gateway/ingest` modules with unit tests, `gateway-ingest rebuild --profile local` populating Qdrant inside the container, coverage report stub.
- **Early Close Items:**
  - CLI command, settings loader, discovery (`gateway/ingest/discovery.py`), chunker (`gateway/ingest/chunking.py`), embedder wrapper, and pipeline orchestrator delivered with dummy-embedding and dry-run support.
- **Outcome:** Repository discovery, chunking, embeddings, audit logging, and coverage report generation in place; CLI exposes `gateway-ingest` flows with dummy/real embedding support.

## Work Package 4 — Graph Model Integration *(Completed)*
- **Scope:** Define Neo4j schema migrations, create node/relationship upserts, connect vector chunks to graph context, and expose `/graph/...` endpoints.
- **Prerequisites:** WP3 (ingestion producing metadata to project into the graph).
- **Deliverables:** Neo4j initialization scripts, ingest-to-graph sync, API responses enriched with subsystem/telemetry links, graph-specific tests.
- **Early Close Items:** Graph schema defined in design docs and implemented via `gateway/ingest/neo4j_writer.py` (constraints, node relationships, chunk links).
- **Outcome:** Neo4j migrations create domain entities, ingestion writer emits subsystem/Leyline/Telemetry relationships, `/graph/*` endpoints and hybrid search tests validate payloads.

## Work Package 5 — Observability & Security Hardening *(In Progress)*
- **Scope:** Add metrics endpoint, structured logging, OpenTelemetry spans, token-based auth with reader/maintainer scopes, rate limiting, and scheduling (APScheduler jobs for periodic ingest/coverage).
- **Prerequisites:** WP2–WP4 (functional gateway and ingestion flows to instrument and secure).
- **Deliverables:** `/metrics` endpoint, auth middleware, scheduler configuration, documentation of env vars, alert/readiness tests, and optional tracing hooks.
- **Early Close Items:** Metrics, JSON logging, bearer tokens, rate limiting, scheduler guardrails, coverage reports, and OTLP-compatible tracing toggles are implemented and tested.
- **Remaining Prerequisites:** Tighten `/coverage` integration tests and capture alerting automation examples as the deployment model solidifies.

## Work Package 6 — Release Tooling & Documentation
- **Scope:** Produce quick-start scripts, backup/restore utilities, size-budget CI check, smoke-test workflow, and release packaging (image tag, tarball, checksums). Finalize README, troubleshooting, and risk updates.
- **Prerequisites:** WP1–WP5 completed.
- **Deliverables:** CI pipeline definitions, `bin/` helper scripts, published release artifacts, updated docs (quick start, troubleshooting, CHANGELOG kickoff).
- **Early Close Items:** README/CONTRIBUTING scaffolding, risk plan, work packages doc in place.
- **Remaining Prerequisites:** Docker build/test workflows, release scripts, checksum generation, CHANGELOG scaffolding.
- **Detailed Plan:** See `docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md` for phase/step/task breakdown aligned with Phase 4 execution.

## Work Package 7 — Autonomous Analysis Interface
- **Scope:** Integrate an OpenAI ChatGPT-5 (or equivalent) client that exposes an MCP-style command for autonomous deep dives. The gateway should accept requests such as “analyze subsystem X,” fetch relevant code and design chunks, and coordinate with the frontier AI using a stored API key.
- **Prerequisites:** WP2–WP5 (API endpoints, ingestion coverage, security scaffolding) and WP6 (documentation hooks for configuration).
- **Deliverables:**
  - Configurable OpenAI client module with rate limiting and timeout guards.
  - API/CLI endpoint (e.g., `POST /analysis/run`) that orchestrates retrieval, prompts the model, and returns structured findings (agreements, gaps, risks).
  - Documentation for supplying credentials, tuning prompt templates, and auditing model output.
  - Tests and dry-run mode validating prompt assembly without invoking the external service.
- **Early Close Items:** User story and requirements captured; risk plan framework ready for security considerations.
- **Remaining Prerequisites:** Implement OpenAI client module, define MCP command schema, add configuration/UI for API keys.

## Optional Extensions (Post-MVP)
1. **Hybrid Search Enhancements:** Combine dense and lexical retrieval strategies, tune HNSW parameters, and expose query knobs.
2. **Plugin SDK:** Provide scaffolding for third-party ingestion adapters and reference implementations.
3. **Managed-Services Connectors:** Document/automate deployment against hosted Qdrant/Neo4j for users who prefer external services.

## Recommended Implementation Order
1. WP1 — Container Runtime Foundation
2. WP2 — Gateway Core Skeleton
3. WP3 — Ingestion Pipeline MVP
4. WP4 — Graph Model Integration
5. WP5 — Observability & Security Hardening
6. WP6 — Release Tooling & Documentation *(see `docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md` for detailed milestones)*
7. WP7 — Autonomous Analysis Interface
8. Optional extensions in priority order as demanded by adopters

This ordering respects dependencies: the container shell enables the gateway, the gateway enables ingestion, and the ingestion artifacts unlock graph and hardening work. Release automation follows once the functional stack is stable.
