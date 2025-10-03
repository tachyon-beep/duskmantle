## gateway/search/service.py

**File path**: `gateway/search/service.py`
**Purpose**: Compose vector retrieval, filter normalisation, graph enrichment, heuristic scoring, and optional ML reranking to serve search responses.
**Dependencies**: External – __future__.annotations, collections.abc.Callable, collections.abc.Iterable, datetime.datetime, logging, qdrant_client.QdrantClient, qdrant_client.http.models.ScoredPoint, re; Internal – gateway.graph.service.GraphService, gateway.ingest.embedding.Embedder, gateway.observability.SEARCH_SCORE_DELTA, gateway.search.filtering.build_filter_state, gateway.search.filtering.parse_iso_datetime, gateway.search.filtering.payload_passes_filters, gateway.search.graph_enricher.GraphEnricher, gateway.search.ml.ModelScorer, gateway.search.models.SearchOptions, gateway.search.models.SearchResponse, gateway.search.models.SearchResult, gateway.search.models.SearchWeights, gateway.search.scoring.HeuristicScorer, gateway.search.trainer.ModelArtifact, gateway.search.vector_retriever.VectorRetriever
**Related modules**: gateway/api/routes/search.py, gateway/api/dependencies.py, gateway/search/filtering.py, gateway/search/graph_enricher.py, gateway/search/vector_retriever.py, gateway/search/scoring.py, gateway/search/ml.py

### Classes
- `SearchService` (line 23) — Executes hybrid vector/graph search by coordinating dedicated collaborators and returning structured results.

#### `SearchService` methods
- `__init__(...)` (line 26) — Wires configuration, weights, and collaborators (vector retriever, graph enricher, heuristic scorer, model scorer).
- `search(...) -> SearchResponse` (line 47) — Normalises filters, retrieves vectors, applies graph enrichment and scoring, and assembles metadata.

### Functions
- `_subsystems_from_context(graph_context: dict[str, Any] | None) -> set[str]` (line 203) — Extracts subsystem names from cached graph context for filter checks.
- `_detect_query_subsystems(query: str) -> set[str]` (line 214) — Tokenises query text for subsystem affinity scoring.
- `_normalise_hybrid_weights(vector_weight: float, lexical_weight: float) -> tuple[float, float]` (line 220) — Guards against zero-weight blends.
- `_resolve_chunk_datetime(chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> datetime | None` (line 236) — Determines timestamps for recency filtering.

### Collaborator Usage
- Delegates vector lookup to `VectorRetriever` (Qdrant embed + search with optional HNSW tuning).
- Delegates graph enrichment, caching, and budgets to `GraphEnricher`.
- Relies on `HeuristicScorer` for signal aggregation and coverage/criticality handling.
- Applies `ModelScorer` when ML scoring is enabled, falling back to heuristic mode on errors.

### Data Flow
- Retrieves vectors from Qdrant, filters payloads, enriches with Neo4j context subject to slot/time budgets, combines heuristic signals, optionally reranks via ML coefficients, and emits Prometheus deltas.

### Integration Points
- Qdrant search API for vector retrieval; Neo4j via `GraphService` for node lookups; Prometheus metrics for scoring deltas; FastAPI dependencies instantiate this class per-request.

### Code Quality Notes
- Core orchestration logic now delegates to single-responsibility helpers, reducing in-module complexity and improving test coverage (see `tests/search/test_*.py`).

## gateway/search/models.py

**File path**: `gateway/search/models.py`
**Purpose**: Provide shared dataclasses and helpers describing search options, weights, filter state, and scoring metadata.
**Dependencies**: External – __future__.annotations, dataclasses.dataclass, datetime.UTC, datetime.datetime; Internal – None
**Related modules**: gateway/search/service.py, gateway/search/scoring.py, gateway/search/graph_enricher.py

### Classes
- `SearchResult` (line 9) — Represents a single ranked chunk including optional graph context and scoring metadata.
- `SearchResponse` (line 17) — Container for query string, result list, and response metadata.
- `SearchOptions` (line 25) — Runtime knobs controlling limits, graph budgets, and scoring mode.
- `SearchWeights` (line 37) — Configurable weight profile for heuristic scoring signals.
- `FilterState` (line 49) — Preprocessed filters for subsystems, artifact types, namespaces, tags, and recency cutoff.
- `CoverageInfo` (line 62) — Captures coverage ratios and penalties for scoring calculations.

### Functions
- `ensure_utc(dt: datetime) -> datetime` (line 72) — Normalises datetimes to UTC for serialisation.

### Data Flow
- Acts as a DTO layer; objects are created by service collaborators and returned via API responses.

### Integration Points
- Consumed by FastAPI dependencies, search collaborators, and tests to share configuration/state.

### Code Quality Notes
- All dataclasses use slots for memory efficiency; type hints are exhaustive.


## gateway/search/filtering.py

**File path**: `gateway/search/filtering.py`
**Purpose**: Normalise incoming filter payloads and provide predicate helpers for search payload evaluation.
**Dependencies**: External – __future__.annotations, collections.abc.Mapping, collections.abc.Sequence, datetime.UTC, datetime.datetime, datetime.timedelta; Internal – gateway.search.models.FilterState
**Related modules**: gateway/search/service.py, gateway/api/routes/search.py

### Functions
- `build_filter_state(filters: Mapping[str, Any] | None) -> FilterState` (line 12) — Produces normalised filter sets and applied metadata, including recency cut-offs.
- `payload_passes_filters(payload: Mapping[str, Any], state: FilterState) -> bool` (line 52) — Evaluates Qdrant payloads against allowed types, namespaces, and tags.
- `parse_iso_datetime(value: object) -> datetime | None` (line 65) — Parses numeric or string timestamps into timezone-aware datetimes.

### Data Flow
- Converts API-level filter payloads into preprocessed sets, enabling efficient evaluation within the search loop.

### Integration Points
- Used by `SearchService` during request handling and tested in `tests/search/test_filtering.py`.

### Code Quality Notes
- Pure functions with deterministic behaviour, simplifying unit testing.


## gateway/search/vector_retriever.py

**File path**: `gateway/search/vector_retriever.py`
**Purpose**: Encapsulate query embedding and Qdrant vector search with optional HNSW tuning and failure callbacks.
**Dependencies**: External – __future__.annotations, collections.abc.Callable, collections.abc.Sequence, logging, qdrant_client.QdrantClient, qdrant_client.http.models.ScoredPoint; Internal – gateway.ingest.embedding.Embedder
**Related modules**: gateway/search/service.py

### Classes
- `VectorRetrievalError` (line 13) — Raised when encoding or searching fails prior to emitting results.
- `VectorRetriever` (line 19) — Executes embedding and Qdrant search.
  - Methods: `__init__(...)` (line 21) initialises dependencies; `search(query: str, limit: int, request_id: str | None = None) -> Sequence[ScoredPoint]` (line 34) executes the search with telemetry logging and failure callbacks.

### Data Flow
- Encodes query text, issues Qdrant search with optional HNSW parameters, and returns scored points to the orchestrator.

### Integration Points
- Used exclusively by `SearchService`; tests simulate Qdrant responses in `tests/search/test_vector_retriever.py`.

### Code Quality Notes
- Centralises error handling; failure callbacks allow circuit breakers to react to Qdrant outages.


## gateway/search/graph_enricher.py

**File path**: `gateway/search/graph_enricher.py`
**Purpose**: Manage graph context lookups, caching, and enrichment budgets for search results while emitting telemetry.
**Dependencies**: External – __future__.annotations, dataclasses.dataclass, logging, time, neo4j.exceptions.Neo4jError; Internal – gateway.graph.service.GraphService, gateway.graph.service.GraphServiceError, gateway.observability.SEARCH_GRAPH_CACHE_EVENTS, gateway.observability.SEARCH_GRAPH_LOOKUP_SECONDS, gateway.observability.SEARCH_GRAPH_SKIPPED_TOTAL, gateway.search.models.FilterState
**Related modules**: gateway/search/service.py, gateway/search/models.py

### Classes
- `GraphEnrichmentResult` (line 17) — Holds enriched graph context and optional path depth.
- `GraphEnricher` (line 24) — Coordinates cache usage, Neo4j lookups, and budget tracking.
  - Methods: `__init__(...)` (line 26) configures budgets and telemetry; `resolve(payload: dict[str, Any], subsystem_match: bool, warnings: list[str]) -> GraphEnrichmentResult` (line 53) retrieves/caches graph context respecting budgets; properties `slots_exhausted` and `time_exhausted` expose budget state.

### Functions
- `_label_for_artifact(artifact_type: str | None) -> str` (line 208) — Maps artifact types to graph labels.
- `_summarize_graph_context(data: dict[str, Any]) -> dict[str, Any]` (line 217) — Normalises Neo4j node data for scoring.

### Data Flow
- Decides whether graph lookups are needed, records cache hits/misses/errors, and returns enriched context with path depth for scoring.

### Integration Points
- Interacts with `GraphService` for Neo4j access and Prometheus counters for observability; verified in `tests/search/test_graph_enricher.py`.

### Code Quality Notes
- Collocates all budget and telemetry logic, simplifying future enhancements (e.g., retries/backoff).


## gateway/search/scoring.py

**File path**: `gateway/search/scoring.py`
**Purpose**: Provide heuristic scoring utilities for combining vector scores with graph-derived signals and metadata.
**Dependencies**: External – __future__.annotations, datetime.UTC, datetime.datetime, re; Internal – gateway.search.filtering.parse_iso_datetime, gateway.search.models.CoverageInfo, gateway.search.models.SearchWeights
**Related modules**: gateway/search/service.py, gateway/search/ml.py

### Classes
- `HeuristicScorer` (line 17) — Aggregates scoring signals and populates metadata for each result.
  - Methods include `build_chunk`, `lexical_score`, `base_scoring`, `apply_graph_scoring`, `populate_additional_signals`, and `compute_freshness_days`.

### Functions
- Internal helper methods normalise coverage ratios, extract subsystem criticality, and estimate path depth from graph context.

