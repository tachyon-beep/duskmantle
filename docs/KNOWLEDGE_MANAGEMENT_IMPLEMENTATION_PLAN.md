# Knowledge Management Implementation Plan

## 1. Overview

This plan translates the turnkey single-container design into concrete implementation steps. Work is organized into focused phases that culminate in an open-source image delivering the Knowledge Gateway, Qdrant, and Neo4j as an integrated drop-in solution for a small group of expert users.

## 2. Phase Breakdown

### Phase 1: Container Foundation (Weeks 1-2)

**Goals:** Establish project scaffolding, supervise co-located services, ingest documentation.

- Task 1.1 Set up repository structure (`gateway/`, `gateway/plugins/`, `infra/`, `tests/`, `gateway/config/`).
- Task 1.2 Create base Dockerfile with multi-stage build, install embedding model assets offline, and integrate supervisor (e.g., s6-overlay).
- Task 1.3 Package Qdrant and Neo4j binaries/configs within the image; configure process startup order and health checks.
- Task 1.4 Implement FastAPI skeleton plus health endpoints, config loader, and CLI entry point.
- Task 1.5 Build initial ingestion CLI for `docs/` content with chunking, embeddings, Qdrant upserts, and audit ledger.
- **Exit Criteria:** `docker run` with mounted repo indexes docs successfully; `/healthz` responds; volume layout created under `/opt/knowledge/var`.
- **Status (Sept 2025):** Complete — image builds with Qdrant/Neo4j, supervisord orchestration, readiness checks, and smoke test script.

### Phase 2: Full Corpus & Graph Enrichment (Weeks 3-4)

**Goals:** Cover code/tests, populate Neo4j, enrich API payloads.

- Task 2.1 Implement repository discovery for source/tests based on `critical_paths.yaml` mapping.
- Task 2.2 Add subsystem classification, Integration/telemetry tagging, and validation tests.
- Task 2.3 Apply Neo4j schema migrations, node/edge upsert logic, and `HAS_CHUNK` linkage.
- Task 2.4 Enhance `/search` to include graph context; expose `/graph/...` endpoints; add contract tests.
- Task 2.5 Generate nightly coverage report and store under `/opt/knowledge/var/reports/`.
- **Exit Criteria:** End-to-end ingestion populates both stores; search payloads include subsystem metadata; graph endpoints return expected relationships.
- **Status (Sept 2025):** Complete — ingestion writes full graph/linkage, coverage reports surface via `/coverage`, and graph/search contract tests exercise the enriched payloads.

### Phase 3: Turnkey Hardening (Weeks 5-6)

**Goals:** Finalize security knobs, observability, scheduling, offline readiness.

- Task 3.1 Add APScheduler jobs (periodic ingest, coverage report) with run gating on repo HEAD.
- Task 3.2 Implement token-based auth with reader/maintainer scopes and rate limiting.
- Task 3.3 Expose Prometheus metrics and structured logging; document log/metric scraping.
- Task 3.4 Bundle optional helper scripts (`bin/km-run`, `bin/km-backup`) and example reverse proxy configs.
- Task 3.5 Create smoke-test workflow that builds the image, runs minimal ingestion, and checks health endpoints.
- Task 3.6 Update the FastAPI app to use lifespan handlers (drop deprecated `on_event`) and extend ingest writer unit coverage (Neo4j/Qdrant) to reduce warning noise and harden regression detection.
- **Exit Criteria:** Container passes smoke tests, supports offline start, metrics/auth configurable via env vars, documentation updated.
- **Status (Sept 2025):** Complete — scheduler reliability, auth hardening, observability, lifespan migration, writer coverage, and operational tooling delivered.

### Phase 4: Release Packaging & Adoption (Week 7)

**Goals:** Publish final artifacts and onboarding material for power users.

- Task 4.1 Produce versioned container image and downloadable tarball; verify checksum pipeline.
- Task 4.2 Write quick-start guide, troubleshooting appendix, and upgrade procedure.
- Task 4.3 Capture minimal support model (FAQ, issue template) aligned with small user base expectations.
- Task 4.4 Run acceptance demo exercising search, graph queries, re-index, backup/restore.
- **Exit Criteria:** Release notes published, reference `docker run` command validated, acceptance criteria met.
- **Status (Sept 2025):** Step 5.1 complete; Step 5.2 MCP server implemented (server package + CLI); Step 5.3 complete (tests + telemetry wired into CI); Step 5.4 documentation updates published.

## 2.2 Phase 4 Execution Plan

### Step 4.1 Artifact Production & Verification

