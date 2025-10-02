# Observability & Troubleshooting Guide

This guide explains how to operate and monitor the Duskmantle Knowledge Gateway. It covers metrics, logs, tracing, rate limiting, scheduling, and common failure scenarios so operators can detect and resolve incidents quickly.

## 1. Instrumentation Overview

- **Metrics:** Prometheus-compatible counters, gauges, and histograms published at `/metrics`.
- **Logs:** JSON-structured stdout/stderr streams captured by the container runtime. Each record carries `ingest_run_id`, subsystem, and key counts.
- **Tracing:** Optional OpenTelemetry spans that capture HTTP requests and ingestion stages. Export spans to an OTLP collector, APM tool, or stdout.
- **Audit Ledger:** SQLite database under `/opt/knowledge/var/audit/audit.db` with per-run provenance records accessible via `/audit/history`.
- **Coverage Report:** Accessible via `/coverage` (maintainer scope) or `/opt/knowledge/var/reports/coverage_report.json`, detailing indexed artifacts, missing coverage, and the `removed_artifacts` list for files deleted from the repo but recently cleaned from the graph. Historical snapshots live under `/opt/knowledge/var/reports/history/coverage_*.json` and are pruned to the limit defined by `KM_COVERAGE_HISTORY_LIMIT`.
- **Lifecycle Report:** Available at `/lifecycle` (maintainer scope) or `/opt/knowledge/var/reports/lifecycle_report.json`, capturing isolated graph nodes, stale design docs (older than `KM_LIFECYCLE_STALE_DAYS`), and subsystems missing tests. Use it to prioritise authoring or tagging work after each ingest. Historical snapshots live under `/opt/knowledge/var/reports/lifecycle_history/` and are surfaced via `/lifecycle/history` for the UI spark lines.
- **Recipe Audit:** Running `km-recipe-run` appends JSONL entries to `/opt/knowledge/var/audit/recipes.log` summarising step status and captured outputs. Tail this log to monitor automation runs or integrate with alerting.

## 2. Metrics Reference

Expose metrics with:

```bash
curl -H "Authorization: Bearer $KM_ADMIN_TOKEN" http://localhost:8000/metrics
```

Key time-series:

