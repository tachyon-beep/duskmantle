# Quick Wins

| Order | Work Package | Impact | Effort | Rationale |
|-------|--------------|--------|--------|-----------|
| 1 | WP-001 Enforce UI Auth on Sensitive Observability Views | High | S | Eliminates unauthenticated access to lifecycle data with minimal code changes (attach existing auth deps). |
| 2 | WP-003 Fail Fast on Critical Dependency Outages | High | S | Prevents unhealthy rollouts by reusing existing connection checks and readiness plumbing. |
| 3 | WP-004 Cap Maintainer Cypher Query Resource Usage | Medium | S | Small parser enhancement that avoids expensive graph scans driven by maintenance users. |
| 4 | WP-007 Validate Backup Script Availability at Startup | Medium | S | Simple filesystem check that surfaces backup gaps early. |
| 5 | WP-008 Surface Search ML Mode Telemetry | Medium | S | Adds observability for ML fallback with light-touch metric changes. |
| 6 | WP-009 Document Coverage & Lifecycle History Retention Controls | Medium | XS | Documentation-only task clarifying retention knobs to operators. |