- Task 4.1.1 Finalize version tagging strategy (SemVer mapping, prerelease conventions) and document in `RELEASE.md`.
- Task 4.1.2 Configure CI to publish Docker images/tarballs and wheels on tags (ensure `release.yml` uploads final artifacts, not draft-only).
- Task 4.1.3 Validate checksum workflow (`scripts/checksums.sh`, `dist/IMAGE_SHA256SUMS`) and provide verification commands in release notes.

### Step 4.2 Operator Enablement & Documentation

- Task 4.2.1 Expand `docs/QUICK_START.md` with upgrade and rollback procedures (backup/restore, config changes, token rotation).
- Task 4.2.2 Create troubleshooting appendix (auth errors, scheduler skips, tracing failures, smoke-test triage) referencing observability metrics.
- Task 4.2.3 Update README/AGENTS with release pipeline overview, artifact download commands, and support expectations.

### Step 4.3 Support Model & Adoption

- Task 4.3.1 Draft FAQ and issue templates (common questions, log collection steps, reproducible bug checklist).
- Task 4.3.2 Define communication cadence (release announcements, changelog updates) and backlog triage policy.
- Task 4.3.3 Capture minimum support SLOs (response times, smoke-test results) in project docs or `SUPPORT.md`.

### Step 4.4 Acceptance Demo & Validation

- Task 4.4.1 Build a script/playbook that runs end-to-end demo (ingest sample repo, search, graph queries, backup/restore, metrics sanity checks) **(Completed: `docs/ACCEPTANCE_DEMO_PLAYBOOK.md`)**.
- Task 4.4.2 Record demo results and link to release notes or onboarding materials.
- Task 4.4.3 After demo approval, publish GitHub release with final artifacts, changelog entry, and verification checklist.

## 2.1 Detailed Phase Execution Plan

### Phase 3 — Turnkey Hardening

- **Step 3.1 Scheduler & Coverage Reliability**
  - Task 3.1.1 Scheduler Interval Management
    - Subtask 3.1.1.a Implement configuration for interval/cron profiles with repo HEAD gating.
    - Subtask 3.1.1.b Add lockfile contention tests ensuring concurrent triggers skip gracefully.
    - Subtask 3.1.1.c Document scheduler tuning knobs (interval, cron, dummy embeddings) in README/AGENTS.
  - Task 3.1.2 Coverage Report Rotation
    - Subtask 3.1.2.a Extend coverage writer to maintain multiple snapshots and prune old reports.
    - Subtask 3.1.2.b Add integration tests simulating consecutive scheduler runs verifying rotation/metrics.
    - Subtask 3.1.2.c Update observability guide with coverage health checks and alert thresholds.
- **Step 3.2 Auth & Access Controls** *(Completed in v1.0.1)*
  - Status: MCP upload/storetext tooling now enforces maintainer scope with audit logging. CLI and HTTP endpoints validate tokens, and README/AGENTS/MCP guides document rotation plus error handling.
  - Task 3.2.1 Scope Enforcement
    - Subtask 3.2.1.a Align API dependencies to enforce `reader`/`maintainer` scopes consistently (CLI + HTTP).
    - Subtask 3.2.1.b Add regression tests covering missing/invalid tokens per endpoint.
    - Subtask 3.2.1.c Ensure scheduler/ingest CLIs respect maintainer scope when invoked remotely.
  - Task 3.2.2 Token Operations & Documentation
    - Subtask 3.2.2.a Document token rotation, storage, and env var management in README/AGENTS.
    - Subtask 3.2.2.b Describe failure modes (401 vs 403) and troubleshooting steps in OBSERVABILITY_GUIDE.
    - Subtask 3.2.2.c Provide sample scripts or commands for token regeneration and verification.
- **Step 3.3 Observability Enhancements**
  - Task 3.3.1 Metrics & Alerting
    - Subtask 3.3.1.a Introduce scheduler run counters/gauges (success, skipped, failure) and wire logging hooks.
    - Subtask 3.3.1.b Add unit tests validating metric increments for scheduler outcomes and coverage history writes.
    - Subtask 3.3.1.c Refresh OBSERVABILITY_GUIDE alerts to reference new metrics and provide example Prometheus rules.
  - Task 3.3.2 Tracing Pipeline Validation
    - Subtask 3.3.2.a Support OTLP exporter configuration (endpoint/headers) with console fallback and add smoke tests covering both modes.
    - Subtask 3.3.2.b Document tracing setup, including sample curl checks and failure diagnostics, in README/OBSERVABILITY_GUIDE.
