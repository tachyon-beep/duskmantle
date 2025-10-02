#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-duskmantle/km:dev}
CONTAINER_NAME=${CONTAINER_NAME:-km-smoke}
DATA_DIR=$(mktemp -d -t km-smoke-var-XXXX)
REPO_DIR=$(mktemp -d -t km-smoke-repo-XXXX)
SMOKE_PASSWORD=${KM_SMOKE_NEO4J_PASSWORD:-SmokePass123!}

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker run --rm -v "$DATA_DIR":/data alpine:3.20 sh -c "rm -rf /data/*" >/dev/null 2>&1 || true
  docker run --rm -v "$REPO_DIR":/data alpine:3.20 sh -c "rm -rf /data/*" >/dev/null 2>&1 || true
  rm -rf "$DATA_DIR" "$REPO_DIR"
}
trap cleanup EXIT

docker build --network=host -t "$IMAGE" .

docker run -d --name "$CONTAINER_NAME" \
  -p 8000:8000 -p 6333:6333 -p 7687:7687 \
  -e KM_NEO4J_PASSWORD="$SMOKE_PASSWORD" \
  -e KM_NEO4J_AUTH_ENABLED=true \
  -e KM_SEED_SAMPLE_REPO=true \
  -v "$DATA_DIR":/opt/knowledge/var \
  -v "$REPO_DIR":/workspace/repo \
  "$IMAGE"

echo "Waiting for gateway readiness..."
ready=false
for _ in {1..30}; do
  if docker exec "$CONTAINER_NAME" curl -fsS http://localhost:8000/readyz >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
  docker ps --filter "name=$CONTAINER_NAME" >/dev/null
done

if [[ "$ready" != true ]]; then
  echo "Gateway failed to become ready" >&2
  exit 1
fi

echo "Verifying Neo4j authentication enforcement..."
if docker exec "$CONTAINER_NAME" /opt/knowledge/bin/neo4j-distribution/bin/cypher-shell -u neo4j -p neo4j "SHOW DATABASES" >/dev/null 2>&1; then
  echo "Expected default Neo4j password to be rejected" >&2
  exit 1
fi

docker exec "$CONTAINER_NAME" /opt/knowledge/bin/neo4j-distribution/bin/cypher-shell -u neo4j -p "$SMOKE_PASSWORD" "SHOW DATABASES" >/dev/null

echo "Running migrations and ingest..."
docker exec "$CONTAINER_NAME" /opt/knowledge/.venv/bin/gateway-graph migrate >/dev/null
docker exec "$CONTAINER_NAME" /opt/knowledge/.venv/bin/gateway-ingest rebuild --profile smoke --dummy-embeddings --full-rebuild >/dev/null

echo "Validating subsystem endpoint and coverage..."
docker exec "$CONTAINER_NAME" curl -fsS http://localhost:8000/graph/subsystems/Sample?depth=1 >/dev/null
docker exec "$CONTAINER_NAME" test -f /opt/knowledge/var/reports/coverage_report.json
docker exec "$CONTAINER_NAME" curl -fsS http://localhost:8000/coverage >/dev/null

echo "Gateway smoke test completed successfully"
