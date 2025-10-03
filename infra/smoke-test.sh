#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-duskmantle/km:dev}
QDRANT_IMAGE=${KM_SMOKE_QDRANT_IMAGE:-qdrant/qdrant:v1.15.5}
NEO4J_IMAGE=${KM_SMOKE_NEO4J_IMAGE:-neo4j:5.26.0}
PROJECT="km-smoke-$$"
WORK_DIR=$(mktemp -d -t km-smoke-XXXX)
COMPOSE_DIR="$WORK_DIR/compose"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"
SECRETS_FILE="$WORK_DIR/secrets.env"
REPO_DIR="$COMPOSE_DIR/repo"
STATE_DIR="$COMPOSE_DIR/config/gateway"
SMOKE_PASSWORD=${KM_SMOKE_NEO4J_PASSWORD:-SmokePass123!}

cleanup() {
  docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
  docker run --rm -v "$WORK_DIR":/work busybox:1.36 sh -c 'rm -rf /work/*' >/dev/null 2>&1 || true
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

mkdir -p "$COMPOSE_DIR/config/gateway" "$COMPOSE_DIR/config/neo4j/data" "$COMPOSE_DIR/config/neo4j/logs" "$COMPOSE_DIR/config/qdrant" "$REPO_DIR"

cp infra/examples/docker-compose.sample.yml "$COMPOSE_FILE"

TARGET_DB=neo4j

mapfile -t secrets < <(python <<'PY'
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
READER_TOKEN=${secrets[0]}
ADMIN_TOKEN=${secrets[1]}

cat >"$SECRETS_FILE" <<SMOKE_ENV
KM_IMAGE=$IMAGE
KM_QDRANT_IMAGE=$QDRANT_IMAGE
KM_NEO4J_IMAGE=$NEO4J_IMAGE
KM_AUTH_ENABLED=true
KM_READER_TOKEN=$READER_TOKEN
KM_ADMIN_TOKEN=$ADMIN_TOKEN
KM_NEO4J_PASSWORD=$SMOKE_PASSWORD
KM_NEO4J_AUTH_ENABLED=true
KM_NEO4J_DATABASE=neo4j
KM_QDRANT_URL=http://qdrant:6333
KM_NEO4J_URI=bolt://neo4j:7687
KM_DATA_DIR=$STATE_DIR
KM_REPO_DIR=$REPO_DIR
KM_CONTENT_ROOT=/workspace/repo
KM_CONTENT_DOCS_SUBDIR=docs
KM_INGEST_USE_DUMMY=true
KM_UPLOAD_DEFAULT_OVERWRITE=false
KM_UPLOAD_DEFAULT_INGEST=false
KM_ALLOW_INSECURE_BOOT=false
SMOKE_ENV

ln -s ../secrets.env "$COMPOSE_DIR/gateway.env"

docker build --network=host -t "$IMAGE" .

export KM_IMAGE="$IMAGE" KM_QDRANT_IMAGE="$QDRANT_IMAGE" KM_NEO4J_IMAGE="$NEO4J_IMAGE" KM_NEO4J_PASSWORD="$SMOKE_PASSWORD"

docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" up -d

TARGET_DB=neo4j

if [ "$TARGET_DB" != "neo4j" ]; then
  docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" exec -T neo4j \
    cypher-shell -u neo4j -p "$SMOKE_PASSWORD" -d system "CREATE DATABASE `$TARGET_DB` IF NOT EXISTS" >/dev/null
fi

echo "Waiting for gateway readiness..."
ready=false
for _ in {1..40}; do
  if curl -fsS http://localhost:8000/readyz >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done

if [[ "$ready" != true ]]; then
  echo "Gateway failed to become ready" >&2
  exit 1
fi

READER_HEADER="Authorization: Bearer $READER_TOKEN"
ADMIN_HEADER="Authorization: Bearer $ADMIN_TOKEN"

uid=$(docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" exec -T gateway id -u)
if [[ "$uid" == "0" ]]; then
  echo "Gateway container is running as root" >&2
  exit 1
fi

echo "Running migrations and ingest..."
docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" exec -T gateway /opt/knowledge/.venv/bin/gateway-graph migrate >/dev/null
docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" exec -T gateway /opt/knowledge/.venv/bin/gateway-ingest rebuild --profile smoke --dummy-embeddings --full-rebuild >/dev/null

graph_status='degraded'
for _ in {1..15}; do
  graph_status=$(curl -fsS http://localhost:8000/healthz -H "$ADMIN_HEADER" | python -c 'import json,sys; print(json.load(sys.stdin)["checks"]["graph"]["status"])')
  if [ "$graph_status" = "ok" ]; then
    break
  fi
  sleep 2
done
if [ "$graph_status" != "ok" ]; then
  echo "Graph dependency not healthy (status=$graph_status)" >&2
  exit 1
fi

echo "Validating subsystem endpoint and coverage..."
curl -fsS http://localhost:8000/graph/subsystems/Sample?depth=1 -H "$READER_HEADER" >/dev/null
curl -fsS http://localhost:8000/coverage -H "$ADMIN_HEADER" >/dev/null

echo "Checking Neo4j password enforcement..."
if docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" exec -T neo4j cypher-shell -u neo4j -p neo4j "SHOW DATABASES" >/dev/null 2>&1; then
  echo "Expected default Neo4j password to be rejected" >&2
  exit 1
fi

docker compose --project-name "$PROJECT" -f "$COMPOSE_FILE" exec -T neo4j cypher-shell -u neo4j -p "$SMOKE_PASSWORD" "SHOW DATABASES" >/dev/null

echo "Gateway smoke test completed successfully"
