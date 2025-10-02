# Work Packages

## Priority: CRITICAL

## WP-001: Enforce Secure Authentication Defaults *(Completed)*

**Category**: Security
**Priority**: CRITICAL
**Effort**: S
**Risk Level**: Critical

### Description
Ensure the container ships with secure-by-default behaviour so unauthenticated access is never exposed inadvertently.

### Current State
As of the latest hardening pass the entrypoint generates reader/maintainer tokens and a strong Neo4j password on first boot, persists them to `${KM_VAR}/secrets.env`, and fails fast when credentials are missing while auth remains enabled. Documentation and samples now reference the stored secrets and the `KM_ALLOW_INSECURE_BOOT` escape hatch for demos.

### Desired State
Continue to enforce and document secure defaults, and monitor for regressions in future releases (e.g., non-container deployments or custom entrypoints).

### Impact if Not Addressed
Regressions would reintroduce the risk of accidental anonymous access to REST and MCP surfaces.

### Proposed Solution
Maintain automated tests guarding against missing/weak credentials, keep documentation up to date, and include secure-boot verification in release smoke tests.

### Affected Components
- gateway/api/app.py
- gateway/config/settings.py
- infra/docker-entrypoint.sh
- infra/examples/docker-compose.sample.yml
- Dockerfile
- bin/km-bootstrap
- tests/test_app_smoke.py
- tests/test_settings_defaults.py

### Dependencies
- None

### Acceptance Criteria
- [x] Startup aborts with clear error when auth is enabled but tokens/passwords are missing or weak
- [x] Docker compose example and README describe secure bootstrapping steps
- [x] pytest smoke covering new behaviours passes

### Related Issues
RISK-001

## WP-002: Protect Qdrant Collections From Accidental Recreate *(Completed)*

**Category**: Operational
**Priority**: CRITICAL
**Effort**: S
**Risk Level**: Critical

### Description
Prior behaviour recreated the Qdrant collection whenever existence checks failed, wiping embeddings during transient outages. The package captures the remediation and guards needed to keep collection management safe.

### Current State
`QdrantWriter.ensure_collection()` now performs idempotent `create_collection` calls with bounded retries and exposes a separate `reset_collection` helper for explicit destructive resets. New unit tests cover retry/backoff, conflict handling, and the reset path.

### Desired State
Collection creation remains idempotent and data-preserving; destructive recreation is only triggered through the explicit reset helper.

### Impact if Not Addressed
Addressed; regression tests should guard against future reintroduction of destructive behaviour.

### Proposed Solution
Maintained via regression tests around the non-destructive ensure path and explicit reset helper.

### Affected Components
- gateway/ingest/qdrant_writer.py
- gateway/ingest/service.py
- tests/test_qdrant_writer.py

### Dependencies
- WP-001

### Acceptance Criteria
- [x] Integration/unit tests prove ensure_collection survives transient errors without data loss
- [x] Collection recreation happens only when an explicit destructive helper is invoked
- [ ] Operational runbook updated to explain safe recovery steps

### Related Issues
RISK-002

## Priority: HIGH

## WP-003: Harden Maintainer Cypher Endpoint

**Category**: Security
**Priority**: HIGH
**Effort**: M
**Risk Level**: High

### Description
The /graph/cypher endpoint relies on simple string checks to enforce read-only queries, which can be bypassed with obfuscated Cypher.

### Current State
Cypher requests now execute via a read-only driver (when configured) with `RoutingControl.READ`, the summary counters are inspected for write activity, literals/comments are stripped before validation, and procedure calls are whitelisted to schema inspection routines. New unit tests cover write attempts (including counters) and disallowed procedures. Operators can supply `KM_NEO4J_READONLY_*` credentials to enforce read-only access at the driver level.

### Desired State
Maintain the read-only enforcement and expand documentation/runbooks so operations teams routinely configure separate read-only credentials for maintainer queries.

### Impact if Not Addressed
A compromised maintainer token or auth-disabled deployment could allow hostile graph mutations or data exfiltration beyond expectations.

### Proposed Solution
Completed in code (read-only driver option, stricter validation/whitelisting, regression tests); update operational docs to prescribe the read-only credential setup and add monitoring for repeated blocked calls.

### Affected Components
- gateway/api/routes/graph.py
- gateway/graph/service.py
- infra/neo4j.conf
- tests/test_graph_api.py

