# Acceptance Demo Snapshot (Per Release)

Capture these metrics immediately after running the acceptance playbook. Copy the latest values into release notes (CHANGELOG entry) and share with reviewers when requesting a tag.

## 1. Build & Image Details
- **Image tag:** `duskmantle/km:demo`
- **Image ID:** `sha256:431882b7826ed710774e38ec5ae01dfa32beedbd790c8cdaabbb5846d3b1dfc6`
- **Image size:** 8.85 GB (8848540314 bytes)
- **Build timestamp:** 2025-09-27T23:52:22.086853816+10:00
- **Build script output reference:** `scripts/build-image.sh duskmantle/km:demo`

## 2. Ingestion Summary
| Field | Value |
| --- | --- |
| Ingest run ID | `0bb9321bf56e427aaa1d60e23d8b571f` |
| Profile | `demo` |
| Started at (UTC) | 2025-09-27T13:52:56.871921Z |
| Duration (s) | 19.11 |
| Total artifacts | 45 |
| Total chunks | 355 |
| Repo head (commit) | `null` (git metadata unavailable in container) |
| Dummy embeddings? (`true`/`false`) | false |

If any warnings/errors appeared during ingestion, list them here:

```
INFO Ingestion completed (run_id=0bb9321bf56e427aaa1d60e23d8b571f, chunk_count=355)
```

## 3. Search & Graph Verification
| Check | Observed |
| --- | --- |
| `/search` sample result (artifact path + adjusted score) | `docs/WORK_PACKAGES.md` @ 0.4726 |
| `/graph/subsystems/{name}` key relationships | **Blocked** – no `Subsystem` nodes present; endpoint returns 404 |
| `/graph/nodes/{id}` relationships verified | **Blocked** – `km-graph-node` returned 404 for `DesignDoc:docs/WORK_PACKAGES.md` |
| `/graph/search` snippet | **Failed** – `/graph/search?q=docs` returned 500 (missing subsystem metadata) |

Paste the most illustrative JSON fragments (redact sensitive data as needed):

```
km-search -> {"chunk.artifact_path": "docs/WORK_PACKAGES.md", "scoring.adjusted_score": 0.4726}
km-ingest-status -> {"run_id": "0bb9321bf56e427aaa1d60e23d8b571f", "profile": "demo", "artifact_count": 45, "chunk_count": 355}
km-coverage-summary -> {"artifact_total": 45, "chunk_count": 355}
km-backup-trigger -> executed via container (`/workspace/repo/bin/km-backup`, archive `/opt/knowledge/var/backups/km-backup-20250927T135810.tgz`)
```

## 4. Coverage Snapshot
- **Endpoint status (`/coverage`):** 200 OK
- **Chunk count:** 355
- **Artifact total:** 45 (`test`: 28, `doc`: 17)
- **Missing artifacts:** None
- **Report path:** `/opt/knowledge/var/reports/coverage_report.json`

## 5. Backup Confirmation
- **Backup archive path:** `/opt/knowledge/var/backups/km-backup-20250927T135810.tgz`
- **Restore validation:** Not yet performed (backup verified for presence only)

## 6. MCP Smoke Test
- **Adapter transport used:** `http` (FastMCP HTTP transport at `http://127.0.0.1:8822/mcp`)
- **Command executed:** `pytest -m mcp_smoke --maxfail=1 --disable-warnings`
- **Result:** Pass (`tests/mcp/test_server_tools.py::test_mcp_smoke_run`)
- **Prometheus metrics observed:** Host adapter increments counters; gateway `/metrics` currently shows metric definitions only (shared registry TBD)

## 7. Additional Notes
Record anything reviewers should know before sign-off (e.g., unusual warnings, config overrides, manual steps outside the playbook).
- Graph endpoints currently return 404/500 because the demo dataset produces no `Subsystem` nodes. Needs investigation before release.
- `km-backup-trigger` fails when the adapter runs on the host; execute `/workspace/repo/bin/km-backup` inside the container with `KM_BACKUP_SOURCE=/opt/knowledge/var`.

---
> After filling this document, link the snapshot in the release notes and attach any referenced logs/artifacts.
