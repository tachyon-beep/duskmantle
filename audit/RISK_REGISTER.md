# Risk Register

## RISK-001: Gateway deployed with authentication disabled or default credentials

**Likelihood**: Low
**Impact**: Critical

### Description
Earlier revisions shipped with auth disabled and well-known credentials. The entrypoint now auto-generates strong secrets, but regressions or deliberate use of `KM_ALLOW_INSECURE_BOOT` can still expose the surface if misused.

### Mitigation Strategy
Keep WP-001 protections in place, bake secure-boot checks into release smoke tests, and document when insecure boot is permissible.

### Risk Ownership
Platform engineering

### Monitoring & Alerts
Add startup log assertions and periodic security scans to verify auth posture; review environment configs during release checklist.

### Review Cadence
Quarterly security review and pre-release penetration test.

## RISK-002: Qdrant collection recreated on transient errors

**Likelihood**: Medium
**Impact**: Critical

### Description
Recreating the collection erases embeddings; current logic does so if existence checks fail, including during minor outages.

### Mitigation Strategy
Apply WP-002 to remove destructive recreation, add retries, and alert on connectivity faults instead.

### Risk Ownership
Search platform

### Monitoring & Alerts
Emit metrics/alerts for Qdrant connectivity and collection mutations; audit ingestion logs for recreate events.

### Review Cadence
Review after each release involving ingest changes and during quarterly DR drills.

## RISK-003: Maintainer Cypher endpoint allows graph mutation

**Likelihood**: Low
**Impact**: High

### Description
String-based query filtering can be bypassed, enabling writes or admin operations when a maintainer token leaks.

### Mitigation Strategy
Deliver WP-003 to enforce read-only roles or AST validation and expand tests.

### Risk Ownership
Graph services

### Monitoring & Alerts
Log all /graph/cypher invocations with safe auditing; alert on client errors or suspicious patterns.

### Review Cadence
Security review after mitigation and annually thereafter.

## RISK-004: Long-lived Neo4j/Qdrant handles fail after dependency restart

**Likelihood**: Medium
**Impact**: High

### Description
The API caches drivers forever; service restarts lead to stuck 503/500 responses until manual intervention.

### Mitigation Strategy
Complete WP-004 to add health probes, auto-reconnect logic, and surfaced metrics.

### Risk Ownership
Platform engineering

### Monitoring & Alerts
Track dependency health metrics and alert on repeated auto-restart attempts or 5xx rates.

### Review Cadence
Include in on-call weekly health check and post-incident reviews.

## RISK-005: No automated backups for graph/vector state

**Likelihood**: Medium
**Impact**: High

### Description
State lives on local disk; only ad-hoc MCP backups exist, risking irrecoverable loss after hardware failure.

### Mitigation Strategy
Execute WP-005 to schedule backups, replicate archives, and document recovery.

### Risk Ownership
SRE / operations

### Monitoring & Alerts
Alert when scheduled backups fail or grow stale; track restore tests in runbook.

### Review Cadence
Include in quarterly DR exercises and after infrastructure changes.

## RISK-006: Monolithic container running as root

**Likelihood**: Low
**Impact**: High

### Description
Compromise of any process yields root access and full control of Neo4j and Qdrant data.

### Mitigation Strategy
Adopt WP-006 to split services, drop privileges, and tighten runtime policies.

### Risk Ownership
DevOps

### Monitoring & Alerts
Container scanning, runtime security events, and periodic CIS benchmark checks.

### Review Cadence
Security review after implementation and on each base-image update.

## RISK-007: Search latency and disk pressure from enrichment and feedback logs

**Likelihood**: High
**Impact**: Medium

### Description
Sequential graph enrichment and unbounded feedback logging can cause timeouts and fill storage during heavy usage.

### Mitigation Strategy
Implement WP-007 and WP-008 to batch graph calls, add timeouts, and rotate feedback artifacts.

### Risk Ownership
Search platform

### Monitoring & Alerts
Track graph lookup latency histograms, file sizes for events.log, and alert when thresholds are exceeded.

### Review Cadence
Monthly performance review and after major ingest/search releases.

## RISK-008: Incremental ingest ledger corruption

**Likelihood**: Medium
**Impact**: Medium

### Description
Ledger writes lack locking/validation, so partial writes or concurrent runs can break incremental ingest.

### Mitigation Strategy
Deliver WP-009 to introduce atomic writes, validation, and recovery tooling.

### Risk Ownership
Ingestion team

### Monitoring & Alerts
Add checksums/alerts when ledger fails to parse; monitor ingestion skip metrics.

### Review Cadence
Post-ingest incident review and quarterly ingest pipeline audit.

## RISK-009: Unversioned API contracts

**Likelihood**: Low
**Impact**: Medium

### Description
REST and MCP clients have no explicit compatibility guarantees, increasing breakage risk during releases.

### Mitigation Strategy
Complete WP-010 to add versioning, documentation, and contract tests.

### Risk Ownership
Platform engineering

### Monitoring & Alerts
Track API changes in release checklist; add CI contract tests.

### Review Cadence
With each API-affecting release.
