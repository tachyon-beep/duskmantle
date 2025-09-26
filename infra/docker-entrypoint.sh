#!/usr/bin/env bash
set -euo pipefail

KM_HOME=${KM_HOME:-/opt/knowledge}
KM_VAR=${KM_VAR:-/opt/knowledge/var}
LOG_DIR="${KM_VAR}/logs"
RUN_DIR="${KM_VAR}/run"
QDRANT_STORAGE="${KM_VAR}/qdrant"
NEO4J_DATA_ROOT="${KM_VAR}/neo4j"

mkdir -p "$LOG_DIR" "$RUN_DIR" "$QDRANT_STORAGE" "$QDRANT_STORAGE/snapshots" \
  "$NEO4J_DATA_ROOT/data" "$NEO4J_DATA_ROOT/logs" "$NEO4J_DATA_ROOT/plugins" "$NEO4J_DATA_ROOT/run"

if [[ ! -w "$KM_VAR" ]]; then
  echo "[entrypoint] ERROR: Persistence directory $KM_VAR is not writable. Mount a host volume." >&2
  exit 1
fi

if [[ -n "${KM_EXPECTED_UID:-}" && "$(id -u)" != "$KM_EXPECTED_UID" ]]; then
  echo "[entrypoint] WARNING: Container running as UID $(id -u), expected $KM_EXPECTED_UID" >&2
fi

exec /usr/bin/supervisord -c "$KM_HOME/etc/supervisord.conf"