### Data Flow
- Consumes Qdrant payloads and graph context, produces weighted scores, signal dictionaries, and freshness metrics for response metadata.

### Integration Points
- Used by `SearchService`; unit tested in `tests/search/test_scoring.py`.

### Code Quality Notes
- Encapsulates previously inlined heuristics, reducing cognitive load in `SearchService` and enabling focused unit tests.


## gateway/search/ml.py

**File path**: `gateway/search/ml.py`
**Purpose**: Wrap linear model artifacts to produce ML-adjusted scores and per-feature contributions.
**Dependencies**: External – __future__.annotations, dataclasses.dataclass; Internal – gateway.search.trainer.ModelArtifact
**Related modules**: gateway/search/service.py, gateway/search/scoring.py

### Classes
- `ModelScore` (line 10) — Simple dataclass containing model score and feature contributions.
- `ModelScorer` (line 18) — Applies model coefficients when ML mode is enabled.
  - Methods: `__init__(artifact: ModelArtifact | None)`, `score(...) -> ModelScore` (line 28), `_build_features(...)`, `_apply(features: dict[str, float]) -> tuple[float, dict[str, float]]`.

### Data Flow
- Builds feature vectors from heuristic scoring signals, applies stored coefficients, and returns contributions for response metadata.

### Integration Points
- Consumed by `SearchService` when `KM_SEARCH_SCORING_MODE=ml`; behaviour validated in `tests/search/test_ml_scorer.py`.

### Code Quality Notes
- Gracefully handles missing artifacts by signalling availability; raises clear errors for schema mismatches.


## gateway/search/trainer.py

**File path**: `gateway/search/trainer.py`
**Purpose**: Training utilities for search ranking models.
**Dependencies**: External – __future__.annotations, collections.abc.Sequence, dataclasses.dataclass, datetime.UTC, datetime.datetime, json, math, numpy, pathlib.Path; Internal – gateway.search.dataset.DatasetLoadError, gateway.search.dataset.build_feature_matrix, gateway.search.dataset.load_dataset_records
**Related modules**: gateway.search.dataset.DatasetLoadError, gateway.search.dataset.build_feature_matrix, gateway.search.dataset.load_dataset_records

### Classes
- `TrainingResult` (line 29) — Capture optimiser output for debug or inspection. Inherits from object.
  - Attributes: weights: list[float], intercept: float, mse: float, r2: float, rows: int
  - Methods: None
- `ModelArtifact` (line 40) — Persisted search model metadata and coefficients. Inherits from object.
  - Attributes: model_type: str, created_at: str, feature_names: list[str], coefficients: list[float], intercept: float, metrics: dict[str, float], training_rows: int
  - Methods: None

### Functions
- `train_from_dataset(path: Path) -> ModelArtifact` (line 52) — Train a logistic regression model from the labelled dataset.
- `save_artifact(artifact: ModelArtifact, path: Path) -> None` (line 75) — Write the model artifact to disk as JSON.
- `load_artifact(path: Path) -> ModelArtifact` (line 90) — Load a saved model artifact from disk.
- `_linear_regression(X: np.ndarray, y: np.ndarray) -> TrainingResult` (line 104) — No docstring provided.

### Constants and Configuration
- FEATURE_FIELDS : Sequence[str] = ('vector_score', 'signal_subsystem_affinity', 'signal_relationship_count', 'signal_supporting_bonus', 'signal_coverage_missing', 'graph_context_present', 'metadata_graph_context_included', 'metadata_warnings_count') (line 16)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, dataclasses, datetime, json, math, numpy, pathlib

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/ui/__init__.py

**File path**: `gateway/ui/__init__.py`
**Purpose**: UI utilities and routers.
**Dependencies**: External – routes.get_static_path, routes.router; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- routes

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ui/routes.py

**File path**: `gateway/ui/routes.py`
**Purpose**: UI router exposing static assets and HTML entry points.
**Dependencies**: External – __future__.annotations, fastapi.APIRouter, fastapi.HTTPException, fastapi.Request, fastapi.responses.HTMLResponse, fastapi.responses.JSONResponse, fastapi.templating.Jinja2Templates, json, logging, pathlib.Path; Internal – gateway.config.settings.get_settings, gateway.observability.UI_EVENTS_TOTAL, gateway.observability.UI_REQUESTS_TOTAL
**Related modules**: gateway.config.settings.get_settings, gateway.observability.UI_EVENTS_TOTAL, gateway.observability.UI_REQUESTS_TOTAL

### Classes
- None

### Functions
- `get_static_path() -> Path` (line 25) — Return the absolute path to UI static assets.
- `async ui_index(request: Request) -> HTMLResponse` (line 32) — Render the landing page for the embedded UI.
- `async ui_search(request: Request) -> HTMLResponse` (line 44) — Render the search console view.
- `async ui_subsystems(request: Request) -> HTMLResponse` (line 70) — Render the subsystem explorer view.
- `async ui_lifecycle(request: Request) -> HTMLResponse` (line 86) — Render the lifecycle dashboard view.
- `async ui_lifecycle_report(request: Request) -> JSONResponse` (line 102) — Serve the lifecycle report JSON while recording UI metrics.
- `async ui_event(request: Request, payload: dict[str, object]) -> JSONResponse` (line 124) — Record a UI event for observability purposes.

### Constants and Configuration
- STATIC_DIR = Path(__file__).resolve().parent / 'static' (line 16)
- TEMPLATES_DIR = Path(__file__).resolve().parent / 'templates' (line 17)

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- fastapi, json, logging, pathlib

### Code Quality Notes
- No immediate issues detected from static scan.

## scripts/generate-changelog.py

**File path**: `scripts/generate-changelog.py`
**Purpose**: Generate changelog entries from Conventional Commits.
**Dependencies**: External – __future__.annotations, argparse, collections.defaultdict, datetime.date, pathlib.Path, subprocess, sys; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_run_git(args: list[str]) -> str` (line 25) — No docstring provided.
- `discover_commits(since: str | None) -> list[str]` (line 30) — No docstring provided.
- `categorize(commits: list[str]) -> dict[str, list[str]]` (line 36) — No docstring provided.
- `update_changelog(version: str, released: str, entries: dict[str, list[str]]) -> None` (line 46) — No docstring provided.
- `main() -> None` (line 64) — No docstring provided.

### Constants and Configuration
- ROOT = Path(__file__).resolve().parents[1] (line 12)
- CHANGELOG = ROOT / 'CHANGELOG.md' (line 13)
- CATEGORY_MAP = {'feat': 'Added', 'fix': 'Fixed', 'docs': 'Documentation', 'perf': 'Performance', 'refactor': 'Changed', 'chore': 'Chore', 'test': 'Tests'} (line 14)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- argparse, collections, datetime, pathlib, subprocess, sys

### Code Quality Notes
- 5 public element(s) lack docstrings.

## tests/__init__.py

**File path**: `tests/__init__.py`
**Purpose**: Test package for the knowledge gateway.
**Dependencies**: External – None; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- standard library only

### Code Quality Notes
- No immediate issues detected from static scan.

## tests/conftest.py

**File path**: `tests/conftest.py`
**Purpose**: Module tests/conftest.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.abc.Iterator, neo4j.GraphDatabase, os, pytest, shutil, subprocess, sys, time, types.SimpleNamespace, types.TracebackType, typing.NoReturn, uuid.uuid4, warnings; Internal – None
**Related modules**: None

### Classes
- `_NullSession` (line 50) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 51) — No method docstring provided.
    - `__enter__(self) -> _NullSession` (line 54) — No method docstring provided.
    - `__exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 57) — No method docstring provided.
    - `close(self) -> None` (line 65) — No method docstring provided.
    - `execute_read(self, func: object, *args: object, **kwargs: object) -> NoReturn` (line 68) — No method docstring provided.
    - `run(self, *args: object, **kwargs: object) -> SimpleNamespace` (line 71) — No method docstring provided.
- `_NullDriver` (line 75) — No class docstring provided. Inherits from object.
  - Methods:
    - `session(self, **kwargs: object) -> _NullSession` (line 76) — No method docstring provided.
    - `close(self) -> None` (line 79) — No method docstring provided.

### Functions
- `disable_real_graph_driver(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None` (line 84) — No docstring provided.
- `default_authentication_env(monkeypatch: pytest.MonkeyPatch) -> None` (line 149) — Provide secure default credentials so create_app() can boot under auth-on defaults.
- `neo4j_test_environment() -> Iterator[dict[str, str | None]]` (line 158) — No docstring provided.
- `pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None` (line 259) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, neo4j, os, pytest, shutil, subprocess, sys, time, types, typing, uuid, warnings

### Code Quality Notes
- 13 public element(s) lack docstrings.

## tests/mcp/test_server_tools.py

**File path**: `tests/mcp/test_server_tools.py`
**Purpose**: Integration tests for MCP server tools and metrics wiring.
**Dependencies**: External – __future__.annotations, asyncio, collections.abc.Awaitable, collections.abc.Callable, collections.abc.Iterator, pathlib.Path, prometheus_client.Counter, prometheus_client.Histogram, prometheus_client.generate_latest, pytest, typing.Any, typing.cast; Internal – gateway.mcp.config.MCPSettings, gateway.mcp.exceptions.GatewayRequestError, gateway.mcp.server.FastMCP, gateway.mcp.server.MCPServerState, gateway.mcp.server.build_server, gateway.observability.metrics.MCP_FAILURES_TOTAL, gateway.observability.metrics.MCP_REQUESTS_TOTAL, gateway.observability.metrics.MCP_REQUEST_SECONDS, gateway.observability.metrics.MCP_STORETEXT_TOTAL, gateway.observability.metrics.MCP_UPLOAD_TOTAL
**Related modules**: gateway.mcp.config.MCPSettings, gateway.mcp.exceptions.GatewayRequestError, gateway.mcp.server.FastMCP, gateway.mcp.server.MCPServerState, gateway.mcp.server.build_server, gateway.observability.metrics.MCP_FAILURES_TOTAL, gateway.observability.metrics.MCP_REQUESTS_TOTAL, gateway.observability.metrics.MCP_REQUEST_SECONDS, gateway.observability.metrics.MCP_STORETEXT_TOTAL, gateway.observability.metrics.MCP_UPLOAD_TOTAL

