# Release Playbook

This checklist produces a reproducible wheel, Docker image, and checksum manifest for Duskmantle. Complete these steps from a clean `main` branch.

## 1. Prepare

1. Ensure the working tree is clean: `git status`.
2. Run the full test suite: `.venv/bin/pytest`.
3. Update `pyproject.toml` version and add release notes to `CHANGELOG.md` under a new heading (e.g., `## 1.1.0 - 2025-10-01`).

## 2. Build Artifacts

```bash
# build Python wheel into dist/release
scripts/build-wheel.sh dist/release

# optionally build a source distribution
python -m pip install build
python -m build --sdist --outdir dist/release

# build container image (tag manually as needed)
scripts/build-image.sh duskmantle/km:1.1.0
```

## 3. Generate Checksums

```bash
scripts/checksums.sh dist/release dist/SHA256SUMS
# For container image tarball (optional)
docker save duskmantle/km:1.1.0 -o dist/duskmantle-km.tar
scripts/checksums.sh dist dist/IMAGE_SHA256SUMS
```

## 4. Verify

- Inspect the checksum files and ensure they reference the expected artifacts.
- Run a smoke test with the new wheel and container (e.g., `pip install dist/release/*.whl`, `./infra/smoke-test.sh duskmantle/km:1.1.0`). The script triggers a smoke ingest and validates `/coverage`.
- Capture acceptance demo outputs by completing `docs/ACCEPTANCE_DEMO_SNAPSHOT.md` (image metadata, ingest stats, API excerpts, backup confirmation, MCP smoke result). Attach or link this snapshot in the release notes draft.

## 5. Tag & Publish

1. Commit changelog/version updates: `git commit -am "chore(release): 1.1.0"`.
2. Create an annotated tag: `git tag -a v1.1.0 -m "Duskmantle 1.1.0"`.
3. Push changes and tag: `git push origin main --tags`.
4. (Optional) Attach wheel, sdist, container tar (if created), and checksum files to the GitHub release. Use the changelog entry as release notes.

## 6. Post-Release

- Update `CHANGELOG.md` with a fresh `## Unreleased` section.
- Monitor production metrics (`km_ingest_last_run_status`, `uvicorn_requests_total`) for anomalies.
- Rotate access tokens if required by your security policy.

> Tip: the GitHub Actions workflow `release.yml` automates build/test/smoke on tagged pushes and drafts a release with artifacts. See `docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md` for the long-term roadmap.
