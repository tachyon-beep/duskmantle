# Upgrade & Rollback Guide

This document explains how to safely upgrade the Duskmantle knowledge gateway container (and revert if needed). Follow it alongside `RELEASE.md` when applying new versions.

## 1. Pre-Upgrade Checklist

1. **Review release notes / changelog.** Confirm schema changes, required env vars, and MCP updates.
2. **Check health:**

   ```bash
   curl http://localhost:8000/healthz | jq
   curl http://localhost:8000/metrics | grep km_ingest_last_run_status
   ```

   Ensure `status: ok` and no failing gauges.
3. **Create a backup:**

   ```bash
   bin/km-backup
   ls .duskmantle/backups/archives
   ```

   Copy the archive (`.duskmantle/backups/archives/km-backup-YYYYMMDDTHHMMSS.tgz`) to a safe location.
4. **Note current config:** record `KM_*` env vars, `.codex` MCP entries, and `bin/km-run` overrides.
5. **Capture the current acceptance snapshot:** run the quick checks from `docs/ACCEPTANCE_DEMO_PLAYBOOK.md` (at minimum `/healthz`, `/api/v1/coverage`, and a sample `/search`) and refresh `docs/ACCEPTANCE_DEMO_SNAPSHOT.md` so you know the pre-upgrade baseline.

## 2. Upgrade Procedure

1. **Stop the running container:**

   ```bash
   docker rm -f duskmantle
   ```

2. **Pull/build the new image:**

   ```bash
   docker pull duskmantle/km:<new-tag>
   # or
   scripts/build-image.sh duskmantle/km:<new-tag>
   ```

3. **Launch with existing data:**

   ```bash
   KM_IMAGE=duskmantle/km:<new-tag> \
   KM_NEO4J_DATABASE=neo4j \
   KM_ADMIN_TOKEN=<token> \
   bin/km-run --detach
   ```

   (Include any additional env vars used previously; authentication is enabled by default.) Secure mode refuses to start with default credentials—ensure `KM_ADMIN_TOKEN` and a non-default `KM_NEO4J_PASSWORD` are set before launch. Use `KM_ALLOW_INSECURE_BOOT=true` only for isolated demos.
4. **Run an ingest if required:**

   ```bash
   docker exec duskmantle gateway-ingest rebuild --profile production
   ```

5. **Validate:**
   - `/healthz` and `/readyz` respond with `status: ok`.
   - `/api/v1/coverage` reflects expected artifact/chunk totals.
   - `./infra/smoke-test.sh duskmantle/km:<new-tag>` completes without errors.
   - `KM_GATEWAY_URL=http://localhost:8000 pytest -m mcp_smoke --maxfail=1 --disable-warnings` passes.
   - Update `docs/ACCEPTANCE_DEMO_SNAPSHOT.md` with the new run details.

## 3. Rollback Procedure

1. **Stop the upgraded container:** `docker rm -f duskmantle`.
2. **Restore data:**

   ```bash
   rm -rf .duskmantle/config/*
   tar -xzf .duskmantle/backups/archives/km-backup-YYYYMMDDTHHMMSS.tgz -C .duskmantle/config
   ```

3. **Launch previous version:**

   ```bash
   KM_IMAGE=duskmantle/km:<old-tag> bin/km-run --detach
   ```

4. **Verify health and recent metrics** just like the upgrade validation (`/healthz`, `/api/v1/coverage`, smoke test, MCP smoke) and capture the rollback snapshot in `docs/ACCEPTANCE_DEMO_SNAPSHOT.md`.

## 4. Notes

- Keep at least two backup snapshots; prune older archives after verifying new versions.
- For schema changes, follow release notes: some versions may require `gateway-graph migrate` or manual config updates.
- MCP configs: update `.codex/config.toml` if command paths changed or new tools were introduced.
- Support is community-driven via GitHub Issues. When requesting help, attach the latest `docs/ACCEPTANCE_DEMO_SNAPSHOT.md`, `/healthz`, `/metrics`, key logs, and MCP smoke output.
