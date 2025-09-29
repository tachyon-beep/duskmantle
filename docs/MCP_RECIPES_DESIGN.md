# MCP Recipe Design

Phase 5 Step 5.1 captures the scope and execution plan for the “knowledge recipes” initiative. Recipes orchestrate repeatable workflows (ingest → validation → backup, etc.) purely through MCP tools so agents and operators can execute checklists without bespoke scripting.

## 1. Workflow Catalogue (Task 5.1.1)

| Recipe ID | Goal | Trigger | MCP Steps (draft) | Outputs |
|-----------|------|---------|-------------------|---------|
| `daily-health` | Confirm ingest freshness and coverage each morning. | Scheduler (0600) or manual call. | `km-ingest-status` → `km-coverage-summary` → `km-lifecycle-report` → `km-help {tool:"km-watch"}` for watcher hints. | Health JSON (status, deltas), Prometheus scrape hints, optional Slack summary. |
| `authoring-loop` | Capture new notes/files, re-ingest, validate search visibility. | Ad-hoc by maintainers. | `km-upload` or `km-storetext` (batched) → `km-ingest-trigger` (profile `manual`) → poll `km-ingest-status` until success → `km-search` sanity query. | Paths of new docs, ingest run id, verification snippet. |
| `stale-audit` | Identify stale design docs and isolated nodes for remediation. | Weekly (proposed). | `km-lifecycle-report --json` → optional `km-graph-subsystem` drill-down for affected subsystems → open GitHub issue via agent. | JSON list of stale docs, subsystems missing tests, next actions. |
| `release-prep` | Validate graph/search health and snapshot state prior to tagging. | Before release tag. | `km-ingest-trigger` (profile `release`) → `km-ingest-status` → `km-coverage-summary` → `km-search {query:"release checklist"}` → `km-backup-trigger`. | Structured checklist: ingest status, coverage numbers, search assurances, backup archive path, SHA list. |
| `post-restore-verify` | After restoring from backup, ensure environment is sane. | Disaster recovery drills. | `km-search` smoke queries → `km-graph-node` targeted doc → `km-coverage-summary` → `km-lifecycle-report`. | Report summarising restored data integrity. |
| `feedback-triage` | Review recent feedback and adjust weights. | Ops cadence (bi-weekly). | `km-help {tool:"km-feedback-submit", include_spec:true}` for schema hints → query telemetry (future `km-feedback-export`) → `km-search show-weights` (CLI) → note adjustments. | CSV/JSON of feedback, recommended weight adjustments. |

The first release will focus on `daily-health`, `stale-audit`, and `release-prep`, with others following once the harness exists.

## 2. Recipe Schema & Harness (Task 5.1.2)

### 2.1 Schema Snapshot

Recipes live as YAML (or JSON) documents under `recipes/`. Example skeleton:

```yaml
version: 1
name: release-prep
summary: Verify ingest health, lifecycle status, and capture a state backup.
variables:
  profile: release
  backup_tag: "$(date --utc +%Y%m%dT%H%M%SZ)"
steps:
  - id: trigger-ingest
    tool: km-ingest-trigger
    params:
      profile: "${profile}"
      dry_run: false
    expect:
      status: success
    capture: ingest_run
  - id: wait-for-ingest
    wait:
      poll:
        tool: km-ingest-status
        params:
          profile: "${profile}"
        until:
          path: status
          equals: ok
        interval_seconds: 10
        timeout_seconds: 600
  - id: coverage-summary
    tool: km-coverage-summary
    capture: coverage
  - id: lifecycle
    tool: km-lifecycle-report
    capture: lifecycle
  - id: smoke-search
    tool: km-search
    params:
      query: "release checklist"
      limit: 3
    assert:
      - path: results[0]
        exists: true
  - id: backup
    tool: km-backup-trigger
    params:
      tag: "${backup_tag}"
    capture: backup
outputs:
  ingest_run: "${steps.trigger-ingest.capture.run}"
  coverage: "${steps.coverage-summary.capture}"
  lifecycle: "${steps.lifecycle.capture}"
  backup_archive: "${steps.backup.capture.archive}"
```

Key fields:

- `version`: schema version for forward compatibility.
- `variables`: user-supplied values or expressions (later mapped to CLI `--var`).
- `steps`: ordered actions.
  - `tool`: MCP tool id; `wait` blocks evaluate polls without extra scripts.
  - `params`: JSON-like map sent verbatim to the tool.
  - `expect`: simple equality assertions on the returned payload.
  - `capture`: optional alias to stash full response or specific path (default entire object unless a `path` key is supplied).
  - `assert`: list of additional assertions (existence, equals, regex, numeric comparison); JSONPath-lite grammar.
  - `prompt`: optional human guidance string to surface in agent UI.
- `outputs`: summary values exported for downstream use (shell, Slack, GitHub issue template).

### 2.2 Execution Harness

Target artefact: `gateway-recipes` CLI (later mirrored by `bin/km-recipe-run` wrapper) and an MCP helper tool `km-recipe-run`. Design highlights:

1. **Executor backends**
   - **CLI mode** (default): spawn MCP server (if not already running) and drive recipes by issuing tool calls over stdio. Returns JSON transcript.
   - **MCP tool mode**: expose `km-recipe-run {"recipe":"release-prep","vars":{"profile":"prod"}}` so agents can orchestrate recipes without shell access. Tool reuses the same execution core.
2. **Engine responsibilities**
   - Load YAML, resolve variables/env, validate schema (jsonschema or pydantic model).
   - Serialize each step into `GatewayClient` calls (existing MCP client), capturing results and performing assertions.
   - Emit structured log for each step (start/end, latency, response snippet). Fail fast on assertion mismatch or tool failure.
   - Support `--dry-run` to print planned actions without invoking tools.
   - Provide `--output json|table` format options; JSON includes raw transcripts for audit.
3. **Extensibility hooks**
   - `plugins`: optional key for future enhancements (e.g., custom Python actions submitted by maintainers or direct HTTP calls).
   - `notifications`: optional block describing follow-up actions (Slack webhook, GitHub issue) — Phase 5.2 candidate.
   - `secrets`: reference environment-variable names; harness resolves them during execution.
4. **Storage conventions**
   - Recipes stored under `recipes/<name>.yaml` with README summarising available workflows.
   - Execution history appended to `KM_STATE_PATH/audit/recipes.log` (JSONL) capturing run id, recipe name, status, duration, captured outputs hash.
5. **Error semantics**
   - Distinguish `tool_failed`, `assert_failed`, `timeout`, `schema_invalid`.
   - Provide exit codes for CLI: `0` success, `2` assertion, `3` tool failure, `4` configuration error.

### 2.3 Testing & Validation Plan

- Unit tests for schema loader/validator (pydantic models) and step execution with mocked `GatewayClient`.
- Integration smoke test using a minimal recipe referencing `km-search` to ensure harness drives the MCP server.
- Lint recipes via CI (`gateway-recipes validate recipes/`).
- Extend MCP smoke marker (`pytest -m mcp_smoke`) with a “hello world” recipe execution once implementation lands.

### 2.4 Roadmap Alignment

- Step 5.2 (implementation) will: 
  1. Build the executor module under `gateway/recipes/` using the above schema.
  2. Provide baseline recipes (`daily-health`, `stale-audit`, `release-prep`).
  3. Add `km-recipe-run` MCP tool and CLI wrappers.
- Step 5.3 (optional UI) can consume the same YAML to render dashboards or HTML runbooks.

This design document satisfies Phase 5 Step 5.1 by cataloguing target workflows and defining the schema/execution harness that subsequent tasks will implement.
