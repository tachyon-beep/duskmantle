# Acceptance Demo Snapshot (Per Release)

Capture these metrics immediately after running the acceptance playbook. Copy the latest values into release notes (CHANGELOG entry) and share with reviewers when requesting a tag.

## 1. Build & Image Details

- **Image tag:** `duskmantle/km:1.0.0`
- **Image ID:** `sha256:04f92b929e8d83fca6624c25760320ef7c5650804fb40d05fcd5fffd5b690d8d`
- **Image size:** 8.85 GB (8848665564 bytes)
- **Build timestamp:** 2025-09-28T10:15:43.75353824+10:00
- **Build script output reference:** `scripts/build-image.sh duskmantle/km:1.0.0`
- **Checksums:**
  - Wheel `dist/release/duskmantle_knowledge_gateway-1.0.0-py3-none-any.whl` → `c123678b58ee17b83b51291bf531517bda34023d7ca7510660ff1d4508e9a724`
  - Image tar `dist/duskmantle-km.tar` → `461bae860041818d38e14d525a6741fa80e5d950c6cdee65cbb2edbc52d772ef`
  - Checksum manifests recorded in `dist/SHA256SUMS` and `dist/IMAGE_SHA256SUMS`

## 2. Ingestion Summary

| Field | Value |
| --- | --- |
| Ingest run ID | `c821eb34956345bc8ef7cb3765b4ab63` |
| Profile | `demo` |
| Started at (UTC) | 2025-09-27T23:18:35.810Z |
| Duration (s) | 19.14 |
| Total artifacts | 49 (`test`: 28, `doc`: 21) |
| Total chunks | 386 |
| Repo head (commit) | `null` (git metadata unavailable inside container) |
| Dummy embeddings? (`true`/`false`) | false |

If any warnings/errors appeared during ingestion, list them here:

```
INFO Ingestion run completed (profile=demo, run_id=c821eb34956345bc8ef7cb3765b4ab63, chunk_count=386)
```

## 3. Search & Graph Verification

| Check | Observed |
| --- | --- |
| `/search` sample result (artifact path + adjusted score) | `docs/archive/WORK_PACKAGES.md` @ 0.9726 |
| `/graph/subsystems/{name}` key relationships | 200 OK – `ReleaseTooling` returns 3 associated design docs |
| `/graph/nodes/{id}` relationships verified | 200 OK – `DesignDoc:docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md` links to chunk nodes |
| `/graph/search` snippet | 200 OK – `q=Release` returns subsystem + design doc hits |

Paste the most illustrative JSON fragments (redact sensitive data as needed):

```
km-search -> {"chunk.artifact_path": "docs/archive/WORK_PACKAGES.md", "scoring.adjusted_score": 0.9726}
km-search metadata -> {"hybrid_weights": {"vector": 1.0, "lexical": 0.25}, "hnsw_ef_search": 128}
km-graph-node -> {"node.id": "DesignDoc:docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md", "relationships[0].type": "HAS_CHUNK"}
km-graph-subsystem -> {"subsystem.properties.name": "ReleaseTooling", "artifacts|len": 3}
km-graph-search -> {"results[0].id": "Subsystem:ReleaseTooling", "results[0].score": 0.95}
 gateway-ingest audit-history -> {"run_id": "c821eb34956345bc8ef7cb3765b4ab63", "chunk_count": 386}
```

## 4. Coverage Snapshot

- **Endpoint status (`/coverage`):** 200 OK
- **Chunk count:** 386
- **Artifact total:** 49 (`test`: 28, `doc`: 21)
- **Missing artifacts:** None
- **Report path:** `/opt/knowledge/var/reports/coverage_report.json`

## 5. Backup Confirmation

- **Backup archive path:** `backups/km-backup-20250927T231955.tgz`
- **Restore validation:** Not yet performed (archive verified for presence only)

## 6. MCP Smoke Test

- **Adapter transport used:** `stdio` (local CLI launch `gateway-mcp --transport stdio`)
- **Command executed:** `KM_GATEWAY_URL=http://localhost:8000 pytest -m mcp_smoke --maxfail=1 --disable-warnings`
- **Result:** Pass (`tests/mcp/test_server_tools.py::test_mcp_smoke_run`)
- **Prometheus metrics observed:** `/metrics` exposes `km_mcp_requests_total`/`km_mcp_request_seconds`; counters increment when tools run during the smoke slice.

## 7. Additional Notes

Record anything reviewers should know before sign-off (e.g., unusual warnings, config overrides, manual steps outside the playbook).

- Container launched with `KM_NEO4J_DATABASE=knowledge` to avoid `DatabaseNotFound` errors during ingest.
- MCP smoke ran locally against the running container; run the same slice with maintainer tokens in secured environments.
- Backup archive captured but restore drill postponed—schedule one before final tag if time permits.

---
> After filling this document, link the snapshot in the release notes and attach any referenced logs/artifacts.
