# Acceptance Demo Snapshot (Per Release)

Capture these metrics immediately after running the acceptance playbook. Copy the latest values into release notes (CHANGELOG entry) and share with reviewers when requesting a tag.

## 1. Build & Image Details

- **Image tag:** `duskmantle/km:1.1.0`
- **Image ID:** _TBD_
- **Image size:** _TBD_
- **Build timestamp:** _TBD_
- **Build script output reference:** `scripts/build-image.sh duskmantle/km:1.1.0`
- **Checksums:**
  - Wheel `dist/release/duskmantle_knowledge_gateway-1.1.0-py3-none-any.whl` → _TBD_
  - Image tar `dist/duskmantle-km.tar` → _TBD_
  - Checksum manifests recorded in `dist/SHA256SUMS` and `dist/IMAGE_SHA256SUMS`

## 2. Ingestion Summary

| Field | Value |
| --- | --- |
| Ingest run ID | _TBD_ |
| Profile | `demo` |
| Started at (UTC) | _TBD_ |
| Duration (s) | _TBD_ |
| Total artifacts | _TBD_ |
| Total chunks | _TBD_ |
| Repo head (commit) | _TBD_ |
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
Pending acceptance run.
```

## 4. Coverage Snapshot

- **Endpoint status (`/api/v1/coverage`):** 200 OK
- **Chunk count:** _TBD_
- **Artifact total:** _TBD_
- **Missing artifacts:** _TBD_
- **Report path:** `/opt/knowledge/var/reports/coverage_report.json`

## 5. Backup Confirmation

- **Backup archive path:** _TBD_
- **Restore validation:** _TBD_

## 6. MCP Smoke Test

- **Adapter transport used:** _TBD_
- **Command executed:** _TBD_
- **Result:** _TBD_
- **Prometheus metrics observed:** _TBD_

## 7. Additional Notes

Record anything reviewers should know before sign-off (e.g., unusual warnings, config overrides, manual steps outside the playbook).

- Notes to capture after acceptance run.

---
> After filling this document, link the snapshot in the release notes and attach any referenced logs/artifacts.
