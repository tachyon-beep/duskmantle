# Quick Wins

| Order | Work Package | Impact | Effort | Rationale |
|-------|--------------|--------|--------|-----------|
| 1 | WP-001 Enforce UI Auth on Sensitive Observability Views *(Done)* | High | S | Delivered in this cycle; UI routes now respect reader/maintainer scopes. |
| 2 | WP-003 Fail Fast on Critical Dependency Outages *(Done)* | High | S | Implemented strict-startup toggle and readiness degradation reporting. |
| 3 | WP-004 Cap Maintainer Cypher Query Resource Usage | Medium | S | Small parser enhancement that avoids expensive graph scans driven by maintenance users. |
| 4 | WP-007 Validate Backup Script Availability at Startup | Medium | S | Simple filesystem check that surfaces backup gaps early. |
| 5 | WP-008 Surface Search ML Mode Telemetry | Medium | S | Adds observability for ML fallback with light-touch metric changes. |
| 6 | WP-009 Document Coverage & Lifecycle History Retention Controls | Medium | XS | Documentation-only task clarifying retention knobs to operators. |
