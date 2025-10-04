# Risk Register

| ID | Description | Category | Likelihood | Impact | Mitigation / Owner | Monitoring |
|----|-------------|----------|------------|--------|--------------------|------------|
| R1 | UI lifecycle/event endpoints remain unauthenticated when auth is enabled, exposing operational data. | Security | Medium | High | WP-001 (Platform) | Add auth regression tests & monitor access logs |
| R2 | In-memory rate limiter resets per process; multi-node deployments bypass throttles. | Operational | High | Medium | WP-002 (SRE) | Configure shared backend metrics & alerts on request burst rate |
| R3 | Gateway reports ready even when Neo4j/Qdrant unreachable, causing brown-outs on rollout. | Operational | Low | Medium | Mitigated by WP-003 (Platform) | Monitor readiness metrics & strict-startup alarms |
| R4 | Maintainer Cypher endpoint allows unrestricted LIMIT values leading to heavy queries. | Performance | Medium | Medium | WP-004 (Graph Team) | Alert on high-duration cypher queries |
| R5 | Sequential graph enrichment in search causes timeouts under load, degrading relevance. | Performance | Medium | Medium | WP-005 (Search) | Track search latency histogram, graph warnings |
| R6 | `gateway/graph/service.py` monolith increases regression risk and hampers onboarding. | Quality | Medium | Medium | WP-006 (Platform) | PR checklists + static analysis complexity budget |
| R7 | Backup script misconfiguration only detected during scheduled run; backups silently missing. | Operational | Medium | Medium | WP-007 (SRE) | Health check alerts on backup status gauge |
| R8 | ML scoring fallback lacks telemetry; operators unaware when heuristic mode active. | Enhancement | Medium | Medium | WP-008 (Search) | Add metric alarms and metadata inspection |
