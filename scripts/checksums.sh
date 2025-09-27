#!/usr/bin/env bash
set -euo pipefail

TARGET=${1:-dist}
OUTPUT=${2:-SHA256SUMS}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}" )/.." && pwd)

cd "${PROJECT_ROOT}"
if [[ ! -d "$TARGET" ]]; then
  echo "[checksums] error: target directory '$TARGET' does not exist" >&2
  exit 1
fi

: > "$OUTPUT"
find "$TARGET" -type f -print0 | sort -z | while IFS= read -r -d '' file; do
  sha256sum "$file" >> "$OUTPUT"
done

echo "[checksums] wrote $(wc -l < "$OUTPUT") entries to $OUTPUT"
