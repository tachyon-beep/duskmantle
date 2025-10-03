# Search Scoring Modernisation Plan

## Context

Duskmantle's `/search` endpoint currently combines vector similarity with hand-tuned graph signals (subsystem affinity, relationship density, supporting artifacts, coverage penalties). While effective, the static blend cannot adapt to user intent or future heuristics without manual reweighting.

Our primary consumer is an autonomous MCP-connected LLM that can provide immediate feedback on result quality. We will leverage this to build a data-driven ranking stack that remains explainable and easy to operate.

## Objective

Replace fixed heuristics with a model-driven scorer that:

- Learns from live relevance feedback supplied by the MCP agent (no human annotation expected).
- Retains low-latency inference suitable for online queries.
- Preserves transparency by surfacing per-result feature contributions.
- Offers a sane fallback (`heuristic` mode) and effortless rollback.

## Phased Delivery

### Phase 1 — Signal Capture & Telemetry

- Instrument `/search` responses to log `query`, `result_id`, and `scoring_breakdown` (vector, subsystem boost, relationship count, support boost, coverage penalty) into an append-only store under `/opt/knowledge/var/feedback`.
- Extend the MCP dialogue so every search request collects an ordinal relevance vote from the frontier model (default `3/5` if unsure) and persist it alongside the feature vector.
- Tag entries with request UUID, timestamp, and optional `analysis_context` to enable audits.

### Phase 2 — Feature Pipeline & Storage

- Define a stable feature schema encompassing existing signals plus placeholders for upcoming metrics (path depth, artifact freshness, etc.).
- Implemented: `gateway-search export-training-data` transforms raw telemetry into CSV or JSONL datasets stored in `/opt/knowledge/var/feedback/datasets/`. Flags allow filtering to rows with explicit votes (`--require-vote`) and limiting sample size.
- Document retention and redaction controls; allow operators to cap history or scrub sensitive query terms.
- Implemented: `gateway-search prune-feedback` enforces age/count retention on `events.log`, and `gateway-search redact-dataset` blanks queries/context/notes before sharing datasets externally.

### Phase 3 — Modeling & Evaluation

- Implemented: linear regression trainer (`gateway-search train-model`) uses captured signals to fit coefficients via least-squares and exports JSON artifacts (feature order, coefficients, intercept, metrics).
- Implemented: evaluation harness (`gateway-search evaluate-model`) loads exported datasets + model artifacts and reports MSE/R²/NDCG@k/Spearman scores. Use holdout datasets (e.g., validators captured via MCP) before enabling inference.
- Next: extend evaluation with replay suites (`pytest -m ranking`) once sufficient labelled data accumulates and publish promotion thresholds.
- Package model artifacts (feature order + coefficients) with semantic versions and checksums for traceability.

-### Phase 4 — Advanced Signals & Profiles (In Progress)

- ✅ Introduced new signals: coverage ratio and freshness now flow from ingestion → scoring → telemetry; subsystem criticality falls back to graph metadata when chunk annotations are absent.
- ✅ Provide curated weight bundles (`default`, `analysis`, `operations`, `docs-heavy`) selectable via `KM_SEARCH_WEIGHT_PROFILE`; granular `KM_SEARCH_W_*` variables still override individual weights when operators need bespoke tuning. Defaults were recalibrated after synthetic benchmarking so the new criticality weight (`KM_SEARCH_W_CRITICALITY`) integrates without over-powering vector scores.
- ✅ Shortest-path depth to subsystems now computed in Neo4j (within four hops) and exposed as a signal; search requests memoise graph lookups per artifact so repeated hits reuse the same context without extra queries.
- ✅ Instrument caching metrics (hit/miss/error counters, lookup latency histogram, ranking delta histogram) to monitor ML-mode performance.
- Update unit tests and operator docs to cover new signals and profiles.
- Subsystem metadata can be sourced from `docs/subsystems.json` (or `.metadata/subsystems.json`) containing entries such as `{ "Kasmina": { "criticality": "high" } }`.

### Phase 5 — Inference Integration

- Implemented: `SearchService` now delegates to `VectorRetriever`, `GraphEnricher`, `HeuristicScorer`, and `ModelScorer` collaborators. Model artifacts are loaded when `KM_SEARCH_SCORING_MODE=ml` is set (with optional `KM_SEARCH_MODEL_PATH`) and the orchestrator falls back to heuristics if the model is missing or invalid.
- Responses surface `metadata.scoring_mode` and per-feature contributions under `scoring.model`, giving MCP clients clear provenance for ranking decisions while preserving the existing heuristic snapshot in metadata.
- Each collaborator has focused unit coverage under `tests/search/test_*.py`, making future signal additions safer and faster.
- Next: explore memoising graph lookups for large result sets and adding runtime health checks that verify the configured model matches the expected feature schema.

### Phase 6 — Ops & Governance

- Update docs (README, GRAPH_API_DESIGN, OBSERVABILITY_GUIDE) with the feedback loop, retrain workflow, and rollback steps.
- Schedule retraining or provide a CLI (`gateway-search train-model`) operators can run on demand.
- Monitor concept drift and feedback integrity; surface telemetry (e.g., histogram of vector vs adjusted deltas) to detect anomalies.

## Risks & Mitigations

- **Sparse Feedback:** Bootstrapped using MCP self-evaluation signals to avoid cold-start; supplement with synthetic benchmarks from design docs if needed.
- **Latency Impact:** Keep feature extraction memoized per query, guard graph enrichment with per-request concurrency/time budgets, and prefer linear models; fall back automatically if model loading fails.
- **Explainability:** Continue exposing raw features and model contributions to satisfy audit requirements.
- **Data Volume:** Rotate feedback files (e.g., daily) and document archival/cleanup commands.

## Next Actions

1. Implement Phase 1 instrumentation and storage.
2. Validate feedback collection end-to-end with MCP client stub.
3. Iterate on Phase 2 ETL once sufficient telemetry accumulates.

## Weight Bundles & Inspection

- **default:** balanced blend for general use; favours subsystem affinity while modestly rewarding supporting artifacts and critical subsystems.
- **analysis:** increases subsystem/criticality weights for deep architectural reviews where design intent is paramount.
- **operations:** emphasises coverage penalties to surface under-tested components; pair with on-call dashboards.
- **docs-heavy:** boosts supporting artifacts for knowledge-base reviews, keeping criticality lower to prioritise procedure docs.

Inspect active weights via:

- CLI: `gateway-search show-weights` (prints profile, thresholds, and individual weights).
- API: `GET /search/weights` (maintainer scope) returns JSON for dashboards or automated checks.

Weights remain clamped to `[0, 1]` via configuration validation; override values outside this range are coerced automatically but should be avoided in production. Document rationale for any custom profile so future tuning can revisit the decision.
