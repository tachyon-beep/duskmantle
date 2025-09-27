#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-duskmantle/km:dev}
CONTEXT=${2:-.}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}" )/.." && pwd)

export DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-1}
PROGRESS=${KM_BUILD_PROGRESS:-plain}

cd "$PROJECT_ROOT"

echo "[build-image] building $IMAGE from $CONTEXT"
docker build --progress "$PROGRESS" -t "$IMAGE" ${KM_BUILD_ARGS:-} "$CONTEXT"

echo "[build-image] image metadata"
docker image inspect "$IMAGE" --format 'ID={{.Id}}\nRepoTags={{.RepoTags}}\nSize={{.Size}}\nCreated={{.Created}}'
