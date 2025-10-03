# Changelog

All notable changes to this project will be documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- Hardened backup retention: backups now default to `${KM_STATE_PATH}/backups/archives`, the scheduler only prunes `km-backup-*.tgz` archives, and a new metric (`km_backup_retention_deletes_total`) tracks deletions while leaving operator-managed files untouched.

## 1.1.0 - 2025-10-01

- _TBD: populate with highlights for the 1.1.0 release._

## 1.0.1 - 2025-09-30

### Added

- Embedded lifecycle console: lifecycle spark lines, subsystem explorer, and Playwright UI smoke tests (navigation, lifecycle, search, subsystem flows).
- Lifecycle reporting pipeline (`km-lifecycle-report` CLI, `/lifecycle` + `/lifecycle/history` endpoints) including MCP tooling and recipes.
- Incremental ingest (`gateway-ingest rebuild --incremental`), artifact cleanup, and enhanced scheduler/watch observability metrics.
- Grafana search observability dashboard export (`infra/grafana/search_observability.json`).

### Changed

- Roadmap/implementation plan updated to reflect completed MCP tooling, console telemetry, and release readiness tasks.
- Observability guide expanded with UI metrics, lifecycle alerts, and sparkline guidance; risk mitigation plan refreshed.
- Release workflows now run Playwright UI tests and MCP smoke slice on nightly/tagged builds; helper `bin/km-playwright` introduced.

### Fixed

- Addressed security hardening gaps (mandatory maintainer tokens when auth enabled, stale artifact cleanup) and tightened watcher/scheduler behaviour under contention.

## 1.0.0 - 2025-09-28

### Added

- Hybrid dense+lexical search with tunable weights (`KM_SEARCH_VECTOR_WEIGHT`, `KM_SEARCH_LEXICAL_WEIGHT`) and optional HNSW recall control (`KM_SEARCH_HNSW_EF_SEARCH`).
- MCP server (`gateway-mcp`) exposing search, graph, ingest, coverage, backup, and feedback tools with Prometheus instrumentation.
- Release automation scripts (`scripts/build-wheel.sh`, `scripts/build-image.sh`, `scripts/checksums.sh`) and GitHub Actions workflow to build, test, and draft releases.
- Observability enhancements: new search metrics (`km_search_graph_lookup_seconds`, `km_search_adjusted_minus_vector`), structured logs, and expanded `/healthz` coverage checks.
- Acceptance demo playbook and snapshot documenting build metadata, ingest stats (run `c821eb34956345bc8ef7cb3765b4ab63`), backup validation, and MCP smoke results.

### Changed

- Archived historical work-package plans under `docs/archive/` now that 1.0.0 is locked; living docs reference the new paths.
- Repository version bumped to `1.0.0`; Docker image tagged `duskmantle/km:1.0.0` with supporting wheel/checksum artifacts.
- README, FAQ, and upgrade guide refreshed to reflect GitHub-only support model and acceptance snapshot expectations.

### Removed

- Temporary backup artifacts and planning documents from the active docs tree (moved to archive).
