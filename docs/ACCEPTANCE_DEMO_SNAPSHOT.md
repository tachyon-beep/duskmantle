# Acceptance Demo Snapshot (Per Release)

Capture these metrics immediately after running the acceptance playbook. Copy the latest values into release notes (CHANGELOG entry) and share with reviewers when requesting a tag.

## 1. Build & Image Details
- **Image tag:** `duskmantle/km:demo`
- **Image ID:** `sha256:50d5b28b00966c491b31ddbf9dc30f3437ec51679de879aaeac9883c0858e219`
- **Image size:** 8.85 GB (8848592467 bytes)
- **Build timestamp:** 2025-09-28T02:35:47.015537927+10:00
- **Build script output reference:** `scripts/build-image.sh duskmantle/km:demo`

## 2. Ingestion Summary
| Field | Value |
| --- | --- |
| Ingest run ID | `f001fef04dca46e288d8439793ef3fef` |
| Profile | `demo` |
| Started at (UTC) | 2025-09-27T16:41:45Z (log timestamp) |
| Duration (s) | 9.02 |
| Total artifacts | 46 |
| Total chunks | 365 |
| Repo head (commit) | `null` (git metadata unavailable in container) |
| Dummy embeddings? (`true`/`false`) | false |

If any warnings/errors appeared during ingestion, list them here:

```
INFO Ingestion completed (run_id=f001fef04dca46e288d8439793ef3fef, chunk_count=365)
```

## 3. Search & Graph Verification
| Check | Observed |
| --- | --- |
| `/search` sample result (artifact path + adjusted score) | `docs/ACCEPTANCE_DEMO_PLAYBOOK.md` @ 0.7545 |
| `/graph/subsystems/{name}` key relationships | 200 OK – `ReleaseTooling` returns three associated design docs |
| `/graph/nodes/{id}` relationships verified | 200 OK – `DesignDoc:docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md` links to chunk nodes |
| `/graph/search` snippet | 200 OK – `/graph/search?q=docs` lists DesignDoc nodes |

Paste the most illustrative JSON fragments (redact sensitive data as needed):

```
km-search -> {"chunk.artifact_path": "docs/ACCEPTANCE_DEMO_PLAYBOOK.md", "scoring.adjusted_score": 0.7545}
km-graph-node -> {"node.id": "DesignDoc:docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md", "relationships[0].type": "HAS_CHUNK"}
km-ingest-status -> {"run_id": "f001fef04dca46e288d8439793ef3fef", "profile": "demo", "artifact_count": 46, "chunk_count": 365}
km-coverage-summary -> {"artifact_total": 46, "chunk_count": 365}
km-backup-trigger -> archive `/opt/knowledge/var/backups/km-backup-20250927T164135.tgz`
```

## 4. Coverage Snapshot
- **Endpoint status (`/coverage`):** 200 OK
- **Chunk count:** 365
- **Artifact total:** 46 (`test`: 28, `doc`: 18)
- **Missing artifacts:** None
- **Report path:** `/opt/knowledge/var/reports/coverage_report.json`

## 5. Backup Confirmation
- **Backup archive path:** `/opt/knowledge/var/backups/km-backup-20250927T164135.tgz`
- **Restore validation:** Not yet performed (backup verified for presence only)

## 6. MCP Smoke Test
- **Adapter transport used:** `http` (`km-mcp` exec'd within container at `http://127.0.0.1:8822/mcp`)
- **Command executed:** `pytest -m mcp_smoke --maxfail=1 --disable-warnings`
- **Result:** Pass (`tests/mcp/test_server_tools.py::test_mcp_smoke_run`)
- **Prometheus metrics observed:** `/metrics` shows `km_mcp_requests_total{result="success",tool="km-search"}` and related counters after the smoke run

## 7. Additional Notes
Record anything reviewers should know before sign-off (e.g., unusual warnings, config overrides, manual steps outside the playbook).
- Export `KM_NEO4J_DATABASE=knowledge` when launching the container or running ingestion/graph CLI commands; this keeps API and MCP graph queries aligned with the dataset.
- Use `./bin/km-mcp-container` in your Codex configuration when you want to run the MCP server inside the container (ensures `/workspace/repo` and backup helpers are available).

---
> After filling this document, link the snapshot in the release notes and attach any referenced logs/artifacts.
