
# Quick Wins

- **WP-202 – Make Scheduled Backup Pruning Safe** ✔️ Completed
  - Scheduler now prunes only `km-backup-*.tgz` archives within `${KM_STATE_PATH}/backups/archives`, exposes `km_backup_retention_deletes_total`, and leaves operator-managed files untouched. Docs and tests updated accordingly.

- **WP-203 – Rotate Search Feedback Event Logs** ✔️ Completed
  - `SearchFeedbackStore` now enforces size-based rotation (`KM_FEEDBACK_LOG_MAX_BYTES`, `KM_FEEDBACK_LOG_MAX_FILES`) and exposes Prometheus metrics (`km_feedback_log_bytes`, `km_feedback_rotations_total`).
  - Touch points: `gateway/search/feedback.py`, `gateway/observability/metrics.py`, `gateway/config/settings.py`.
  - Verification: `tests/test_search_feedback.py` covers rotation behaviour and metric updates.

- **WP-208 – Clamp Audit History Window** (Medium impact / XS effort)
  - Cap `/audit/history` limits to a safe maximum and document the ceiling to prevent accidental DoS.
  - Touch points: `gateway/api/routes/reporting.py`, `tests/test_coverage_report.py`.
  - Verification: new unit tests asserting clamped responses and warning metadata.
