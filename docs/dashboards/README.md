# Grafana Dashboards

Import `gateway_overview.json` into Grafana (Dashboard > Import > Upload JSON). It visualises:

- `km_ingest_last_run_status` and `km_ingest_last_run_timestamp` for quick ingest health.
- Request latency (p95) using `histogram_quantile` on `uvicorn_request_duration_seconds_bucket`.
- Throughput comparison between `/search` and `/graph/*` via `uvicorn_requests_total` labels.
- Watcher activity panels (`km_watch_runs_total`, `km_watch_errors_total`, `km_watch_last_run_timestamp`) when watcher metrics are enabled.

**Publishing**

The release workflow attaches `docs/dashboards/gateway_overview.json` to each tagged release so teams can import the latest dashboard directly.
