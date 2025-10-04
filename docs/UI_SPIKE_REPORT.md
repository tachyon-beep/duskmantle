# UI Spike Report

## 1. Scope Recap

The Phase 5 UI spike delivered a preview console hosted under `/ui/` with three views:

- **Search** – hybrid query form with result metadata (vector, lexical, adjusted scores) and feedback prompts.
- **Subsystem Explorer** – depth/limit controls, dependency tables, and artifact listings powered by `/graph/subsystems`.
- **Lifecycle Dashboard** – summary metrics and tabular breakdowns for stale docs, isolated nodes, test gaps, and removed artifacts.

The spike deliberately focused on read-only experiences, reusing existing API contracts so the container exposes an agent-friendly UX without introducing new backend workflows.

## 2. Integration Cost Summary

| Dimension | Impact | Notes |
|-----------|--------|-------|
| **Build footprint** | Minimal | Assets (CSS/JS/templates) live under `gateway/ui/` and ship with the wheel; no external Node/Vite toolchain required. Docker image size unchanged. |
| **Runtime surface** | +3 HTML routes, +1 JSON proxy | FastAPI now mounts `/ui/static`, `/ui/search`, `/ui/subsystems`, `/ui/lifecycle`, and `/ui/lifecycle/report`. All reuse existing dependency injection, so no extra services or background tasks. |
| **Auth/security** | Token modal backed by sessionStorage | Search/subsystems honour reader scope; lifecycle requires maintainer scope. No cookies added; the browser forwards bearer tokens on each request. Splash copy warns when lifecycle reporting disabled or tokens missing. |
| **Observability** | New metrics | `km_ui_requests_total{view}` and `km_ui_events_total{event}` expose page visits and lifecycle downloads. Request IDs from FastAPI middleware surface in the footer for log correlation. |
| **Docs/tests** | README, Quick Start, UI smoke tests | /ui guidance is documented for bootstrap flows; `tests/test_ui_routes.py` covers each view and the download path. |
| **Maintenance** | Low | Styling is hand-rolled (no Tailwind/Bulma). JS stays in one file with defensive guards; templates are server-rendered. Future work should keep the bundle small or consider a lightweight build step if charts land. |

## 3. Follow-up Recommendations

1. **Elevate to Work Package** – Promote the console to its own roadmap milestone (e.g., “WP7 Knowledge Console”) covering telemetry spark lines, MCP launch shortcuts, and accessibility polish.
2. **Telemetry backlog** – Instrument lifecycle history so future chart components have real data (`km_lifecycle_*` gauges or paged `/api/v1/lifecycle/history`).
3. **Docs & dashboards** – Extend `docs/OBSERVABILITY_GUIDE.md` and Grafana JSON to chart the new UI metrics.
4. **QA automation** – Consider adding Playwright smoke tests once the views accept live data from the container.

## 4. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| UI drift vs API changes | Keep the console reading from existing JSON payloads; add unit tests that stub API responses for edge cases. |
| Token persistence expectations | Current storage is session-bound. Document behaviour and revisit if offline caching is required. |
| Telemetry volume | Monitor `km_ui_requests_total` to ensure console traffic does not skew rate limits; add label-based filters in dashboards. |

## 5. Next Steps Snapshot *(Completed / Tracked)*

- Roadmap Phase 5 Step 5.3 now references the Knowledge Console milestone (see `docs/ROADMAP.md`).
- Observability guide documents UI metrics, lifecycle history, and sparkline telemetry alerts (`docs/OBSERVABILITY_GUIDE.md`).
- Sparkline telemetry plan is captured under Work Package B (Release 1.1.0) with implementation tracked via `RELEASE101_PACKAGES.md`.
