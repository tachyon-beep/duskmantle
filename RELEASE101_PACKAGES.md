# Release 1.0.1 Work Packages

## Work Package A – MCP Content Capture & Tooling *(Completed)*
- Follow ROADMAP §5 tasks for `km-upload`/`km-storetext` and shared MCP utilities.
- Wire helpers into MCP server, update specs/docs, and enforce maintainer/audit requirements.
- Add regression tests per Roadmap Phase 1–3 and close Implementation Plan §3.2 scope enforcement items.

## Work Package B – Console Telemetry & UI Polish *(Completed)*
- Knowledge Console Phase 1 lifecycle history and sparkline plumbing is live; documentation notes remaining Grafana export work (ROADMAP §142–150).
- Observability guide incorporates UI metrics, lifecycle history guidance, and sparkline alerting; UI spike report marked up-to-date.
- Nightly observability workflow provisions Node/Playwright and runs `npx playwright test`, integrating the UI suite into CI (ROADMAP §170).

## Work Package C – Operational Hardening & Observability *(Completed)*
- Phase 3 items (scheduler metrics, scope enforcement, token docs, tracing guidance) captured in the implementation plan.
- Observability guide refreshed with lifecycle metrics, UI telemetry, and alert cookbook updates.
- Grafana search dashboard exported to `infra/grafana/search_observability.json` for automation.

## Work Package D – Release Engineering & Packaging *(Completed)*
- Phase 4 release automation/operator enablement/acceptance validation tasks are documented as complete in the Implementation Plan.
- Risk mitigation notes updated to track container size quantization follow-up and signed image decision.

## Work Package E – Relevance & Risk Follow-ups *(Completed)*
- Hybrid search backlog consolidated into actionable steps (weight monitoring, HNSW benchmarking, sparse query fallback plan) in `docs/HYBRID_SEARCH_TODO.md`.
- Risk mitigation open questions updated with follow-up actions for quantization, classification samples, compatibility matrix, alert integrations, and signed images.
- Implementation plan Phase 5 status now reflects MCP telemetry integration through `release.yml`.