### Classes
- None

### Functions
- `_reset_mcp_metrics() -> Iterator[None]` (line 25) — No docstring provided.
- `mcp_server() -> Iterator[ServerFixture]` (line 40) — No docstring provided.
- `_counter_value(counter: Counter, *labels: str) -> float` (line 47) — No docstring provided.
- `_histogram_sum(histogram: Histogram, *labels: str) -> float` (line 52) — No docstring provided.
- `_upload_counter(result: str) -> float` (line 57) — No docstring provided.
- `_storetext_counter(result: str) -> float` (line 62) — No docstring provided.
- `_tool_fn(tool: object) -> ToolCallable` (line 70) — No docstring provided.
- `async test_km_help_lists_tools_and_provides_details(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 75) — No docstring provided.
- `async test_metrics_export_includes_tool_labels(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 104) — No docstring provided.
- `async test_km_search_success_records_metrics(mcp_server: ServerFixture) -> None` (line 118) — No docstring provided.
- `async test_km_search_gateway_error_records_failure(mcp_server: ServerFixture) -> None` (line 142) — No docstring provided.
- `async test_graph_tools_delegate_to_client_and_record_metrics(mcp_server: ServerFixture) -> None` (line 164) — No docstring provided.
- `async test_lifecycle_report_records_metrics(mcp_server: ServerFixture) -> None` (line 236) — No docstring provided.
- `async test_coverage_summary_records_metrics(mcp_server: ServerFixture) -> None` (line 256) — No docstring provided.
- `async test_ingest_status_handles_missing_history(mcp_server: ServerFixture) -> None` (line 276) — No docstring provided.
- `async test_ingest_trigger_succeeds(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 297) — No docstring provided.
- `async test_ingest_trigger_failure_records_metrics(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 333) — No docstring provided.
- `async test_backup_trigger(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 354) — No docstring provided.
- `async test_feedback_submit(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 374) — No docstring provided.
- `async test_km_upload_copies_file_and_records_metrics(tmp_path: Path) -> None` (line 399) — No docstring provided.
- `async test_km_upload_missing_source_raises(tmp_path: Path) -> None` (line 436) — No docstring provided.
- `async test_km_upload_requires_admin_token(tmp_path: Path) -> None` (line 463) — No docstring provided.
- `async test_km_upload_triggers_ingest_when_requested(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 490) — No docstring provided.
- `async test_km_storetext_creates_document_with_front_matter(tmp_path: Path) -> None` (line 536) — No docstring provided.
- `async test_km_storetext_requires_content(tmp_path: Path) -> None` (line 577) — No docstring provided.
- `async test_km_storetext_triggers_ingest_when_requested(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 608) — No docstring provided.
- `async test_km_storetext_requires_admin_token(tmp_path: Path) -> None` (line 657) — No docstring provided.
- `async test_mcp_smoke_run(monkeypatch: pytest.MonkeyPatch, mcp_server: ServerFixture) -> None` (line 686) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- asyncio, collections, pathlib, prometheus_client, pytest, typing

### Code Quality Notes
- 28 public element(s) lack docstrings.

## tests/mcp/test_utils_files.py

**File path**: `tests/mcp/test_utils_files.py`
**Purpose**: Module tests/mcp/test_utils_files.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pathlib.Path, pytest; Internal – gateway.mcp.utils.files
**Related modules**: gateway.mcp.utils.files

### Classes
- None

### Functions
- `test_sweep_documents_copies_supported_files(tmp_path: Path) -> None` (line 10) — No docstring provided.
- `test_sweep_documents_dry_run_reports_actions(tmp_path: Path) -> None` (line 25) — No docstring provided.
- `test_copy_into_root_prevents_traversal(tmp_path: Path) -> None` (line 36) — No docstring provided.
- `test_write_text_document_requires_content(tmp_path: Path) -> None` (line 46) — No docstring provided.
- `test_slugify_generates_fallback_when_empty() -> None` (line 54) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pathlib, pytest

### Code Quality Notes
- 5 public element(s) lack docstrings.

## tests/playwright_server.py

**File path**: `tests/playwright_server.py`
**Purpose**: Module tests/playwright_server.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, datetime.UTC, datetime.datetime, datetime.timedelta, json, os, pathlib.Path, shutil, signal, uvicorn; Internal – gateway.api.app.create_app
**Related modules**: gateway.api.app.create_app

### Classes
- None

### Functions
- `_write_json(path: Path, payload: dict) -> None` (line 15) — No docstring provided.
- `_prepare_state(state_path: Path) -> None` (line 19) — No docstring provided.
- `_configure_environment(state_path: Path) -> None` (line 147) — No docstring provided.
- `main() -> None` (line 156) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- datetime, json, os, pathlib, shutil, signal, uvicorn

### Code Quality Notes
- 4 public element(s) lack docstrings.

## tests/test_api_security.py

**File path**: `tests/test_api_security.py`
**Purpose**: Module tests/test_api_security.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, fastapi.testclient.TestClient, json, logging, pathlib.Path, pytest, typing.Any; Internal – gateway.api.app.create_app, gateway.config.settings.get_settings, gateway.get_version, gateway.graph.service.GraphService, gateway.ingest.audit.AuditLogger, gateway.ingest.pipeline.IngestionResult, gateway.search.service.SearchResponse
**Related modules**: gateway.api.app.create_app, gateway.config.settings.get_settings, gateway.get_version, gateway.graph.service.GraphService, gateway.ingest.audit.AuditLogger, gateway.ingest.pipeline.IngestionResult, gateway.search.service.SearchResponse

### Classes
- None

### Functions
- `reset_settings_cache() -> None` (line 20) — No docstring provided.
- `test_audit_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 27) — No docstring provided.
- `test_audit_history_limit_clamped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 55) — No docstring provided.
- `test_audit_history_limit_too_low_normalized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 93) — No docstring provided.
- `test_coverage_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 129) — No docstring provided.
- `test_coverage_missing_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 159) — No docstring provided.
- `test_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None` (line 176) — No docstring provided.
- `test_startup_logs_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None` (line 190) — No docstring provided.
- `test_secure_mode_without_admin_token_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 206) — No docstring provided.
- `test_secure_mode_requires_custom_neo4j_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 216) — No docstring provided.
- `test_rate_limiting_search(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 226) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- fastapi, json, logging, pathlib, pytest, typing

### Code Quality Notes
- 11 public element(s) lack docstrings.

## tests/test_app_smoke.py

**File path**: `tests/test_app_smoke.py`
**Purpose**: Module tests/test_app_smoke.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, fastapi.testclient.TestClient, json, logging, os, pathlib.Path, pytest, time, unittest.mock; Internal – gateway.api.app.create_app, gateway.api.connections.DependencyStatus, gateway.config.settings.get_settings, gateway.ingest.audit.AuditLogger
**Related modules**: gateway.api.app.create_app, gateway.api.connections.DependencyStatus, gateway.config.settings.get_settings, gateway.ingest.audit.AuditLogger

### Classes
- None

### Functions
- `reset_settings_cache() -> None` (line 20) — No docstring provided.
- `_stub_connection_managers(monkeypatch: pytest.MonkeyPatch) -> None` (line 26) — No docstring provided.
- `test_health_endpoint_reports_diagnostics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 66) — No docstring provided.
- `test_health_endpoint_ok_when_artifacts_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 86) — No docstring provided.
- `test_ready_endpoint_returns_ready() -> None` (line 113) — No docstring provided.
- `test_lifecycle_history_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 121) — No docstring provided.
- `test_requires_non_default_neo4j_password_when_auth_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 155) — No docstring provided.
- `test_requires_non_empty_neo4j_password_when_auth_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 173) — No docstring provided.
- `test_logs_warning_when_neo4j_auth_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None` (line 191) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- fastapi, json, logging, os, pathlib, pytest, time, unittest

### Code Quality Notes
- 9 public element(s) lack docstrings.

## tests/test_connection_managers.py

**File path**: `tests/test_connection_managers.py`
**Purpose**: Module tests/test_connection_managers.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, prometheus_client.Gauge, pytest, types.SimpleNamespace, unittest.mock; Internal – gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.observability.GRAPH_DEPENDENCY_LAST_SUCCESS, gateway.observability.GRAPH_DEPENDENCY_STATUS, gateway.observability.QDRANT_DEPENDENCY_LAST_SUCCESS, gateway.observability.QDRANT_DEPENDENCY_STATUS
**Related modules**: gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.observability.GRAPH_DEPENDENCY_LAST_SUCCESS, gateway.observability.GRAPH_DEPENDENCY_STATUS, gateway.observability.QDRANT_DEPENDENCY_LAST_SUCCESS, gateway.observability.QDRANT_DEPENDENCY_STATUS

### Classes
- None

### Functions
- `_reset_metric(metric: Gauge) -> None` (line 18) — No docstring provided.
- `reset_metrics() -> None` (line 23) — No docstring provided.
- `make_settings(**overrides: object) -> SimpleNamespace` (line 35) — No docstring provided.
- `_make_dummy_driver() -> mock.Mock` (line 51) — No docstring provided.
- `test_neo4j_manager_records_success_and_failure(monkeypatch: pytest.MonkeyPatch) -> None` (line 62) — No docstring provided.
- `test_qdrant_manager_handles_health_failures(monkeypatch: pytest.MonkeyPatch) -> None` (line 97) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- prometheus_client, pytest, types, unittest

### Code Quality Notes
- 6 public element(s) lack docstrings.

## tests/test_coverage_report.py

**File path**: `tests/test_coverage_report.py`
**Purpose**: Module tests/test_coverage_report.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, fastapi.testclient.TestClient, json, pathlib.Path, prometheus_client.REGISTRY, pytest; Internal – gateway.api.app.create_app, gateway.ingest.coverage.write_coverage_report, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.COVERAGE_HISTORY_SNAPSHOTS, gateway.observability.metrics.COVERAGE_LAST_RUN_STATUS, gateway.observability.metrics.COVERAGE_LAST_RUN_TIMESTAMP, gateway.observability.metrics.COVERAGE_MISSING_ARTIFACTS, gateway.observability.metrics.COVERAGE_STALE_ARTIFACTS
**Related modules**: gateway.api.app.create_app, gateway.ingest.coverage.write_coverage_report, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.COVERAGE_HISTORY_SNAPSHOTS, gateway.observability.metrics.COVERAGE_LAST_RUN_STATUS, gateway.observability.metrics.COVERAGE_LAST_RUN_TIMESTAMP, gateway.observability.metrics.COVERAGE_MISSING_ARTIFACTS, gateway.observability.metrics.COVERAGE_STALE_ARTIFACTS

### Classes
- `StubQdrantWriter` (line 64) — No class docstring provided. Inherits from object.
  - Methods:
    - `ensure_collection(self, vector_size: int) -> None` (line 65) — No method docstring provided.
    - `upsert_chunks(self, chunks: Iterable[object]) -> None` (line 68) — No method docstring provided.
- `StubNeo4jWriter` (line 72) — No class docstring provided. Inherits from object.
  - Methods:
    - `ensure_constraints(self) -> None` (line 73) — No method docstring provided.
    - `sync_artifact(self, artifact: object) -> None` (line 76) — No method docstring provided.
    - `sync_chunks(self, chunk_embeddings: Iterable[object]) -> None` (line 79) — No method docstring provided.

### Functions
- `test_write_coverage_report(tmp_path: Path) -> None` (line 23) — No docstring provided.
- `test_coverage_endpoint_after_report_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 83) — No docstring provided.
- `test_coverage_history_rotation(tmp_path: Path) -> None` (line 133) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, fastapi, json, pathlib, prometheus_client, pytest

