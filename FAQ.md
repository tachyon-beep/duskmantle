# FAQ

### How is support provided?
Support is community-driven via GitHub Issues. For bugs, fill out `.github/ISSUE_TEMPLATE/bug_report.md` with `/healthz`, `/metrics`, and MCP smoke output. Feature requests follow `.github/ISSUE_TEMPLATE/feature_request.md`.

### How do I upgrade safely?
See `docs/UPGRADE_ROLLBACK.md` for the full checklist (backup, stop container, pull new image, relaunch with `KM_NEO4J_DATABASE=knowledge`, validate). Quick Start §11 gives a summary.

### Where are release artifacts?
Container images are published to Docker Hub (`duskmantle/km:<tag>`). Wheels/tarballs and checksums land in GitHub Releases per `RELEASE.md`.

### How do I run MCP tools?
Follow `docs/MCP_INTEGRATION.md` or Quick Start §10. Use `./bin/km-mcp` locally or `./bin/km-mcp-container` inside the container context.

### How do I file issues responsibly?
Search existing issues first. Include version/tag, environment details, `/healthz`, relevant metrics, logs, and MCP smoke output. Attach your acceptance snapshot when relevant.

### What’s the roadmap for hybrid search?
Hybrid dense/lexical fusion, HNSW parameter tuning, and query weighting controls are tracked in `docs/HYBRID_SEARCH_TODO.md` and the implementation plan. Contributions welcome.

### Can I contribute?
Yes. Open PRs with tests, docs, and the PR template. For larger changes, discuss via issues first.

### Licensing?
MIT License. Reuse with attribution; no warranty.

### Who maintains this?
Community contributors. Response times are best-effort; monitor RELEASE.md and changelog for updates.
