# Knowledge Management Risk Mitigation Plan

This document tracks the key delivery risks for the turnkey knowledge management container and the concrete mitigation activities approved to address them. Items marked **Open** require follow-up when new data becomes available; others have actionable tasks that can begin immediately.

## 1. Container Image Size

- **Risk:** Bundling embedding models, Qdrant, and Neo4j may inflate the image, slowing downloads and adoption.
- **Status:** Mitigation planned.
- **Approved Actions:**
  - Use multi-stage Docker builds with separate builder/runtime stages and aggressive layer pruning.
  - Vendor `sentence-transformers/all-MiniLM-L6-v2` via `pip install --no-cache-dir` in the runtime stage only; confirm model weights are stored under `/opt/knowledge/models` for easy compression.
  - Add CI job to compute image size after each build and fail if it exceeds the documented budget (target <3.5 GB compressed).
- **Open Questions:** Whether further model quantization is acceptable for target users (requires accuracy validation). Documented as TBD.

## 2. Persistence Safety

- **Risk:** Misconfigured host volume could lead to data loss during upgrades.
- **Status:** Mitigation defined.
- **Approved Actions:**
  - Implement startup guard in the entrypoint script that checks `/opt/knowledge/var` is writable and not an in-container tmpfs before launching services.
  - Provide `bin/km-backup` and `bin/km-restore` scripts (tar-based) referenced in the implementation plan.
  - Document explicit `docker run` examples in README that mount a host path and explain upgrade backups.
- **Status Update:** Entry-point guard implemented via `infra/docker-entrypoint.sh`; backup tooling still pending.
- **Open Questions:** None at this time.

## 3. Resource Contention

- **Risk:** Co-located services may compete for CPU/RAM, degrading performance.
- **Status:** Partial mitigation available.
- **Approved Actions:**
  - Author `infra/resource_profiles.md` describing baseline host requirements (initial guidance: 4 vCPU / 8 GB RAM) and tunable env vars (`KM_QDRANT_MEMORY_LIMIT`, `KM_NEO4J_HEAP_SIZE`).
  - Include smoke test that runs ingestion on sample repo and records resource usage for future tuning.
  - Provide instructions for optional GPU enablement when available.
- **Open Questions:** Final recommended hardware profile pending real benchmarks.

## 4. Classification Accuracy

- **Risk:** Path-based heuristics may mis-tag subsystems or Leyline assets.
- **Status:** Mitigation actionable.
- **Approved Actions:**
  - Create regression fixture set under `tests/data/classification/` mirroring expected repository layouts.
  - Implement confidence scoring in classification module and emit warnings when below threshold.
  - Allow override map via mounted YAML (e.g., `/opt/knowledge/config/custom_subsystems.yaml`).
- **Open Questions:** Need real repository samples to calibrate regex coverage (leave TBD until repos are available).

## 5. Authentication Defaults

- **Risk:** Users might expose the API without securing tokens.
- **Status:** Mitigation actionable.
- **Approved Actions:**
  - Ship the container with auth enabled by default; require explicit `KM_AUTH_MODE=insecure` to disable.
  - Log a prominent warning on startup when auth is disabled and port binding is non-localhost.
  - Document token rotation procedure and example reverse proxy config for TLS termination.
- **Open Questions:** None.

## 6. Host Compatibility & Support

- **Risk:** Users may struggle with Docker flags, GPU drivers, or unsupported OS versions.
- **Status:** Mitigation defined.
- **Approved Actions:**
  - Maintain compatibility matrix covering tested Docker versions and host OSes.
  - Provide troubleshooting appendix (`docs/TROUBLESHOOTING.md`) outlining common errors and fixes (e.g., volume permissions, SELinux contexts).
  - Offer CPU-only fallback instructions, including environment variables to disable GPU detection.
- **Open Questions:** Actual test matrix values pending hands-on validation.

## 7. Observability Coverage

- **Risk:** Ingestion issues might go unnoticed without robust observability.
- **Status:** Mitigation actionable.
- **Approved Actions:**
- Expose `/metrics` with Prometheus counters and histograms; bundle default alert thresholds in documentation.
- Log end-of-run summaries with processed file counts and failure indicators; ensure logs route to stdout.
- Publish and maintain an operator-focused observability guide (`docs/OBSERVABILITY_GUIDE.md`) covering alerts, tracing, and troubleshooting steps.
- Include optional `KM_ALERT_WEBHOOK` integration placeholder (left unimplemented until requirements clarified).
- **Open Questions:** Choice of alerting integrations for specific users remains TBD.

## 8. Release Distribution Integrity

- **Risk:** Users may deploy corrupted images or mismatch versions.
- **Status:** Mitigation actionable.
- **Approved Actions:**
  - Generate SHA256 checksums for image tarballs and publish alongside releases.
  - Document verification commands (`sha256sum duskmantle-km-vX.tar.gz`) in the quick-start guide.
  - Maintain CHANGELOG entries summarizing risk-affecting updates.
- **Open Questions:** Whether signed container images (e.g., cosign) are required is TBD pending user feedback.

---
This plan will be updated after each implementation phase review. Open items require explicit confirmation from stakeholders once real-world data is available.
