- **Weight validation (baseline complete, ongoing monitoring required)**
  - Reference metrics: acceptance demo on 2025-09-27 produced average weighted vector contribution 0.4588 vs lexical 0.2411 with defaults (1.0 / 0.25).
  - Action: capture live relevance telemetry (nDCG@k, recall@k) once production query logs are available. Use `docs/OBSERVABILITY_GUIDE.md` ranking drift panel and `km_search_adjusted_minus_vector` histogram to monitor day-to-day shifts.
  - Next Step: schedule quarterly evaluation using annotator-labelled queries; adjust `KM_SEARCH_VECTOR_WEIGHT` / `KM_SEARCH_LEXICAL_WEIGHT` if mean delta leaves [-0.2, 0.2].

- **HNSW recall vs latency benchmarking (pending real dataset)**
  - Use the `gateway-search` CLI with a labelled query set (~200 queries) to measure recall at efSearch values 64/96/128/160. Record `km_search_graph_lookup_seconds` P95 alongside recall metrics.
  - TODO: produce benchmark notebook once telemetry is captured; target release 1.0.2 for any defaults change.

- **Sparse query fallback research (deferred)**
  - Investigate BM25 or phrase-based search using Qdrant payload or a lightweight inverted index. Requires sample of sparse queries that currently miss.
  - Decision: defer implementation until after weight/efSearch benchmarking; track under Knowledge Console WP7 backlog.
