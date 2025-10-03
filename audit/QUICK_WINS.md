
# Quick Wins

- **WP-202 – Make Scheduled Backup Pruning Safe** ✔️ Completed
  - Scheduler now prunes only `km-backup-*.tgz` archives within `${KM_STATE_PATH}/backups/archives`, exposes `km_backup_retention_deletes_total`, and leaves operator-managed files untouched. Docs and tests updated accordingly.

- **WP-203 – Rotate Search Feedback Event Logs** (Medium impact / S effort)
  - Introduce log rotation and metrics so `events.log` cannot fill disks silently.
  - Touch points: `gateway/search/feedback.py`, `gateway/observability/metrics.py`.
  - Verification: extend `tests/test_search_service.py` to cover rotation paths.

- **WP-208 – Clamp Audit History Window** (Medium impact / XS effort)
  - Cap `/audit/history` limits to a safe maximum and document the ceiling to prevent accidental DoS.
  - Touch points: `gateway/api/routes/reporting.py`, `tests/test_coverage_report.py`.
  - Verification: new unit tests asserting clamped responses and warning metadata.
