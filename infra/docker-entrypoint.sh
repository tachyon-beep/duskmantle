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
SECRETS_FILE="${KM_VAR}/secrets.env"
LOG_DIR="${KM_VAR}/logs"
RUN_DIR="${KM_VAR}/run"

mkdir -p "$KM_VAR" "$LOG_DIR" "$RUN_DIR"

if [[ ! -w "$KM_VAR" ]]; then
  echo "[entrypoint] ERROR: Persistence directory $KM_VAR is not writable. Mount a host volume." >&2
  exit 1
fi

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

allow_insecure=${KM_ALLOW_INSECURE_BOOT,,}

if [[ -f "$SECRETS_FILE" ]]; then
  echo "[entrypoint] Loading persisted credentials from $SECRETS_FILE"
  set -a
  source "$SECRETS_FILE"
  set +a
fi

missing_reader=false
missing_admin=false

if [[ -z "${KM_READER_TOKEN:-}" ]]; then
  missing_reader=true
fi
if [[ -z "${KM_ADMIN_TOKEN:-}" ]]; then
  missing_admin=true
fi

if [[ "$missing_reader" == true || "$missing_admin" == true ]]; then
  if [[ "$allow_insecure" == "true" ]]; then
    echo "[entrypoint] WARNING: Booting without managed credentials (KM_ALLOW_INSECURE_BOOT=true)." >&2
  else
    echo "[entrypoint] Generating API credentials" >&2
    mapfile -t generated < <(python <<'PY'
import secrets
import string
import uuid
alphabet = string.ascii_letters + string.digits
reader = str(uuid.uuid4())
admin = str(uuid.uuid4())
print(reader)
print(admin)
PY
    )
    if [[ "$missing_reader" == true ]]; then
      KM_READER_TOKEN="${generated[0]}"
    fi
    if [[ "$missing_admin" == true ]]; then
      KM_ADMIN_TOKEN="${generated[1]}"
    fi
    umask 077
    cat >"$SECRETS_FILE" <<SECRETS
KM_READER_TOKEN=${KM_READER_TOKEN}
KM_ADMIN_TOKEN=${KM_ADMIN_TOKEN}
SECRETS
    echo "[entrypoint] Stored generated credentials in $SECRETS_FILE" >&2
  fi
fi

if [[ "$allow_insecure" != "true" ]]; then
  if [[ -z "${KM_READER_TOKEN:-}" || -z "${KM_ADMIN_TOKEN:-}" ]]; then
    echo "[entrypoint] ERROR: Required credentials are missing and KM_ALLOW_INSECURE_BOOT is not enabled." >&2
    exit 1
  fi
fi

export KM_READER_TOKEN KM_ADMIN_TOKEN

if [[ -z "${KM_AUTH_ENABLED:-}" ]]; then
  if [[ "$allow_insecure" == "true" ]]; then
    KM_AUTH_ENABLED=false
  else
    KM_AUTH_ENABLED=true
  fi
fi
export KM_AUTH_ENABLED

if [[ -z "${KM_NEO4J_PASSWORD:-}" ]]; then
  echo "[entrypoint] ERROR: KM_NEO4J_PASSWORD must be provided; see deployment docs for managing Neo4j credentials." >&2
  exit 1
fi
if [[ -z "${KM_QDRANT_URL:-}" ]]; then
  KM_QDRANT_URL="http://qdrant:6333"
fi
export KM_QDRANT_URL

if [[ -z "${KM_NEO4J_URI:-}" ]]; then
  KM_NEO4J_URI="bolt://neo4j:7687"
fi
export KM_NEO4J_URI

if [[ -n "${KM_EXPECTED_UID:-}" && "$(id -u)" != "$KM_EXPECTED_UID" ]]; then
  echo "[entrypoint] WARNING: Container running as UID $(id -u), expected $KM_EXPECTED_UID" >&2
fi

if [[ "${KM_WATCH_ENABLED:-false}" == "true" ]]; then
  echo "[entrypoint] NOTICE: KM_WATCH_ENABLED is no longer supported inside the API container. Run km-watch externally." >&2
fi

exec "$@"