| Metric | Type | Labels | Description | Alert Hint |
|--------|------|--------|-------------|------------|
| `km_ingest_duration_seconds` | Histogram | `profile`, `status` | Duration of ingestion runs segmented by success/failure. | Alert if `status="failure"` count spikes or P95 > ingestion SLA. |
| `km_ingest_artifacts_total` | Counter | `profile`, `artifact_type` | Total artifacts discovered per type (docs, code, tests). | Alert on sudden drops across runs. |
| `km_ingest_chunks_total` | Counter | `profile` | Total chunks embedded. | Alert if value is stagnant vs expected growth. |
| `km_ingest_last_run_status` | Gauge | `profile` | 1=success, 0=failure for last run. | Page when `== 0` for any profile. |
| `km_ingest_last_run_timestamp` | Gauge | `profile` | Epoch of last run. | Alert when older than 2× expected schedule interval. |
| `km_coverage_last_run_status` | Gauge | `profile` | 1=coverage report written successfully. | Alert when `== 0` for two consecutive scrapes. |
| `km_coverage_last_run_timestamp` | Gauge | `profile` | Epoch of last coverage report. | Alert when older than max(2× schedule interval, 1h) or >24h when scheduler disabled. |
| `km_coverage_missing_artifacts_total` | Gauge | `profile` | Count of artifacts with zero chunks in last run. | Alert when count grows between runs. |
| `km_coverage_stale_artifacts_total` | Gauge | `profile` | Removed/stale artifacts detected in the latest ingest. | Alert when value stays >0 for multiple runs (cleanup failing). |
| `km_ingest_stale_resolved_total` | Counter | `profile` | Number of stale artifacts removed during ingestion (cumulative). | Alert when spikes exceed expected churn (possible mass deletions). |
| `km_ingest_skips_total` | Counter | `reason` | Scheduler/automation ingest skips partitioned by reason. | Alert on sustained `auth`, `lock`, or `head` growth. |
| `km_watch_runs_total` | Counter | `result` | Watcher outcomes (`success`, `error`, `no_change`). | Alert when `error` outpaces `success` or `no_change` dominates unexpectedly. |
| `km_coverage_history_snapshots` | Gauge | `profile` | Number of retained coverage snapshots under `reports/history/`. | Alert when value drops below configured history limit (e.g., disk cleanup failure). |
| `km_backup_runs_total` | Counter | `result` (`success`,`failure`,`skipped_lock`) | Scheduled backup outcomes. | Alert when failures grow or locks skip repeatedly. |
| `km_backup_last_status` | Gauge | _none_ | Last backup status (1=success, 0=failure). | Alert when zero for sustained intervals. |
| `km_backup_last_success_timestamp` | Gauge | _none_ | Unix timestamp of the last successful backup run. | Alert when stale relative to expected cadence. |
| `km_search_requests_total` | Counter | `status` (`success`,`failure`) | Search API requests partitioned by outcome. | Alert when failure ratio rises above baseline. |
| `km_search_graph_cache_events_total` | Counter | `status` (`miss`,`hit`,`error`) | Tracks graph context cache utilisation. | Alert when `status="error"` climbs or hit ratio drops suddenly. |
| `km_search_graph_lookup_seconds` | Histogram | _none_ | Latency of Neo4j lookups for search enrichment. | Alert when P95 exceeds expected threshold (e.g., >250 ms). |
| `km_search_adjusted_minus_vector` | Histogram | _none_ | Distribution of adjusted minus vector scores per result. | Alert when distribution skews heavily positive/negative (ranking drift). |
| `km_graph_dependency_status` | Gauge | _none_ | 1 when Neo4j dependency is healthy, 0 when connection attempts fail. | Page if value stays at 0 across scrapes (graph unavailable). |
| `km_graph_dependency_last_success_timestamp` | Gauge | _none_ | Unix timestamp of the last successful Neo4j heartbeat. | Alert when timestamp is older than the expected heartbeat window. |
| `km_qdrant_dependency_status` | Gauge | _none_ | 1 when Qdrant health checks succeed, 0 for failures. | Page if value stays at 0 across scrapes (vector store unavailable). |
| `km_qdrant_dependency_last_success_timestamp` | Gauge | _none_ | Unix timestamp of the last successful Qdrant heartbeat. | Alert when timestamp is older than the expected heartbeat window. |
| `km_graph_cypher_denied_total` | Counter | `reason` (`keyword`,`procedure`,`structure`,`mutation`) | Maintainer `/graph/cypher` requests blocked by read-only safeguards. | Alert when non-zero growth occurs outside intentional testing (possible intrusion or misconfiguration). |
| `km_ui_requests_total` | Counter | `view` | Embedded console visits by view (`landing`, `search`, `subsystems`, `lifecycle`). | Alert on prolonged spikes (possible scraping) or sudden drops during active adoption. |
| `km_ui_events_total` | Counter | `event` | UI-triggered events (`lifecycle_download`, MCP recipe copy buttons, subsystem downloads). | Alert when error events appear or download volume surges unexpectedly. |
| `km_lifecycle_stale_docs` | Gauge | `profile` | Latest stale document count emitted during ingest. | Alert when value exceeds the stale-days threshold for >24h. |
| `km_lifecycle_isolated_nodes` | Gauge | `profile` | Orphaned/isolated graph nodes detected in last ingest. | Alert when count increases between runs. |
| `km_lifecycle_missing_tests` | Gauge | `profile` | Subsystems lacking tests. | Alert when value remains above zero.
| `km_lifecycle_removed_artifacts` | Gauge | `profile` | Recently removed artifacts pending cleanup. | Alert when value stays non-zero across runs. |
| `km_graph_migration_last_status` | Gauge | _none_ | 1=success, 0=failure, -1=skipped (auto-migrate state). | Alert on 0 or when paired timestamp is stale. |
| `km_graph_migration_last_timestamp` | Gauge | _none_ | Unix timestamp of last graph migration attempt. | Alert when older than deployment policy while auto-migrate is enabled. |
| `km_scheduler_runs_total` | Counter | `result` (`success`,`failure`,`skipped_head`,`skipped_lock`,`skipped_auth`) | Scheduled ingestion job outcomes. | Alert if `result="failure"` or `skipped_auth` increments unexpectedly. |
| `km_scheduler_last_success_timestamp` | Gauge | _none_ | Unix timestamp of last successful scheduled ingestion run. | Alert when stale relative to configured schedule. |
| `uvicorn_requests_total` (via OTEL / ASGI) | Counter | `method`, `path`, `status_code` | Requires tracing enabled. | Alert on elevated 5xx rates or 429 spikes. |

