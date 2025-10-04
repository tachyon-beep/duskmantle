# Phase 0 Risk Reduction Notes

## R0.1 Prototype tree-sitter build (Python + TypeScript)
- **Workspace**: `tmp/phase0/tree-sitter` with fresh clones of `tree-sitter-python` and `tree-sitter-typescript` (typescript + tsx grammars).
- **Build command**:
  ```bash
  python - <<'PY'
  from pathlib import Path
  import time
  from tree_sitter import Language

  root = Path('tmp/phase0/tree-sitter').resolve()
  build_dir = root / 'build'
  build_dir.mkdir(exist_ok=True)
  grammars = [
      root / 'tree-sitter-python',
      root / 'tree-sitter-typescript' / 'typescript',
      root / 'tree-sitter-typescript' / 'tsx',
  ]

  start = time.perf_counter()
  Language.build_library(str(build_dir / 'languages.so'), [str(path) for path in grammars])
  print(f"Build completed in {time.perf_counter() - start:.2f} seconds")
  PY
  ```
- **Results**:
  - Build time: **1.09 s** on RTX 4060 Ti host.
  - Output shared library: **`build/languages.so` = 3.3 MiB** (`ls -lh`).
  - Grammar clones weigh ~4.7 MiB (Python) and 20 MiB (TypeScript/TSX) checked out at depth 1.
- **Dockerfile guidance**:
  - Add a short build stage (`FROM python:3.12-alpine` or debian slim) with `build-base`/`gcc` and `tree-sitter` Python package installed.
  - Clone grammars under `/tmp/tree-sitter` (depth 1) and run the above snippet to emit `/opt/knowledge/tree-sitter/languages.so`.
  - Copy only the compiled `.so` into the runtime image (`COPY --from=builder /opt/knowledge/tree-sitter/languages.so /opt/knowledge/tree-sitter/languages.so`) and remove the grammar sources to keep the final layer under ~4 MiB.
  - Optionally cache the grammar repos as tarballs to avoid Git during offline builds; ensure the Docker layer that runs `build_library` is invalidated only when grammars change.


## R0.2 ONNXRuntime footprint spike
- **Wheel download (CPU build)**: `onnxruntime-1.23.0` + deps total **~40 MiB** (primary wheel 17.3 MiB, numpy 16.6 MiB, remainder <7 MiB) captured under `tmp/phase0/onnx/`.
- **Installation**: `pip install onnxruntime` within project `.venv` adds ~60 MiB to site-packages (matches wheel sizes, no compiled extras beyond bundled shared libs).
- **Runtime probe**:
  ```bash
  python - <<'PY'
  import resource
  import numpy as np
  import onnxruntime as ort
  from onnxruntime.datasets import get_example

  usage_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  session = ort.InferenceSession(get_example('mul_1.onnx'), providers=['CPUExecutionProvider'])
  input_tensor = np.arange(6, dtype=np.float32).reshape(3, 2)
  session.run(None, {session.get_inputs()[0].name: input_tensor})
  usage_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  print('Peak delta (MB):', (usage_after - usage_before) / 1024)
  PY
  ```
  - Peak RSS increase: **~9 MB** (total RSS ~48 MB) when running a tiny CPU inference session.
- **Packaging recommendation**:
  - Ship ONNXRuntime as an **optional extra** (`pip install duskmantle-knowledge-gateway[rerank]`) to avoid inflating the base image by ~40 MB when re-ranking is disabled.
  - If bundling in Docker, install in a dedicated layer (`pip install --no-cache-dir onnxruntime`) so it can be pruned for CPU-only deployments; GPU builds (onnxruntime-gpu) jump to >200 MB so keep them out of default image.
  - Document minimum RAM headroom (~50 MB) for enabling the re-rank pass; negligible compared with Qdrant/Neo4j services.


## R0.3 Neo4j symbol payload validation
- **Scratch DB**: `docker run -d --rm -p 7688:7687 -e NEO4J_AUTH=neo4j/testpass neo4j:5` (clean container for the spike).
- **Migration check**: `Neo4jWriter.ensure_constraints()` executed against the fresh database; verified the constraint + two indexes for `Symbol` now exist (`SHOW INDEXES` returned ids for `id`, `name`, `language`).
- **Sample ingest**: `Neo4jWriter.sync_artifact()` invoked with a `SourceFile` carrying a single symbol record (`src/service.py::handler`).
- **Legacy query sanity**:
  - `MATCH (f:SourceFile {path: 'src/service.py'}) RETURN f.path, f.subsystem` ➜ still resolves as before.
  - `MATCH (s:Subsystem {name: 'Telemetry'}) RETURN count(s)` ➜ unchanged.
  - New edge check: `MATCH (:SourceFile {path:'src/service.py'})-[:DECLARES_SYMBOL]->(:Symbol)` ➜ 1 row, confirming linkage without touching existing `DECLARES` edges.
- **Conclusion**: Symbol payloads coexist with existing Cypher patterns; no query rewrites required. Documented index names (`constraint_acd7a3bc`, `index_a5940833`, `index_5047dfe3`) to monitor during migrations. Recommend adding a smoke test that runs `SHOW INDEXES WHERE labelsOrTypes=['Symbol']` post-migration in CI.

## R0.4 UI feasibility follow-up
- The production search UI now ships the planned elements, so the original static mock is redundant:
  - Symbol chips for kind/language filters are rendered from `gateway/ui/templates/search.html` and wired through `gateway/ui/static/app.js` (chips broadcast to the MCP/CLI payload builder).
  - Hit cards surface the symbol badge cluster plus optional “Open in editor” link (same JS module, lines ~394-705).
  - Playwright regression `playwright/tests/search.spec.ts` exercises chip selection + link rendering, providing stronger coverage than the original static mock would have.
- No additional mock assets required; documentation should point to the live implementation and Playwright screenshots if we want visual references in the future.

