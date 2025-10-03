# Operations Playbook

This guide captures the day-to-day operational tasks for the knowledge gateway: how to run stateful backups, perform restores, and verify automation.

## Automated Backups

Scheduled backups are controlled via the `KM_BACKUP_*` environment variables.

| Variable | Default | Purpose |
|----------|---------|---------|
| `KM_BACKUP_ENABLED` | `false` | Enable scheduled backup jobs. |
| `KM_BACKUP_INTERVAL_MINUTES` | `720` | Interval cadence (in minutes) when a cron expression is not supplied. |
| `KM_BACKUP_CRON` | _unset_ | Cron expression (UTC); takes precedence over the interval. |
| `KM_BACKUP_RETENTION_LIMIT` | `7` | Number of most recent archives preserved under the destination path. |
| `KM_BACKUP_DEST_PATH` | `${KM_STATE_PATH}/backups/archives` | Directory receiving managed backup archives. |
| `KM_BACKUP_SCRIPT` | `<repo>/bin/km-backup` | Override path to the helper script executed by the scheduler/MCP tool. |

When enabled, the scheduler executes the backup script, writes archives into the destination directory, updates Prometheus metrics (`km_backup_runs_total`, `km_backup_last_status`, `km_backup_last_success_timestamp`, `km_backup_retention_deletes_total`), and trims older `km-backup-*.tgz` archives once the retention limit is exceeded. Files that do not match this naming scheme are ignored. `/healthz` exposes a `backup` check with the most recent status.

## Manual Backup Invocation

You can still launch an on-demand backup using the MCP tool or directly via the helper script:

```bash
# Using the MCP CLI
python -m gateway.mcp.cli backup

# Manual execution (inside the container)
KM_BACKUP_SOURCE=${KM_STATE_PATH} \
KM_BACKUP_DEST=${KM_STATE_PATH}/backups/archives \
    bin/km-backup
```

The helper prints the archive path (`Backup written to ...`). Scheduled runs use the same script, so customisations applied here apply globally.

## Restore Procedure

1. Stop the gateway services to avoid writes during the restore.
2. Copy the desired archive from `${KM_BACKUP_DEST}` to a safe working directory.
3. Extract the archive (tarball) into an empty staging location:
   ```bash
   tar -xzf backup-20240201T120000Z.tar.gz -C /tmp/km-restore
   ```
4. Replace the live state directory:
   ```bash
   sudo systemctl stop duskmantle-gateway
   rm -rf /opt/knowledge/var
   mv /tmp/km-restore /opt/knowledge/var
   sudo systemctl start duskmantle-gateway
   ```
5. Verify the restore via `/healthz` (backup check should report the timestamp of the recovered archive) and run a smoke search/graph query.

For HA deployments, restore the backing stores (Neo4j, Qdrant) individually before restarting the API containers.

## Verification Checklist

- `pytest -k backup` to run the backup scheduler unit tests.
- `curl http://localhost:8000/healthz` → `checks.backup.status` should be `ok` after a successful run or `disabled` when automation is off.
- Prometheus dashboard should display the latest `km_backup_*` metrics.

Keep this playbook with your runbooks so on-call responders have clear restore steps.
