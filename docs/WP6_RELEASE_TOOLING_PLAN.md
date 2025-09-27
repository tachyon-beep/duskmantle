# Work Package 6 — Release Tooling & Documentation

## Phase Breakdown

### Phase A: Build & Packaging Automation
- **Step A1: Docker Build Pipeline**
  - Task A1.1 Create reusable build script (Makefile or `scripts/` entry) encapsulating build args, BuildKit flags, and version tagging **(Completed via `scripts/build-image.sh`)**.
  - Task A1.2 Add CI workflow to build the image on push/tag, fail on lints/tests, and produce artifacts **(Release workflow updated)**.
  - Task A1.3 Capture image metadata (size, layers) and store in CI logs to monitor growth **(Handled by build script logging)**.
- **Step A2: Artifact Signing & Checksums**
  - Task A2.1 Extend `scripts/checksums.sh` (or new script) to generate SHA256/TUF hashes for image tarballs and binaries **(SHA256 automation in place)**.
  - Task A2.2 Publish checksum files alongside artifacts and document verification commands **(Documented in README/RELEASE notes)**.

### Phase B: Operational Tooling
- **Step B1: Helper Scripts**
  - Task B1.1 Finalize `bin/km-run` (runtime launcher) with environment overrides and logging guidance **(Completed)**.
  - Task B1.2 Finalize `bin/km-backup` (state archive) with rotate/prune instructions **(Completed)**.
  - Task B1.3 Provide restore script or documented commands for unpacking archives back into `KM_STATE_PATH` **(Documented in `docs/QUICK_START.md`)**.
- **Step B2: Smoke & Regression Tests**
  - Task B2.1 Upgrade `infra/smoke-test.sh` to run ingest/coverage checks **(Completed)**.
  - Task B2.2 Wire smoke test into CI workflow post-build; fail the pipeline if ingest/coverage verification fails **(Completed via `release.yml`)**.

### Phase C: Documentation & Release Process
- **Step C1: Quick Start & Troubleshooting**
  - Task C1.1 Write quick-start guide covering prerequisites, `bin/km-run`, and sample ingest commands **(Completed: `docs/QUICK_START.md`)**.
  - Task C1.2 Expand troubleshooting appendix (auth errors, scheduler skips, tracing setup) referencing observability docs **(Updates to README & OBSERVABILITY_GUIDE)**.
- **Step C2: Release Checklist & Notes**
  - Task C2.1 Define release checklist (build, smoke test, backups, docs review) stored in repo (`RELEASE.md`) **(Checklist refreshed)**.
  - Task C2.2 Template CHANGELOG entries per release and note manual verification steps **(Unreleased heading maintained)**.
- **Step C3: Distribution Logistics**
  - Task C3.1 Document artifact hosting (registry URL, checksum location) and provide copy-paste commands **(README Release Artifacts section)**.
  - Task C3.2 If applicable, publish compressed tarball of the repo for air-gapped environments with instructions **(Documented usage via image tarball)**.

### Step D: Acceptance Demo (Phase 4.4)
- Task D1 Produce acceptance playbook covering build → ingest → search/graph → backup/restore → smoke test **(Completed: `docs/ACCEPTANCE_DEMO_PLAYBOOK.md`)**.
- Task D2 Capture demo outputs for release notes and update checklists before final tagging **(Completed: see `docs/ACCEPTANCE_DEMO_SNAPSHOT.md` and RELEASE step 4)**.
