#!/usr/bin/env bash
set -euo pipefail

KM_HOME=${KM_HOME:-/opt/knowledge}
KM_BIN=${KM_BIN:-/opt/knowledge/bin}
KM_VAR=${KM_VAR:-/opt/knowledge/var}
KM_ETC=${KM_ETC:-/opt/knowledge/etc}
KM_REPO_PATH=${KM_REPO_PATH:-/workspace/repo}
KM_SAMPLE_CONTENT_DIR=${KM_SAMPLE_CONTENT_DIR:-/opt/knowledge/infra/examples/sample-repo}
KM_SEED_SAMPLE_REPO=${KM_SEED_SAMPLE_REPO:-true}
LOG_DIR="${KM_VAR}/logs"
RUN_DIR="${KM_VAR}/run"
QDRANT_STORAGE="${KM_VAR}/qdrant"
NEO4J_DATA_ROOT="${KM_VAR}/neo4j"
NEO4J_CONF_FILE="${KM_ETC}/neo4j/neo4j.conf"

mkdir -p "$LOG_DIR" "$RUN_DIR" "$QDRANT_STORAGE" "$QDRANT_STORAGE/snapshots" \
  "$NEO4J_DATA_ROOT/data" "$NEO4J_DATA_ROOT/logs" "$NEO4J_DATA_ROOT/plugins" "$NEO4J_DATA_ROOT/run"

seed_sample=${KM_SEED_SAMPLE_REPO,,}
if [[ -d "$KM_REPO_PATH" ]]; then
  if [[ -z "$(ls -A "$KM_REPO_PATH" 2>/dev/null)" && "$seed_sample" != "false" ]]; then
    if [[ -d "$KM_SAMPLE_CONTENT_DIR" ]]; then
      echo "[entrypoint] Seeding repository with sample content"
      cp -R "$KM_SAMPLE_CONTENT_DIR"/. "$KM_REPO_PATH"/
      touch "$KM_REPO_PATH/.km-sample-repo"
    else
      echo "[entrypoint] Sample content directory $KM_SAMPLE_CONTENT_DIR not found" >&2
    fi
  fi
else
  echo "[entrypoint] Creating repository directory at $KM_REPO_PATH"
  mkdir -p "$KM_REPO_PATH"
  if [[ -d "$KM_SAMPLE_CONTENT_DIR" && "$seed_sample" != "false" ]]; then
    echo "[entrypoint] Seeding repository with sample content"
    cp -R "$KM_SAMPLE_CONTENT_DIR"/. "$KM_REPO_PATH"/
    touch "$KM_REPO_PATH/.km-sample-repo"
  fi
fi

auth_setting=${KM_NEO4J_AUTH_ENABLED:-true}
if [[ -f "$NEO4J_CONF_FILE" ]]; then
  case "${auth_setting,,}" in
    false)
      sed -i 's/^dbms\.security\.auth_enabled=.*/dbms.security.auth_enabled=false/' "$NEO4J_CONF_FILE"
      echo "[entrypoint] WARNING: Neo4j authentication disabled via KM_NEO4J_AUTH_ENABLED=false" >&2
      ;;
    *)
      sed -i 's/^dbms\.security\.auth_enabled=.*/dbms.security.auth_enabled=true/' "$NEO4J_CONF_FILE"
      ;;
  esac
fi

if [[ ! -w "$KM_VAR" ]]; then
  echo "[entrypoint] ERROR: Persistence directory $KM_VAR is not writable. Mount a host volume." >&2
  exit 1
fi

if [[ -n "${KM_EXPECTED_UID:-}" && "$(id -u)" != "$KM_EXPECTED_UID" ]]; then
  echo "[entrypoint] WARNING: Container running as UID $(id -u), expected $KM_EXPECTED_UID" >&2
fi

NEO4J_ADMIN="${KM_BIN}/neo4j-distribution/bin/neo4j-admin"
NEO4J_AUTH_FILE="${NEO4J_DATA_ROOT}/data/dbms/auth"
NEO4J_PASSWORD="${KM_NEO4J_PASSWORD:-neo4jadmin}"
if [[ -x "$NEO4J_ADMIN" && ! -f "$NEO4J_AUTH_FILE" && "${auth_setting,,}" != "false" ]]; then
  echo "[entrypoint] Setting initial Neo4j password"
  "$NEO4J_ADMIN" dbms set-initial-password "$NEO4J_PASSWORD" || true
fi

exec /usr/bin/supervisord -c "$KM_HOME/etc/supervisord.conf"