### Code Quality Notes
- 10 public element(s) lack docstrings.

## tests/test_graph_api.py

**File path**: `tests/test_graph_api.py`
**Purpose**: Module tests/test_graph_api.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, fastapi.FastAPI, fastapi.testclient.TestClient, neo4j.GraphDatabase, os, pathlib.Path, pytest, typing.Any; Internal – gateway.api.app.create_app, gateway.graph.GraphNotFoundError, gateway.graph.migrations.runner.MigrationRunner, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline
**Related modules**: gateway.api.app.create_app, gateway.graph.GraphNotFoundError, gateway.graph.migrations.runner.MigrationRunner, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline

### Classes
- `DummyGraphService` (line 19) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, responses: dict[str, Any]) -> None` (line 20) — No method docstring provided.
    - `get_subsystem(self, name: str, **kwargs: object) -> dict[str, Any]` (line 24) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 29) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 35) — No method docstring provided.
    - `get_subsystem_graph(self, name: str, depth: int) -> dict[str, Any]` (line 38) — No method docstring provided.
    - `list_orphan_nodes(self, label: str | None, cursor: str | None, limit: int) -> dict[str, Any]` (line 41) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 44) — No method docstring provided.

### Functions
- `app(monkeypatch: pytest.MonkeyPatch) -> FastAPI` (line 49) — No docstring provided.
- `test_graph_subsystem_returns_payload(app: FastAPI) -> None` (line 165) — No docstring provided.
- `test_graph_subsystem_not_found(app: FastAPI) -> None` (line 179) — No docstring provided.
- `test_graph_subsystem_graph_endpoint(app: FastAPI) -> None` (line 185) — No docstring provided.
- `test_graph_orphans_endpoint(app: FastAPI) -> None` (line 194) — No docstring provided.
- `test_graph_node_endpoint(app: FastAPI) -> None` (line 202) — No docstring provided.
- `test_graph_node_accepts_slash_encoded_ids(app: FastAPI) -> None` (line 211) — No docstring provided.
- `test_graph_node_endpoint_live(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None` (line 220) — No docstring provided.
- `test_graph_search_endpoint_live(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None` (line 266) — No docstring provided.
- `test_graph_search_endpoint(app: FastAPI) -> None` (line 312) — No docstring provided.
- `test_graph_cypher_requires_maintainer_token(monkeypatch: pytest.MonkeyPatch) -> None` (line 319) — No docstring provided.
- `test_graph_reader_scope(monkeypatch: pytest.MonkeyPatch) -> None` (line 345) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- fastapi, neo4j, os, pathlib, pytest, typing

### Code Quality Notes
- 20 public element(s) lack docstrings.

## tests/test_graph_auto_migrate.py

**File path**: `tests/test_graph_auto_migrate.py`
**Purpose**: Module tests/test_graph_auto_migrate.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, neo4j.exceptions.Neo4jError, prometheus_client.REGISTRY, pytest, unittest.mock; Internal – gateway.api.app.create_app, gateway.api.connections.DependencyStatus, gateway.observability.metrics.GRAPH_MIGRATION_LAST_STATUS, gateway.observability.metrics.GRAPH_MIGRATION_LAST_TIMESTAMP
**Related modules**: gateway.api.app.create_app, gateway.api.connections.DependencyStatus, gateway.observability.metrics.GRAPH_MIGRATION_LAST_STATUS, gateway.observability.metrics.GRAPH_MIGRATION_LAST_TIMESTAMP

### Classes
- None

### Functions
- `reset_settings_cache() -> None` (line 15) — No docstring provided.
- `reset_migration_metrics() -> None` (line 24) — No docstring provided.
- `_metric(name: str) -> float | None` (line 32) — No docstring provided.
- `_stub_managers(monkeypatch: pytest.MonkeyPatch, driver: mock.Mock | None = None, qdrant_client: mock.Mock | None = None, write_driver_error: Exception | None = None) -> tuple[mock.Mock, mock.Mock]` (line 37) — No docstring provided.
- `test_auto_migrate_runs_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None` (line 127) — No docstring provided.
- `test_auto_migrate_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None` (line 150) — No docstring provided.
- `test_auto_migrate_records_failure(monkeypatch: pytest.MonkeyPatch) -> None` (line 167) — No docstring provided.
- `test_missing_database_disables_graph_driver(monkeypatch: pytest.MonkeyPatch) -> None` (line 190) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- neo4j, prometheus_client, pytest, unittest

### Code Quality Notes
- 8 public element(s) lack docstrings.

## tests/test_graph_cli.py

**File path**: `tests/test_graph_cli.py`
**Purpose**: Module tests/test_graph_cli.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pytest, unittest.mock; Internal – gateway.graph.cli
**Related modules**: gateway.graph.cli

### Classes
- `DummySettings` (line 10) — No class docstring provided. Inherits from object.
  - Attributes: neo4j_uri = 'bolt://dummy', neo4j_user = 'neo4j', neo4j_password = 'password', neo4j_database = 'knowledge'
  - Methods: None

### Functions
- `test_graph_cli_migrate_runs_runner(monkeypatch: pytest.MonkeyPatch) -> None` (line 17) — No docstring provided.
- `test_graph_cli_dry_run_prints_pending(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 33) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pytest, unittest

### Code Quality Notes
- 3 public element(s) lack docstrings.

## tests/test_graph_database_validation.py

**File path**: `tests/test_graph_database_validation.py`
**Purpose**: Module tests/test_graph_database_validation.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, neo4j.exceptions.ClientError, unittest.mock; Internal – gateway.api.app
**Related modules**: gateway.api.app

### Classes
- None

### Functions
- `test_verify_graph_database_returns_false_when_database_missing() -> None` (line 10) — No docstring provided.
- `test_verify_graph_database_returns_true_on_success() -> None` (line 26) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- neo4j, unittest

### Code Quality Notes
- 2 public element(s) lack docstrings.

## tests/test_graph_migrations.py

**File path**: `tests/test_graph_migrations.py`
**Purpose**: Module tests/test_graph_migrations.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, collections.deque, types.TracebackType; Internal – gateway.graph.migrations.runner.MIGRATIONS, gateway.graph.migrations.runner.MigrationRunner
**Related modules**: gateway.graph.migrations.runner.MIGRATIONS, gateway.graph.migrations.runner.MigrationRunner

### Classes
- `FakeResult` (line 9) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, record: dict[str, object] | None = None) -> None` (line 10) — No method docstring provided.
    - `single(self) -> dict[str, object] | None` (line 13) — No method docstring provided.
- `FakeTransaction` (line 17) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, applied_ids: set[str], results: deque[tuple[str, dict[str, object]]]) -> None` (line 18) — No method docstring provided.
    - `run(self, query: str, **params: object) -> FakeResult` (line 22) — No method docstring provided.
    - `commit(self) -> None` (line 28) — No method docstring provided.
    - `rollback(self) -> None` (line 31) — No method docstring provided.
    - `__enter__(self) -> FakeTransaction` (line 34) — No method docstring provided.
    - `__exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool` (line 37) — No method docstring provided.
- `FakeSession` (line 46) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, applied_ids: set[str], records: deque[tuple[str, dict[str, object]]]) -> None` (line 47) — No method docstring provided.
    - `run(self, query: str, **params: object) -> FakeResult` (line 51) — No method docstring provided.
    - `begin_transaction(self) -> FakeTransaction` (line 62) — No method docstring provided.
    - `close(self) -> None` (line 65) — No method docstring provided.
    - `__enter__(self) -> FakeSession` (line 68) — No method docstring provided.
    - `__exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool` (line 71) — No method docstring provided.
- `FakeDriver` (line 80) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 81) — No method docstring provided.
    - `session(self, database: str) -> FakeSession` (line 85) — No method docstring provided.
    - `close(self) -> None` (line 88) — No method docstring provided.

### Functions
- `test_migration_runner_applies_pending_migrations() -> None` (line 92) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, types

### Code Quality Notes
- 22 public element(s) lack docstrings.

## tests/test_graph_service_startup.py

**File path**: `tests/test_graph_service_startup.py`
**Purpose**: Module tests/test_graph_service_startup.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, fastapi.FastAPI, fastapi.HTTPException, pytest, starlette.requests.Request, unittest.mock; Internal – gateway.api.app.create_app
**Related modules**: gateway.api.app.create_app

### Classes
- None

### Functions
- `reset_settings_cache() -> None` (line 13) — No docstring provided.
- `set_state_path(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None` (line 22) — No docstring provided.
- `async _receive() -> dict[str, object]` (line 26) — No docstring provided.
- `_make_request(app: FastAPI) -> Request` (line 30) — No docstring provided.
- `test_graph_dependency_returns_503_when_database_missing(monkeypatch: pytest.MonkeyPatch) -> None` (line 41) — No docstring provided.
- `test_graph_dependency_returns_service_when_available(monkeypatch: pytest.MonkeyPatch) -> None` (line 62) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- fastapi, pytest, starlette, unittest

### Code Quality Notes
- 6 public element(s) lack docstrings.

## tests/test_graph_service_unit.py

**File path**: `tests/test_graph_service_unit.py`
**Purpose**: Module tests/test_graph_service_unit.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, collections.abc.Callable, collections.abc.Iterable, pytest, types.SimpleNamespace, types.TracebackType, unittest.mock; Internal – gateway.graph.service, gateway.graph.service.GraphNotFoundError, gateway.graph.service.GraphQueryError, gateway.graph.service.GraphService, gateway.observability.metrics.GRAPH_CYPHER_DENIED_TOTAL
**Related modules**: gateway.graph.service, gateway.graph.service.GraphNotFoundError, gateway.graph.service.GraphQueryError, gateway.graph.service.GraphService, gateway.observability.metrics.GRAPH_CYPHER_DENIED_TOTAL

### Classes
- `DummyNode` (line 28) — No class docstring provided. Inherits from dict[str, object].
  - Methods:
    - `__init__(self, labels: Iterable[str], element_id: str, **props: object) -> None` (line 29) — No method docstring provided.
- `DummyRelationship` (line 35) — No class docstring provided. Inherits from dict[str, object].
  - Methods:
    - `__init__(self, start_node: DummyNode, end_node: DummyNode, rel_type: str, **props: object) -> None` (line 36) — No method docstring provided.
- `DummySession` (line 49) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 50) — No method docstring provided.
    - `__enter__(self) -> DummySession` (line 56) — No method docstring provided.
    - `__exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 59) — No method docstring provided.
    - `execute_read(self, func: Callable[..., object], *args: object, **kwargs: object) -> object` (line 67) — No method docstring provided.
    - `run(self, query: str, **params: object) -> SimpleNamespace` (line 70) — No method docstring provided.
