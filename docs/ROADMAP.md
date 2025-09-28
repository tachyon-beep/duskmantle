# Roadmap

This roadmap captures future enhancements aimed at making the knowledge gateway friendlier for MCP-driven workflows. Items are grouped from high to low priority, balancing expected impact (utility for LLM agents and maintainers) against implementation effort. “Quick win” tags highlight relatively low-effort tasks that deliver outsized value.

## Work Package: MCP Content Capture (High Priority, Quick Wins)

A single work package covers both file and text-based content ingestion via MCP.

### Tasks

1. **Shared Utilities**
   - Extract reusable file-copy and slug-generation helpers from `bin/km-sweep` into a Python module (`gateway/mcp/utils/files.py`).
   - Add settings entries for content root, default doc directory, and ingest defaults.
   - Instrument telemetry counters for write-oriented tools (`km_mcp_upload_total`, etc.).

2. **km-upload Tool**
   - Implement handler (`gateway/mcp/upload.py`) that validates source paths, copies into `.duskmantle/data/`, and optionally triggers ingest.
   - Support controls: `destination`, `overwrite`, `ingest`, `metadata` map.
   - Return structured result (`stored_path`, `ingest_triggered`, `ingest_run_id`, `next_steps`).
   - Unit tests: success copy, overwrite prevention, missing files, ingest invocation.

3. **km-storetext Tool**
   - Implement handler (`gateway/mcp/storetext.py`) that writes arbitrary text into `.duskmantle/data/docs/` (or destination) using generated filenames.
   - Support optional `title`, `subsystem`, `tags`, `format`, `metadata`, `ingest`.
   - Ensure metadata is captured (front matter or sidecar JSON) and collisions resolved.
   - Unit tests: slug generation, metadata persistence, empty content guard, ingest flow.

4. **Integration & Docs**
   - Register new tools in the MCP server and update FastAPI dependency injection as needed.
   - Update `docs/MCP_INTERFACE_SPEC.md`, `docs/MCP_RECIPES.md`, README “LLM Agent Workflow,” and `docs/MCP_AGENT_PLAYBOOK.md` (new).
   - Add roadmap note, acceptance demo examples, and release checklist reminders.

5. **Security & Audit**
   - Require maintainer token for both tools; emit scope errors otherwise.
   - Optionally append entries to an audit log (`/opt/knowledge/var/audit/mcp_actions.log`).

## Medium Priority

- **km-bundle** – ...
[retain remaining roadmap sections unchanged]

## Work Package: MCP Upload & StoreText Execution Plan

### Phase 1 – Foundations & Utilities
- **Step 1.1 Shared Helper Extraction**
  - Task 1.1.1 Refactor `bin/km-sweep` logic into `gateway/mcp/utils/files.py` (copy routines, slug generator, extension allowlist).
  - Task 1.1.2 Add new settings (content root, default doc folder, ingest defaults) and ensure MCP uses them.
  - Task 1.1.3 Instrument Prometheus counters (`km_mcp_upload_total`, `km_mcp_storetext_total`, result labels).
  - *Risk reduction:* write unit tests for the helper module to guard against path traversal and duplicate filename issues.

### Phase 2 – km-upload Tool
- **Step 2.1 Core Handler**
  - Task 2.1.1 Implement handler (`gateway/mcp/upload.py`) with validation, copy, ingest trigger hook.
  - Task 2.1.2 Extend MCP server registry and update tool schema/spec.
  - Task 2.1.3 Cover tests: valid copy, overwrite error, missing file, ingest trigger path, permission errors.
  - *Risk reduction:* add quarantine option or dry-run flag to preview actions; log audit entry.

### Phase 3 – km-storetext Tool
- **Step 3.1 Text Capture**
  - Task 3.1.1 Implement handler (`gateway/mcp/storetext.py`) to write text files, apply metadata, and optionally ingest.
  - Task 3.1.2 Support metadata serialization (front matter or sidecar) and slug collision handling.
  - Task 3.1.3 Tests: empty content rejection, metadata persistence, ingest success/failure handling.
  - *Risk reduction:* guard against excessive payload size, enforce UTF-8 encoding, add basic sanitizer if HTML allowed.

### Phase 4 – Integration & Documentation
- **Step 4.1 Tool Wiring**
  - Task 4.1.1 Register tools with MCP server, update FastAPI dependency injection if needed.
  - Task 4.1.2 Update CLI (optional) to expose similar functionality for parity.
- **Step 4.2 Documentation & Samples**
  - Task 4.2.1 Update `docs/MCP_INTERFACE_SPEC.md` & `docs/MCP_RECIPES.md` with request/response schemas and examples.
  - Task 4.2.2 Extend README + `docs/MCP_AGENT_PLAYBOOK.md` (new) with step-by-step agent flows.
  - Task 4.2.3 Add bundle examples to `docs/ACCEPTANCE_DEMO_PLAYBOOK.md` once available.
  - *Risk reduction:* prepare manual validation checklist (upload text, run ingest, confirm `/search` hit) before merging.

### Phase 5 – Security & Operational Hardening
- **Step 5.1 Auth & Audit**
  - Task 5.1.1 Ensure maintainer scope enforced; add explicit error messages for reader tokens.
  - Task 5.1.2 Append optional audit entries (`mcp_upload`, `mcp_storetext`) with caller/tool metadata.
- **Step 5.2 Failure Handling**
  - Task 5.2.1 Define retry/backoff behaviour for ingest triggers; surface actionable errors to MCP clients.
  - Task 5.2.2 Document operational impacts (e.g., storage growth, ingest throughput) and update runbook.
  - *Risk reduction:* include targeted tests for race conditions (simultaneous uploads) and watch metrics to ensure triggers don’t overload scheduler.

### Overall Risks & Mitigations
- **Path Traversal / Overwrite** – unit tests + helper utilities ensure normalized paths and require explicit `overwrite=true`.
- **Unauthorized Writes** – maintainer-token enforcement, clear error messages, audit logging.
- **Ingest Overload** – optional ingest flag defaults to `false`, plus backoff/retry guidance and watcher metric monitoring.
- **Large Payloads** – configurable max file size for uploads/storetext; document limits to the agent.
- **Consistency with Existing Tools** – shared helper module keeps CLI and MCP behaviour aligned; add regression tests that exercise both code paths.

