# Draft PR: MCP Tooling, Lifecycle Console, and Operational Hardening

## Summary
- Introduced the embedded UI (search, subsystem explorer, lifecycle dashboard) with accessible styling, lifecycle spark lines, and Playwright UI test coverage.
- Added lifecycle reporting pipeline (`km-lifecycle-report`), MCP upload/storetext tools, recipe runner/recipes, and supporting docs.
- Hardened ingestion and observability: incremental ingest, artifact cleanup, scheduler/watch metrics, Grafana dashboard export, and risk plan updates.
- Enhanced release packaging: CI release workflow, km-watch helper, `.duskmantle` defaults, acceptance demo guidance, and CHANGELOG/RELEASE documentation.
- Updated hybrid search TODOs and risk plan follow-ups (quantization, classification samples, host matrix, alert integrations, signed images).

## Testing
- `pytest tests/mcp/test_server_tools.py`
- `pytest tests/test_scheduler.py`
- `pytest tests/test_ingest_pipeline.py`
- `pytest tests/test_lifecycle_report.py`
- `pytest tests/test_ui_routes.py`
- `npx playwright test`

## Docs
- ROADMAP, Implementation Plan, Observability Guide, UI Spike Report, Risk Plan, Hybrid Search TODOs.
- Quick Start, README, FAQ, Upgrade/Rollback, MCP guides, Acceptance demo playbook/snapshot.
- Grafana dashboards (`infra/grafana/search_observability.json`).
- Release guidance (CHANGELOG, RELEASE.md).

## Commits

| Commit | Description |
|--------|-------------|
| 4a644c6 | feat: Update ROADMAP and release notes for completed work packages |
| a49d178 | chore: remove obsolete config file and update .gitignore for new exclusions |
| 51cadd8 | Enhance accessibility and styling in UI components |
| 737e6d5 | feat(ui): Implement new UI components for lifecycle dashboard and subsystem explorer |
| 04182a6 | feat(ui): introduce embedded UI with search and lifecycle features, including styling and routing |
| 01fc404 | Pre 5.2 checkpoint |
| f53c815 | feat: add lifecycle reporting functionality and related CLI tools |
| 32c5d7a | refactor: simplify command structure for watcher program in supervisord configuration |
| 09e91e4 | feat(graph-api): Enhance subsystem endpoint to support multi-hop caching and new graph features |
| e189147 | feat: add incremental ingest support and enhance CLI options for rebuild |
| d429c76 | feat: enhance observability metrics and logging for ingestion and watch processes |
| f14e2b3 | Enhance security and artifact management in the knowledge gateway |
| 3567e37 | docs: update README and QUICK_START to include audit log details for MCP actions |
| e2129b0 | Refactor tests and update documentation for IntegrationSync |
| 926d965 | docs: enhance README and MCP_RECIPES with LLM Agent Workflow and command usage examples |
| 19381d0 | feat: default local mounts to .duskmantle (adds km-watch helper, backup/run scripts, docs updates) |

### Detailed Changes

- **4a644c6**: roadmap/docs refresh; Playwright tooling/tests; Grafana search dashboard; CI workflows updated; ADDED `bin/km-playwright`, Playwright configs.
- **a49d178**: cleaned ` .codex` config; updated `.gitignore` for build artefacts and Playwright state.
- **51cadd8**: accessibility overhaul (skip links, ARIA roles, focus styles); templates/styling/test updates.
- **737e6d5**: lifecycle dashboard, subsystem explorer, lifecycle ingest module, UI metrics, UI spike documentation, tests.
- **04182a6**: initial embedded UI scaffold (routes/templates/static assets) and UI route smoke tests.
- **01fc404**: recipe runner CLI/executor, sample recipes, docs, and unit tests.
- **f53c815**: lifecycle reporting CLI/module, `/lifecycle` endpoint, MCP integration, recipes executor enhancements, docs/tests.
- **32c5d7a**: watcher command simplified in `supervisord.conf`.
- **09e91e4**: upgraded graph service (multi-hop caching, orphan node endpoint, graph export), docs, tests.
- **e189147**: incremental ingest pipeline, CLI flags, settings, and coverage tests.
- **d429c76**: observability improvements (scheduler/watch/search metrics), km-watch tests, dashboard tweaks.
- **f14e2b3**: secure-mode enforcement, artifact deletion pipeline, stale artifact metrics, docs/tests.
- **3567e37**: doc updates noting MCP audit log entries in README/Quick Start.
- **e2129b0**: MCP server + utilities, upload/storetext handlers, docs refresh, tests.
- **926d965**: documentation updates for LLM agent workflow and MCP recipe usage.
- **19381d0**: default `.duskmantle` mounts; added km-watch; bootstrap/run script refresh; config reference, dashboards, tests.
