# WP5 Observability & Security — Remaining Tasks

## Overview
WP5 delivered tracing, metrics, rate limiting, auth, scheduler guardrails, and documentation. Outstanding work focuses on automated verification and documentation polish.

## Task Breakdown

### 1. CI Observability Checks
1. **Design:** Specify nightly GitHub Actions workflow that boots the stack, exercises `/healthz`, `/readyz`, `/metrics`, and `/coverage`, and fails on anomalies. ✅
2. **Implementation:** `.github/workflows/observability.yml` builds the container, runs it locally, and performs curl-based assertions. ✅
3. **Documentation:** `docs/OBSERVABILITY_GUIDE.md` and `STATUS.md` now reference the workflow. ✅

### 2. Metrics & Logging Polish
1. **Log Field Audit:** Ensure major subsystems emit `component` and `run_id` fields consistently (search warnings now include `component` metadata). *Partial*
2. **Metrics Inventory:** Document Prometheus queries and add missing signals (`km_search_requests_total` added; docs updated). ✅
3. **Alert Cookbook:** Expand `docs/OBSERVABILITY_GUIDE.md` with alert thresholds for new metrics introduced during WP4 (search ML mode). *Pending*

### 3. Security Hardening
1. **Token Rotation Playbook:** Document process for rotating `KM_READER_TOKEN`/`KM_ADMIN_TOKEN`.
2. **Rate-Limit Tests:** Extend `pytest` suite with targeted rate-limit coverage.
3. **Audit Ledger CLI:** Evaluate need for read-only CLI to export audit history (optional).

## Prioritisation
1. CI Observability Checks (blocks release confidence).
2. Metrics & Logging Polish.
3. Security Hardening (documentation/testing enhancements).