- `DummyDriver` (line 75) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, session: DummySession) -> None` (line 76) — No method docstring provided.
    - `session(self, **kwargs: object) -> DummySession` (line 88) — No method docstring provided.
    - `execute_query(self, query: str, parameters: dict[str, object], database_: str) -> SimpleNamespace` (line 91) — No method docstring provided.

### Functions
- `_reset_metric(reason: str) -> None` (line 16) — No docstring provided.
- `_metric_value(reason: str) -> float` (line 23) — No docstring provided.
- `patch_graph_types(monkeypatch: pytest.MonkeyPatch) -> None` (line 102) — No docstring provided.
- `dummy_driver() -> DriverFixture` (line 108) — No docstring provided.
- `test_get_subsystem_paginates_and_includes_artifacts(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 119) — No docstring provided.
- `test_get_subsystem_missing_raises(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 167) — No docstring provided.
- `test_get_subsystem_graph_returns_nodes_and_edges(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 182) — No docstring provided.
- `test_fetch_subsystem_paths_inlines_depth_literal(monkeypatch: pytest.MonkeyPatch) -> None` (line 221) — No docstring provided.
- `test_get_node_with_relationships(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 233) — No docstring provided.
- `test_list_orphan_nodes_rejects_unknown_label(dummy_driver: DriverFixture) -> None` (line 268) — No docstring provided.
- `test_list_orphan_nodes_serializes_results(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 274) — No docstring provided.
- `test_get_node_missing_raises(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 295) — No docstring provided.
- `test_search_serializes_results(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 310) — No docstring provided.
- `test_shortest_path_depth(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 331) — No docstring provided.
- `test_shortest_path_depth_none(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 346) — No docstring provided.
- `test_run_cypher_serializes_records(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` (line 354) — No docstring provided.
- `test_run_cypher_rejects_non_read_queries(dummy_driver: DriverFixture) -> None` (line 382) — No docstring provided.
- `test_run_cypher_rejects_updates_detected_in_counters(dummy_driver: DriverFixture) -> None` (line 394) — No docstring provided.
- `test_run_cypher_allows_whitelisted_procedure(dummy_driver: DriverFixture) -> None` (line 414) — No docstring provided.
- `test_run_cypher_rejects_disallowed_procedure(dummy_driver: DriverFixture) -> None` (line 435) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, pytest, types, unittest

### Code Quality Notes
- 34 public element(s) lack docstrings.

## tests/test_graph_validation.py

**File path**: `tests/test_graph_validation.py`
**Purpose**: End-to-end validation of ingestion and graph-backed search.
**Dependencies**: External – __future__.annotations, collections.abc.Sequence, neo4j.GraphDatabase, os, pathlib.Path, pytest, qdrant_client.QdrantClient, typing.cast; Internal – gateway.graph.migrations.runner.MigrationRunner, gateway.graph.service.get_graph_service, gateway.ingest.embedding.Embedder, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.search.SearchService
**Related modules**: gateway.graph.migrations.runner.MigrationRunner, gateway.graph.service.get_graph_service, gateway.ingest.embedding.Embedder, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.search.SearchService

### Classes
- `_DummyEmbedder` (line 120) — Minimal embedder returning deterministic vectors for tests. Inherits from Embedder.
  - Methods:
    - `__init__(self) -> None` (line 123) — No method docstring provided.
    - `dimension(self) -> int` (line 127) — No method docstring provided.
    - `encode(self, texts: Sequence[str]) -> list[list[float]]` (line 130) — No method docstring provided.
- `_FakePoint` (line 134) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, payload: dict[str, object], score: float) -> None` (line 135) — No method docstring provided.
- `_DummyQdrantClient` (line 140) — Stub Qdrant client that returns pre-seeded points. Inherits from object.
  - Methods:
    - `__init__(self, points: list[_FakePoint]) -> None` (line 143) — No method docstring provided.
    - `search(self, **_kwargs: object) -> list[_FakePoint]` (line 146) — No method docstring provided.

### Functions
- `test_ingestion_populates_graph(tmp_path: Path) -> None` (line 23) — Run ingestion and verify graph nodes, edges, and metadata.
- `test_search_replay_against_real_graph(tmp_path: Path) -> None` (line 151) — Replay saved search results against the populated knowledge graph.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Interacts with Qdrant collections for vector search or persistence.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, neo4j, os, pathlib, pytest, qdrant_client, typing

### Code Quality Notes
- 7 public element(s) lack docstrings.

## tests/test_ingest_cli.py

**File path**: `tests/test_ingest_cli.py`
**Purpose**: Module tests/test_ingest_cli.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pathlib.Path, pytest, time, unittest.mock; Internal – gateway.config.settings.get_settings, gateway.ingest.audit.AuditLogger, gateway.ingest.cli, gateway.ingest.pipeline.IngestionResult
**Related modules**: gateway.config.settings.get_settings, gateway.ingest.audit.AuditLogger, gateway.ingest.cli, gateway.ingest.pipeline.IngestionResult

### Classes
- None

### Functions
- `reset_settings_cache() -> None` (line 16) — No docstring provided.
- `sample_repo(tmp_path: Path) -> Path` (line 22) — No docstring provided.
- `test_cli_rebuild_dry_run(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 31) — No docstring provided.
- `test_cli_rebuild_requires_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 50) — No docstring provided.
- `test_cli_rebuild_with_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 60) — No docstring provided.
- `test_cli_rebuild_full_rebuild_flag(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 75) — No docstring provided.
- `test_cli_rebuild_incremental_flag(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 85) — No docstring provided.
- `test_cli_audit_history_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 99) — No docstring provided.
- `test_cli_audit_history_limit_clamped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 123) — No docstring provided.
- `test_cli_audit_history_no_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 153) — No docstring provided.
- `test_audit_logger_recent_normalizes_limit(tmp_path: Path) -> None` (line 163) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pathlib, pytest, time, unittest

### Code Quality Notes
- 9 public element(s) lack docstrings.

## tests/test_ingest_pipeline.py

**File path**: `tests/test_ingest_pipeline.py`
**Purpose**: Module tests/test_ingest_pipeline.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, pathlib.Path, prometheus_client.REGISTRY, pytest; Internal – gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.ingest.pipeline.IngestionResult
**Related modules**: gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.ingest.pipeline.IngestionResult

### Classes
- `StubQdrantWriter` (line 12) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 13) — No method docstring provided.
    - `ensure_collection(self, vector_size: int) -> None` (line 18) — No method docstring provided.
    - `upsert_chunks(self, chunks: Iterable[object]) -> None` (line 21) — No method docstring provided.
    - `delete_artifact(self, artifact_path: str) -> None` (line 24) — No method docstring provided.
- `StubNeo4jWriter` (line 33) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 34) — No method docstring provided.
    - `ensure_constraints(self) -> None` (line 39) — No method docstring provided.
    - `sync_artifact(self, artifact: object) -> None` (line 42) — No method docstring provided.
    - `sync_chunks(self, chunk_embeddings: Iterable[object]) -> None` (line 45) — No method docstring provided.
    - `delete_artifact(self, path: str) -> None` (line 49) — No method docstring provided.

### Functions
- `_metric_value(name: str, labels: dict[str, str]) -> float` (line 28) — No docstring provided.
- `sample_repo(tmp_path: Path) -> Path` (line 54) — No docstring provided.
- `test_pipeline_generates_chunks(sample_repo: Path) -> None` (line 65) — No docstring provided.
- `test_pipeline_removes_stale_artifacts(tmp_path: Path) -> None` (line 86) — No docstring provided.
- `test_pipeline_skips_unchanged_artifacts(tmp_path: Path) -> None` (line 136) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, pathlib, prometheus_client, pytest

### Code Quality Notes
- 16 public element(s) lack docstrings.

## tests/test_km_watch.py

**File path**: `tests/test_km_watch.py`
**Purpose**: Module tests/test_km_watch.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, os, pathlib.Path, prometheus_client.REGISTRY, runpy, sys; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_metric_value(name: str, labels: dict[str, str]) -> float` (line 15) — No docstring provided.
- `test_compute_fingerprints(tmp_path: Path) -> None` (line 24) — No docstring provided.
- `test_diff_fingerprints_detects_changes() -> None` (line 33) — No docstring provided.
- `test_watch_metrics_increment(tmp_path: Path) -> None` (line 44) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- os, pathlib, prometheus_client, runpy, sys

