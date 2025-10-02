#!/usr/bin/env bash
set -euo pipefail

KM_HOME=${KM_HOME:-/opt/knowledge}
KM_BIN=${KM_BIN:-/opt/knowledge/bin}
KM_VAR=${KM_VAR:-/opt/knowledge/var}
KM_ETC=${KM_ETC:-/opt/knowledge/etc}
KM_REPO_PATH=${KM_REPO_PATH:-/workspace/repo}
KM_SAMPLE_CONTENT_DIR=${KM_SAMPLE_CONTENT_DIR:-/opt/knowledge/infra/examples/sample-repo}
KM_SEED_SAMPLE_REPO=${KM_SEED_SAMPLE_REPO:-true}
KM_ALLOW_INSECURE_BOOT=${KM_ALLOW_INSECURE_BOOT:-false}
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

SECRETS_FILE="${KM_VAR}/secrets.env"
allow_insecure=${KM_ALLOW_INSECURE_BOOT,,}

# Load previously generated secrets if available.
if [[ -f "$SECRETS_FILE" ]]; then
  echo "[entrypoint] Loading persisted credentials from $SECRETS_FILE"
  set -a
  source "$SECRETS_FILE"
  set +a
fi

missing_reader=false
missing_admin=false
missing_password=false

if [[ -z "${KM_READER_TOKEN:-}" ]]; then
  missing_reader=true
fi
if [[ -z "${KM_ADMIN_TOKEN:-}" ]]; then
  missing_admin=true
fi
if [[ -z "${KM_NEO4J_PASSWORD:-}" || "${KM_NEO4J_PASSWORD}" == "neo4jadmin" ]]; then
  missing_password=true
fi

if [[ "$missing_reader" == true || "$missing_admin" == true || "$missing_password" == true ]]; then
  if [[ "$allow_insecure" == "true" ]]; then
    echo "[entrypoint] WARNING: Booting without managed credentials (KM_ALLOW_INSECURE_BOOT=true)." >&2
  else
    echo "[entrypoint] Generating secure credentials" >&2
    mapfile -t generated < <(python <<'PY'
import secrets
import string
import uuid

alphabet = string.ascii_letters + string.digits

def random_password(length: int = 48) -> str:
    return ''.join(secrets.choice(alphabet) for _ in range(length))

reader = str(uuid.uuid4())
admin = str(uuid.uuid4())
password = random_password()
print(reader)
print(admin)
print(password)
PY
    )
    if [[ "$missing_reader" == true ]]; then
      KM_READER_TOKEN="${generated[0]}"
    fi
    if [[ "$missing_admin" == true ]]; then
      KM_ADMIN_TOKEN="${generated[1]}"
    fi
    if [[ "$missing_password" == true ]]; then
      KM_NEO4J_PASSWORD="${generated[2]}"
    fi
    umask 077
    cat >"$SECRETS_FILE" <<EOF
KM_READER_TOKEN=${KM_READER_TOKEN}
KM_ADMIN_TOKEN=${KM_ADMIN_TOKEN}
KM_NEO4J_PASSWORD=${KM_NEO4J_PASSWORD}
EOF
    echo "[entrypoint] Stored generated credentials in $SECRETS_FILE" >&2
  fi
fi

# Abort if credentials are still missing when insecure boot is not allowed.
if [[ "$allow_insecure" != "true" ]]; then
  if [[ -z "${KM_READER_TOKEN:-}" || -z "${KM_ADMIN_TOKEN:-}" || -z "${KM_NEO4J_PASSWORD:-}" ]]; then
    echo "[entrypoint] ERROR: Required credentials are missing and KM_ALLOW_INSECURE_BOOT is not enabled." >&2
    exit 1
  fi
fi

# Ensure credentials are exported for downstream consumers.
export KM_READER_TOKEN KM_ADMIN_TOKEN KM_NEO4J_PASSWORD

# Default to secure API authentication unless explicitly disabled.
if [[ -z "${KM_AUTH_ENABLED:-}" ]]; then
  if [[ "$allow_insecure" == "true" ]]; then
    KM_AUTH_ENABLED=false
  else
    KM_AUTH_ENABLED=true
  fi
fi
export KM_AUTH_ENABLED

if [[ -z "${KM_NEO4J_AUTH_ENABLED:-}" ]]; then
  if [[ "$allow_insecure" == "true" ]]; then
    KM_NEO4J_AUTH_ENABLED=false
  else
    KM_NEO4J_AUTH_ENABLED=true
  fi
fi
export KM_NEO4J_AUTH_ENABLED

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
