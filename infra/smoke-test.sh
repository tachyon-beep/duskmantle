#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-duskmantle/km:dev}
CONTAINER_NAME=${CONTAINER_NAME:-km-smoke}
DATA_DIR=$(mktemp -d -t km-smoke-XXXX)
REPO_MOUNT=${REPO_MOUNT:-$(pwd)}

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker run --rm -v "$DATA_DIR":/data alpine:3.20 sh -c "rm -rf /data/*" >/dev/null 2>&1 || true
  rm -rf "$DATA_DIR"
}
trap cleanup EXIT

docker build --network=host -t "$IMAGE" .

docker run -d --name "$CONTAINER_NAME" \
  -v "$DATA_DIR":/opt/knowledge/var \
  -v "$REPO_MOUNT":/workspace/repo \
  "$IMAGE"

echo "Waiting for gateway readiness..."
for _ in {1..30}; do
  if docker exec "$CONTAINER_NAME" curl -fsS http://localhost:8000/readyz >/dev/null 2>&1; then
    echo "Gateway ready"
    docker logs "$CONTAINER_NAME"
    exit 0
  fi
  sleep 2
  docker ps --filter "name=$CONTAINER_NAME"
done

echo "Gateway failed to become ready" >&2
exit 1