### Code Quality Notes
- 4 public element(s) lack docstrings.

## tests/test_lifecycle_cli.py

**File path**: `tests/test_lifecycle_cli.py`
**Purpose**: Module tests/test_lifecycle_cli.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, json, pathlib.Path, pytest; Internal – gateway.lifecycle.cli.main
**Related modules**: gateway.lifecycle.cli.main

### Classes
- None

### Functions
- `test_lifecycle_cli_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None` (line 11) — No docstring provided.
- `test_lifecycle_cli_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None` (line 26) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- json, pathlib, pytest

### Code Quality Notes
- 2 public element(s) lack docstrings.

## tests/test_lifecycle_report.py

**File path**: `tests/test_lifecycle_report.py`
**Purpose**: Unit tests for lifecycle report generation and graph enrichment.
**Dependencies**: External – __future__.annotations, datetime.UTC, datetime.datetime, json, pathlib.Path, prometheus_client.REGISTRY, pytest, typing.cast; Internal – gateway.graph.GraphService, gateway.ingest.lifecycle.LifecycleConfig, gateway.ingest.lifecycle.write_lifecycle_report, gateway.ingest.pipeline.IngestionResult
**Related modules**: gateway.graph.GraphService, gateway.ingest.lifecycle.LifecycleConfig, gateway.ingest.lifecycle.write_lifecycle_report, gateway.ingest.pipeline.IngestionResult

### Classes
- `DummyGraphService` (line 18) — Test double that returns pre-seeded orphan graph nodes. Inherits from object.
  - Methods:
    - `__init__(self, pages: dict[str, list[list[dict[str, object]]]]) -> None` (line 21) — No method docstring provided.
    - `list_orphan_nodes(self, label: str | None, cursor: str | None, limit: int) -> dict[str, object]` (line 24) — Yield nodes in pages for the requested label.

### Functions
- `_ingestion_result() -> IngestionResult` (line 49) — Build a representative ingestion result for lifecycle reporting tests.
- `test_write_lifecycle_report_without_graph(tmp_path: Path, ingestion_result: IngestionResult) -> None` (line 98) — Reports render correctly when graph enrichment is disabled.
- `test_write_lifecycle_report_with_graph(tmp_path: Path, ingestion_result: IngestionResult) -> None` (line 132) — Graph enrichment populates isolated node information in the payload.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- datetime, json, pathlib, prometheus_client, pytest, typing

### Code Quality Notes
- 1 public element(s) lack docstrings.

## tests/test_mcp_recipes.py

**File path**: `tests/test_mcp_recipes.py`
**Purpose**: Module tests/test_mcp_recipes.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, json, pathlib.Path, pytest; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `test_snippets_are_valid_json(snippet: str) -> None` (line 19) — No docstring provided.

### Constants and Configuration
- RECIPES = Path('docs/MCP_RECIPES.md').read_text() (line 8)

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- json, pathlib, pytest

### Code Quality Notes
- 1 public element(s) lack docstrings.

## tests/test_mcp_smoke_recipes.py

**File path**: `tests/test_mcp_smoke_recipes.py`
**Purpose**: Module tests/test_mcp_smoke_recipes.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, json, pathlib.Path, pytest; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_recipe_params() -> list[pytest.ParameterSet]` (line 11) — No docstring provided.
- `test_recipe_lines_are_valid_json(line: str) -> None` (line 21) — No docstring provided.

### Constants and Configuration
- RECIPES = Path('docs/MCP_RECIPES.md').read_text().splitlines() (line 8)

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- json, pathlib, pytest

### Code Quality Notes
- 2 public element(s) lack docstrings.

## tests/test_neo4j_writer.py

**File path**: `tests/test_neo4j_writer.py`
**Purpose**: Unit tests for the lightweight Neo4j writer integration layer.
**Dependencies**: External – __future__.annotations, neo4j.Driver, pathlib.Path, types.SimpleNamespace, types.TracebackType, typing.Any, typing.cast; Internal – gateway.ingest.artifacts.Artifact, gateway.ingest.artifacts.Chunk, gateway.ingest.artifacts.ChunkEmbedding, gateway.ingest.neo4j_writer.Neo4jWriter
**Related modules**: gateway.ingest.artifacts.Artifact, gateway.ingest.artifacts.Chunk, gateway.ingest.artifacts.ChunkEmbedding, gateway.ingest.neo4j_writer.Neo4jWriter

### Classes
- `RecordingSession` (line 15) — Stubbed session that records Cypher queries for assertions. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 18) — No method docstring provided.
    - `run(self, query: str, **params: object) -> SimpleNamespace` (line 21) — No method docstring provided.
    - `__enter__(self) -> RecordingSession` (line 25) — No method docstring provided.
    - `__exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 28) — No method docstring provided.
- `RecordingDriver` (line 37) — Stubbed driver that yields recording sessions. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 40) — No method docstring provided.
    - `session(self, database: str | None = None) -> RecordingSession` (line 43) — Return a new recording session; database name is ignored.

### Functions
- `_make_writer() -> tuple[Neo4jWriter, RecordingDriver]` (line 51) — Create a writer bound to a recording driver for inspection.
- `test_sync_artifact_creates_domain_relationships() -> None` (line 58) — Artifacts trigger the expected Cypher commands and relationships.
- `test_sync_artifact_merges_subsystem_edge_once() -> None` (line 108) — Syncing an artifact does not duplicate the subsystem relationship.
- `test_sync_chunks_links_chunk_to_artifact() -> None` (line 129) — Chunk synchronization creates chunk nodes and linking edges.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- neo4j, pathlib, types, typing

### Code Quality Notes
- 5 public element(s) lack docstrings.

## tests/test_qdrant_writer.py

**File path**: `tests/test_qdrant_writer.py`
**Purpose**: Module tests/test_qdrant_writer.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, httpx, pytest, qdrant_client.http.exceptions.UnexpectedResponse, unittest.mock; Internal – gateway.ingest.qdrant_writer.QdrantWriter
**Related modules**: gateway.ingest.qdrant_writer.QdrantWriter

### Classes
- None

### Functions
- `stub_qdrant_models(monkeypatch: pytest.MonkeyPatch) -> None` (line 13) — No docstring provided.
- `build_client(**kwargs: object) -> mock.Mock` (line 23) — No docstring provided.
- `test_ensure_collection_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None` (line 35) — No docstring provided.
- `test_ensure_collection_noop_when_collection_exists() -> None` (line 46) — No docstring provided.
- `test_ensure_collection_retries_on_transient_failure(monkeypatch: pytest.MonkeyPatch) -> None` (line 56) — No docstring provided.
- `test_ensure_collection_handles_conflict() -> None` (line 72) — No docstring provided.
- `test_reset_collection_invokes_recreate() -> None` (line 84) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Interacts with Qdrant collections for vector search or persistence.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- httpx, pytest, qdrant_client, unittest

### Code Quality Notes
- 7 public element(s) lack docstrings.

## tests/test_recipes_executor.py

**File path**: `tests/test_recipes_executor.py`
**Purpose**: Module tests/test_recipes_executor.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pathlib.Path, pytest, types.TracebackType, typing.Any; Internal – gateway.mcp.config.MCPSettings, gateway.recipes.executor.RecipeExecutionError, gateway.recipes.executor.RecipeRunner, gateway.recipes.models.Recipe
**Related modules**: gateway.mcp.config.MCPSettings, gateway.recipes.executor.RecipeExecutionError, gateway.recipes.executor.RecipeRunner, gateway.recipes.models.Recipe

### Classes
- `FakeToolExecutor` (line 14) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, responses: dict[str, list[Any] | Any]) -> None` (line 15) — No method docstring provided.
    - `async __aenter__(self) -> FakeToolExecutor` (line 19) — No method docstring provided.
    - `async __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 22) — No method docstring provided.
    - `async call(self, tool: str, params: dict[str, object]) -> object` (line 25) — No method docstring provided.

### Functions
- `async test_recipe_runner_success(tmp_path: Path) -> None` (line 39) — No docstring provided.
- `async test_recipe_runner_wait(tmp_path: Path) -> None` (line 66) — No docstring provided.
- `async test_recipe_runner_expect_failure(tmp_path: Path) -> None` (line 103) — No docstring provided.
- `async test_recipe_runner_dry_run(tmp_path: Path) -> None` (line 126) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pathlib, pytest, types, typing

### Code Quality Notes
- 9 public element(s) lack docstrings.

## tests/test_release_scripts.py