Grafana dashboard updates:

- **Stale Artifacts Removed** visualises `increase(km_ingest_stale_resolved_total[1h])` per profile so you can spot unexpected purges.
- **Ingest Skips by Reason** overlays `increase(km_ingest_skips_total[1h])` so auth/lock/head skips stand out.
- **Watcher Outcomes** charts `rate(km_watch_runs_total{result}[5m])` for success/error/no-change to highlight automation drift.

### Lifecycle Sparklines & History

- `/lifecycle/history` returns enriched entries with a `counts` map powering the UI spark lines. The console requests this endpoint after loading `/lifecycle` and renders inline SVGs for stale docs, isolated nodes, missing tests, and removed artifacts.
- Persist at least three history snapshots per environment so trends are visible. Set `KM_LIFECYCLE_HISTORY_LIMIT` to balance storage vs fidelity (default 30).
- When plotting in Grafana, combine the gauges (`km_lifecycle_*`) with transforms or the history endpoint to show short-term trends alongside absolute counts.

### Prometheus Scrape Example

```yaml
scrape_configs:
  - job_name: 'duskmantle-gateway'
    metrics_path: /metrics
    static_configs:
      - targets: ['gateway:8000']
        labels:
          profile: prod
    authorization:
      type: bearer
      credentials: ${KM_ADMIN_TOKEN}
```

### Alert Cookbook

- **Ingestion Failure:** Alert when `km_ingest_last_run_status == 0` for any profile or when `time() - km_ingest_last_run_timestamp > 2 * interval`.
- **Stale Coverage:** `time() - km_coverage_last_run_timestamp > 7200` or `km_coverage_last_run_status == 0` for two scrapes.
- **Search Failure Ratio:** `rate(km_search_requests_total{status="failure"}[15m]) / rate(km_search_requests_total[15m]) > 0.05` sustained for 10 minutes.
- **Graph Lookup Latency:** `histogram_quantile(0.95, rate(km_search_graph_lookup_seconds_bucket[10m])) > 0.25` indicates Neo4j responsiveness issues—investigate database health or enable caching.
- **Cypher Denials:** Alert when `increase(km_graph_cypher_denied_total[15m]) > 0` and `reason` is not tied to load-testing. Blocked write attempts may indicate a leaked maintainer token or a broken client.
- **Ranking Drift:** Monitor `km_search_adjusted_minus_vector` moving average; sustained positive deltas may mean graph weighting dominates vectors (or vice versa if negative). Alert when mean delta leaves the [-0.2, 0.2] band.
- **Rate Limit Hotspot:** `rate(uvicorn_requests_total{status_code="429"}[5m]) > 5` indicates throttling pressure; investigate abusive clients or increase `KM_RATE_LIMIT_REQUESTS`.
- **High Ingestion Latency:** `histogram_quantile(0.95, sum(rate(km_ingest_duration_seconds_bucket[15m])) by (le)) > <SLO>`.
- **Scheduler Regression:** Alert when `time() - km_scheduler_last_success_timestamp > 2 * expected_interval` or when `rate(km_scheduler_runs_total{result="failure"}[30m]) > 0`.
- **Lifecycle Regression:** Trigger when `km_lifecycle_stale_docs > threshold` or `km_lifecycle_isolated_nodes > 0` for more than 24 h. Use `/lifecycle/history` as a secondary check to confirm trend direction before paging.
- **UI Engagement Drop:** Alert when `rate(km_ui_requests_total[30m])` drops below baseline during active business hours, or when `km_ui_events_total{event="lifecycle_download"}` flatlines (users may have lost access).

