# Work Package 5 Execution Plan — Observability & Security Hardening

## Objectives
1. Provide runtime visibility via metrics, structured logs, and optional tracing so smoke and production deployments can detect ingestion failures quickly.
2. Introduce guarded API access (bearer scopes) and rate limiting to keep the turnkey package safe for multi-user environments.
3. Automate routine ingestion via APScheduler and capture coverage/provenance outputs promised in the design.

## Deliverables
- `/metrics` endpoint (Prometheus-compatible) exporting ingestion counters, latencies, and queue sizes.
- Structured logging with ingest run IDs, subsystem/artifact metadata, and optional OpenTelemetry spans.
- Bearer-token auth middleware (reader vs maintainer scopes) with configurable tokens via env vars.
- Rate limiting for search/graph endpoints (configurable burst/limit) using Starlette middleware.
- APScheduler job(s) for periodic ingest and nightly coverage report generation; persisted job state to avoid duplicate runs.
- Provenance/audit ledger stored under `/opt/knowledge/var/audit/` with API/CLI access.
- Documentation updates detailing new env vars, operational guidance, and troubleshooting tips.
- Regression tests covering metrics output, auth gating, scheduler dry-run, and CLI coverage report export.

## Task Breakdown
1. **Metrics Layer**
   - Add dependency (e.g., `prometheus-client`) and expose `/metrics` route.
   - Instrument ingestion pipeline timings and Qdrant/Neo4j interactions.
   - Update smoke test to curl `/metrics`.

2. **Structured Logging & Tracing**
   - Configure standard logger to emit JSON (or key-value) with ingest_run_id plus subsystem/artifact tags.
   - Optional: wrap pipeline stages with OpenTelemetry spans (config toggle).

3. **Auth & Rate Limiting**
   - Implement FastAPI dependencies validating bearer tokens from env (`KM_ADMIN_TOKEN`, `KM_READER_TOKEN`).
   - Protect ingestion endpoints with maintainer scope; allow read-only for search/graph.
   - Add rate limiter middleware (e.g., `slowapi`) with env-configured thresholds.

4. **Scheduler & Coverage** (coverage report completed)
   - Integrate APScheduler in the gateway startup to schedule default ingest & coverage jobs.
   - Extend coverage report with scheduling metadata once cron runs are enabled.
   - Ensure scheduler respects `KM_INGEST_DRY_RUN` and repo HEAD gating.

5. **Provenance & Audit Ledger**
   - Persist ingestion runs to SQLite (e.g., `audit.db`) with timestamp, repo HEAD, model, chunk counts.
   - Expose `/audit/history` and CLI flag to dump recent runs.

6. **Documentation & Tests**
   - Update README/AGENTS to explain metrics, auth tokens, scheduler toggles.
   - Extend work packages/implementation plan to mark WP5 progress.
   - Add pytest coverage for new modules and smoke scenario for secured tokens.

## Dependencies & Open Questions
- Decide on logging format (JSON vs key-value) and whether OpenTelemetry should be optional or always enabled.
- Confirm storage location & retention policy for audit DB to align with risk plan.
- Determine default cron frequency (30 minutes) and adjust for testing so scheduler does not thrash.
- Align rate limiting defaults with prospective agent workloads.

## Success Criteria
- `./infra/smoke-test.sh` passes and verifies `/metrics` output.
- `gateway-ingest rebuild` succeeds under auth-enabled configuration with tokens.
- Automated tests cover metrics endpoint, auth failure paths, scheduler dry-run, and coverage report generation.
- Documentation accurately reflects new knobs and operational expectations.