### Dependencies
- WP-001

### Acceptance Criteria
- [x] Attempted write queries are rejected in unit/integration tests
- [x] Documentation/runbook instructs operators to configure read-only Neo4j credentials for maintainer queries
- [x] Observability guidance captures monitoring for blocked Cypher attempts

### Related Issues
RISK-003

## WP-004: Add Dependency Health Checks and Auto-Reconnect

**Category**: Operational
**Priority**: HIGH
**Effort**: M
**Risk Level**: High

### Description
Once booted, the API keeps long-lived Neo4j and Qdrant handles without periodic validation or automatic recovery.

### Current State
graph_driver and qdrant_client are created at startup and reused; if the backing services restart, calls return 503 or raise exceptions until a manual restart.

### Desired State
Background probes detect unhealthy dependencies, refresh clients, and expose degraded status via /healthz and metrics.

### Impact if Not Addressed
Service restarts or network partitions cause prolonged downtime and confusing 500s for MCP tools and API consumers.

### Proposed Solution
Add async tasks or dependency wrappers that retry and recreate clients, extend /healthz to include connectivity, and emit Prometheus gauges for dependency status.

### Affected Components
- gateway/api/app.py
- gateway/api/dependencies.py
- gateway/api/routes/health.py
- gateway/observability/metrics.py
- tests/test_app_smoke.py

### Dependencies
- WP-001
- WP-002

### Acceptance Criteria
- [ ] Automated test simulates Neo4j restart and verifies client recovery without full API reboot
- [ ] /healthz surfaces dependency degradation and recovery timing
- [ ] Runbook updated with troubleshooting guidance

### Related Issues
RISK-004

## WP-005: Automate State Backups and Recovery Playbooks

**Category**: Operational
**Priority**: HIGH
**Effort**: M
**Risk Level**: High

### Description
Backups exist only as a manual MCP tool; there is no scheduled capture or documented restoration workflow.

### Current State
km-backup is exposed via MCP but relies on operators remembering to run it; archives are stored locally with no retention policy.

### Desired State
Automated, scheduled backups with configurable retention and documented recovery drills.

### Impact if Not Addressed
Operational mistakes or disk loss could permanently delete Neo4j/Qdrant state.

### Proposed Solution
Add scheduler hooks or external scripts to trigger backups, stream archives to durable storage, document restore procedure, and add smoke tests validating archives.

### Affected Components
- gateway/mcp/backup.py
- gateway/scheduler.py
- docs/OPERATIONS.md
- infra/examples/docker-compose.sample.yml

### Dependencies
- WP-002

### Acceptance Criteria
- [ ] Backup job runs on configurable cadence and surfaces metrics
- [ ] Disaster-recovery doc demonstrates restoring a fresh environment
- [ ] CI smoke test validates archive integrity

### Related Issues
RISK-005

## WP-006: Harden Container Runtime and Service Isolation

**Category**: BestPractice
**Priority**: HIGH
**Effort**: M
**Risk Level**: Medium

### Description
The Docker image runs as root and bundles Neo4j, Qdrant, and the API in a single container.

### Current State
docker-entrypoint launches supervisord that controls all processes; file permissions and network ports are fully exposed.

### Desired State
Least-privilege runtime with separated services (compose or helm), non-root users, and minimal exposed ports.

### Impact if Not Addressed
A single compromise grants access to graph/vector data and OS-level privileges.

### Proposed Solution
Create dedicated users, split services into separate containers (or document compose topology), tighten filesystem permissions, and add securityContext guidance.

### Affected Components
- Dockerfile
- infra/docker-entrypoint.sh
- infra/examples/docker-compose.sample.yml
- docs/DEPLOYMENT.md

### Dependencies
- WP-001

### Acceptance Criteria
- [ ] Containers run as non-root in CI smoke tests
- [ ] Sample deployment separates API/Qdrant/Neo4j with documented networking
- [ ] Security guide updated with hardening steps

### Related Issues
RISK-006

## Priority: MEDIUM

## WP-008: Bound Search Feedback Store Growth

**Category**: Operational
**Priority**: MEDIUM
**Effort**: S
**Risk Level**: Medium

### Description
Search feedback events append to a single JSONL file without retention or rotation.

### Current State
events.log grows indefinitely; corrupted writes or disk exhaustion are not handled.

### Desired State
Feedback storage rotates, validates writes, and surfaces capacity metrics.