**File path**: `tests/test_release_scripts.py`
**Purpose**: Module tests/test_release_scripts.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, os, pathlib.Path, subprocess; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_env_with_venv() -> dict[str, str]` (line 11) — No docstring provided.
- `test_build_wheel_script(tmp_path: Path) -> None` (line 19) — No docstring provided.
- `test_checksums_script(tmp_path: Path) -> None` (line 32) — No docstring provided.
- `test_generate_changelog(tmp_path: Path) -> None` (line 54) — No docstring provided.

### Constants and Configuration
- REPO_ROOT = Path(__file__).resolve().parents[1] (line 7)
- SCRIPTS_DIR = REPO_ROOT / 'scripts' (line 8)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- os, pathlib, subprocess

### Code Quality Notes
- 4 public element(s) lack docstrings.

## tests/test_scheduler.py

**File path**: `tests/test_scheduler.py`
**Purpose**: Unit tests exercising the ingestion scheduler behaviour and metrics.
**Dependencies**: External – __future__.annotations, apscheduler.triggers.cron.CronTrigger, apscheduler.triggers.interval.IntervalTrigger, collections.abc.Generator, filelock.Timeout, os, pathlib.Path, prometheus_client.REGISTRY, pytest, unittest.mock; Internal – gateway.backup.exceptions.BackupExecutionError, gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.BACKUP_LAST_STATUS, gateway.scheduler.IngestionScheduler
**Related modules**: gateway.backup.exceptions.BackupExecutionError, gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.BACKUP_LAST_STATUS, gateway.scheduler.IngestionScheduler

### Classes
- None

### Functions
- `reset_cache() -> Generator[None, None, None]` (line 26) — Clear cached settings before and after each test.
- `scheduler_settings(tmp_path: Path) -> AppSettings` (line 34) — Provide scheduler settings pointing at a temporary repo.
- `make_scheduler(settings: AppSettings) -> IngestionScheduler` (line 50) — Instantiate a scheduler with its APScheduler stubbed out.
- `_metric_value(name: str, labels: dict[str, str] | None = None) -> float` (line 57) — Fetch a Prometheus sample value with defaults for missing metrics.
- `make_result(head: str) -> IngestionResult` (line 63) — Construct a minimal ingestion result for scheduler tests.
- `test_scheduler_skips_when_repo_head_unchanged(scheduler_settings: AppSettings) -> None` (line 77) — Scheduler skips when repository head hash matches the cached value.
- `test_scheduler_runs_when_repo_head_changes(scheduler_settings: AppSettings) -> None` (line 106) — Scheduler triggers ingestion when the repository head changes.
- `test_scheduler_start_uses_interval_trigger(scheduler_settings: AppSettings) -> None` (line 123) — Schedulers without cron use the configured interval trigger.
- `test_scheduler_start_uses_cron_trigger(tmp_path: Path) -> None` (line 133) — Cron expressions configure a cron trigger instead of interval.
- `test_scheduler_schedules_backup_job(tmp_path: Path) -> None` (line 152) — Standalone backup schedules a job even when ingestion is disabled.
- `test_scheduler_backup_run_records_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 174) — Backup job updates metrics and retention tracking.
- `test_scheduler_backup_failure_records_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 222) — Failures set the status gauge and increment failure counters.
- `test_scheduler_skips_when_lock_contended(scheduler_settings: AppSettings) -> None` (line 252) — Lock contention causes the scheduler to skip runs and record metrics.
- `test_scheduler_requires_maintainer_token(tmp_path: Path) -> None` (line 270) — Schedulers skip setup when auth is enabled without a maintainer token.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Schedules background jobs using APScheduler.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- apscheduler, collections, filelock, os, pathlib, prometheus_client, pytest, unittest

### Code Quality Notes
- No immediate issues detected from static scan.

## tests/test_search_api.py

**File path**: `tests/test_search_api.py`
**Purpose**: Module tests/test_search_api.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, datetime.datetime, fastapi.testclient.TestClient, json, pathlib.Path, pytest; Internal – gateway.api.app.create_app, gateway.search.service.SearchResponse, gateway.search.service.SearchResult
**Related modules**: gateway.api.app.create_app, gateway.search.service.SearchResponse, gateway.search.service.SearchResult

### Classes
- `DummySearchService` (line 14) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self) -> None` (line 15) — No method docstring provided.
    - `search(self, query: str, limit: int, include_graph: bool, graph_service: object, sort_by_vector: bool = False, request_id: str | None = None, filters: dict[str, object] | None = None) -> SearchResponse` (line 18) — No method docstring provided.

### Functions
- `test_search_endpoint_returns_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 59) — No docstring provided.
- `test_search_reuses_incoming_request_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 83) — No docstring provided.
- `test_search_requires_reader_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 106) — No docstring provided.
- `test_search_allows_maintainer_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 131) — No docstring provided.
- `test_search_feedback_logged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 153) — No docstring provided.
- `test_search_filters_passed_to_service(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 186) — No docstring provided.
- `test_search_filters_invalid_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 224) — No docstring provided.
- `test_search_filters_invalid_namespaces(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 244) — No docstring provided.
- `test_search_filters_invalid_updated_after(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 264) — No docstring provided.
- `test_search_filters_invalid_max_age(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 284) — No docstring provided.
- `test_search_weights_endpoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 304) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- datetime, fastapi, json, pathlib, pytest

### Code Quality Notes
- 14 public element(s) lack docstrings.

## tests/test_search_cli_show_weights.py

**File path**: `tests/test_search_cli_show_weights.py`
**Purpose**: Module tests/test_search_cli_show_weights.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pathlib.Path, pytest; Internal – gateway.search.cli
**Related modules**: gateway.search.cli

### Classes
- None

### Functions
- `clear_settings_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 11) — No docstring provided.
- `test_show_weights_command(capsys: pytest.CaptureFixture[str]) -> None` (line 20) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pathlib, pytest

### Code Quality Notes
- 2 public element(s) lack docstrings.

## tests/test_search_evaluation.py

**File path**: `tests/test_search_evaluation.py`
**Purpose**: Module tests/test_search_evaluation.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, json, math, pathlib.Path, pytest; Internal – gateway.search.cli.evaluate_trained_model, gateway.search.dataset.DatasetLoadError, gateway.search.evaluation.evaluate_model
**Related modules**: gateway.search.cli.evaluate_trained_model, gateway.search.dataset.DatasetLoadError, gateway.search.evaluation.evaluate_model

### Classes
- None

