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
- Task 2.2 Add subsystem classification, Leyline/telemetry tagging, and validation tests.
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
- **Status (Sept 2025):** Not started.

### Phase 4: Release Packaging & Adoption (Week 7)
**Goals:** Publish final artifacts and onboarding material for power users.
- Task 4.1 Produce versioned container image and downloadable tarball; verify checksum pipeline.
- Task 4.2 Write quick-start guide, troubleshooting appendix, and upgrade procedure.
- Task 4.3 Capture minimal support model (FAQ, issue template) aligned with small user base expectations.
- Task 4.4 Run acceptance demo exercising search, graph queries, re-index, backup/restore.
- **Exit Criteria:** Release notes published, reference `docker run` command validated, acceptance criteria met.
- **Status (Sept 2025):** Not started.

## 2.1 Detailed Phase Execution Plan

### Phase 3 — Turnkey Hardening
- **Step 3.1 Scheduler & Coverage Reliability**
  - Task 3.1.1 Wire APScheduler interval and cron profiles with repo HEAD gating and lockfile tests.
  - Task 3.1.2 Add integration tests that simulate multiple scheduler ticks and verify coverage report rotation.
- **Step 3.2 Auth & Access Controls**
  - Task 3.2.1 Enforce reader/maintainer token scopes across CLI and API entry points.
  - Task 3.2.2 Document token rotation, env var management, and failure modes.
- **Step 3.3 Observability Enhancements**
  - Task 3.3.1 Expand Prometheus metrics (ingest latency, graph cache events) and ensure alerts reference OBSERVABILITY_GUIDE.
  - Task 3.3.2 Enable optional OTLP tracing pipeline with smoke validation of span export.
- **Step 3.4 Runtime & Test Hardening**
  - Task 3.4.1 Replace FastAPI `on_event` usage with lifespan handlers; update unit tests accordingly.
  - Task 3.4.2 Increase ingest writer coverage, including Qdrant writer idempotency tests.
- **Step 3.5 Operational Tooling**
  - Task 3.5.1 Ship helper scripts (`km-run`, `km-backup`) with docs and examples.
  - Task 3.5.2 Implement container smoke-test workflow (build → run → healthz → ingest dry-run → coverage check).

### Phase 4 — Release Packaging & Adoption
- **Step 4.1 Release Automation**
  - Task 4.1.1 Create CI pipeline to build, tag, and publish images/tarballs with checksums.
  - Task 4.1.2 Capture release metadata in CHANGELOG/RELEASE docs per Conventional Commits.
- **Step 4.2 Operator Enablement**
  - Task 4.2.1 Produce quick-start guide, upgrade notes, and troubleshooting appendix.
  - Task 4.2.2 Provide backup/restore and smoke-test runbooks referencing OBSERVABILITY_GUIDE.
- **Step 4.3 Acceptance Validation**
  - Task 4.3.1 Run end-to-end acceptance demo (search, graph, reindex, backup/restore).
  - Task 4.3.2 Finalise support expectations (issue templates, FAQ) and confirm Work Package 6 alignment.

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
| Persistence safety | Lost indexes/graph state | Medium | Actions defined (startup guard, backup scripts) — see §2. |
| Resource contention | Ingestion/search slowdowns | Medium | Actions defined; benchmarking data still pending (open question §3). |
| Classification accuracy | Incorrect metadata | Medium | Actions defined with outstanding need for real repos (§4). |
| Authentication defaults | Accidental open access | Low | Actions defined; must implement before release (§5). |
| Host compatibility | Deployment failures | Low | Actions defined with pending compatibility matrix (§6). |
| Observability coverage | Silent ingestion failures | Medium | Actions defined (§7). |
| Release distribution integrity | Corrupted deployments | Low | Actions defined (§8). |

## 5. Tracking & Communication
- Maintain a lightweight issue list (GitHub Projects) tagged per phase; update weekly.
- Record design/plan adjustments directly in `docs/` with changelog entries.
- Share fortnightly status notes summarizing completed tasks, upcoming focus, and risk updates for stakeholders represented by the agent.

## 6. Acceptance & Rollout Criteria
- **Functional:** Single container ingests mounted repo, serves `/search` and `/graph` endpoints with accurate context, and supports manual reindexing.
- **Operational:** Metrics/logging accessible via container output or `/metrics`; scheduled ingest runs succeed; backup/restore scripts verified.
- **Packaging:** Image published with signed checksums, quick-start/upgrade docs ready, example commands tested on Linux and macOS hosts.
- **Support Model:** Issue templates and FAQ explain expectations for self-service adopters within the small user community.