### Impact if Not Addressed
Disk fill leads to ingestion/search failures and loss of feedback data.

### Proposed Solution
Integrate log rotation or SQLite, guard writes with fsync/size limits, and emit Prometheus metrics for event counts.

### Affected Components
- gateway/search/feedback.py
- gateway/observability/metrics.py
- tests/test_search_service.py

### Dependencies
- None

### Acceptance Criteria
- [ ] Feedback store enforces configurable max file size/count
- [ ] Metrics or alerts fire when rotation occurs
- [ ] Existing tests updated to cover rotation edge cases

### Related Issues
RISK-007

## WP-009: Stabilise Incremental Ledger Handling

**Category**: TechnicalDebt
**Priority**: MEDIUM
**Effort**: S
**Risk Level**: Medium

### Description
The artifact ledger is plain JSON with no locking or schema validation, making incremental ingest brittle.

### Current State
Ledger writes overwrite the entire file, concurrent runs can corrupt it, and malformed entries are silently discarded.

### Desired State
Ledger updates are atomic, schema-validated, and recoverable after crashes.

### Impact if Not Addressed
Incremental ingest may skip updates or reprocess large sections when ledger corruption occurs.

### Proposed Solution
Use file locking, atomic temp-file writes, JSON schema validation, and recovery tooling for corrupt ledgers.

### Affected Components
- gateway/ingest/pipeline.py
- gateway/ingest/service.py
- tests/test_ingest_pipeline.py

### Dependencies
- WP-002

### Acceptance Criteria
- [ ] Ledger writes use atomic rename and acquire locks
- [ ] Schema validation rejects malformed entries with metrics/alerts
- [ ] Regression tests simulate interrupted writes without data loss

### Related Issues
RISK-008

## WP-007: Optimize Graph Enrichment Latency for Search

**Category**: Performance
**Priority**: MEDIUM
**Effort**: M
**Risk Level**: Medium

### Description
SearchService fetches graph context per result sequentially, risking latency spikes for larger result sets.

### Current State
Graph lookups run synchronously with per-result sessions; caching mitigates repeats but high-limit queries still incur N round-trips.

### Desired State
Graph enrichment batches lookups, honours timeouts, and emits metrics/alerts when graph fetches dominate response time.

### Impact if Not Addressed
User-facing MCP tools and API calls experience slow responses, undermining search experience.

### Proposed Solution
Introduce concurrent/batched graph fetches, enrich metadata with timings, add thresholds for disabling graph context when Neo4j is slow.

### Affected Components
- gateway/search/service.py
- gateway/graph/service.py
- gateway/observability/metrics.py
- tests/test_search_service.py

### Dependencies
- WP-004

### Acceptance Criteria
- [ ] Load test demonstrates improved p95 latency for include_graph=true
- [ ] Metrics expose graph enrichment timing per request
- [ ] Feature flag toggles graph enrichment when Neo4j is degraded

### Related Issues
RISK-007

## WP-010: Clarify API Versioning and Contract Guarantees

**Category**: BestPractice
**Priority**: MEDIUM
**Effort**: S
**Risk Level**: Low

### Description
Public REST and MCP contracts lack explicit versioning or deprecation policy.

### Current State
Routes live under /search, /graph, /coverage without version prefix; docs omit change management guidance.

### Desired State
Versioned API surface with changelog and compatibility expectations.

### Impact if Not Addressed
Client updates risk breaking changes, slowing adoption.

### Proposed Solution
Introduce /v1 prefix (or header-based versioning), publish schema docs, and add contract tests.

### Affected Components
- gateway/api/app.py
- gateway/api/routes/*
- docs/API_REFERENCE.md
- tests/test_app_smoke.py

### Dependencies
- WP-001

### Acceptance Criteria
- [ ] OpenAPI spec reflects versioned paths
- [ ] Docs describe upgrade policy and breaking-change process
- [ ] Contract tests assert backwards compatibility for core endpoints

### Related Issues
RISK-009
## Summary Statistics

### Counts by Category
- BestPractice: 2
- Operational: 4
- Performance: 1
- Security: 2
- TechnicalDebt: 1

### Counts by Priority
- CRITICAL: 2
- HIGH: 4
- MEDIUM: 4

### Estimated Effort (hours) by Priority
- CRITICAL: ~8h
- HIGH: ~64h
- MEDIUM: ~28h