- **Step 3.4 Runtime & Test Hardening**
  - Task 3.4.1 FastAPI Lifespan Migration
    - Subtask 3.4.1.a Replace `@app.on_event` usage with lifespan context managers (startup/shutdown) and ensure services teardown cleanly.
    - Subtask 3.4.1.b Update tests to accommodate lifespan (TestClient usage, tracing fixtures).
    - Subtask 3.4.1.c Document the lifespan migration and note deprecation removal in README/AGENTS.
  - Task 3.4.2 Ingestion Writer Coverage
    - Subtask 3.4.2.a Add tests for Qdrant writer idempotency (collection ensure, payload dedupe) and failure handling.
    - Subtask 3.4.2.b Extend Neo4j writer tests to cover config file nodes and telemetry relationships.
    - Subtask 3.4.2.c Ensure pipeline-level tests assert writer interactions (mock injection) and update coverage thresholds accordingly.
- **Step 3.5 Operational Tooling**
  - Task 3.5.1 Ship helper scripts (`km-run`, `km-backup`) with docs and examples.
  - Task 3.5.2 Implement container smoke-test workflow (build → run → healthz → ingest dry-run → coverage check).

### Phase 4 — Release Packaging & Adoption

- **Step 4.1 Release Automation** *(Completed)*
  - Task 4.1.1 Create CI pipeline to build, tag, and publish images/tarballs with checksums. **(Completed – `release.yml` builds, tests, pushes images, and publishes wheel/checksum artifacts.)**
  - Task 4.1.2 Capture release metadata in CHANGELOG/RELEASE docs per Conventional Commits. **(Completed – CHANGELOG/RELEASE playbook maintained.)**
- **Step 4.2 Operator Enablement** *(Completed)*
  - Task 4.2.1 Produce quick-start guide, upgrade notes, and troubleshooting appendix. **(Completed – README, QUICK_START, and UPGRADE docs cover these flows.)**
  - Task 4.2.2 Provide backup/restore and smoke-test runbooks referencing OBSERVABILITY_GUIDE. **(Completed – `bin/km-backup`, smoke script, and guides documented.)**
- **Step 4.3 Acceptance Validation** *(Completed)*
  - Task 4.3.1 Run end-to-end acceptance demo (search, graph, reindex, backup/restore). **(Completed – playbook + snapshot kept up to date.)**
  - Task 4.3.2 Finalise support expectations (issue templates, FAQ) and confirm Work Package 6 alignment. **(Completed – FAQ and support notes documented.)**

### Phase 5: MCP Interface & Agent Integration (Weeks 8-9)

**Goals:** Provide a first-class Model Context Protocol (MCP) server so Codex CLI and other agents can access the gateway entirely through MCP tools without direct HTTP interaction.

- Task 5.1 MCP Tooling Design.
- Task 5.2 MCP Server Implementation.
- Task 5.3 Testing & Telemetry.
- Task 5.4 Documentation & Distribution.
- **Exit Criteria:** Agents can invoke search/graph/coverage/backups via MCP commands; automated smoke test validates MCP flows; documentation covers setup and troubleshooting.
- **Status (Oct 2025):** Steps 5.1–5.3 complete; MCP telemetry counters ship in Prometheus and tagged builds run the MCP smoke slice in `release.yml`.

## 2.3 Phase 5 Execution Plan

### Step 5.1 MCP Tooling Design

- Task 5.1.1 Define tool contract: enumerate gateway operations exposed via MCP (`search`, `graph.node`, `graph.subsystem`, `graph.search`, `coverage.summary`, `ingest.status`, `backup.trigger`, `feedback.submit`) **(Completed in `docs/MCP_INTERFACE_SPEC.md`)**.
- Task 5.1.2 Specify request/response schemas, filters, error handling, and authentication requirements for each tool **(Completed in `docs/MCP_INTERFACE_SPEC.md`)**.
- Task 5.1.3 Plan token management (reader vs maintainer scopes) and configuration (environment variables, secret injection) **(Documented in spec §1)**.
- Task 5.1.4 Determine telemetry expectations (metrics/log entries per MCP invocation) **(Documented in spec §5)**.

### Step 5.2 MCP Server Implementation

- Task 5.2.1 Scaffold an MCP server package (e.g., `mcp/`) with CLI entry point (`bin/km-mcp`). **(Completed via `gateway/mcp/` + `bin/km-mcp`)**
- Task 5.2.2 Implement tool handlers that call gateway REST endpoints and translate responses to MCP format. **(Implemented for search/graph/coverage/ingest/backup/feedback)**
- Task 5.2.3 Support configuration via env vars (`KM_GATEWAY_URL`, `KM_READER_TOKEN`, `KM_ADMIN_TOKEN`, etc.). **(Handled by `MCPSettings`)**
- Task 5.2.4 Bundle the server for distribution (Python console script or Node package) and integrate with container runtime if desired. **(Python console script `gateway-mcp` and shell wrapper `bin/km-mcp`)**