### Health Endpoints

- `GET /healthz` returns an overall `status` (`ok` or `degraded`) plus detailed checks for `coverage`, `audit`, `scheduler`, `graph`, `qdrant`, and `backup`.
  - Coverage check tracks file freshness, missing artifact count, and falls back to `stale` when older than twice the scheduler interval (or 24h without a scheduler).
  - Audit check ensures the SQLite ledger is present and readable.
  - Scheduler check reports `running`, `stopped`, or `disabled` alongside the configured interval.
- `GET /readyz` remains a lightweight readiness probe and still returns `{ "status": "ready" }` when the API stack is serving requests.

## 3. Structured Logging

Logs are emitted as JSON to stdout. Sample entry:

```json
{
  "level": "INFO",
  "logger": "gateway.ingest.pipeline",
  "message": "Generated chunks",
  "ingest_run_id": "4f5c...",
  "profile": "prod",
  "chunk_count": 1242
}
```

### Tips

- Route container stdout to a log shipper (Fluent Bit, Vector). Configure parsers for JSON to index key fields.
- On startup the API emits a `event="startup_config"` log summarizing version, auth mode, ingest chunk settings, embedding model, and resolved search weights—capture it for release notes and audits.
- Search for `"level": "ERROR"` to surface ingestion failures.
- Correlate application logs with scheduler logs under `/opt/knowledge/var/logs/supervisor/` if running under Supervisord.

### Correlating with Audit History

Use the `ingest_run_id` from logs to fetch provenance:

```bash
curl -H "Authorization: Bearer $KM_ADMIN_TOKEN" \
  "http://localhost:8000/audit/history?limit=5" | jq
```

## 4. Tracing

Enable tracing by setting environment variables:

- `KM_TRACING_ENABLED=true`
- `KM_TRACING_ENDPOINT=http://otel-collector:4318/v1/traces`
- `KM_TRACING_HEADERS="authorization=Bearer <token>"` (optional)
- `KM_TRACING_SAMPLE_RATIO=0.25` (sample 25% of requests/jobs)
- `KM_TRACING_SERVICE_NAME` to override default name.
- `KM_TRACING_CONSOLE_EXPORT=true` to mirror spans to stdout (local debugging).

### Components Covered

- FastAPI request lifecycles (handled by `opentelemetry-instrumentation-fastapi`).
- Outgoing HTTP calls made with `requests` (Qdrant, Neo4j, model downloads).
- Ingestion pipeline spans: `ingestion.discover`, `ingestion.chunk`, `ingestion.embed`, `ingestion.persist` with success flags and counts.

### Collector Quick Start

To run a local OTLP mirror with Jaeger UI:

```bash
docker run --rm -p 16686:16686 -p 4318:4318 \
  -e COLLECTOR_OTLP_ENABLED=true \
  jaegertracing/all-in-one:1.57
```

Then point `KM_TRACING_ENDPOINT=http://localhost:4318/v1/traces`.

## 5. Auth & Rate Limiting Signals

- 401/403 responses increment `uvicorn_requests_total{status_code="401"}` when tracing is enabled. Watch for misconfigured tokens.
- Rate limiter uses SlowAPI; repeated throttling surfaces as 429 responses. Consider exposing a Prometheus counter via SlowAPI if rate spikes are common.
- For proactive monitoring, scrape nginx or reverse-proxy logs if fronting the gateway.

## 6. Scheduler & Coverage Monitoring

- Scheduler state lives under `/opt/knowledge/var/scheduler/`. Presence of `.lock` files indicates active runs.
- File `scheduler.log` (if supervisor-managed) shows job launches and skip reasons.
- Coverage reports detail repository parity:

```bash
jq '.summary' /opt/knowledge/var/reports/coverage_report.json
```

- Alert if coverage completion percentage drops or number of missing artifacts increases by more than X% between runs.

## 7. Troubleshooting Scenarios

### 7.1 Ingestion Fails Repeatedly

