# FAQ

### How is support provided?

Support is community-driven and limited to GitHub Issues—no email, chat, or commercial channels exist. Use the bug/feature templates in `.github/ISSUE_TEMPLATE/` after searching for similar reports. Include `/healthz`, relevant `/metrics`, MCP smoke output, logs, and (when possible) your latest `docs/ACCEPTANCE_DEMO_SNAPSHOT.md` so maintainers can reproduce quickly.

### How do I upgrade safely?

See `docs/UPGRADE_ROLLBACK.md` for the full checklist (back up `.duskmantle/`, stop the compose stack, pull new images, relaunch, validate). Quick Start §11 gives a summary.

### Where are release artifacts?

Container images are published to Docker Hub (`duskmantle/km:<tag>` for the API) and ghcr for signed tags. Wheels/tarballs and checksums land in GitHub Releases per `RELEASE.md`.

### Where do I put files for ingestion?

`bin/km-run` creates a compose directory under `.duskmantle/compose` and mounts `.duskmantle/data` to `/workspace/repo` inside the gateway container. Drop or symlink the repository you want indexed into that directory before triggering `gateway-ingest`. Persistent state lives under `.duskmantle/compose/config/{gateway,neo4j,qdrant}`.

### Is there a one-command bootstrap?

Yes. Run `bin/km-bootstrap`. It pulls `ghcr.io/tachyon-beep/duskmantle-km:latest`, fetches the matching Qdrant/Neo4j images, lays down `.duskmantle/{config,data,backups,compose}`, generates random reader/maintainer tokens plus a Neo4j password, writes them to `.duskmantle/secrets.env`, and launches the compose stack via `bin/km-run`.

### Can the system auto-ingest when files change?

Yes. Start `bin/km-watch` on the host (it hashes `.duskmantle/data` and calls `gateway-ingest` via `docker compose exec`). In-container watchers were removed as part of the hardening work, so keep automation outside the gateway container. Configure cadence via `KM_WATCH_INTERVAL`, profile via `KM_WATCH_PROFILE`, and metrics exposure via `--metrics-port` (defaults to `9103`). Set `KM_WATCH_USE_DUMMY=false` to use live embeddings.

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

John Morrissey (<john@foundryside.dev>). Response times are best-effort; monitor `RELEASE.md` and the changelog for updates.
