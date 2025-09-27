#!/usr/bin/env bash
set -euo pipefail

DIST_DIR=${1:-dist}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}" )/.." && pwd)

mkdir -p "${DIST_DIR}"
cd "${PROJECT_ROOT}"
python -m pip wheel . --no-deps -w "${DIST_DIR}"