### Step 5.3 Testing & Telemetry

- Task 5.3.1 Add unit tests mocking gateway responses for each MCP tool. **(Completed in `tests/mcp/test_server_tools.py`)**
- Task 5.3.2 Create an MCP smoke test that launches the server, executes sample MCP commands (search, coverage, backup), and asserts success. **(Covered by `test_mcp_smoke_run`)**
- Task 5.3.3 Instrument metrics/logs (`km_mcp_requests_total`, latency histograms) and surface them via Prometheus. **(Implemented via `gateway/observability/metrics.py` + server instrumentation)**
- Task 5.3.4 Update CI release workflow to optionally run the MCP smoke test after image build. **(Release workflow runs `pytest -m mcp_smoke` post-build)**

### Step 5.4 Documentation & Distribution *(Complete for 1.0; broader agent automation deferred post-1.0)*

- Task 5.4.1 Expand README/QUICK_START with MCP setup instructions (starting server, Codex CLI config, sample commands). **(Completed: Quick Start §10 and README updates)**
- Task 5.4.2 Update `docs/MCP_INTEGRATION.md` with detailed tool descriptions, troubleshooting, and auth guidance. **(Completed: guide rewritten with launch/validation steps)**
- Task 5.4.3 Note release artifacts for the MCP server (npm/PyPI) and align versioning with gateway releases. **(Completed: CI now runs MCP smoke tests; release docs reference the adapter)**
- Task 5.4.4 Extend `docs/ACCEPTANCE_DEMO_PLAYBOOK.md` to include MCP verification steps. **(Completed: Section 10 added to playbook)**
- Post-1.0 backlog: prompt orchestration, retrieval QA, and OpenAI client integration (captured under future roadmap/WP7).

## 3. Dependencies & Tooling

- **Runtime:** Python 3.12+, FastAPI, APScheduler, `qdrant-client`, `neo4j` driver.
- **Embedding Assets:** `sentence-transformers/all-MiniLM-L6-v2` downloaded during image build; optional GPU support documented.
- **Build Tooling:** Docker (BuildKit recommended), Makefile or task runner for repeatable builds.
- **Repository Access:** Users mount repository directories when running container; plan assumes Linux/macOS hosts.

## 4. Key Risks & Mitigation

Detailed mitigation activities are tracked in `docs/RISK_MITIGATION_PLAN.md`. The table below summarizes execution status.

| Risk | Impact | Likelihood | Mitigation Status |
|------|--------|------------|-------------------|
| Container image size | Slow downloads, adoption friction | Medium | Actions defined (multi-stage build, CI size check) — see §1 of mitigation plan. |
| Persistence safety | Lost indexes/graph state | Medium | Actions underway: stale artifact ledger/removal shipped; backup scripts and startup guard tracked in §2. |
| Resource contention | Ingestion/search slowdowns | Medium | Actions defined; benchmarking data still pending (open question §3). |
| Classification accuracy | Incorrect metadata | Medium | Actions defined with outstanding need for real repos (§4). |
| Authentication defaults | Accidental open access | Low | Mitigated: secure mode now requires maintainer token + custom Neo4j password; docs updated with migration steps (§5). |
| Host compatibility | Deployment failures | Low | Actions defined with pending compatibility matrix (§6). |
| Observability coverage | Silent ingestion failures | Medium | Actions defined (§7). |
| Release distribution integrity | Corrupted deployments | Low | Actions defined (§8). |
| Hybrid search tuning | Suboptimal retrieval relevance | Medium | Mitigated for 1.0 — dense + lexical scoring knobs (`KM_SEARCH_VECTOR_WEIGHT`/`KM_SEARCH_LEXICAL_WEIGHT`) and `KM_SEARCH_HNSW_EF_SEARCH` shipped; continue monitoring relevance metrics post-release. |

## 5. Tracking & Communication

- Maintain a lightweight issue list (GitHub Projects) tagged per phase; update weekly.
- Record design/plan adjustments directly in `docs/` with changelog entries.
- Share fortnightly status notes summarizing completed tasks, upcoming focus, and risk updates for stakeholders represented by the agent.

## 6. Acceptance & Rollout Criteria

- **Functional:** Single container ingests mounted repo, serves `/search` and `/graph` endpoints with accurate context, and supports manual reindexing.
- **Operational:** Metrics/logging accessible via container output or `/metrics`; scheduled ingest runs succeed; backup/restore scripts verified.
- **Packaging:** Image published with signed checksums, quick-start/upgrade docs ready, example commands tested on Linux and macOS hosts.
- **Support Model:** Issue templates and FAQ explain expectations for self-service adopters within the small user community.