1. Check logs for exceptions (`ERROR` level) referencing Qdrant/Neo4j.
2. Inspect audit history to confirm failure reason.
3. Verify external services are reachable (`nc gateway-qdrant 6333`).
4. Re-run `gateway-ingest rebuild --dry-run` to reproduce locally; capture spans if tracing is enabled.

### 7.2 Scheduler Never Triggers

1. Confirm `KM_SCHEDULER_ENABLED=true` and inspect supervisor logs for startup errors.
2. Ensure state directory is writable; look for permission issues under `/opt/knowledge/var/scheduler`.
3. Check `KM_SCHEDULER_INTERVAL_MINUTES`; values under 1 minute are coerced by APScheduler (avoid extremely low values).

### 7.3 Tracing Produces No Spans

1. Confirm `KM_TRACING_ENABLED=true` and that the collector endpoint is reachable (`curl -I $KM_TRACING_ENDPOINT`).
2. Verify OTLP headers (typos in `KM_TRACING_HEADERS` are ignored silently).
3. Set `KM_TRACING_CONSOLE_EXPORT=true` to validate spans locally; disable after testing to reduce noise.
4. Ensure `KM_TRACING_SAMPLE_RATIO` > 0.

### 7.4 Metrics 401s with Auth Enabled

1. Use maintainer token (`KM_ADMIN_TOKEN`) when scraping `/metrics`.
2. If using Prometheus, configure bearer token in job config (see §2).
3. Confirm rate limiting is not throttling your collector (increase `KM_RATE_LIMIT_REQUESTS`).

### 7.5 API 401/403 Diagnostics

1. `401 Unauthorized` indicates missing credentials—ensure the `Authorization: Bearer <token>` header is present. Reader endpoints accept either `KM_READER_TOKEN` or `KM_ADMIN_TOKEN`.
2. `403 Forbidden` indicates invalid or mis-scoped tokens. Verify the token value matches the configured env var and use the maintainer token for ingestion, coverage, or `/graph/cypher` operations.
3. Rotate tokens by updating `KM_READER_TOKEN`/`KM_ADMIN_TOKEN` and restarting the container; stale clients should be updated immediately to avoid auth failures.

### 7.6 Coverage Report Missing

1. Set `KM_COVERAGE_ENABLED=true`.
2. Confirm ingestion ran successfully (audit + metrics).
3. Check container logs for permission errors writing to `/opt/knowledge/var/reports`.

## 8. Alerting Recommendations

- **Ingestion Success:** Alert on `km_ingest_last_run_status == 0` or stale `km_ingest_last_run_timestamp`.
- **Ingestion Latency:** Alert when `histogram_quantile(0.95, rate(km_ingest_duration_seconds_bucket[15m])) > SLO`.
- **API Health:** Alert on `rate(uvicorn_requests_total{status_code=~"5.."}[5m])` > threshold.
- **Rate Limit Hotspot:** Page when 429 responses exceed 1% of total for 10 minutes.
- **Storage Usage:** Monitor `/opt/knowledge/var` disk usage via node exporter or container runtime.
- **Search-Specific Alerts:** Implement the Prometheus rules in `docs/DASHBOARD_SEARCH_HEALTH.md` (`SearchGraphCacheHitRatioLow`, `SearchGraphLookupLatencyHigh`, `SearchRankingDeltaDrift`) to catch Neo4j regressions and ranking drift early.

## 9. Operational Runbooks

- **Daily:** Review Prometheus dashboard for ingest and API metrics. Spot-check tracing sample.
- **Weekly:** Validate audit ledger and coverage report; export snapshots for compliance if needed.
- **Monthly:** Rotate tokens (`KM_ADMIN_TOKEN`, `KM_READER_TOKEN`) and OTLP credentials; update `.env` accordingly.
- **Search Graph Cache:** When cache hit ratio drops below 85%, inspect the cache utilisation panel and confirm repeated queries reuse cached context. Investigate Neo4j availability if errors spike.
- **Search Graph Latency:** If lookup P95 exceeds 250 ms, profile Neo4j resource usage/queries and check for infrastructure contention.
- **Ranking Drift:** When ranking delta exceeds ±0.2, review recent weight changes or ML model rollouts; compare against MCP feedback quality.
- **Slow Graph Lookups:** Warning logs emit `event="graph_lookup_slow"` with a `request_id` when enrichment exceeds `KM_SEARCH_WARN_GRAPH_MS`. Join on the same request ID in feedback telemetry for deeper analysis.

