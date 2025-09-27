# WP6 Release Tooling & Documentation Plan

Duskmantle ships as a turnkey container plus Python project. WP6 focuses on providing a reliable release process so operators can reproduce artifacts, verify integrity, and understand changes between versions.

## Goals
1. **Deterministic Builds:** Document commands and scripts that generate the Docker image and Python wheel/sdist with fixed versions.
2. **Artifact Verification:** Produce checksums/signatures for release bundles.
3. **Release Notes & Changelog:** Automate changelog drafting from Conventional Commit history and provide a release-notes template.
4. **Operator Documentation:** Offer a RELEASE.md playbook covering build, test, tag, and publish steps.

## Deliverables (Proposed Milestones)

### Milestone 1 — Baseline Scripts
- `scripts/build-wheel.sh`: create wheel/sdist into `dist/` with reproducible flags.
- `scripts/build-image.sh`: wrap `docker build` with pinned build args and logging.
- `scripts/checksums.sh`: compute SHA256 hashes for `dist/*` and the container image tarball (`docker save`).
- Add `make release` task chaining: lint → tests → wheel → image → checksums.
- Document in `RELEASE.md` ( new file ) the manual release flow.

### Milestone 2 — Changelog Automation
- Add `scripts/generate-changelog.py` using git + Conventional Commits to assemble markdown by category.
- Maintain `CHANGELOG.md` with “Unreleased” and versioned sections.
- Extend pipeline to update changelog during `make release` (with manual review step).

### Milestone 3 — CI Packaging & Publishing
- GitHub Actions workflow (placeholder `.github/workflows/release.yml`) to:
  1. Build wheel & container on tags.
  2. Run `scripts/checksums.sh`.
  3. Attach assets to the GH release (or publish to registry if configured later).
- Smoke test built artifacts (run container, execute `gateway-ingest` dry run).
- Publish release notes using generated markdown.

### Milestone 4 — Extended Docs & Troubleshooting
- Expand `RELEASE.md` with common issues (e.g., docker login, version bump conflicts).
- Add section to `docs/OBSERVABILITY_GUIDE.md` summarising release validation signals (critical metrics to watch post-release).
- Ensure `README.md` references release process and changelog link.

## Immediate Next Steps (Sprint Scope)
1. **Create scripts skeletons** for build/checksum with unit-ish tests verifying expected output files.
2. **Add RELEASE.md** with detailed manual steps and explanation of new scripts.
3. **Draft CHANGELOG.md** with placeholder “Unreleased” section and note that releases will follow Semantic Versioning.

## Dependencies & Considerations
- Requires Docker and build toolchain available in CI environment.
- For checksum generation, rely on `sha256sum` (available in Debian base image); fallback to Python script if portability needed.
- Ensure that the repository version (e.g., `pyproject.toml`) is in sync with git tags; might adopt bumpversion or Poetry version tasks later.

## Open Questions
- Registry destinations: are we publishing to Docker Hub, GHCR, or an internal registry? For now, scripts log `docker tag` commands without pushing.
- Signing strategy: should we generate cosign signatures? Defer until requirements clarified.
- Release cadence: assume manual release triggered by maintainers after WPs complete.

## Remaining Tasks & Estimates

| Task | Description | Estimate | Dependencies |
|------|-------------|----------|--------------|
| CI packaging workflow | Add `.github/workflows/release.yml` to build wheel/image, run smoke tests, and upload artifacts on tag pushes. | 1.5 days | Milestone 1 scripts, GitHub secrets for registry (optional). |
| Automated changelog update | Extend `scripts/generate-changelog.py` to parse Conventional Commits and update `CHANGELOG.md` during release; integrate into `make release`. | 1 day | Changelog skeleton; git tag naming convention. |
| Docker image signing | Evaluate cosign or similar to sign `duskmantle/km` images; document verification steps. | 1 day (optional) | Decision on signing tool, registry access. |
| Release smoke automation | Enhance `infra/smoke-test.sh` to accept build artifacts and run post-build checks in CI. | 0.5 day | Existing smoke script. |
| Documentation polish | Expand `RELEASE.md` with troubleshooting, add release section to `README.md`, link metrics to observe during rollout. | 0.5 day | Feedback from initial release dry run. |

> Estimations assume a single engineer familiar with the repository and available tooling. Adjust as new requirements emerge.
