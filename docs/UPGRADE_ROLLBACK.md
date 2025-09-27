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
   ls backups
   ```
   Copy the archive (`backups/km-backup-YYYYMMDDTHHMMSS.tgz`) to a safe location.
4. **Note current config:** record `KM_*` env vars, `.codex` MCP entries, and `bin/km-run` overrides.

## 2. Upgrade Procedure
1. **Stop the running container:**
   ```bash
   docker rm -f km-gateway
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
   KM_NEO4J_DATABASE=knowledge \
   KM_AUTH_ENABLED=true \
   KM_ADMIN_TOKEN=<token> \
   bin/km-run --detach
   ```
   (Include any additional env vars used previously.)
4. **Run an ingest if required:**
   ```bash
   docker exec km-gateway gateway-ingest rebuild --profile production
   ```
5. **Validate:** re-run `/healthz`, `/coverage`, smoke test (`./infra/smoke-test.sh duskmantle/km:<new-tag>`), and MCP smoke (`pytest -m mcp_smoke`).

## 3. Rollback Procedure
1. **Stop the upgraded container:** `docker rm -f km-gateway`.
2. **Restore data:**
   ```bash
   rm -rf data/*
   tar -xzf backups/km-backup-YYYYMMDDTHHMMSS.tgz -C data
   ```
3. **Launch previous version:**
   ```bash
   KM_IMAGE=duskmantle/km:<old-tag> bin/km-run --detach
   ```
4. **Verify health and recent metrics** as in the upgrade step.

## 4. Notes
- Keep at least two backup snapshots; prune older archives after verifying new versions.
- For schema changes, follow release notes: some versions may require `gateway-graph migrate` or manual config updates.
- MCP configs: update `.codex/config.toml` if command paths changed.
- Support is community-driven via GitHub Issues (MIT-licensed). Include `/healthz`, logs, and MCP smoke output when filing bugs.