### Graph Health Checklist

1. **Metrics Sweep:** Confirm `km_graph_migration_last_status` == 1 (or -1 if intentionally disabled) and that `km_graph_migration_last_timestamp` is recent when auto-migrate is enabled. Pair with search graph metrics to spot lookup errors.
2. **Dry-Run Migrations:** Execute `gateway-graph migrate --dry-run` against the target environment to list pending IDs; investigate any unexpected migrations before approving rollout.
3. **Validation Harness:** Run `pytest -m neo4j` (or trigger the "Neo4j Integration Tests" workflow) to exercise ingestion + search replay against a live database. Failures usually indicate schema drift or broken relationships.
4. **Log Review:** Search for `graph_context_error` / `graph_path_depth_error` log events; spikes correlate with cache errors surfaced in Prometheus.
5. **Rollback Prep:** Ensure rollback Cypher scripts (see §9 in `GRAPH_API_DESIGN.md`) are accessible alongside deployment playbooks.

## 10. Reference Commands

| Task | Command |
|------|---------|
| Tail latest logs | `docker logs -f duskmantle-km` |
| Manual ingest with tracing | `KM_TRACING_ENABLED=true gateway-ingest rebuild --profile prod` |
| Export ranking dataset | `gateway-search export-training-data --require-vote --output feedback/datasets/train.csv` |
| Train ranking model | `gateway-search train-model feedback/datasets/train.csv --output feedback/models/model.json` |
| Evaluate ranking model | `gateway-search evaluate-model feedback/datasets/val.csv feedback/models/model.json` |
| Prune feedback log | `gateway-search prune-feedback --max-age-days 30 --max-requests 5000` |
| Redact dataset columns | `gateway-search redact-dataset feedback/datasets/train.csv --drop-query --drop-context` |

### Ranking Operations

- **Feedback hygiene:** schedule `gateway-search prune-feedback` to keep `/opt/knowledge/var/feedback/events.log` under control (age + max-request bounds). Run before daily exports to avoid stale training data.
- **Dataset privacy:** if exporting datasets beyond the trust boundary, run `gateway-search redact-dataset` to blank queries, context payloads, and reviewer notes. Redacted files retain the numeric features required by the trainer/evaluator.
- **Evaluation cadence:** keep a holdout dataset (e.g., `feedback/datasets/validation.csv`) and benchmark new models with `gateway-search evaluate-model` before flipping `KM_SEARCH_SCORING_MODE=ml`. Record MSE/NDCG deltas in release notes for auditability.
- **CI health checks:** GitHub Actions workflow `Observability Checks` runs nightly (03:00 UTC) to build the container, launch it locally, and assert `/readyz`, `/healthz`, `/metrics`, and `/coverage` behave as expected. Monitor workflow results for early warning signals.
| Show audit history via CLI | `gateway-ingest audit-history --limit 10` |
| Verify scheduler status | `ls -l /opt/knowledge/var/scheduler` |
| Inspect audit DB | `sqlite3 /opt/knowledge/var/audit/audit.db "select * from audit_runs order by created_at desc limit 5;"` |
| Reset tracing during development | `python -c "from gateway.observability.tracing import reset_tracing_for_tests; reset_tracing_for_tests()"` |

## 11. Review Log

- _2025-02-18:_ Added search dashboard & alert plan (pending Grafana deployment validation by SRE + Applied ML).

## 12. Further Reading

- `docs/RISK_MITIGATION_PLAN.md` (§7) for observability risks and mitigations.
- `docs/archive/WP5/WP5_EXECUTION_PLAN.md` for milestone-level objectives.
- `README.md` — quick start and environment variable reference.
- `AGENTS.md` — contributor expectations for testing and validation flows.

Maintain this guide alongside code changes that affect telemetry so operators always have up-to-date runbooks.