### Functions
- `test_evaluate_model(tmp_path: Path) -> None` (line 14) — No docstring provided.
- `test_evaluate_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 25) — No docstring provided.
- `test_evaluate_model_with_empty_dataset(tmp_path: Path) -> None` (line 38) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- json, math, pathlib, pytest

### Code Quality Notes
- 3 public element(s) lack docstrings.

## tests/test_search_exporter.py

**File path**: `tests/test_search_exporter.py`
**Purpose**: Module tests/test_search_exporter.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, csv, json, pathlib.Path, pytest; Internal – gateway.config.settings.get_settings, gateway.search.cli.export_training_data, gateway.search.cli.train_model, gateway.search.exporter.ExportOptions, gateway.search.exporter.export_training_dataset, gateway.search.trainer.train_from_dataset
**Related modules**: gateway.config.settings.get_settings, gateway.search.cli.export_training_data, gateway.search.cli.train_model, gateway.search.exporter.ExportOptions, gateway.search.exporter.export_training_dataset, gateway.search.trainer.train_from_dataset

### Classes
- None

### Functions
- `_write_events(path: Path, events: list[dict[str, object]]) -> None` (line 15) — No docstring provided.
- `_sample_event(request_id: str, vote: float | None) -> dict[str, object]` (line 20) — No docstring provided.
- `test_export_training_dataset_csv(tmp_path: Path) -> None` (line 50) — No docstring provided.
- `test_export_training_data_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 70) — No docstring provided.
- `test_train_model_from_dataset(tmp_path: Path) -> None` (line 94) — No docstring provided.
- `test_train_model_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 117) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- csv, json, pathlib, pytest

### Code Quality Notes
- 6 public element(s) lack docstrings.

## tests/test_search_feedback.py

**File path**: `tests/test_search_feedback.py`
**Purpose**: Module tests/test_search_feedback.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pathlib.Path, pytest, typing.Any; Internal – gateway.observability.metrics.SEARCH_FEEDBACK_LOG_BYTES, gateway.observability.metrics.SEARCH_FEEDBACK_ROTATIONS_TOTAL, gateway.search.feedback.SearchFeedbackStore, gateway.search.service.SearchResponse, gateway.search.service.SearchResult
**Related modules**: gateway.observability.metrics.SEARCH_FEEDBACK_LOG_BYTES, gateway.observability.metrics.SEARCH_FEEDBACK_ROTATIONS_TOTAL, gateway.search.feedback.SearchFeedbackStore, gateway.search.service.SearchResponse, gateway.search.service.SearchResult

### Classes
- None

### Functions
- `_make_response(query: str, note: str) -> SearchResponse` (line 16) — No docstring provided.
- `test_feedback_store_writes_entries(tmp_path: Path) -> None` (line 44) — No docstring provided.
- `test_feedback_store_rotates_when_threshold_exceeded(tmp_path: Path) -> None` (line 55) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pathlib, pytest, typing

### Code Quality Notes
- 3 public element(s) lack docstrings.

## tests/test_search_maintenance.py

**File path**: `tests/test_search_maintenance.py`
**Purpose**: Tests for the search maintenance helpers.
**Dependencies**: External – __future__.annotations, datetime.UTC, datetime.datetime, datetime.timedelta, json, os, pathlib.Path, pytest, stat; Internal – gateway.search.maintenance.PruneOptions, gateway.search.maintenance.RedactOptions, gateway.search.maintenance.prune_feedback_log, gateway.search.maintenance.redact_dataset
**Related modules**: gateway.search.maintenance.PruneOptions, gateway.search.maintenance.RedactOptions, gateway.search.maintenance.prune_feedback_log, gateway.search.maintenance.redact_dataset

### Classes
- None

### Functions
- `_write_events(path: Path, requests: list[tuple[str, datetime, list[dict[str, object]]]]) -> None` (line 16) — Write JSON lines representing feedback events for the supplied requests.
- `test_prune_feedback_log_parses_various_timestamp_formats(tmp_path: Path) -> None` (line 34) — Ensure prune handles numeric, Z-suffixed, and missing timestamps.
- `test_prune_feedback_log_by_age(tmp_path: Path) -> None` (line 88) — Retains only entries newer than the configured age threshold.
- `test_prune_feedback_log_missing_file(tmp_path: Path) -> None` (line 116) — Raises if the feedback log file is absent.
- `test_prune_feedback_log_requires_limit(tmp_path: Path) -> None` (line 124) — Rejects calls without an age or request limit configured.
- `test_prune_feedback_log_empty_file(tmp_path: Path) -> None` (line 134) — Returns zeroed stats when the log contains no events.
- `test_prune_feedback_log_guard_when_pruning_everything(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None` (line 147) — Leaves the log intact when filters would drop every request.
- `test_prune_feedback_log_max_requests_prefers_newest(tmp_path: Path) -> None` (line 176) — Keeps only the newest requests when enforcing a max count.
- `test_redact_dataset_csv(tmp_path: Path) -> None` (line 215) — Redacts populated CSV fields for queries, contexts, and notes.
- `test_redact_dataset_csv_handles_missing_and_blank_fields(tmp_path: Path) -> None` (line 236) — Leaves missing or blank CSV fields untouched while redacting non-empty ones.
- `test_redact_dataset_jsonl(tmp_path: Path) -> None` (line 256) — Redacts JSONL query and context fields when toggled.
- `test_redact_dataset_jsonl_handles_missing_and_blank_fields(tmp_path: Path) -> None` (line 286) — Leaves absent or empty JSONL fields untouched while redacting populated ones.
- `test_redact_dataset_missing_file(tmp_path: Path) -> None` (line 312) — Raises if the target dataset file is absent.
- `test_redact_dataset_unsupported_suffix(tmp_path: Path) -> None` (line 320) — Rejects unsupported dataset extensions.
- `test_redact_dataset_output_path_copies_metadata(tmp_path: Path) -> None` (line 330) — Preserves metadata when writing to an alternate output path.
- `test_redact_dataset_jsonl_handles_blank_lines(tmp_path: Path) -> None` (line 353) — Preserves blank lines in JSONL datasets while redacting content.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- datetime, json, os, pathlib, pytest, stat

### Code Quality Notes
- No immediate issues detected from static scan.

## tests/test_search_profiles.py

**File path**: `tests/test_search_profiles.py`
**Purpose**: Module tests/test_search_profiles.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pytest; Internal – gateway.config.settings.AppSettings, gateway.config.settings.SEARCH_WEIGHT_PROFILES
**Related modules**: gateway.config.settings.AppSettings, gateway.config.settings.SEARCH_WEIGHT_PROFILES

### Classes
- None

### Functions
- `clear_weight_env(monkeypatch: pytest.MonkeyPatch) -> None` (line 9) — No docstring provided.
- `test_resolved_search_weights_default() -> None` (line 17) — No docstring provided.
- `test_resolved_search_weights_profile_selection(monkeypatch: pytest.MonkeyPatch) -> None` (line 25) — No docstring provided.
- `test_resolved_search_weights_overrides(monkeypatch: pytest.MonkeyPatch) -> None` (line 34) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pytest

### Code Quality Notes
- 4 public element(s) lack docstrings.

## tests/test_search_service.py

**File path**: `tests/test_search_service.py`
**Purpose**: Module tests/test_search_service.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, collections.abc.Sequence, datetime.UTC, datetime.datetime, datetime.timedelta, prometheus_client.REGISTRY, pytest, time, typing.Any; Internal – gateway.graph.service.GraphService, gateway.search.SearchOptions, gateway.search.SearchService, gateway.search.SearchWeights, gateway.search.trainer.ModelArtifact
**Related modules**: gateway.graph.service.GraphService, gateway.search.SearchOptions, gateway.search.SearchService, gateway.search.SearchWeights, gateway.search.trainer.ModelArtifact

### Classes
- `FakeEmbedder` (line 21) — No class docstring provided. Inherits from object.
  - Methods:
    - `encode(self, texts: Sequence[str]) -> list[list[float]]` (line 22) — No method docstring provided.
- `FakePoint` (line 26) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, payload: dict[str, Any], score: float) -> None` (line 27) — No method docstring provided.
- `FakeQdrantClient` (line 32) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, points: list[FakePoint]) -> None` (line 33) — No method docstring provided.
    - `search(self, **kwargs: object) -> list[FakePoint]` (line 37) — No method docstring provided.
- `DummyGraphService` (line 42) — No class docstring provided. Inherits from GraphService.
  - Methods:
    - `__init__(self, response: dict[str, Any]) -> None` (line 43) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 46) — No method docstring provided.
    - `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]` (line 49) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 52) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 55) — No method docstring provided.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 58) — No method docstring provided.
- `SlowGraphService` (line 62) — No class docstring provided. Inherits from DummyGraphService.
  - Methods:
    - `__init__(self, response: dict[str, Any], delay: float) -> None` (line 63) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 67) — No method docstring provided.
- `MapGraphService` (line 189) — No class docstring provided. Inherits from GraphService.
  - Methods:
    - `__init__(self, data: dict[str, dict[str, Any]]) -> None` (line 190) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 193) — No method docstring provided.
    - `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]` (line 196) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 199) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 202) — No method docstring provided.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 205) — No method docstring provided.
- `CountingGraphService` (line 209) — No class docstring provided. Inherits from GraphService.
  - Methods:
    - `__init__(self, response: dict[str, Any], depth: int = 2) -> None` (line 210) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 216) — No method docstring provided.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 220) — No method docstring provided.
    - `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]` (line 224) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 227) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 230) — No method docstring provided.

### Functions
- `_metric_value(name: str, labels: dict[str, str] | None = None) -> float` (line 16) — No docstring provided.
- `sample_points() -> list[FakePoint]` (line 73) — No docstring provided.
- `graph_response() -> dict[str, Any]` (line 92) — No docstring provided.
- `test_search_service_enriches_with_graph(sample_points: list[FakePoint], graph_response: dict[str, Any]) -> None` (line 123) — No docstring provided.
- `test_search_service_handles_missing_graph(sample_points: list[FakePoint]) -> None` (line 161) — No docstring provided.
- `test_search_hnsw_search_params(sample_points: list[FakePoint]) -> None` (line 234) — No docstring provided.
- `test_lexical_score_affects_ranking() -> None` (line 256) — No docstring provided.
- `test_search_service_orders_by_adjusted_score() -> None` (line 300) — No docstring provided.
- `test_search_service_caches_graph_lookups(sample_points: list[FakePoint], graph_response: dict[str, Any]) -> None` (line 384) — No docstring provided.
- `test_search_service_filters_artifact_types() -> None` (line 445) — No docstring provided.
- `test_search_service_filters_namespaces() -> None` (line 494) — No docstring provided.
- `test_search_service_filters_tags() -> None` (line 543) — No docstring provided.
- `test_search_service_filters_recency_updated_after() -> None` (line 592) — No docstring provided.
- `test_search_service_filters_recency_max_age_days() -> None` (line 647) — No docstring provided.
- `test_search_service_filters_subsystem_via_graph(graph_response: dict[str, Any]) -> None` (line 697) — No docstring provided.
- `test_search_service_ml_model_reorders_results() -> None` (line 752) — No docstring provided.
- `test_search_service_limits_graph_results(graph_response: dict[str, Any]) -> None` (line 822) — No docstring provided.
- `test_search_service_respects_graph_time_budget(graph_response: dict[str, Any]) -> None` (line 856) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, datetime, prometheus_client, pytest, time, typing

### Code Quality Notes
- 49 public element(s) lack docstrings.

## tests/test_settings_defaults.py

**File path**: `tests/test_settings_defaults.py`
**Purpose**: Module tests/test_settings_defaults.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, pytest; Internal – gateway.config.settings.AppSettings
**Related modules**: gateway.config.settings.AppSettings

### Classes
- None

### Functions
- `test_neo4j_database_defaults_to_neo4j(monkeypatch: pytest.MonkeyPatch) -> None` (line 8) — No docstring provided.
- `test_neo4j_auth_enabled_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None` (line 14) — No docstring provided.
- `test_auth_enabled_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None` (line 20) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- pytest

### Code Quality Notes
- 3 public element(s) lack docstrings.

## tests/test_tracing.py

**File path**: `tests/test_tracing.py`
**Purpose**: Module tests/test_tracing.py lacks docstring; review source for intent.
**Dependencies**: External – __future__.annotations, opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter, opentelemetry.sdk.trace.TracerProvider, opentelemetry.sdk.trace.export.ConsoleSpanExporter, pytest.MonkeyPatch; Internal – gateway.api.app.create_app, gateway.config.settings.get_settings, gateway.observability.tracing.reset_tracing_for_tests
**Related modules**: gateway.api.app.create_app, gateway.config.settings.get_settings, gateway.observability.tracing.reset_tracing_for_tests

### Classes
- None

### Functions
- `test_tracing_disabled_by_default(monkeypatch: MonkeyPatch) -> None` (line 13) — No docstring provided.
- `test_tracing_enabled_instruments_app(monkeypatch: MonkeyPatch) -> None` (line 27) — No docstring provided.
- `test_tracing_uses_otlp_exporter(monkeypatch: MonkeyPatch) -> None` (line 60) — No docstring provided.
- `test_tracing_console_fallback(monkeypatch: MonkeyPatch) -> None` (line 93) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- opentelemetry, pytest

### Code Quality Notes
- 4 public element(s) lack docstrings.

## tests/test_ui_routes.py

**File path**: `tests/test_ui_routes.py`
**Purpose**: Smoke tests covering the HTML console routes exposed by the gateway API.
**Dependencies**: External – __future__.annotations, fastapi.testclient.TestClient, pathlib.Path, prometheus_client.REGISTRY, pytest.MonkeyPatch, pytest.approx; Internal – gateway.api.app.create_app, gateway.config.settings.get_settings
**Related modules**: gateway.api.app.create_app, gateway.config.settings.get_settings

### Classes
- None

### Functions
- `_reset_settings(tmp_path: Path | None = None) -> None` (line 15) — Clear cached settings and ensure the state directory exists for tests.
- `test_ui_landing_served(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` (line 22) — The landing page renders successfully and increments the landing metric.
- `test_ui_search_view(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` (line 49) — The search view renders and increments the search metric.
- `test_ui_subsystems_view(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` (line 75) — The subsystems view renders and increments the subsystem metric.
- `test_ui_lifecycle_download(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` (line 97) — Lifecycle report downloads are returned and recorded in metrics.
- `test_ui_events_endpoint(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` (line 123) — Custom UI events are accepted and reflected in Prometheus metrics.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- fastapi, pathlib, prometheus_client, pytest

### Code Quality Notes
- No immediate issues detected from static scan.
