# Module Documentation

## gateway/__init__.py

**File path**: `gateway/__init__.py`
**Purpose**: Core package for the Duskmantle knowledge gateway.
**Dependencies**: External – __future__; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `get_version() -> str` — Return the current package version.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- General-purpose helpers supporting the knowledge gateway.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/__main__.py

**File path**: `gateway/__main__.py`
**Purpose**: Console entry point that launches the FastAPI application.
**Dependencies**: External – __future__, uvicorn; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `main() -> None:  # pragma: no cover - thin wrapper` — Run the gateway API using Uvicorn.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- General-purpose helpers supporting the knowledge gateway.

### Integration Points
- Uvicorn ASGI server

### Code Quality Notes
- No major issues detected during static review.

## gateway/api/__init__.py

**File path**: `gateway/api/__init__.py`
**Purpose**: API layer for the knowledge gateway.
**Dependencies**: External – None; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/api/app.py

**File path**: `gateway/api/app.py`
**Purpose**: Primary FastAPI application wiring for the knowledge gateway.
**Dependencies**: External – __future__, apscheduler.schedulers.base, collections.abc, contextlib, fastapi, fastapi.responses, fastapi.staticfiles, json, logging, neo4j, neo4j.exceptions, qdrant_client, slowapi, slowapi.errors, slowapi.middleware, slowapi.util, time, typing, uuid; Internal – gateway, gateway.api.routes, gateway.config.settings, gateway.graph, gateway.graph.migrations, gateway.observability, gateway.scheduler, gateway.search.feedback, gateway.search.trainer, gateway.ui
**Related modules**: gateway, gateway.api.routes, gateway.config.settings, gateway.graph, gateway.graph.migrations, gateway.observability, gateway.scheduler, gateway.search.feedback, gateway.search.trainer, gateway.ui

### Classes
- None

### Functions
- `_validate_auth_settings(settings: AppSettings) -> None` — No docstring provided.
- `_log_startup_configuration(settings: AppSettings) -> None` — No docstring provided.
- `_build_lifespan(settings: AppSettings) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]` — No docstring provided.
- `_configure_rate_limits(app: FastAPI, settings: AppSettings) -> Limiter` — No docstring provided.
- `_init_feedback_store(settings: AppSettings) -> SearchFeedbackStore | None` — No docstring provided.
- `_load_search_model(settings: AppSettings) -> ModelArtifact | None` — No docstring provided.
- `_init_graph_driver(settings: AppSettings) -> tuple[Driver | None, Driver | None]` — No docstring provided.
- `_init_qdrant_client(settings: AppSettings) -> QdrantClient | None` — No docstring provided.
- `_create_graph_driver(` — No docstring provided.
- `_create_readonly_driver(settings: AppSettings, *, primary_driver: Driver) -> Driver | None` — No docstring provided.
- `_verify_graph_database(driver: Driver, database: str) -> bool` — No docstring provided.
- `_run_graph_auto_migration(driver: Driver, database: str) -> None` — No docstring provided.
- `_fetch_pending_migrations(runner: MigrationRunner) -> list[str] | None` — No docstring provided.
- `_log_migration_plan(pending: list[str] | None) -> None` — No docstring provided.
- `_log_migration_completion(pending: list[str] | None) -> None` — No docstring provided.
- `_set_migration_metrics(status: int, *, timestamp: float | None) -> None` — No docstring provided.
- `create_app() -> FastAPI` — Create the FastAPI application instance.
- `_rate_limit_handler(_request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover - thin wrapper` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- APScheduler background scheduling, FastAPI web framework, Neo4j GraphDatabase driver, Qdrant vector database SDK, SlowAPI rate limiting

### Code Quality Notes
- 17 helper function(s) missing docstrings.

## gateway/api/auth.py

**File path**: `gateway/api/auth.py`
**Purpose**: Authentication dependencies used across the FastAPI surface.
**Dependencies**: External – __future__, collections.abc, fastapi, fastapi.security; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

### Classes
- None

### Functions
- `require_scope(scope: str) -> Callable[[HTTPAuthorizationCredentials | None], None]` — Return a dependency enforcing the given scope.
- `_allowed_tokens_for_scope(settings: AppSettings, scope: str) -> list[str]` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- FastAPI web framework

### Code Quality Notes
- 1 helper function(s) missing docstrings.

## gateway/api/dependencies.py

**File path**: `gateway/api/dependencies.py`
**Purpose**: FastAPI dependency helpers for the gateway application.
**Dependencies**: External – __future__, fastapi, logging, slowapi; Internal – gateway.config.settings, gateway.graph, gateway.ingest.embedding, gateway.search, gateway.search.feedback, gateway.search.trainer
**Related modules**: gateway.config.settings, gateway.graph, gateway.ingest.embedding, gateway.search, gateway.search.feedback, gateway.search.trainer

### Classes
- None

### Functions
- `get_app_settings(request: Request) -> AppSettings` — Return the application settings attached to the FastAPI app.
- `get_limiter(request: Request) -> Limiter` — Return the rate limiter configured on the FastAPI app.
- `get_search_model(request: Request) -> ModelArtifact | None` — Return the cached search ranking model from application state.
- `get_graph_service_dependency(` — Return a memoised graph service bound to the current FastAPI app.
- `get_search_service_dependency(` — Construct (and cache) the hybrid search service for the application.
- `get_feedback_store(request: Request) -> SearchFeedbackStore | None` — Return the configured search feedback store, if any.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- FastAPI web framework, SlowAPI rate limiting

### Code Quality Notes
- No major issues detected during static review.

## gateway/api/routes/__init__.py

**File path**: `gateway/api/routes/__init__.py`
**Purpose**: FastAPI route modules for the gateway application.
**Dependencies**: External – None; Internal – gateway.api
**Related modules**: gateway.api

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/api/routes/graph.py

**File path**: `gateway/api/routes/graph.py`
**Purpose**: Graph API routes.
**Dependencies**: External – __future__, fastapi, fastapi.responses, slowapi, typing; Internal – gateway.api.auth, gateway.api.dependencies, gateway.graph
**Related modules**: gateway.api.auth, gateway.api.dependencies, gateway.graph

### Classes
- None

### Functions
- `create_router(limiter: Limiter, metrics_limit: str) -> APIRouter` — Create an API router exposing graph endpoints with shared rate limits.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- FastAPI web framework, SlowAPI rate limiting

### Code Quality Notes
- Cypher guard relies on call whitelisting and read-only driver; ensure tests cover bypass attempts.

## gateway/api/routes/health.py

**File path**: `gateway/api/routes/health.py`
**Purpose**: Health and observability endpoints.
**Dependencies**: External – __future__, contextlib, fastapi, json, prometheus_client, slowapi, sqlite3, time, typing; Internal – gateway.api.dependencies, gateway.config.settings
**Related modules**: gateway.api.dependencies, gateway.config.settings

### Classes
- None

### Functions
- `create_router(limiter: Limiter, metrics_limit: str) -> APIRouter` — Wire up health, readiness, and metrics endpoints.
- `build_health_report(app: FastAPI, settings: AppSettings) -> dict[str, object]` — Assemble the health payload consumed by `/healthz`.
- `_coverage_health(settings: AppSettings) -> dict[str, Any]` — No docstring provided.
- `_audit_health(settings: AppSettings) -> dict[str, Any]` — No docstring provided.
- `_scheduler_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- FastAPI web framework, Prometheus metrics client, SlowAPI rate limiting

### Code Quality Notes
- 3 helper function(s) missing docstrings.

## gateway/api/routes/reporting.py

**File path**: `gateway/api/routes/reporting.py`
**Purpose**: Observability and reporting routes.
**Dependencies**: External – __future__, fastapi, fastapi.responses, json, pathlib, slowapi, typing; Internal – gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.ingest.audit, gateway.ingest.lifecycle
**Related modules**: gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.ingest.audit, gateway.ingest.lifecycle

### Classes
- None

### Functions
- `create_router(limiter: Limiter) -> APIRouter` — Expose reporting and audit endpoints protected by maintainer auth.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- FastAPI web framework, SlowAPI rate limiting

### Code Quality Notes
- No major issues detected during static review.

## gateway/api/routes/search.py

**File path**: `gateway/api/routes/search.py`
**Purpose**: Search API routes.
**Dependencies**: External – __future__, collections.abc, datetime, fastapi, fastapi.responses, logging, qdrant_client.http.exceptions, slowapi, typing, uuid; Internal – gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.graph, gateway.observability, gateway.search, gateway.search.feedback
**Related modules**: gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.graph, gateway.observability, gateway.search, gateway.search.feedback

### Classes
- None

### Functions
- `create_router(limiter: Limiter, metrics_limit: str) -> APIRouter` — Return an API router for the search endpoints with shared rate limits.
- `_parse_iso8601_to_utc(value: str) -> datetime | None` — No docstring provided.
- `_has_vote(mapping: Mapping[str, Any] | None) -> bool` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Handles FastAPI request routing, dependency wiring, and HTTP responses.

### Integration Points
- FastAPI web framework, Qdrant vector database SDK, SlowAPI rate limiting

### Code Quality Notes
- 2 helper function(s) missing docstrings.

## gateway/config/__init__.py

**File path**: `gateway/config/__init__.py`
**Purpose**: Configuration helpers for the knowledge gateway.
**Dependencies**: External – __future__; Internal – gateway.settings
**Related modules**: gateway.settings

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Loads environment-driven runtime configuration for the gateway.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/config/settings.py

**File path**: `gateway/config/settings.py`
**Purpose**: Pydantic-based configuration for the knowledge gateway.
**Dependencies**: External – __future__, functools, pathlib, pydantic, pydantic_settings, typing; Internal – None
**Related modules**: None

### Classes
- `AppSettings(BaseSettings)` — Runtime configuration for the knowledge gateway.
  - Attributes: `api_host: str = Field('0.0.0.0', alias='KM_API_HOST')`; `api_port: int = Field(8000, alias='KM_API_PORT')`; `auth_mode: Literal['secure', 'insecure'] = Field('secure', alias='KM_AUTH_MODE')`; `auth_enabled: bool = Field(False, alias='KM_AUTH_ENABLED')`; `reader_token: str | None = Field(None, alias='KM_READER_TOKEN')`; `maintainer_token: str | None = Field(None, alias='KM_ADMIN_TOKEN')`; `rate_limit_requests: int = Field(120, alias='KM_RATE_LIMIT_REQUESTS')`; `rate_limit_window_seconds: int = Field(60, alias='KM_RATE_LIMIT_WINDOW')`; `repo_root: Path = Field(Path('/workspace/repo'), alias='KM_REPO_PATH')`; `state_path: Path = Field(Path('/opt/knowledge/var'), alias='KM_STATE_PATH')`; `content_root: Path = Field(Path('/workspace/repo'), alias='KM_CONTENT_ROOT')`; `content_docs_subdir: Path = Field(Path('docs'), alias='KM_CONTENT_DOCS_SUBDIR')`; `upload_default_overwrite: bool = Field(False, alias='KM_UPLOAD_DEFAULT_OVERWRITE')`; `upload_default_ingest: bool = Field(False, alias='KM_UPLOAD_DEFAULT_INGEST')`; `qdrant_url: str = Field('http://localhost:6333', alias='KM_QDRANT_URL')`; `qdrant_api_key: str | None = Field(None, alias='KM_QDRANT_API_KEY')`; `qdrant_collection: str = Field('km_knowledge_v1', alias='KM_QDRANT_COLLECTION')`; `neo4j_uri: str = Field('bolt://localhost:7687', alias='KM_NEO4J_URI')`; `neo4j_user: str = Field('neo4j', alias='KM_NEO4J_USER')`; `neo4j_password: str = Field('neo4jadmin', alias='KM_NEO4J_PASSWORD')`; `neo4j_database: str = Field('knowledge', alias='KM_NEO4J_DATABASE')`; `neo4j_auth_enabled: bool = Field(True, alias='KM_NEO4J_AUTH_ENABLED')`; `neo4j_readonly_uri: str | None = Field(None, alias='KM_NEO4J_READONLY_URI')`; `neo4j_readonly_user: str | None = Field(None, alias='KM_NEO4J_READONLY_USER')`; `neo4j_readonly_password: str | None = Field(None, alias='KM_NEO4J_READONLY_PASSWORD')`; `embedding_model: str = Field('sentence-transformers/all-MiniLM-L6-v2', alias='KM_EMBEDDING_MODEL')`; `ingest_window: int = Field(1000, alias='KM_INGEST_WINDOW')`; `ingest_overlap: int = Field(200, alias='KM_INGEST_OVERLAP')`; `ingest_use_dummy_embeddings: bool = Field(False, alias='KM_INGEST_USE_DUMMY')`; `ingest_incremental_enabled: bool = Field(True, alias='KM_INGEST_INCREMENTAL')`; `ingest_parallel_workers: int = Field(2, alias='KM_INGEST_PARALLEL_WORKERS')`; `ingest_max_pending_batches: int = Field(4, alias='KM_INGEST_MAX_PENDING_BATCHES')`; `scheduler_enabled: bool = Field(False, alias='KM_SCHEDULER_ENABLED')`; `scheduler_interval_minutes: int = Field(30, alias='KM_SCHEDULER_INTERVAL_MINUTES')`; `scheduler_cron: str | None = Field(None, alias='KM_SCHEDULER_CRON')`; `coverage_enabled: bool = Field(True, alias='KM_COVERAGE_ENABLED')`; `coverage_history_limit: int = Field(5, alias='KM_COVERAGE_HISTORY_LIMIT')`; `lifecycle_report_enabled: bool = Field(True, alias='KM_LIFECYCLE_REPORT_ENABLED')`; `lifecycle_stale_days: int = Field(30, alias='KM_LIFECYCLE_STALE_DAYS')`; `lifecycle_history_limit: int = Field(10, alias='KM_LIFECYCLE_HISTORY_LIMIT')`; `tracing_enabled: bool = Field(False, alias='KM_TRACING_ENABLED')`; `tracing_endpoint: str | None = Field(None, alias='KM_TRACING_ENDPOINT')`; `tracing_headers: str | None = Field(None, alias='KM_TRACING_HEADERS')`; `tracing_service_name: str = Field('duskmantle-knowledge-gateway', alias='KM_TRACING_SERVICE_NAME')`; `tracing_sample_ratio: float = Field(1.0, alias='KM_TRACING_SAMPLE_RATIO')`; `tracing_console_export: bool = Field(False, alias='KM_TRACING_CONSOLE_EXPORT')`; `graph_auto_migrate: bool = Field(False, alias='KM_GRAPH_AUTO_MIGRATE')`; `graph_subsystem_cache_ttl_seconds: int = Field(30, alias='KM_GRAPH_SUBSYSTEM_CACHE_TTL')`; `graph_subsystem_cache_max_entries: int = Field(128, alias='KM_GRAPH_SUBSYSTEM_CACHE_MAX')`; `search_weight_profile: Literal['default', 'analysis', 'operations', 'docs-heavy'] = Field('default', alias='KM_SEARCH_WEIGHT_PROFILE')`; `search_weight_subsystem: float = Field(0.28, alias='KM_SEARCH_W_SUBSYSTEM')`; `search_weight_relationship: float = Field(0.05, alias='KM_SEARCH_W_RELATIONSHIP')`; `search_weight_support: float = Field(0.09, alias='KM_SEARCH_W_SUPPORT')`; `search_weight_coverage_penalty: float = Field(0.15, alias='KM_SEARCH_W_COVERAGE_PENALTY')`; `search_weight_criticality: float = Field(0.12, alias='KM_SEARCH_W_CRITICALITY')`; `search_sort_by_vector: bool = Field(False, alias='KM_SEARCH_SORT_BY_VECTOR')`; `search_scoring_mode: Literal['heuristic', 'ml'] = Field('heuristic', alias='KM_SEARCH_SCORING_MODE')`; `search_model_path: Path | None = Field(None, alias='KM_SEARCH_MODEL_PATH')`; `search_warn_slow_graph_ms: int = Field(250, alias='KM_SEARCH_WARN_GRAPH_MS')`; `search_vector_weight: float = Field(1.0, alias='KM_SEARCH_VECTOR_WEIGHT')`; `search_lexical_weight: float = Field(0.25, alias='KM_SEARCH_LEXICAL_WEIGHT')`; `search_hnsw_ef_search: int | None = Field(128, alias='KM_SEARCH_HNSW_EF_SEARCH')`; `dry_run: bool = Field(False, alias='KM_INGEST_DRY_RUN')`; `model_config = {'env_file': '.env', 'extra': 'ignore'}`
  - Methods: `_clamp_tracing_ratio(cls, value: float) -> float` — Ensure the tracing sampling ratio stays within [0, 1].; `_clamp_search_weights(cls, value: float) -> float` — Clamp search weights to [0, 1] for stability.; `_sanitize_hnsw_ef(cls, value: int | None) -> int | None` — No docstring provided.; `_sanitize_graph_cache_ttl(cls, value: int) -> int` — No docstring provided.; `_sanitize_graph_cache_max(cls, value: int) -> int` — No docstring provided.; `resolved_search_weights(self) -> tuple[str, dict[str, float]]` — Return the active search weight profile name and resolved weights.; `scheduler_trigger_config(self) -> dict[str, object]` — Return trigger configuration for the ingestion scheduler.; `_validate_history_limit(cls, value: int) -> int` — No docstring provided.; `_validate_lifecycle_stale(cls, value: int) -> int` — No docstring provided.; `_ensure_positive_parallelism(cls, value: int) -> int` — No docstring provided.

### Functions
- `get_settings() -> AppSettings` — Load settings from environment (cached).

### Constants and Configuration
- Module-level constants: SEARCH_WEIGHT_PROFILES
- Environment variables: Not detected in static scan

### Data Flow
- Loads environment-driven runtime configuration for the gateway.

### Integration Points
- Pydantic validation, Pydantic settings management

### Code Quality Notes
- 6 class method(s) missing docstrings.

## gateway/graph/__init__.py

**File path**: `gateway/graph/__init__.py`
**Purpose**: Graph query utilities and service layer.
**Dependencies**: External – None; Internal – gateway.service
**Related modules**: gateway.service

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Runs read-only Neo4j queries and serialises graph entities for consumers.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/graph/cli.py

**File path**: `gateway/graph/cli.py`
**Purpose**: Command-line utilities for managing the Neo4j graph schema.
**Dependencies**: External – __future__, argparse, logging, neo4j; Internal – gateway.config.settings, gateway.graph.migrations
**Related modules**: gateway.config.settings, gateway.graph.migrations

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` — Return the CLI argument parser for graph administration commands.
- `run_migrations(*, dry_run: bool = False) -> None` — Execute graph schema migrations, optionally printing the pending set.
- `main(argv: list[str] | None = None) -> None` — Entrypoint for the `gateway-graph` command-line interface.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Runs read-only Neo4j queries and serialises graph entities for consumers.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- No major issues detected during static review.

## gateway/graph/migrations/__init__.py

**File path**: `gateway/graph/migrations/__init__.py`
**Purpose**: Graph schema migrations.
**Dependencies**: External – None; Internal – gateway.graph.runner
**Related modules**: gateway.graph.runner

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Runs read-only Neo4j queries and serialises graph entities for consumers.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/graph/migrations/runner.py

**File path**: `gateway/graph/migrations/runner.py`
**Purpose**: Helpers for applying and tracking Neo4j schema migrations.
**Dependencies**: External – __future__, collections.abc, dataclasses, logging, neo4j; Internal – None
**Related modules**: None

### Classes
- `Migration` — Describe a single migration and the Cypher statements it executes.
  - Attributes: `id: str`; `statements: Iterable[str]`
- `MigrationRunner` — Apply ordered graph migrations using a shared Neo4j driver.
  - Attributes: `driver: Driver`; `database: str = 'knowledge'`
  - Methods: `pending_ids(self) -> list[str]` — Return the identifiers of migrations that have not yet been applied.; `run(self) -> None` — Apply all pending migrations to the configured Neo4j database.; `_is_applied(self, migration_id: str) -> bool` — Return whether the given migration has already been recorded.; `_apply(self, migration: Migration) -> None` — Execute migration statements and record completion.

### Functions
- None

### Constants and Configuration
- Module-level constants: MIGRATIONS
- Environment variables: Not detected in static scan

### Data Flow
- Runs read-only Neo4j queries and serialises graph entities for consumers.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- No major issues detected during static review.

## gateway/graph/service.py

**File path**: `gateway/graph/service.py`
**Purpose**: Read-only graph service utilities backed by Neo4j.
**Dependencies**: External – __future__, base64, collections, collections.abc, dataclasses, neo4j, neo4j.graph, threading, time, typing; Internal – gateway.observability.metrics
**Related modules**: gateway.observability.metrics

### Classes
- `GraphServiceError(RuntimeError)` — Base class for graph-related errors.
- `GraphNotFoundError(GraphServiceError)` — Raised when a requested node cannot be found.
- `GraphQueryError(GraphServiceError)` — Raised when a supplied query is invalid or unsafe.
- `SubsystemGraphSnapshot` — Snapshot of a subsystem node and its related graph context.
  - Attributes: `subsystem: dict[str, Any]`; `related: list[dict[str, Any]]`; `nodes: list[dict[str, Any]]`; `edges: list[dict[str, Any]]`; `artifacts: list[dict[str, Any]]`
- `SubsystemGraphCache` — Simple TTL cache for subsystem graph snapshots.
  - Methods: `__init__(self, ttl_seconds: float, max_entries: int) -> None` — Create a cache with an expiry window and bounded size.; `get(self, key: tuple[str, int]) -> SubsystemGraphSnapshot | None` — Return a cached snapshot if it exists and has not expired.; `set(self, key: tuple[str, int], snapshot: SubsystemGraphSnapshot) -> None` — Cache a snapshot for the given key, evicting oldest entries if needed.; `clear(self) -> None` — Remove all cached subsystem snapshots.
- `GraphService` — Service layer for read-only graph queries.
  - Attributes: `driver: Driver`; `database: str`; `subsystem_cache: SubsystemGraphCache | None = None`; `readonly_driver: Driver | None = None`
  - Methods: `get_subsystem(` — Return a windowed view of related nodes for the requested subsystem.; `get_subsystem_graph(self, name: str, *, depth: int) -> dict[str, Any]` — Return the full node/edge snapshot for a subsystem.; `list_orphan_nodes(` — List nodes that have no relationships of the allowed labels.; `clear_cache(self) -> None` — Wipe the subsystem snapshot cache if caching is enabled.; `_load_subsystem_snapshot(self, name: str, depth: int) -> SubsystemGraphSnapshot` — No docstring provided.; `_build_subsystem_snapshot(self, name: str, depth: int) -> SubsystemGraphSnapshot` — No docstring provided.; `get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]` — Return a node and a limited set of relationships using Cypher lookups.; `search(self, term: str, *, limit: int) -> dict[str, Any]` — Search the graph for nodes matching the provided term.; `shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None` — Return the length of the shortest path from the node to any subsystem.

The search is bounded by ``max_depth`` hops across the knowledge graph
relationship types used by ingestion. ``None`` is returned when no
subsystem can be reached within the given depth limit.; `run_cypher(` — Execute an arbitrary Cypher query and serialize the response.

### Functions
- `get_graph_service(` — Factory helper that constructs a `GraphService` with optional caching.
- `_extract_path_components(` — No docstring provided.
- `_record_path_edges(` — No docstring provided.
- `_ensure_serialized_node(` — No docstring provided.
- `_relationship_direction(relationship: Relationship, source_node: Node) -> str` — No docstring provided.
- `_build_related_entry(` — No docstring provided.
- `_append_related_entry(` — No docstring provided.
- `_fetch_subsystem_node(tx: ManagedTransaction, /, name: str) -> Node | None` — No docstring provided.
- `_fetch_subsystem_paths(` — No docstring provided.
- `_fetch_artifacts_for_subsystem(tx: ManagedTransaction, /, name: str) -> list[Node]` — No docstring provided.
- `_fetch_orphan_nodes(` — No docstring provided.
- `_fetch_node_by_id(tx: ManagedTransaction, /, label: str, key: str, value: object) -> Node | None` — No docstring provided.
- `_fetch_node_relationships(` — No docstring provided.
- `_search_entities(tx: ManagedTransaction, /, term: str, limit: int) -> list[dict[str, Any]]` — No docstring provided.
- `_serialize_related(record: dict[str, Any], subsystem_node: Node) -> dict[str, Any]` — No docstring provided.
- `_serialize_node(node: Node) -> dict[str, Any]` — No docstring provided.
- `_serialize_relationship(record: dict[str, Any]) -> dict[str, Any]` — No docstring provided.
- `_serialize_value(value: object) -> object` — No docstring provided.
- `_ensure_node(value: object) -> Node` — No docstring provided.
- `_node_element_id(node: Node | None) -> str` — No docstring provided.
- `_canonical_node_id(node: Node) -> str` — No docstring provided.
- `_parse_node_id(node_id: str) -> tuple[str, str, str]` — No docstring provided.
- `_encode_cursor(offset: int) -> str` — No docstring provided.
- `_decode_cursor(cursor: str | None) -> int` — No docstring provided.
- `_validate_cypher(query: str) -> None` — No docstring provided.
- `_strip_literals_and_comments(query: str) -> str` — No docstring provided.
- `_tokenize_query(upper_query: str) -> list[str]` — No docstring provided.
- `_extract_procedure_calls(tokens: list[str]) -> list[str]` — No docstring provided.
- `_deny_cypher(reason: str, message: str) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: ORPHAN_DEFAULT_LABELS, _ALLOWED_PROCEDURE_PREFIXES
- Environment variables: Not detected in static scan

### Data Flow
- Runs read-only Neo4j queries and serialises graph entities for consumers.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- 28 helper function(s) missing docstrings.
- 2 class method(s) missing docstrings.
- Read-only enforcement uses counters/procedure whitelists; keep regression tests current with Neo4j driver changes.

## gateway/ingest/__init__.py

**File path**: `gateway/ingest/__init__.py`
**Purpose**: Ingestion pipeline components for the knowledge gateway.
**Dependencies**: External – None; Internal – gateway.ingest.pipeline
**Related modules**: gateway.ingest.pipeline

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/artifacts.py

**File path**: `gateway/ingest/artifacts.py`
**Purpose**: Domain models representing artifacts produced during ingestion.
**Dependencies**: External – __future__, dataclasses, pathlib, typing; Internal – None
**Related modules**: None

### Classes
- `Artifact` — Represents a repository artifact prior to chunking.
  - Attributes: `path: Path`; `artifact_type: str`; `subsystem: str | None`; `content: str`; `git_commit: str | None`; `git_timestamp: int | None`; `extra_metadata: dict[str, Any] = field(default_factory=dict)`
- `Chunk` — Represents a chunk ready for embedding and indexing.
  - Attributes: `artifact: Artifact`; `chunk_id: str`; `text: str`; `sequence: int`; `content_digest: str`; `metadata: dict[str, Any]`
- `ChunkEmbedding` — Chunk plus embedding vector.
  - Attributes: `chunk: Chunk`; `vector: list[float]`

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/audit.py

**File path**: `gateway/ingest/audit.py`
**Purpose**: SQLite-backed audit log utilities for ingestion runs.
**Dependencies**: External – __future__, pathlib, sqlite3, time, typing; Internal – gateway.ingest.pipeline
**Related modules**: gateway.ingest.pipeline

### Classes
- `AuditLogger` — Persist and retrieve ingestion run metadata in SQLite.
  - Methods: `__init__(self, db_path: Path) -> None` — Initialise the audit database and ensure the schema exists.; `record(self, result: IngestionResult) -> None` — Insert a new ingestion run entry.; `recent(self, limit: int = 20) -> list[dict[str, Any]]` — Return the most recent ingestion runs up to ``limit`` entries.

### Functions
- None

### Constants and Configuration
- Module-level constants: _INSERT_RUN, _SCHEMA, _SELECT_RECENT
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/chunking.py

**File path**: `gateway/ingest/chunking.py`
**Purpose**: Chunk source artifacts into overlapping windows for indexing.
**Dependencies**: External – __future__, collections.abc, hashlib, math, pathlib, typing; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

### Classes
- `Chunker` — Split artifacts into overlapping textual chunks.
  - Methods: `__init__(self, window: int = DEFAULT_WINDOW, overlap: int = DEFAULT_OVERLAP) -> None` — Configure chunk sizes and overlap.; `split(self, artifact: Artifact) -> Iterable[Chunk]` — Split the artifact content into `Chunk` instances.; `estimate_chunk_count(path: Path, text: str, *, window: int = DEFAULT_WINDOW, overlap: int = DEFAULT_OVERLAP) -> int` — Estimate how many chunks a text would produce with the configured window.

### Functions
- `_derive_namespace(path: Path) -> str` — Infer a namespace from a file path for tagging chunks.
- `_build_tags(extra_metadata: dict[str, Any]) -> list[str]` — Collect tag-like signals from artifact metadata.

### Constants and Configuration
- Module-level constants: DEFAULT_OVERLAP, DEFAULT_WINDOW
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/cli.py

**File path**: `gateway/ingest/cli.py`
**Purpose**: Command-line helpers for triggering and inspecting ingestion runs.
**Dependencies**: External – __future__, argparse, collections.abc, datetime, logging, pathlib, rich.console, rich.table; Internal – gateway.config.settings, gateway.ingest.audit, gateway.ingest.service, gateway.observability
**Related modules**: gateway.config.settings, gateway.ingest.audit, gateway.ingest.service, gateway.observability

### Classes
- None

### Functions
- `_ensure_maintainer_scope(settings: AppSettings) -> None` — Abort execution if maintainer credentials are missing during auth.
- `build_parser() -> argparse.ArgumentParser` — Create an argument parser for the ingestion CLI.
- `rebuild(` — Execute a full ingestion pass.
- `audit_history(` — Display recent ingestion runs from the audit ledger.
- `_render_audit_table(entries: Iterable[dict[str, object]]) -> Table` — Render recent audit entries as a Rich table.
- `_format_timestamp(raw: object) -> str` — Format timestamps from the audit ledger for display.
- `_coerce_int(value: object) -> int | None` — Attempt to interpret the value as an integer.
- `_coerce_float(value: object) -> float | None` — Attempt to interpret the value as a floating point number.
- `main(argv: list[str] | None = None) -> None` — Entry point for the CLI.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Rich console rendering

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/coverage.py

**File path**: `gateway/ingest/coverage.py`
**Purpose**: Utilities for writing ingestion coverage reports.
**Dependencies**: External – __future__, contextlib, datetime, json, pathlib, time; Internal – gateway.ingest.pipeline, gateway.observability.metrics
**Related modules**: gateway.ingest.pipeline, gateway.observability.metrics

### Classes
- None

### Functions
- `write_coverage_report(` — Persist coverage metrics derived from an ingestion result.
- `_write_history_snapshot(payload: dict[str, object], reports_dir: Path, history_limit: int) -> list[Path]` — Write coverage history snapshots and prune old entries.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/discovery.py

**File path**: `gateway/ingest/discovery.py`
**Purpose**: Repository discovery helpers for ingestion pipeline.
**Dependencies**: External – __future__, collections.abc, dataclasses, fnmatch, json, logging, pathlib, re, subprocess, typing; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

### Classes
- `DiscoveryConfig` — Runtime knobs influencing which artifacts are discovered.
  - Attributes: `repo_root: Path`; `include_patterns: tuple[str, ...] = ('docs', 'src', 'tests', '.codacy')`

### Functions
- `discover(config: DiscoveryConfig) -> Iterable[Artifact]` — Yield textual artifacts from the repository.
- `_should_include(path: Path, repo_root: Path, include_patterns: tuple[str, ...]) -> bool` — No docstring provided.
- `_is_textual(path: Path) -> bool` — No docstring provided.
- `_infer_artifact_type(path: Path, repo_root: Path) -> str` — No docstring provided.
- `_lookup_git_metadata(path: Path, repo_root: Path) -> tuple[str | None, int | None]` — No docstring provided.
- `_load_subsystem_catalog(repo_root: Path) -> dict[str, Any]` — No docstring provided.
- `_detect_source_prefixes(repo_root: Path) -> list[tuple[str, ...]]` — Infer source package prefixes (e.g. ``("src", "gateway")``).
- `_collect_pyproject_prefixes(root: Path, prefixes: set[tuple[str, ...]]) -> None` — No docstring provided.
- `_load_pyproject(path: Path) -> Mapping[str, Any] | dict[str, Any]` — No docstring provided.
- `_collect_poetry_prefixes(tool_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None` — No docstring provided.
- `_collect_project_prefixes(project_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None` — No docstring provided.
- `_collect_setuptools_prefixes(tool_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None` — No docstring provided.
- `_collect_src_directory_prefixes(root: Path, prefixes: set[tuple[str, ...]]) -> None` — No docstring provided.
- `_add_prefix(prefixes: set[tuple[str, ...]], include: str | None, base: str | None = "src") -> None` — No docstring provided.
- `_ensure_str_list(value: object) -> list[str]` — No docstring provided.
- `_infer_subsystem(path: Path, repo_root: Path, source_prefixes: list[tuple[str, ...]]) -> str | None` — No docstring provided.
- `_normalize_subsystem_name(value: str | None) -> str | None` — No docstring provided.
- `_match_catalog_entry(path: Path, repo_root: Path, catalog: dict[str, dict[str, Any]]) -> dict[str, Any] | None` — No docstring provided.
- `_iter_metadata_patterns(metadata: Mapping[str, Any]) -> Iterable[str]` — No docstring provided.
- `_pattern_matches(target: str, pattern: str) -> bool` — No docstring provided.
- `dump_artifacts(artifacts: Iterable[Artifact]) -> str` — Serialize artifacts for debugging or dry-run output.

### Constants and Configuration
- Module-level constants: _MESSAGE_PATTERN, _SOURCE_PREFIX_CACHE, _SUBSYSTEM_METADATA_CACHE, _TELEMETRY_PATTERN, _TEXTUAL_SUFFIXES
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Standard library only

### Code Quality Notes
- 18 helper function(s) missing docstrings.

## gateway/ingest/embedding.py

**File path**: `gateway/ingest/embedding.py`
**Purpose**: Embedding helpers used during ingestion.
**Dependencies**: External – __future__, collections.abc, functools, logging, sentence_transformers; Internal – None
**Related modules**: None

### Classes
- `Embedder` — Wrapper around sentence-transformers for configurable embeddings.
  - Methods: `__init__(self, model_name: str) -> None` — Load the requested sentence-transformer model.; `dimension(self) -> int` — Return the embedding dimensionality for the underlying model.; `encode(self, texts: Iterable[str]) -> list[list[float]]` — Embed an iterable of texts using the configured transformer.; `_load_model(model_name: str) -> SentenceTransformer` — Load and cache the requested sentence transformer model.
- `DummyEmbedder(Embedder)` — Deterministic embedder for dry-runs and tests.
  - Methods: `__init__(self) -> None:  # pylint: disable=super-init-not-called` — Initialise the deterministic embedder for testing.; `dimension(self) -> int:  # pragma: no cover - trivial` — Return the fixed dimension used by the dummy embedder.; `encode(self, texts: Iterable[str]) -> list[list[float]]` — Produce deterministic vectors for the provided texts.

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- SentenceTransformers embeddings

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/lifecycle.py

**File path**: `gateway/ingest/lifecycle.py`
**Purpose**: Lifecycle reporting helpers for ingestion outputs.
**Dependencies**: External – __future__, collections, collections.abc, contextlib, dataclasses, datetime, json, neo4j, pathlib, time, typing; Internal – gateway.graph, gateway.ingest.pipeline, gateway.observability.metrics
**Related modules**: gateway.graph, gateway.ingest.pipeline, gateway.observability.metrics

### Classes
- `LifecycleConfig` — Configuration values that influence lifecycle report generation.
  - Attributes: `output_path: Path`; `stale_days: int`; `graph_enabled: bool`; `history_limit: int | None = None`

### Functions
- `write_lifecycle_report(` — Persist lifecycle insights derived from the most recent ingest run.
- `build_graph_service(*, driver: Driver, database: str, cache_ttl: float) -> GraphService` — Construct a graph service with sensible defaults for lifecycle usage.
- `summarize_lifecycle(payload: dict[str, Any]) -> dict[str, Any]` — Produce a summarized view of lifecycle data for reporting.
- `_fetch_isolated_nodes(graph_service: GraphService | None) -> dict[str, list[dict[str, Any]]]` — Collect isolated graph nodes grouped by label.
- `_find_stale_docs(artifacts: Iterable[dict[str, Any]], stale_days: int, now: float) -> list[dict[str, Any]]` — Identify design documents that are older than the stale threshold.
- `_find_missing_tests(artifacts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]` — Determine subsystems lacking corresponding tests.
- `_write_history_snapshot(payload: dict[str, Any], reports_dir: Path, history_limit: int) -> list[Path]` — Write lifecycle history to disk while enforcing retention.
- `_coerce_float(value: object) -> float | None` — Coerce numeric-like values to float when possible.
- `_lifecycle_counts(` — Aggregate lifecycle metrics into counters.

### Constants and Configuration
- Module-level constants: SECONDS_PER_DAY
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- No major issues detected during static review.

## gateway/ingest/neo4j_writer.py

**File path**: `gateway/ingest/neo4j_writer.py`
**Purpose**: Write ingestion artifacts and chunks into Neo4j.
**Dependencies**: External – __future__, collections.abc, logging, neo4j; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

### Classes
- `Neo4jWriter` — Persist artifacts and derived data into a Neo4j database.
  - Methods: `__init__(self, driver: Driver, database: str = "knowledge") -> None` — Initialise the writer with a driver and target database.; `ensure_constraints(self) -> None` — Create required uniqueness constraints if they do not exist.; `sync_artifact(self, artifact: Artifact) -> None` — Upsert the artifact node and related subsystem relationships.; `sync_chunks(self, chunk_embeddings: Iterable[ChunkEmbedding]) -> None` — Upsert chunk nodes and connect them to their owning artifacts.; `delete_artifact(self, path: str) -> None` — Remove an artifact node and its chunks.

### Functions
- `_artifact_label(artifact: Artifact) -> str` — Map artifact types to Neo4j labels.
- `_label_for_type(artifact_type: str) -> str` — Return the default label for the given artifact type.
- `_relationship_for_label(label: str) -> str | None` — Return the relationship used to link artifacts to subsystems.
- `_clean_string_list(values: object) -> list[str]` — No docstring provided.
- `_normalize_subsystem_name(value: str | None) -> str | None` — No docstring provided.
- `_extract_dependencies(metadata: Mapping[str, object] | None) -> list[str]` — No docstring provided.
- `_subsystem_properties(metadata: Mapping[str, object] | None) -> dict[str, object]` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- 4 helper function(s) missing docstrings.

## gateway/ingest/pipeline.py

**File path**: `gateway/ingest/pipeline.py`
**Purpose**: Pipeline orchestrations for ingestion, chunking, and persistence.
**Dependencies**: External – __future__, collections, collections.abc, concurrent.futures, dataclasses, hashlib, json, logging, opentelemetry, opentelemetry.trace, pathlib, subprocess, time, uuid; Internal – gateway.ingest.artifacts, gateway.ingest.chunking, gateway.ingest.discovery, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.qdrant_writer, gateway.observability.metrics
**Related modules**: gateway.ingest.artifacts, gateway.ingest.chunking, gateway.ingest.discovery, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.qdrant_writer, gateway.observability.metrics

### Classes
- `IngestionConfig` — Configuration options controlling ingestion behaviour.
  - Attributes: `repo_root: Path`; `dry_run: bool = False`; `chunk_window: int = 1000`; `chunk_overlap: int = 200`; `embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'`; `use_dummy_embeddings: bool = False`; `environment: str = 'local'`; `include_patterns: tuple[str, ...] = ('docs', 'src', 'tests', '.codacy')`; `audit_path: Path | None = None`; `coverage_path: Path | None = None`; `coverage_history_limit: int = 5`; `ledger_path: Path | None = None`; `incremental: bool = True`; `embed_parallel_workers: int = 2`; `max_pending_batches: int = 4`
- `IngestionResult` — Summary of outputs emitted by an ingestion run.
  - Attributes: `run_id: str`; `profile: str`; `started_at: float`; `duration_seconds: float`; `artifact_counts: dict[str, int] = field(default_factory=dict)`; `chunk_count: int = 0`; `repo_head: str | None = None`; `success: bool = True`; `artifacts: list[dict[str, object]] = field(default_factory=list)`; `removed_artifacts: list[dict[str, object]] = field(default_factory=list)`
- `IngestionPipeline` — Execute the ingestion workflow end-to-end.
  - Methods: `__init__(` — Initialise the pipeline with writer backends and configuration.; `run(self) -> IngestionResult` — Execute discovery, chunking, embedding, and persistence for a repo.; `_build_embedder(self) -> Embedder` — No docstring provided.; `_encode_batch(self, embedder: Embedder, chunks: Sequence[Chunk]) -> list[list[float]]` — No docstring provided.; `_build_embeddings(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> list[ChunkEmbedding]` — No docstring provided.; `_persist_embeddings(self, embeddings: Sequence[ChunkEmbedding]) -> int` — No docstring provided.; `_handle_stale_artifacts(` — No docstring provided.; `_delete_artifact_from_backends(self, path: str) -> str` — No docstring provided.; `_load_artifact_ledger(self) -> dict[str, dict[str, object]]` — No docstring provided.; `_write_artifact_ledger(self, entries: dict[str, dict[str, object]]) -> None` — No docstring provided.

### Functions
- `_current_repo_head(repo_root: Path) -> str | None` — No docstring provided.
- `_coerce_int(value: object) -> int | None` — No docstring provided.
- `_coerce_float(value: object) -> float | None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- OpenTelemetry tracing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- 8 class method(s) missing docstrings.

## gateway/ingest/qdrant_writer.py

**File path**: `gateway/ingest/qdrant_writer.py`
**Purpose**: Helpers for writing chunk embeddings into Qdrant collections.
**Dependencies**: External – __future__, collections.abc, logging, qdrant_client, qdrant_client.http, qdrant_client.http.exceptions, time, uuid; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

### Classes
- `QdrantWriter` — Lightweight adapter around the Qdrant client.
  - Methods: `__init__(self, client: QdrantClient, collection_name: str) -> None` — Initialise the writer with a target collection.; `ensure_collection(` — Ensure the collection exists without destructive recreation.

The method prefers non-destructive `create_collection` calls. Transient
errors trigger bounded retries with exponential backoff; conflicts are
treated as success. Destructive resets are exposed separately via
:meth:`reset_collection` to make data loss an explicit operator choice.; `reset_collection(self, vector_size: int) -> None` — Destructively recreate the collection, wiping all stored vectors.; `upsert_chunks(self, chunks: Iterable[ChunkEmbedding]) -> None` — Upsert chunk embeddings into the configured collection.; `delete_artifact(self, artifact_path: str) -> None` — Delete all points belonging to an artifact path.; `_collection_exists(self) -> bool` — Return True when the collection already exists in Qdrant.; `_create_collection(self, vector_size: int) -> None` — No docstring provided.

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Qdrant vector database SDK

### Code Quality Notes
- 1 class method(s) missing docstrings.
- Ensure Qdrant client failures are monitored; destructive resets are exposed via reset_collection().

## gateway/ingest/service.py

**File path**: `gateway/ingest/service.py`
**Purpose**: High-level orchestration routines for running ingestion.
**Dependencies**: External – __future__, logging, neo4j, pathlib, qdrant_client; Internal – gateway.config.settings, gateway.ingest.audit, gateway.ingest.coverage, gateway.ingest.lifecycle, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.ingest.qdrant_writer
**Related modules**: gateway.config.settings, gateway.ingest.audit, gateway.ingest.coverage, gateway.ingest.lifecycle, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.ingest.qdrant_writer

### Classes
- None

### Functions
- `execute_ingestion(` — Run ingestion using shared settings and return result.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Discovers repository artifacts, chunks content, embeds text, and persists to Neo4j/Qdrant.

### Integration Points
- Neo4j GraphDatabase driver, Qdrant vector database SDK

### Code Quality Notes
- No major issues detected during static review.

## gateway/lifecycle/__init__.py

**File path**: `gateway/lifecycle/__init__.py`
**Purpose**: Lifecycle reporting package.
**Dependencies**: External – None; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Reads lifecycle report artifacts and presents summaries via CLI.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/lifecycle/cli.py

**File path**: `gateway/lifecycle/cli.py`
**Purpose**: Command-line utilities for inspecting lifecycle health reports.
**Dependencies**: External – __future__, argparse, collections.abc, datetime, json, pathlib, rich.console, rich.table; Internal – gateway.config.settings, gateway.observability
**Related modules**: gateway.config.settings, gateway.observability

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` — Create the CLI argument parser shared across entrypoints.
- `render_table(payload: dict[str, object]) -> None` — Pretty-print the lifecycle report payload using Rich tables.
- `_render_isolated_nodes(value: object) -> None` — Render the isolated node section when data is present.
- `_render_stale_docs(value: object) -> None` — Render the stale documentation summary rows.
- `_render_missing_tests(value: object) -> None` — Render subsystems missing tests in a tabular format.
- `_format_timestamp(value: object) -> str` — Convert a timestamp-like input into an ISO formatted string.
- `main(argv: list[str] | None = None) -> None` — CLI entry point for lifecycle reporting.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Reads lifecycle report artifacts and presents summaries via CLI.

### Integration Points
- Rich console rendering

### Code Quality Notes
- No major issues detected during static review.

## gateway/mcp/__init__.py

**File path**: `gateway/mcp/__init__.py`
**Purpose**: Model Context Protocol server integration for the knowledge gateway.
**Dependencies**: External – None; Internal – gateway.config, gateway.server
**Related modules**: gateway.config, gateway.server

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/mcp/backup.py

**File path**: `gateway/mcp/backup.py`
**Purpose**: Backup helpers for the MCP server.
**Dependencies**: External – __future__, asyncio, os, pathlib, re, typing; Internal – gateway.mcp.config, gateway.mcp.exceptions
**Related modules**: gateway.mcp.config, gateway.mcp.exceptions

### Classes
- None

### Functions
- `trigger_backup(settings: MCPSettings) -> dict[str, Any]` — Invoke the km-backup helper and return the resulting archive metadata.
- `_parse_archive_path(output: str) -> str | None` — No docstring provided.
- `_default_backup_script() -> Path` — No docstring provided.

### Constants and Configuration
- Module-level constants: _BACKUP_DONE_PATTERN
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- 2 helper function(s) missing docstrings.

## gateway/mcp/cli.py

**File path**: `gateway/mcp/cli.py`
**Purpose**: Command-line entry point for the MCP server.
**Dependencies**: External – __future__, argparse, collections.abc, logging, sys; Internal – gateway, gateway.mcp.config, gateway.mcp.server
**Related modules**: gateway, gateway.mcp.config, gateway.mcp.server

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` — Return the CLI parser for launching the MCP server.
- `main(argv: Sequence[str] | None = None) -> int` — Entry point for the MCP server management CLI.

### Constants and Configuration
- Module-level constants: _TRANSPORT_CHOICES
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/mcp/client.py

**File path**: `gateway/mcp/client.py`
**Purpose**: HTTP client for interacting with the gateway API.
**Dependencies**: External – __future__, collections.abc, httpx, json, logging, types, typing, urllib.parse; Internal – gateway.mcp.config, gateway.mcp.exceptions
**Related modules**: gateway.mcp.config, gateway.mcp.exceptions

### Classes
- `GatewayClient` — Thin async wrapper over the gateway REST API.
  - Methods: `__init__(self, settings: MCPSettings) -> None` — No docstring provided.; `__aenter__(self) -> GatewayClient` — Open the underlying HTTP client.; `__aexit__(` — No docstring provided.; `settings(self) -> MCPSettings` — Return the settings used to configure the client.; `search(self, payload: dict[str, Any]) -> dict[str, Any]` — Perform a search request against the gateway.; `graph_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]` — Fetch a graph node by ID.; `graph_subsystem(` — Retrieve subsystem details and related artifacts.; `graph_search(self, term: str, *, limit: int) -> dict[str, Any]` — Perform a graph search by term.; `coverage_summary(self) -> dict[str, Any]` — Fetch the coverage summary endpoint as a dict.; `lifecycle_report(self) -> dict[str, Any]` — Fetch the lifecycle report payload.; `audit_history(self, *, limit: int = 10) -> list[dict[str, Any]]` — Return recent audit history entries.; `_request(` — Issue an HTTP request with token management and error handling.

### Functions
- `_extract_error_detail(response: httpx.Response) -> str` — Extract a human-readable error detail from an HTTP response.
- `_safe_json(response: httpx.Response) -> Mapping[str, object] | list[object] | None` — Safely decode a JSON response, returning ``None`` on failure.
- `_quote_segment(value: str) -> str` — No docstring provided.
- `_expect_dict(data: object, operation: str) -> dict[str, Any]` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- HTTPX async client

### Code Quality Notes
- 2 helper function(s) missing docstrings.
- 2 class method(s) missing docstrings.

## gateway/mcp/config.py

**File path**: `gateway/mcp/config.py`
**Purpose**: Configuration for the MCP adapter.
**Dependencies**: External – __future__, pathlib, pydantic, pydantic_settings, typing; Internal – None
**Related modules**: None

### Classes
- `MCPSettings(BaseSettings)` — Settings controlling the MCP server runtime.
  - Attributes: `gateway_url: str = Field('http://localhost:8000', alias='KM_GATEWAY_URL', description='Base URL of the gateway API')`; `reader_token: str | None = Field(default=None, alias='KM_READER_TOKEN', description='Bearer token for reader-scoped operations')`; `admin_token: str | None = Field(default=None, alias='KM_ADMIN_TOKEN', description='Bearer token for maintainer-scoped operations')`; `request_timeout_seconds: float = Field(default=30.0, alias='KM_MCP_TIMEOUT_SECONDS', description='HTTP request timeout when talking to the gateway')`; `verify_ssl: bool = Field(default=True, alias='KM_MCP_VERIFY_SSL', description='Whether to verify TLS certificates when contacting the gateway')`; `state_path: Path = Field(default=Path('/opt/knowledge/var'), alias='KM_STATE_PATH', description='Path containing gateway state files (audit logs, backups, feedback)')`; `content_root: Path = Field(default=Path('/workspace/repo'), alias='KM_CONTENT_ROOT', description='Root directory where MCP upload/storetext helpers write content')`; `content_docs_subdir: Path = Field(default=Path('docs'), alias='KM_CONTENT_DOCS_SUBDIR', description='Default subdirectory under the content root for text documents')`; `upload_default_overwrite: bool = Field(default=False, alias='KM_UPLOAD_DEFAULT_OVERWRITE', description='Allow MCP uploads to overwrite existing files by default')`; `upload_default_ingest: bool = Field(default=False, alias='KM_UPLOAD_DEFAULT_INGEST', description='Trigger an ingest run immediately after MCP uploads by default')`; `ingest_profile_default: str = Field(default='manual', alias='KM_MCP_DEFAULT_INGEST_PROFILE', description='Default profile label applied to manual ingest runs')`; `ingest_repo_override: Path | None = Field(default=None, alias='KM_MCP_REPO_ROOT', description='Optional repository root override for MCP-triggered ingest runs')`; `backup_script: Path | None = Field(default=None, alias='KM_MCP_BACKUP_SCRIPT', description='Override path to the km-backup helper script')`; `log_requests: bool = Field(default=False, alias='KM_MCP_LOG_REQUESTS', description='Enable verbose logging for outbound HTTP requests')`; `transport: Literal['stdio', 'http', 'sse', 'streamable-http'] = Field(default='stdio', alias='KM_MCP_TRANSPORT', description='Default transport used when launching the MCP server')`; `model_config = {'env_file': None, 'case_sensitive': False, 'extra': 'ignore'}`

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Pydantic validation, Pydantic settings management

### Code Quality Notes
- No major issues detected during static review.

## gateway/mcp/exceptions.py

**File path**: `gateway/mcp/exceptions.py`
**Purpose**: Custom exceptions for the MCP adapter.
**Dependencies**: External – __future__; Internal – None
**Related modules**: None

### Classes
- `MCPAdapterError(Exception)` — Base error raised by the MCP bridge.
- `GatewayRequestError(MCPAdapterError)` — Raised when the gateway API returns an error response.
  - Methods: `__init__(self, *, status_code: int, detail: str, payload: object | None = None) -> None` — No docstring provided.
- `MissingTokenError(MCPAdapterError)` — Raised when a privileged operation lacks an authentication token.
  - Methods: `__init__(self, scope: str) -> None` — No docstring provided.
- `BackupExecutionError(MCPAdapterError)` — Raised when the backup helper fails to produce an archive.

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- Class methods omit docstrings; behaviour inferred from names.

## gateway/mcp/feedback.py

**File path**: `gateway/mcp/feedback.py`
**Purpose**: Feedback logging utilities used by MCP tools.
**Dependencies**: External – __future__, asyncio, collections.abc, datetime, json, pathlib, typing; Internal – gateway.mcp.config
**Related modules**: gateway.mcp.config

### Classes
- None

### Functions
- `record_feedback(` — Append a manual feedback entry to the state directory.
- `_append_line(path: Path, line: str) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- 1 helper function(s) missing docstrings.

## gateway/mcp/ingest.py

**File path**: `gateway/mcp/ingest.py`
**Purpose**: Helpers for managing ingestion workflows via MCP.
**Dependencies**: External – __future__, asyncio, dataclasses, typing; Internal – gateway.config.settings, gateway.ingest.service, gateway.mcp.config
**Related modules**: gateway.config.settings, gateway.ingest.service, gateway.mcp.config

### Classes
- None

### Functions
- `trigger_ingest(` — Execute an ingestion run in a worker thread and return a serialisable summary.
- `latest_ingest_status(` — Return the newest ingest record optionally filtered by profile.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/mcp/server.py

**File path**: `gateway/mcp/server.py`
**Purpose**: FastMCP server exposing the knowledge gateway.
**Dependencies**: External – __future__, collections.abc, contextlib, datetime, fastmcp, functools, json, pathlib, textwrap, time, typing; Internal – gateway, gateway.mcp.backup, gateway.mcp.client, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.feedback, gateway.mcp.ingest, gateway.mcp.storetext, gateway.mcp.upload, gateway.observability.metrics
**Related modules**: gateway, gateway.mcp.backup, gateway.mcp.client, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.feedback, gateway.mcp.ingest, gateway.mcp.storetext, gateway.mcp.upload, gateway.observability.metrics

### Classes
- `MCPServerState` — Holds shared state for the MCP server lifespan.
  - Methods: `__init__(self, settings: MCPSettings) -> None` — No docstring provided.; `require_client(self) -> GatewayClient` — No docstring provided.; `lifespan(self) -> LifespanCallable` — No docstring provided.

### Functions
- `build_server(settings: MCPSettings | None = None) -> FastMCP` — Create a FastMCP server wired to the gateway API.
- `_report_info(context: Context | None, message: str) -> None` — No docstring provided.
- `_report_error(context: Context | None, message: str) -> None` — No docstring provided.
- `_record_success(tool: str, start: float) -> None` — No docstring provided.
- `_record_failure(tool: str, exc: Exception, start: float) -> None` — No docstring provided.
- `_clamp(value: int, *, minimum: int, maximum: int) -> int` — No docstring provided.
- `_normalise_filters(payload: dict[str, Any]) -> dict[str, Any]` — No docstring provided.
- `_resolve_usage(tool: str | None) -> dict[str, Any]` — No docstring provided.
- `_ensure_maintainer_scope(settings: MCPSettings) -> None` — No docstring provided.
- `_append_audit_entry(settings: MCPSettings, *, tool: str, payload: dict[str, Any]) -> None` — No docstring provided.
- `_load_help_document() -> str` — No docstring provided.
- `_initialise_metric_labels() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: HELP_DOC_PATH, TOOL_USAGE
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- FastMCP tool runtime

### Code Quality Notes
- 11 helper function(s) missing docstrings.
- Class methods omit docstrings; behaviour inferred from names.
- Large tool registry; consider splitting into focused helpers.

## gateway/mcp/storetext.py

**File path**: `gateway/mcp/storetext.py`
**Purpose**: Handlers for storing text via MCP.
**Dependencies**: External – __future__, datetime, pathlib, typing; Internal – gateway.mcp.config, gateway.mcp.ingest, gateway.mcp.utils.files
**Related modules**: gateway.mcp.config, gateway.mcp.ingest, gateway.mcp.utils.files

### Classes
- None

### Functions
- `_build_filename(title: str | None) -> str` — No docstring provided.
- `_normalise_destination(destination: str | None, default_dir: Path, filename: str) -> Path` — No docstring provided.
- `_compose_content(` — No docstring provided.
- `handle_storetext(` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## gateway/mcp/upload.py

**File path**: `gateway/mcp/upload.py`
**Purpose**: Handlers for MCP file uploads.
**Dependencies**: External – __future__, pathlib, typing; Internal – gateway.mcp.config, gateway.mcp.ingest, gateway.mcp.utils.files
**Related modules**: gateway.mcp.config, gateway.mcp.ingest, gateway.mcp.utils.files

### Classes
- None

### Functions
- `handle_upload(` — Copy ``source_path`` into the configured content root and optionally trigger ingest.
- `_resolve_destination(destination: str | None, default_dir: Path, filename: str) -> Path` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- 1 helper function(s) missing docstrings.

## gateway/mcp/utils/__init__.py

**File path**: `gateway/mcp/utils/__init__.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – None; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/mcp/utils/files.py

**File path**: `gateway/mcp/utils/files.py`
**Purpose**: Shared helpers for MCP content management.
**Dependencies**: External – __future__, collections.abc, dataclasses, os, pathlib, re, shutil, unicodedata; Internal – None
**Related modules**: None

### Classes
- `DocumentCopyResult` — Result of an attempted document copy.
  - Attributes: `source: Path`; `destination: Path`; `copied: bool`; `overwritten: bool = False`; `reason: str | None = None`
- `DocumentCopyError(Exception)` — Raised when a copy operation fails fatally.

### Functions
- `slugify(value: str, *, fallback: str = "document") -> str` — Create a filesystem-friendly slug.
- `is_supported_document(path: Path) -> bool` — Return ``True`` if the path has a supported document extension.
- `_assert_within_root(root: Path, candidate: Path) -> None` — Ensure ``candidate`` is within ``root`` to prevent path traversal.
- `sweep_documents(` — Copy supported documents under ``root`` into ``target``.
- `copy_into_root(` — Copy ``source`` into ``root``.
- `write_text_document(` — Write ``content`` to ``root / relative_path`` ensuring safety.

### Constants and Configuration
- Module-level constants: SUPPORTED_EXTENSIONS, _SLUG_REGEX
- Environment variables: Not detected in static scan

### Data Flow
- Translates MCP tool invocations into gateway API calls and filesystem operations.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/observability/__init__.py

**File path**: `gateway/observability/__init__.py`
**Purpose**: Observability utilities (metrics, logging, tracing).
**Dependencies**: External – None; Internal – gateway.logging, gateway.metrics, gateway.tracing
**Related modules**: gateway.logging, gateway.metrics, gateway.tracing

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Configures logging, metrics, and tracing instrumentation.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/observability/logging.py

**File path**: `gateway/observability/logging.py`
**Purpose**: Structured logging configuration for the gateway.
**Dependencies**: External – __future__, logging, pythonjsonlogger, sys, typing; Internal – None
**Related modules**: None

### Classes
- `IngestAwareFormatter(json.JsonFormatter)` — JSON formatter that enforces consistent keys.
  - Methods: `add_fields(` — No docstring provided.

### Functions
- `configure_logging() -> None` — Configure root logging with a JSON formatter once per process.

### Constants and Configuration
- Module-level constants: _LOG_CONFIGURED
- Environment variables: Not detected in static scan

### Data Flow
- Configures logging, metrics, and tracing instrumentation.

### Integration Points
- Structured JSON logging

### Code Quality Notes
- Class methods omit docstrings; behaviour inferred from names.

## gateway/observability/metrics.py

**File path**: `gateway/observability/metrics.py`
**Purpose**: Prometheus metric definitions for the knowledge gateway.
**Dependencies**: External – __future__, prometheus_client; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: COVERAGE_HISTORY_SNAPSHOTS, COVERAGE_LAST_RUN_STATUS, COVERAGE_LAST_RUN_TIMESTAMP, COVERAGE_MISSING_ARTIFACTS, COVERAGE_STALE_ARTIFACTS, GRAPH_CYPHER_DENIED_TOTAL, GRAPH_MIGRATION_LAST_STATUS, GRAPH_MIGRATION_LAST_TIMESTAMP, INGEST_ARTIFACTS_TOTAL, INGEST_CHUNKS_TOTAL, INGEST_DURATION_SECONDS, INGEST_LAST_RUN_STATUS, INGEST_LAST_RUN_TIMESTAMP, INGEST_SKIPS_TOTAL, INGEST_STALE_RESOLVED_TOTAL, LIFECYCLE_HISTORY_SNAPSHOTS, LIFECYCLE_ISOLATED_NODES_TOTAL, LIFECYCLE_LAST_RUN_STATUS, LIFECYCLE_LAST_RUN_TIMESTAMP, LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL, LIFECYCLE_REMOVED_ARTIFACTS_TOTAL, LIFECYCLE_STALE_DOCS_TOTAL, MCP_FAILURES_TOTAL, MCP_REQUESTS_TOTAL, MCP_REQUEST_SECONDS, MCP_STORETEXT_TOTAL, MCP_UPLOAD_TOTAL, SCHEDULER_LAST_SUCCESS_TIMESTAMP, SCHEDULER_RUNS_TOTAL, SEARCH_GRAPH_CACHE_EVENTS, SEARCH_GRAPH_LOOKUP_SECONDS, SEARCH_REQUESTS_TOTAL, SEARCH_SCORE_DELTA, UI_EVENTS_TOTAL, UI_REQUESTS_TOTAL, WATCH_RUNS_TOTAL
- Environment variables: Not detected in static scan

### Data Flow
- Configures logging, metrics, and tracing instrumentation.

### Integration Points
- Prometheus metrics client

### Code Quality Notes
- No major issues detected during static review.

## gateway/observability/tracing.py

**File path**: `gateway/observability/tracing.py`
**Purpose**: Tracing helpers for wiring OpenTelemetry exporters.
**Dependencies**: External – __future__, fastapi, opentelemetry, opentelemetry.exporter.otlp.proto.http.trace_exporter, opentelemetry.instrumentation.fastapi, opentelemetry.instrumentation.requests, opentelemetry.sdk.resources, opentelemetry.sdk.trace, opentelemetry.sdk.trace.export, opentelemetry.sdk.trace.sampling; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

### Classes
- None

### Functions
- `configure_tracing(app: FastAPI | None, settings: AppSettings) -> None` — Configure OpenTelemetry tracing based on runtime settings.
- `_select_exporter(settings: AppSettings) -> SpanExporter` — Choose the span exporter based on settings.
- `_parse_headers(header_string: str | None) -> dict[str, str] | None` — Parse comma-separated OTLP header strings into a dict.
- `reset_tracing_for_tests() -> None` — Reset module-level state so tests can reconfigure tracing cleanly.

### Constants and Configuration
- Module-level constants: _TRACING_CONFIGURED
- Environment variables: Not detected in static scan

### Data Flow
- Configures logging, metrics, and tracing instrumentation.

### Integration Points
- FastAPI web framework, OpenTelemetry tracing

### Code Quality Notes
- No major issues detected during static review.

## gateway/plugins/__init__.py

**File path**: `gateway/plugins/__init__.py`
**Purpose**: Plugin namespace for future ingestion extensions.
**Dependencies**: External – None; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Namespace placeholder for future plugin registrations.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/recipes/__init__.py

**File path**: `gateway/recipes/__init__.py`
**Purpose**: Utilities for running knowledge recipes.
**Dependencies**: External – None; Internal – gateway.executor, gateway.models
**Related modules**: gateway.executor, gateway.models

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Loads, validates, and executes MCP automation recipes via gateway tools.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/recipes/cli.py

**File path**: `gateway/recipes/cli.py`
**Purpose**: Command-line utilities for inspecting and running MCP recipes.
**Dependencies**: External – __future__, argparse, asyncio, collections.abc, json, logging, pathlib, pydantic, rich.console, rich.table, typing; Internal – gateway.mcp.config, gateway.recipes.executor, gateway.recipes.models
**Related modules**: gateway.mcp.config, gateway.recipes.executor, gateway.recipes.models

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` — Construct the top-level argument parser for the CLI.
- `load_recipe_by_name(recipes_dir: Path, name: str) -> Recipe` — Load a recipe by stem name from the given directory.
- `parse_variables(pairs: list[str]) -> dict[str, str]` — Parse ``key=value`` overrides supplied on the command line.
- `command_list(args: argparse.Namespace) -> None` — List recipes available in the configured directory.
- `command_show(args: argparse.Namespace) -> None` — Print a single recipe definition in JSON form.
- `command_validate(args: argparse.Namespace) -> None` — Validate one or all recipes and report the outcome.
- `recipe_executor_factory(settings: MCPSettings) -> Callable[[], GatewayToolExecutor]` — Create a factory that instantiates a gateway-backed tool executor.
- `command_run(args: argparse.Namespace, settings: MCPSettings) -> None` — Execute a recipe and render the results.
- `_render_run_result(result: dict[str, Any]) -> None` — Pretty-print a recipe execution result in tabular form.
- `main(argv: list[str] | None = None) -> None` — Entry point for the recipes CLI.

### Constants and Configuration
- Module-level constants: DEFAULT_RECIPES_DIR
- Environment variables: Not detected in static scan

### Data Flow
- Loads, validates, and executes MCP automation recipes via gateway tools.

### Integration Points
- Pydantic validation, Rich console rendering

### Code Quality Notes
- No major issues detected during static review.

## gateway/recipes/executor.py

**File path**: `gateway/recipes/executor.py`
**Purpose**: Recipe execution layer for automating MCP-driven workflows.
**Dependencies**: External – __future__, asyncio, collections.abc, contextlib, dataclasses, json, logging, pathlib, re, time, types, yaml; Internal – gateway.mcp.backup, gateway.mcp.client, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.ingest, gateway.recipes.models
**Related modules**: gateway.mcp.backup, gateway.mcp.client, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.ingest, gateway.recipes.models

### Classes
- `RecipeExecutionError(RuntimeError)` — Raised when a recipe step fails.
- `StepResult` — Lightweight representation of a single recipe step outcome.
  - Attributes: `step_id: str`; `status: str`; `duration_seconds: float`; `result: object | None = None`; `message: str | None = None`
- `RecipeRunResult` — Aggregate outcome for a recipe execution, including captured outputs.
  - Attributes: `recipe: Recipe`; `started_at: float`; `finished_at: float`; `success: bool`; `steps: list[StepResult] = field(default_factory=list)`; `outputs: dict[str, object] = field(default_factory=dict)`
  - Methods: `to_dict(self) -> dict[str, object]` — Serialise the run result to a JSON-friendly mapping.
- `ToolExecutor` — Abstract tool executor interface.
  - Methods: `call(self, tool: str, params: dict[str, object]) -> object:  # pragma: no cover - interface` — Invoke a named tool with the given parameters.; `__aenter__(self) -> ToolExecutor:  # pragma: no cover - interface` — Allow derived executors to perform async setup.; `__aexit__(` — Allow derived executors to perform async teardown.
- `GatewayToolExecutor(ToolExecutor)` — Execute tools by reusing gateway HTTP/MCP helpers.
  - Methods: `__init__(self, settings: MCPSettings) -> None` — No docstring provided.; `__aenter__(self) -> GatewayToolExecutor` — Open the shared gateway client for tool execution.; `__aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` — Close the shared gateway client when execution completes.; `call(self, tool: str, params: dict[str, object]) -> object` — Route tool invocations to the appropriate gateway operation.
- `RecipeRunner` — Run recipes using the configured MCP settings.
  - Methods: `__init__(` — No docstring provided.; `make_executor(self) -> ToolExecutor` — Instantiate a tool executor using the configured factory.; `run(` — Execute a recipe end-to-end and return the collected results.; `_execute_wait(` — Repeatedly invoke a wait tool until the condition passes or times out.; `_append_audit(self, result: RecipeRunResult, context: dict[str, object]) -> None` — Append the recipe outcome to the on-disk audit log.

### Functions
- `_resolve_template(value: object, context: Mapping[str, object]) -> object` — No docstring provided.
- `_lookup_expression(expr: str, context: Mapping[str, object]) -> object` — No docstring provided.
- `_descend(current: object, part: str) -> object` — No docstring provided.
- `_evaluate_condition(result: object, condition: Condition) -> None` — No docstring provided.
- `_compute_capture(result: object, capture: Capture) -> object` — No docstring provided.
- `_executor_cm(factory: Callable[[], ToolExecutor]) -> AsyncIterator[ToolExecutor]` — Context manager that yields a tool executor from the provided factory.
- `load_recipe(path: Path) -> Recipe` — Load a recipe file from disk and validate the schema.
- `_ensure_object_map(value: object, label: str) -> dict[str, object]` — Ensure template resolution returned a mapping, raising otherwise.
- `_require_str(params: Mapping[str, object], key: str) -> str` — Fetch a required string parameter from a mapping of arguments.
- `_coerce_optional_str(value: object | None) -> str | None` — Convert optional string-like values to trimmed strings.
- `_coerce_positive_int(value: object | None, *, default: int) -> int` — Convert inputs to a positive integer, falling back to the default.
- `_coerce_int(value: object | None) -> int | None` — Coerce common primitive values to an integer when possible.
- `_coerce_bool(value: object | None, *, default: bool | None = None) -> bool | None` — Interpret truthy/falsey string values and return a boolean.
- `list_recipes(recipes_dir: Path) -> list[Path]` — Return all recipe definition files within the directory.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Loads, validates, and executes MCP automation recipes via gateway tools.

### Integration Points
- Standard library only

### Code Quality Notes
- 5 helper function(s) missing docstrings.
- 2 class method(s) missing docstrings.

## gateway/recipes/models.py

**File path**: `gateway/recipes/models.py`
**Purpose**: Pydantic models describing MCP recipe configuration.
**Dependencies**: External – __future__, pydantic, typing; Internal – None
**Related modules**: None

### Classes
- `Condition(BaseModel)` — Assertion condition evaluated against a step result.
  - Attributes: `path: str = Field(description='Dot path into the result payload')`; `equals: Any | None = None`; `not_equals: Any | None = None`; `exists: bool | None = None`
- `Capture(BaseModel)` — Capture part of a step result into the execution context.
  - Attributes: `name: str`; `path: str | None = None`
- `WaitConfig(BaseModel)` — Poll a tool until a condition is satisfied.
  - Attributes: `tool: str = Field(description='Tool to invoke while waiting')`; `params: dict[str, Any] = Field(default_factory=dict)`; `until: Condition = Field(description='Condition that terminates the wait')`; `interval_seconds: float = Field(default=5.0, ge=0.5, description='Polling interval')`; `timeout_seconds: float = Field(default=300.0, ge=1.0, description='Timeout before failing')`
- `RecipeStep(BaseModel)` — Single step inside a recipe.
  - Attributes: `id: str`; `description: str | None = None`; `tool: str | None = None`; `params: dict[str, Any] = Field(default_factory=dict)`; `expect: dict[str, Any] | None = None`; `asserts: list[Condition] | None = Field(default=None, alias='assert')`; `capture: list[Capture] | None = None`; `wait: WaitConfig | None = None`; `prompt: str | None = None`
  - Methods: `validate_mode(self) -> RecipeStep` — Ensure mutually exclusive tool/wait configuration is respected.
- `Recipe(BaseModel)` — Top level recipe definition.
  - Attributes: `version: int = Field(1, description='Schema version')`; `name: str`; `summary: str | None = None`; `variables: dict[str, Any] = Field(default_factory=dict)`; `steps: list[RecipeStep]`; `outputs: dict[str, str] = Field(default_factory=dict)`
  - Methods: `ensure_unique_step_ids(self) -> Recipe` — Verify step identifiers are unique within the recipe.

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Loads, validates, and executes MCP automation recipes via gateway tools.

### Integration Points
- Pydantic validation

### Code Quality Notes
- No major issues detected during static review.

## gateway/scheduler.py

**File path**: `gateway/scheduler.py`
**Purpose**: Background scheduler that drives periodic ingestion runs.
**Dependencies**: External – __future__, apscheduler.schedulers.background, apscheduler.schedulers.base, apscheduler.triggers.cron, apscheduler.triggers.interval, collections.abc, contextlib, filelock, logging, pathlib, subprocess, time; Internal – gateway.config.settings, gateway.ingest.service, gateway.observability.metrics
**Related modules**: gateway.config.settings, gateway.ingest.service, gateway.observability.metrics

### Classes
- `IngestionScheduler` — APScheduler wrapper that coordinates repo-aware ingestion jobs.
  - Methods: `__init__(self, settings: AppSettings) -> None` — Initialise scheduler state and ensure the scratch directory exists.; `start(self) -> None` — Register the ingestion job and begin scheduling if enabled.; `shutdown(self) -> None` — Stop the scheduler and release APScheduler resources.; `_run_ingestion(self) -> None` — Execute a single ingestion cycle, guarding with a file lock.; `_read_last_head(self) -> str | None` — No docstring provided.; `_write_last_head(self, head: str) -> None` — No docstring provided.

### Functions
- `_current_repo_head(repo_root: Path) -> str | None` — Return the git HEAD sha for the repo, or ``None`` when unavailable.
- `_build_trigger(config: Mapping[str, object]) -> CronTrigger | IntervalTrigger` — Construct the APScheduler trigger based on user configuration.
- `_describe_trigger(config: Mapping[str, object]) -> str` — Provide a human readable summary of the configured trigger.
- `_coerce_positive_int(value: object, *, default: int) -> int` — Best-effort conversion to a positive integer with sane defaults.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- General-purpose helpers supporting the knowledge gateway.

### Integration Points
- APScheduler background scheduling, File locking utilities

### Code Quality Notes
- 2 class method(s) missing docstrings.

## gateway/search/__init__.py

**File path**: `gateway/search/__init__.py`
**Purpose**: Search service exposing vector search with graph context.
**Dependencies**: External – None; Internal – gateway.dataset, gateway.evaluation, gateway.exporter, gateway.feedback, gateway.maintenance, gateway.service
**Related modules**: gateway.dataset, gateway.evaluation, gateway.exporter, gateway.feedback, gateway.maintenance, gateway.service

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/search/cli.py

**File path**: `gateway/search/cli.py`
**Purpose**: Command-line helpers for search training, exports, and maintenance.
**Dependencies**: External – __future__, argparse, datetime, logging, pathlib, rich.console; Internal – gateway.config.settings, gateway.observability, gateway.search.evaluation, gateway.search.exporter, gateway.search.maintenance, gateway.search.trainer
**Related modules**: gateway.config.settings, gateway.observability, gateway.search.evaluation, gateway.search.exporter, gateway.search.maintenance, gateway.search.trainer

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` — Return an argument parser covering all search CLI commands.
- `export_training_data(` — Materialise feedback events into a training dataset file.
- `train_model(` — Train a ranking model from a prepared dataset and save the artifact.
- `show_weights(*, settings: AppSettings) -> None` — Print the active search weight profile to the console.
- `prune_feedback(*, settings: AppSettings, max_age_days: int | None, max_requests: int | None, output: Path | None) -> None` — Trim feedback logs by age/request count and optionally archive removals.
- `redact_training_dataset(` — Strip sensitive fields and emit a sanitized dataset.
- `evaluate_trained_model(*, dataset: Path, model: Path) -> None` — Run offline evaluation of a trained model against a labelled dataset.
- `main(argv: list[str] | None = None) -> None` — Entry point for the `gateway-search` command-line interface.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Rich console rendering

### Code Quality Notes
- No major issues detected during static review.

## gateway/search/dataset.py

**File path**: `gateway/search/dataset.py`
**Purpose**: Utilities for reading and preparing search training datasets.
**Dependencies**: External – __future__, collections.abc, csv, json, pathlib; Internal – gateway.search.exporter
**Related modules**: gateway.search.exporter

### Classes
- `DatasetLoadError(RuntimeError)` — Raised when a dataset cannot be parsed.

### Functions
- `load_dataset_records(path: Path) -> list[Mapping[str, object]]` — Load dataset rows from disk, raising when the file is missing.
- `build_feature_matrix(` — Convert dataset rows into numeric feature vectors and targets.
- `_parse_float(value: object) -> float | None` — No docstring provided.

### Constants and Configuration
- Module-level constants: TARGET_FIELD
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Standard library only

### Code Quality Notes
- 1 helper function(s) missing docstrings.

## gateway/search/evaluation.py

**File path**: `gateway/search/evaluation.py`
**Purpose**: Model evaluation utilities for the search ranking pipeline.
**Dependencies**: External – __future__, collections.abc, dataclasses, math, numpy, numpy.typing, pathlib, statistics, typing; Internal – gateway.search.dataset, gateway.search.trainer
**Related modules**: gateway.search.dataset, gateway.search.trainer

### Classes
- `EvaluationMetrics` — Aggregate metrics produced after evaluating a ranking model.
  - Attributes: `mse: float`; `r2: float`; `ndcg_at_5: float`; `ndcg_at_10: float`; `spearman: float | None`

### Functions
- `evaluate_model(dataset_path: Path, model_path: Path) -> EvaluationMetrics` — Load a dataset and model artifact, returning evaluation metrics.
- `_mean_ndcg(request_ids: Sequence[str], relevance: FloatArray, scores: FloatArray, *, k: int) -> float` — Compute mean NDCG@k for groups identified by request ids.
- `_dcg(relevances: FloatArray, k: int) -> float` — Compute discounted cumulative gain at rank ``k``.
- `_spearman_correlation(y_true: FloatArray, y_pred: FloatArray) -> float | None` — Return Spearman rank correlation between true and predicted values.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- NumPy numeric routines

### Code Quality Notes
- No major issues detected during static review.

## gateway/search/exporter.py

**File path**: `gateway/search/exporter.py`
**Purpose**: Utilities for exporting feedback logs into training datasets.
**Dependencies**: External – __future__, collections.abc, csv, dataclasses, json, logging, pathlib, typing; Internal – None
**Related modules**: None

### Classes
- `ExportOptions` — User-configurable options controlling dataset export.
  - Attributes: `output_path: Path`; `output_format: FeedbackFormat`; `require_vote: bool = False`; `limit: int | None = None`
- `ExportStats` — Basic statistics about the export process.
  - Attributes: `total_events: int`; `written_rows: int`; `skipped_without_vote: int`

### Functions
- `export_training_dataset(events_path: Path, *, options: ExportOptions) -> ExportStats` — Write feedback events into the requested dataset format.
- `iter_feedback_events(path: Path) -> Iterator[dict[str, Any]]` — Yield feedback events from a JSON lines log file.
- `_write_csv(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats` — Write feedback events into a CSV file.
- `_write_jsonl(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats` — Write feedback events into a JSONL file.
- `_flatten_event(event: dict[str, Any]) -> dict[str, Any]` — Flatten nested event data into scalar fields.

### Constants and Configuration
- Module-level constants: FIELDNAMES
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/search/feedback.py

**File path**: `gateway/search/feedback.py`
**Purpose**: Persistent storage helpers for search feedback events.
**Dependencies**: External – __future__, collections.abc, datetime, json, pathlib, threading, uuid; Internal – gateway.search.service
**Related modules**: gateway.search.service

### Classes
- `SearchFeedbackStore` — Append-only store for search telemetry and feedback.
  - Methods: `__init__(self, root: Path) -> None` — Initialise the feedback store beneath the given directory.; `record(` — Persist a feedback event for the supplied search response.; `_append(self, rows: Sequence[Mapping[str, object]]) -> None` — No docstring provided.

### Functions
- `_serialize_results(` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Standard library only

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- 1 class method(s) missing docstrings.

## gateway/search/maintenance.py

**File path**: `gateway/search/maintenance.py`
**Purpose**: Maintenance routines for pruning feedback logs and redacting datasets.
**Dependencies**: External – __future__, collections.abc, csv, dataclasses, datetime, json, logging, pathlib, shutil; Internal – gateway.search.exporter
**Related modules**: gateway.search.exporter

### Classes
- `PruneOptions` — Configures retention rules for the feedback log pruning routine.
  - Attributes: `max_age_days: int | None = None`; `max_requests: int | None = None`; `output_path: Path | None = None`; `current_time: datetime | None = None`
- `PruneStats` — Summary of how many feedback requests were kept versus removed.
  - Attributes: `total_requests: int`; `retained_requests: int`; `removed_requests: int`
- `RedactOptions` — Toggles that control which sensitive fields should be redacted.
  - Attributes: `output_path: Path | None = None`; `drop_query: bool = False`; `drop_context: bool = False`; `drop_note: bool = False`
- `RedactStats` — Summary of how many dataset rows required redaction.
  - Attributes: `total_rows: int`; `redacted_rows: int`

### Functions
- `prune_feedback_log(events_path: Path, *, options: PruneOptions) -> PruneStats` — Prune feedback requests based on age and count thresholds.
- `redact_dataset(dataset_path: Path, *, options: RedactOptions) -> RedactStats` — Redact sensitive fields from datasets stored as CSV or JSON Lines.
- `_parse_timestamp(value: object) -> datetime | None` — Parse timestamps stored as numbers or ISO 8601 strings.
- `_collect_events(` — No docstring provided.
- `_build_timestamps(events_by_request: MutableMapping[str, list[dict[str, object]]]) -> dict[str, datetime]` — No docstring provided.
- `_apply_prune_filters(` — No docstring provided.
- `_preserve_original_order(order: list[str], selected_ids: Iterable[str]) -> list[str]` — No docstring provided.
- `_write_retained_events(` — No docstring provided.
- `_redact_csv(source: Path, destination: Path, options: RedactOptions) -> RedactStats` — Redact sensitive columns from a CSV dataset.
- `_redact_csv_row(row: MutableMapping[str, str], options: RedactOptions) -> bool` — No docstring provided.
- `_clear_field(row: MutableMapping[str, str], field: str, replacement: str) -> bool` — No docstring provided.
- `_redact_jsonl(source: Path, destination: Path, options: RedactOptions) -> RedactStats` — Redact sensitive fields from JSON lines datasets.
- `_redact_json_record(record: MutableMapping[str, object], options: RedactOptions) -> bool` — No docstring provided.
- `_null_field(record: MutableMapping[str, object], field: str) -> bool` — No docstring provided.

### Constants and Configuration
- Module-level constants: _FALLBACK_TIMESTAMP
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Standard library only

### Code Quality Notes
- 9 helper function(s) missing docstrings.

## gateway/search/service.py

**File path**: `gateway/search/service.py`
**Purpose**: Hybrid search orchestration for Duskmantle's knowledge gateway.
**Dependencies**: External – __future__, collections.abc, dataclasses, datetime, logging, neo4j.exceptions, qdrant_client, qdrant_client.http.models, re, time, typing; Internal – gateway.graph.service, gateway.ingest.embedding, gateway.observability, gateway.search.trainer
**Related modules**: gateway.graph.service, gateway.ingest.embedding, gateway.observability, gateway.search.trainer

### Classes
- `SearchResult` — Single ranked chunk returned from the search pipeline.
  - Attributes: `chunk: dict[str, Any]`; `graph_context: dict[str, Any] | None`; `scoring: dict[str, Any]`
- `SearchResponse` — API-friendly container for search results and metadata.
  - Attributes: `query: str`; `results: list[SearchResult]`; `metadata: dict[str, Any]`
- `SearchOptions` — Runtime options controlling the search service behaviour.
  - Attributes: `max_limit: int = 25`; `graph_timeout_seconds: float = 0.25`; `hnsw_ef_search: int | None = None`; `scoring_mode: Literal['heuristic', 'ml'] = 'heuristic'`; `weight_profile: str = 'custom'`; `slow_graph_warn_seconds: float = 0.25`
- `SearchWeights` — Weighting configuration for hybrid scoring.
  - Attributes: `subsystem: float = 0.3`; `relationship: float = 0.05`; `support: float = 0.1`; `coverage_penalty: float = 0.15`; `criticality: float = 0.12`; `vector: float = 1.0`; `lexical: float = 0.25`
- `FilterState` — Preprocessed filter collections derived from request parameters.
  - Attributes: `allowed_subsystems: set[str]`; `allowed_types: set[str]`; `allowed_namespaces: set[str]`; `allowed_tags: set[str]`; `filters_applied: dict[str, Any]`; `recency_cutoff: datetime | None`; `recency_warning_emitted: bool = False`
- `CoverageInfo` — Coverage characteristics used during scoring.
  - Attributes: `ratio: float`; `penalty: float`; `missing_flag: float`
- `SearchService` — Execute hybrid vector/graph search with heuristic or ML scoring.
  - Methods: `__init__(` — Initialise the search service with vector and scoring options.; `search(` — Execute a hybrid search request and return ranked results.; `_resolve_graph_context(` — Fetch and cache graph context for a search result chunk.; `_build_model_features(` — No docstring provided.; `_apply_model(self, features: dict[str, float]) -> tuple[float, dict[str, float]]` — No docstring provided.

### Functions
- `_label_for_artifact(artifact_type: str | None) -> str` — No docstring provided.
- `_summarize_graph_context(data: dict[str, Any]) -> dict[str, Any]` — No docstring provided.
- `_subsystems_from_context(graph_context: dict[str, Any] | None) -> set[str]` — No docstring provided.
- `_detect_query_subsystems(query: str) -> set[str]` — No docstring provided.
- `_normalise_hybrid_weights(vector_weight: float, lexical_weight: float) -> tuple[float, float]` — No docstring provided.
- `_prepare_filter_state(filters: dict[str, Any]) -> FilterState` — No docstring provided.
- `_passes_payload_filters(payload: dict[str, Any], state: FilterState) -> bool` — No docstring provided.
- `_normalise_payload_tags(raw_tags: Sequence[object] | set[object] | None) -> set[str]` — No docstring provided.
- `_build_chunk(payload: dict[str, Any], score: float) -> dict[str, Any]` — No docstring provided.
- `_calculate_subsystem_affinity(subsystem: str, query_tokens: set[str]) -> float` — No docstring provided.
- `_calculate_supporting_bonus(related_artifacts: Iterable[dict[str, Any]]) -> float` — No docstring provided.
- `_calculate_coverage_info(chunk: dict[str, Any], weight_coverage_penalty: float) -> CoverageInfo` — No docstring provided.
- `_coerce_ratio_value(value: object) -> float | None` — No docstring provided.
- `_calculate_criticality_score(chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> float` — No docstring provided.
- `_update_path_depth_signal(` — No docstring provided.
- `_ensure_criticality_signal(` — No docstring provided.
- `_ensure_freshness_signal(` — No docstring provided.
- `_ensure_coverage_ratio_signal(signals: dict[str, Any], chunk: dict[str, Any]) -> None` — No docstring provided.
- `_lexical_score(query: str, chunk: dict[str, Any]) -> float` — No docstring provided.
- `_base_scoring(` — No docstring provided.
- `_compute_scoring(` — No docstring provided.
- `_populate_additional_signals(` — No docstring provided.
- `_estimate_path_depth(graph_context: dict[str, Any] | None) -> float` — No docstring provided.
- `_extract_subsystem_criticality(graph_context: dict[str, Any] | None) -> str | None` — No docstring provided.
- `_normalise_criticality(value: str | float | None) -> float` — No docstring provided.
- `_compute_freshness_days(` — No docstring provided.
- `_resolve_chunk_datetime(` — No docstring provided.
- `_parse_iso_datetime(value: object) -> datetime | None` — No docstring provided.

### Constants and Configuration
- Module-level constants: _TOKEN_PATTERN
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- Neo4j GraphDatabase driver, Qdrant vector database SDK

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- 2 class method(s) missing docstrings.
- Complex scoring pipeline; ensure regression tests cover weighting changes.

## gateway/search/trainer.py

**File path**: `gateway/search/trainer.py`
**Purpose**: Training utilities for search ranking models.
**Dependencies**: External – __future__, collections.abc, dataclasses, datetime, json, math, numpy, pathlib; Internal – gateway.search.dataset
**Related modules**: gateway.search.dataset

### Classes
- `TrainingResult` — Capture optimiser output for debug or inspection.
  - Attributes: `weights: list[float]`; `intercept: float`; `mse: float`; `r2: float`; `rows: int`
- `ModelArtifact` — Persisted search model metadata and coefficients.
  - Attributes: `model_type: str`; `created_at: str`; `feature_names: list[str]`; `coefficients: list[float]`; `intercept: float`; `metrics: dict[str, float]`; `training_rows: int`

### Functions
- `train_from_dataset(path: Path) -> ModelArtifact` — Train a logistic regression model from the labelled dataset.
- `save_artifact(artifact: ModelArtifact, path: Path) -> None` — Write the model artifact to disk as JSON.
- `load_artifact(path: Path) -> ModelArtifact` — Load a saved model artifact from disk.
- `_linear_regression(X: np.ndarray, y: np.ndarray) -> TrainingResult` — No docstring provided.

### Constants and Configuration
- Module-level constants: FEATURE_FIELDS
- Environment variables: Not detected in static scan

### Data Flow
- Transforms user queries into vector search, graph enrichment, and ranked responses.

### Integration Points
- NumPy numeric routines

### Code Quality Notes
- 1 helper function(s) missing docstrings.

## gateway/ui/__init__.py

**File path**: `gateway/ui/__init__.py`
**Purpose**: UI utilities and routers.
**Dependencies**: External – None; Internal – gateway.routes
**Related modules**: gateway.routes

### Classes
- None

### Functions
- None

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Serves embedded UI templates/static assets and logs browser telemetry.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## gateway/ui/routes.py

**File path**: `gateway/ui/routes.py`
**Purpose**: UI router exposing static assets and HTML entry points.
**Dependencies**: External – __future__, fastapi, fastapi.responses, fastapi.templating, json, logging, pathlib; Internal – gateway.config.settings, gateway.observability
**Related modules**: gateway.config.settings, gateway.observability

### Classes
- None

### Functions
- `get_static_path() -> Path` — Return the absolute path to UI static assets.
- `ui_index(request: Request) -> HTMLResponse` — Render the landing page for the embedded UI.
- `ui_search(request: Request) -> HTMLResponse` — Render the search console view.
- `ui_subsystems(request: Request) -> HTMLResponse` — Render the subsystem explorer view.
- `ui_lifecycle(request: Request) -> HTMLResponse` — Render the lifecycle dashboard view.
- `ui_lifecycle_report(request: Request) -> JSONResponse` — Serve the lifecycle report JSON while recording UI metrics.
- `ui_event(request: Request, payload: dict[str, object]) -> JSONResponse` — Record a UI event for observability purposes.

### Constants and Configuration
- Module-level constants: STATIC_DIR, TEMPLATES_DIR
- Environment variables: Not detected in static scan

### Data Flow
- Serves embedded UI templates/static assets and logs browser telemetry.

### Integration Points
- FastAPI web framework

### Code Quality Notes
- No major issues detected during static review.

## scripts/generate-changelog.py

**File path**: `scripts/generate-changelog.py`
**Purpose**: Generate changelog entries from Conventional Commits.
**Dependencies**: External – __future__, argparse, collections, datetime, pathlib, subprocess, sys; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_run_git(args: list[str]) -> str` — No docstring provided.
- `discover_commits(since: str | None) -> list[str]` — No docstring provided.
- `categorize(commits: list[str]) -> dict[str, list[str]]` — No docstring provided.
- `update_changelog(version: str, released: str, entries: dict[str, list[str]]) -> None` — No docstring provided.
- `main() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: CATEGORY_MAP, CHANGELOG, ROOT
- Environment variables: Not detected in static scan

### Data Flow
- Provides repository maintenance or release automation helpers.

### Integration Points
- Standard library only

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

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
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Standard library only

### Code Quality Notes
- No major issues detected during static review.

## tests/conftest.py

**File path**: `tests/conftest.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, collections.abc, neo4j, os, pytest, shutil, subprocess, sys, time, types, typing, uuid, warnings; Internal – None
**Related modules**: None

### Classes
- `_NullSession` — No docstring provided.
  - Methods: `__enter__(self) -> _NullSession:  # pragma: no cover - trivial` — No docstring provided.; `__exit__(` — No docstring provided.; `execute_read(self, func: object, *args: object, **kwargs: object) -> NoReturn:  # pragma: no cover - defensive` — No docstring provided.; `run(self, *args: object, **kwargs: object) -> NoReturn:  # pragma: no cover - defensive` — No docstring provided.
- `_NullDriver` — No docstring provided.
  - Methods: `session(self, **kwargs: object) -> _NullSession:  # pragma: no cover - trivial` — No docstring provided.; `close(self) -> None:  # pragma: no cover - trivial` — No docstring provided.

### Functions
- `disable_real_graph_driver(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None` — No docstring provided.
- `neo4j_test_environment() -> Iterator[dict[str, str | None]]` — No docstring provided.
- `pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Neo4j GraphDatabase driver, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/mcp/test_server_tools.py

**File path**: `tests/mcp/test_server_tools.py`
**Purpose**: Integration tests for MCP server tools and metrics wiring.
**Dependencies**: External – __future__, asyncio, collections.abc, pathlib, prometheus_client, pytest, typing; Internal – gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.server, gateway.observability.metrics
**Related modules**: gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.server, gateway.observability.metrics

### Classes
- None

### Functions
- `_reset_mcp_metrics() -> Iterator[None]` — No docstring provided.
- `mcp_server() -> Iterator[ServerFixture]` — No docstring provided.
- `_counter_value(counter: Counter, *labels: str) -> float` — No docstring provided.
- `_histogram_sum(histogram: Histogram, *labels: str) -> float` — No docstring provided.
- `_upload_counter(result: str) -> float` — No docstring provided.
- `_storetext_counter(result: str) -> float` — No docstring provided.
- `_tool_fn(tool: object) -> ToolCallable` — No docstring provided.
- `test_km_help_lists_tools_and_provides_details(` — No docstring provided.
- `test_metrics_export_includes_tool_labels(` — No docstring provided.
- `test_km_search_success_records_metrics(` — No docstring provided.
- `test_km_search_gateway_error_records_failure(` — No docstring provided.
- `test_graph_tools_delegate_to_client_and_record_metrics(` — No docstring provided.
- `test_lifecycle_report_records_metrics(` — No docstring provided.
- `test_coverage_summary_records_metrics(` — No docstring provided.
- `test_ingest_status_handles_missing_history(` — No docstring provided.
- `test_ingest_trigger_succeeds(` — No docstring provided.
- `test_ingest_trigger_failure_records_metrics(` — No docstring provided.
- `test_backup_trigger(` — No docstring provided.
- `test_feedback_submit(` — No docstring provided.
- `test_km_upload_copies_file_and_records_metrics(tmp_path: Path) -> None` — No docstring provided.
- `test_km_upload_missing_source_raises(tmp_path: Path) -> None` — No docstring provided.
- `test_km_upload_requires_admin_token(tmp_path: Path) -> None` — No docstring provided.
- `test_km_upload_triggers_ingest_when_requested(` — No docstring provided.
- `test_km_storetext_creates_document_with_front_matter(tmp_path: Path) -> None` — No docstring provided.
- `test_km_storetext_requires_content(tmp_path: Path) -> None` — No docstring provided.
- `test_km_storetext_triggers_ingest_when_requested(` — No docstring provided.
- `test_km_storetext_requires_admin_token(tmp_path: Path) -> None` — No docstring provided.
- `test_mcp_smoke_run(` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Prometheus metrics client, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/mcp/test_utils_files.py

**File path**: `tests/mcp/test_utils_files.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pathlib, pytest; Internal – gateway.mcp.utils
**Related modules**: gateway.mcp.utils

### Classes
- None

### Functions
- `test_sweep_documents_copies_supported_files(tmp_path: Path) -> None` — No docstring provided.
- `test_sweep_documents_dry_run_reports_actions(tmp_path: Path) -> None` — No docstring provided.
- `test_copy_into_root_prevents_traversal(tmp_path: Path) -> None` — No docstring provided.
- `test_write_text_document_requires_content(tmp_path: Path) -> None` — No docstring provided.
- `test_slugify_generates_fallback_when_empty() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/playwright_server.py

**File path**: `tests/playwright_server.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, datetime, json, os, pathlib, shutil, signal, uvicorn; Internal – gateway.api.app
**Related modules**: gateway.api.app

### Classes
- None

### Functions
- `_write_json(path: Path, payload: dict) -> None` — No docstring provided.
- `_prepare_state(state_path: Path) -> None` — No docstring provided.
- `_configure_environment(state_path: Path) -> None` — No docstring provided.
- `main() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Uvicorn ASGI server

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_api_security.py

**File path**: `tests/test_api_security.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, fastapi.testclient, json, logging, pathlib, pytest, typing; Internal – gateway, gateway.api.app, gateway.config.settings, gateway.graph.service, gateway.search.service
**Related modules**: gateway, gateway.api.app, gateway.config.settings, gateway.graph.service, gateway.search.service

### Classes
- None

### Functions
- `reset_settings_cache() -> None` — No docstring provided.
- `test_audit_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_coverage_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_coverage_missing_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_startup_logs_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None` — No docstring provided.
- `test_secure_mode_without_admin_token_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_secure_mode_requires_custom_neo4j_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_rate_limiting_search(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_app_smoke.py

**File path**: `tests/test_app_smoke.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, fastapi.testclient, json, logging, pathlib, pytest, time, unittest; Internal – gateway.api.app, gateway.config.settings, gateway.ingest.audit
**Related modules**: gateway.api.app, gateway.config.settings, gateway.ingest.audit

### Classes
- None

### Functions
- `reset_settings_cache() -> None` — No docstring provided.
- `test_health_endpoint_reports_diagnostics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_health_endpoint_ok_when_artifacts_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_ready_endpoint_returns_ready() -> None` — No docstring provided.
- `test_lifecycle_history_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_requires_non_default_neo4j_password_when_auth_enabled(` — No docstring provided.
- `test_requires_non_empty_neo4j_password_when_auth_enabled(` — No docstring provided.
- `test_logs_warning_when_neo4j_auth_disabled(` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_coverage_report.py

**File path**: `tests/test_coverage_report.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, collections.abc, fastapi.testclient, json, pathlib, prometheus_client, pytest; Internal – gateway.api.app, gateway.ingest.coverage, gateway.ingest.pipeline, gateway.observability.metrics
**Related modules**: gateway.api.app, gateway.ingest.coverage, gateway.ingest.pipeline, gateway.observability.metrics

### Classes
- `StubQdrantWriter` — No docstring provided.
  - Methods: `ensure_collection(self, vector_size: int) -> None:  # pragma: no cover - not used` — No docstring provided.; `upsert_chunks(self, chunks: Iterable[object]) -> None:  # pragma: no cover - not used` — No docstring provided.
- `StubNeo4jWriter` — No docstring provided.
  - Methods: `ensure_constraints(self) -> None:  # pragma: no cover - not used` — No docstring provided.; `sync_artifact(self, artifact: object) -> None` — No docstring provided.; `sync_chunks(self, chunk_embeddings: Iterable[object]) -> None` — No docstring provided.

### Functions
- `test_write_coverage_report(tmp_path: Path) -> None` — No docstring provided.
- `test_coverage_endpoint_after_report_generation(` — No docstring provided.
- `test_coverage_history_rotation(tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, Prometheus metrics client, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_graph_api.py

**File path**: `tests/test_graph_api.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, fastapi, fastapi.testclient, neo4j, os, pathlib, pytest, typing; Internal – gateway.api.app, gateway.graph, gateway.graph.migrations.runner, gateway.ingest.neo4j_writer, gateway.ingest.pipeline
**Related modules**: gateway.api.app, gateway.graph, gateway.graph.migrations.runner, gateway.ingest.neo4j_writer, gateway.ingest.pipeline

### Classes
- `DummyGraphService` — No docstring provided.
  - Methods: `__init__(self, responses: dict[str, Any]) -> None` — No docstring provided.; `get_subsystem(self, name: str, **kwargs: object) -> dict[str, Any]` — No docstring provided.; `get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]` — No docstring provided.; `search(self, term: str, *, limit: int) -> dict[str, Any]` — No docstring provided.; `get_subsystem_graph(self, name: str, *, depth: int) -> dict[str, Any]` — No docstring provided.; `list_orphan_nodes(self, *, label: str | None, cursor: str | None, limit: int) -> dict[str, Any]` — No docstring provided.; `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` — No docstring provided.

### Functions
- `app(monkeypatch: pytest.MonkeyPatch) -> FastAPI` — No docstring provided.
- `test_graph_subsystem_returns_payload(app: FastAPI) -> None` — No docstring provided.
- `test_graph_subsystem_not_found(app: FastAPI) -> None` — No docstring provided.
- `test_graph_subsystem_graph_endpoint(app: FastAPI) -> None` — No docstring provided.
- `test_graph_orphans_endpoint(app: FastAPI) -> None` — No docstring provided.
- `test_graph_node_endpoint(app: FastAPI) -> None` — No docstring provided.
- `test_graph_node_accepts_slash_encoded_ids(app: FastAPI) -> None` — No docstring provided.
- `test_graph_node_endpoint_live(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None` — No docstring provided.
- `test_graph_search_endpoint_live(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None` — No docstring provided.
- `test_graph_search_endpoint(app: FastAPI) -> None` — No docstring provided.
- `test_graph_cypher_requires_maintainer_token(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_graph_reader_scope(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, Neo4j GraphDatabase driver, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_graph_auto_migrate.py

**File path**: `tests/test_graph_auto_migrate.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, prometheus_client, pytest, unittest; Internal – gateway.api.app, gateway.observability.metrics
**Related modules**: gateway.api.app, gateway.observability.metrics

### Classes
- None

### Functions
- `reset_settings_cache() -> None` — No docstring provided.
- `reset_migration_metrics() -> None` — No docstring provided.
- `_metric(name: str) -> float | None` — No docstring provided.
- `test_auto_migrate_runs_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_auto_migrate_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_auto_migrate_records_failure(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_missing_database_disables_graph_driver(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Prometheus metrics client, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_graph_cli.py

**File path**: `tests/test_graph_cli.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pytest, unittest; Internal – gateway.graph
**Related modules**: gateway.graph

### Classes
- `DummySettings` — No docstring provided.
  - Attributes: `neo4j_uri = 'bolt://dummy'`; `neo4j_user = 'neo4j'`; `neo4j_password = 'password'`; `neo4j_database = 'knowledge'`

### Functions
- `test_graph_cli_migrate_runs_runner(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_graph_cli_dry_run_prints_pending(` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_graph_database_validation.py

**File path**: `tests/test_graph_database_validation.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, neo4j.exceptions, unittest; Internal – gateway.api
**Related modules**: gateway.api

### Classes
- None

### Functions
- `test_verify_graph_database_returns_false_when_database_missing() -> None` — No docstring provided.
- `test_verify_graph_database_returns_true_on_success() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_graph_migrations.py

**File path**: `tests/test_graph_migrations.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, collections, types; Internal – gateway.graph.migrations.runner
**Related modules**: gateway.graph.migrations.runner

### Classes
- `FakeResult` — No docstring provided.
  - Methods: `__init__(self, record: dict[str, object] | None = None) -> None` — No docstring provided.; `single(self) -> dict[str, object] | None` — No docstring provided.
- `FakeTransaction` — No docstring provided.
  - Methods: `__init__(self, applied_ids: set[str], results: deque[tuple[str, dict[str, object]]]) -> None` — No docstring provided.; `run(self, query: str, **params: object) -> FakeResult` — No docstring provided.; `commit(self) -> None` — No docstring provided.; `rollback(self) -> None` — No docstring provided.; `__enter__(self) -> FakeTransaction` — No docstring provided.; `__exit__(` — No docstring provided.
- `FakeSession` — No docstring provided.
  - Methods: `__init__(self, applied_ids: set[str], records: deque[tuple[str, dict[str, object]]]) -> None` — No docstring provided.; `run(self, query: str, **params: object) -> FakeResult` — No docstring provided.; `begin_transaction(self) -> FakeTransaction` — No docstring provided.; `close(self) -> None` — No docstring provided.; `__enter__(self) -> FakeSession` — No docstring provided.; `__exit__(` — No docstring provided.
- `FakeDriver` — No docstring provided.
  - Methods: `__init__(self) -> None` — No docstring provided.; `session(self, database: str) -> FakeSession:  # noqa: ARG002 - database unused` — No docstring provided.; `close(self) -> None` — No docstring provided.

### Functions
- `test_migration_runner_applies_pending_migrations() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Standard library only

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_graph_service_startup.py

**File path**: `tests/test_graph_service_startup.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, fastapi, pytest, starlette.requests, unittest; Internal – gateway.api.app
**Related modules**: gateway.api.app

### Classes
- None

### Functions
- `reset_settings_cache() -> None` — No docstring provided.
- `set_state_path(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `_receive() -> dict[str, object]` — No docstring provided.
- `_make_request(app) -> Request` — No docstring provided.
- `test_graph_dependency_returns_503_when_database_missing(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_graph_dependency_returns_service_when_available(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_graph_service_unit.py

**File path**: `tests/test_graph_service_unit.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, collections.abc, neo4j, pytest, types, unittest; Internal – gateway.graph, gateway.graph.service, gateway.observability.metrics
**Related modules**: gateway.graph, gateway.graph.service, gateway.observability.metrics

### Classes
- `DummyNode(dict[str, object])` — No docstring provided.
  - Methods: `__init__(self, labels: Iterable[str], element_id: str, **props: object) -> None` — No docstring provided.
- `DummyRelationship(dict[str, object])` — No docstring provided.
  - Methods: `__init__(` — No docstring provided.
- `DummySession` — No docstring provided.
  - Methods: `__init__(self) -> None` — No docstring provided.; `__enter__(self) -> DummySession:  # pragma: no cover - trivial` — No docstring provided.; `__exit__(` — No docstring provided.; `execute_read(self, func: Callable[..., object], *args: object, **kwargs: object) -> object` — No docstring provided.; `run(self, query: str, **params: object) -> SimpleNamespace` — No docstring provided.
- `DummyDriver` — No docstring provided.
  - Methods: `__init__(self, session: DummySession) -> None` — No docstring provided.; `session(self, **kwargs: object) -> DummySession` — No docstring provided.; `execute_query(` — No docstring provided.

### Functions
- `_reset_metric(reason: str) -> None` — No docstring provided.
- `_metric_value(reason: str) -> float` — No docstring provided.
- `patch_graph_types(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `dummy_driver() -> DriverFixture` — No docstring provided.
- `test_get_subsystem_paginates_and_includes_artifacts(` — No docstring provided.
- `test_get_subsystem_missing_raises(` — No docstring provided.
- `test_get_subsystem_graph_returns_nodes_and_edges(` — No docstring provided.
- `test_fetch_subsystem_paths_inlines_depth_literal(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_get_node_with_relationships(` — No docstring provided.
- `test_list_orphan_nodes_rejects_unknown_label(dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_list_orphan_nodes_serializes_results(` — No docstring provided.
- `test_get_node_missing_raises(` — No docstring provided.
- `test_search_serializes_results(` — No docstring provided.
- `test_shortest_path_depth(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_shortest_path_depth_none(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_run_cypher_serializes_records(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_run_cypher_rejects_non_read_queries(dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_run_cypher_rejects_updates_detected_in_counters(dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_run_cypher_allows_whitelisted_procedure(dummy_driver: DriverFixture) -> None` — No docstring provided.
- `test_run_cypher_rejects_disallowed_procedure(dummy_driver: DriverFixture) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Neo4j GraphDatabase driver, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_graph_validation.py

**File path**: `tests/test_graph_validation.py`
**Purpose**: End-to-end validation of ingestion and graph-backed search.
**Dependencies**: External – __future__, collections.abc, neo4j, os, pathlib, pytest, qdrant_client, typing; Internal – gateway.graph.migrations.runner, gateway.graph.service, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.search
**Related modules**: gateway.graph.migrations.runner, gateway.graph.service, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.search

### Classes
- `_DummyEmbedder(Embedder)` — Minimal embedder returning deterministic vectors for tests.
  - Methods: `__init__(self) -> None` — No docstring provided.; `dimension(self) -> int` — No docstring provided.; `encode(self, texts: Sequence[str]) -> list[list[float]]` — No docstring provided.
- `_FakePoint` — No docstring provided.
  - Methods: `__init__(self, payload: dict[str, object], score: float) -> None` — No docstring provided.
- `_DummyQdrantClient` — Stub Qdrant client that returns pre-seeded points.
  - Methods: `__init__(self, points: list[_FakePoint]) -> None` — No docstring provided.; `search(self, **_kwargs: object) -> list[_FakePoint]` — No docstring provided.

### Functions
- `test_ingestion_populates_graph(tmp_path: Path) -> None` — Run ingestion and verify graph nodes, edges, and metadata.
- `test_search_replay_against_real_graph(tmp_path: Path) -> None` — Replay saved search results against the populated knowledge graph.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Neo4j GraphDatabase driver, pytest unit testing, Qdrant vector database SDK

### Code Quality Notes
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_ingest_cli.py

**File path**: `tests/test_ingest_cli.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pathlib, pytest, time, unittest; Internal – gateway.config.settings, gateway.ingest, gateway.ingest.audit, gateway.ingest.pipeline
**Related modules**: gateway.config.settings, gateway.ingest, gateway.ingest.audit, gateway.ingest.pipeline

### Classes
- None

### Functions
- `reset_settings_cache() -> None` — No docstring provided.
- `sample_repo(tmp_path: Path) -> Path` — No docstring provided.
- `test_cli_rebuild_dry_run(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_cli_rebuild_requires_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_cli_rebuild_with_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_cli_rebuild_full_rebuild_flag(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_cli_rebuild_incremental_flag(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_cli_audit_history_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` — No docstring provided.
- `test_cli_audit_history_no_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_ingest_pipeline.py

**File path**: `tests/test_ingest_pipeline.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, collections.abc, pathlib, prometheus_client, pytest; Internal – gateway.ingest.pipeline
**Related modules**: gateway.ingest.pipeline

### Classes
- `StubQdrantWriter` — No docstring provided.
  - Methods: `__init__(self) -> None` — No docstring provided.; `ensure_collection(self, vector_size: int) -> None` — No docstring provided.; `upsert_chunks(self, chunks: Iterable[object]) -> None` — No docstring provided.; `delete_artifact(self, artifact_path: str) -> None` — No docstring provided.
- `StubNeo4jWriter` — No docstring provided.
  - Methods: `__init__(self) -> None` — No docstring provided.; `ensure_constraints(self) -> None:  # pragma: no cover - not used in unit test` — No docstring provided.; `sync_artifact(self, artifact: object) -> None` — No docstring provided.; `sync_chunks(self, chunk_embeddings: Iterable[object]) -> None` — No docstring provided.; `delete_artifact(self, path: str) -> None` — No docstring provided.

### Functions
- `_metric_value(name: str, labels: dict[str, str]) -> float` — No docstring provided.
- `sample_repo(tmp_path: Path) -> Path` — No docstring provided.
- `test_pipeline_generates_chunks(sample_repo: Path) -> None` — No docstring provided.
- `test_pipeline_removes_stale_artifacts(tmp_path: Path) -> None` — No docstring provided.
- `test_pipeline_skips_unchanged_artifacts(tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Prometheus metrics client, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_km_watch.py

**File path**: `tests/test_km_watch.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, os, pathlib, prometheus_client, runpy, sys; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_metric_value(name: str, labels: dict[str, str]) -> float` — No docstring provided.
- `test_compute_fingerprints(tmp_path: Path) -> None` — No docstring provided.
- `test_diff_fingerprints_detects_changes() -> None` — No docstring provided.
- `test_watch_metrics_increment(tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Prometheus metrics client

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_lifecycle_cli.py

**File path**: `tests/test_lifecycle_cli.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, json, pathlib, pytest; Internal – gateway.lifecycle.cli
**Related modules**: gateway.lifecycle.cli

### Classes
- None

### Functions
- `test_lifecycle_cli_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None` — No docstring provided.
- `test_lifecycle_cli_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_lifecycle_report.py

**File path**: `tests/test_lifecycle_report.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, datetime, json, pathlib, prometheus_client, pytest, typing; Internal – gateway.graph, gateway.ingest.lifecycle, gateway.ingest.pipeline
**Related modules**: gateway.graph, gateway.ingest.lifecycle, gateway.ingest.pipeline

### Classes
- `DummyGraphService` — Test double that returns pre-seeded orphan graph nodes.
  - Methods: `__init__(self, pages: dict[str, list[list[dict[str, object]]]]) -> None` — No docstring provided.; `list_orphan_nodes(` — Yield nodes in pages for the requested label.

### Functions
- `_ingestion_result() -> IngestionResult` — Build a representative ingestion result for lifecycle reporting tests.
- `test_write_lifecycle_report_without_graph(tmp_path: Path, ingestion_result: IngestionResult) -> None` — Reports render correctly when graph enrichment is disabled.
- `test_write_lifecycle_report_with_graph(tmp_path: Path, ingestion_result: IngestionResult) -> None` — Graph enrichment populates isolated node information in the payload.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Prometheus metrics client, pytest unit testing

### Code Quality Notes
- 1 class method(s) missing docstrings.

## tests/test_mcp_recipes.py

**File path**: `tests/test_mcp_recipes.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, json, pathlib, pytest; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `test_snippets_are_valid_json(snippet: str) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: RECIPES
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_mcp_smoke_recipes.py

**File path**: `tests/test_mcp_smoke_recipes.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, json, pathlib, pytest; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_recipe_params() -> list[pytest.ParameterSet]` — No docstring provided.
- `test_recipe_lines_are_valid_json(line: str) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: RECIPES
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_neo4j_writer.py

**File path**: `tests/test_neo4j_writer.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, neo4j, pathlib, types, typing; Internal – gateway.ingest.artifacts, gateway.ingest.neo4j_writer
**Related modules**: gateway.ingest.artifacts, gateway.ingest.neo4j_writer

### Classes
- `RecordingSession` — Stubbed session that records Cypher queries for assertions.
  - Methods: `__init__(self) -> None` — No docstring provided.; `run(self, query: str, **params: object) -> SimpleNamespace` — No docstring provided.; `__enter__(self) -> RecordingSession:  # pragma: no cover - trivial` — No docstring provided.; `__exit__(` — No docstring provided.
- `RecordingDriver` — Stubbed driver that yields recording sessions.
  - Methods: `__init__(self) -> None` — No docstring provided.; `session(self, *, database: str | None = None) -> RecordingSession` — Return a new recording session; database name is ignored.

### Functions
- `_make_writer() -> tuple[Neo4jWriter, RecordingDriver]` — Create a writer bound to a recording driver for inspection.
- `test_sync_artifact_creates_domain_relationships() -> None` — Artifacts trigger the expected Cypher commands and relationships.
- `test_sync_artifact_merges_subsystem_edge_once() -> None` — Syncing an artifact does not duplicate the subsystem relationship.
- `test_sync_chunks_links_chunk_to_artifact() -> None` — Chunk synchronization creates chunk nodes and linking edges.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Neo4j GraphDatabase driver

### Code Quality Notes
- 5 class method(s) missing docstrings.

## tests/test_qdrant_writer.py

**File path**: `tests/test_qdrant_writer.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, httpx, pytest, qdrant_client.http.exceptions, unittest; Internal – gateway.ingest.qdrant_writer
**Related modules**: gateway.ingest.qdrant_writer

### Classes
- None

### Functions
- `stub_qdrant_models(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `build_client(**kwargs: object) -> mock.Mock` — No docstring provided.
- `test_ensure_collection_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_ensure_collection_noop_when_collection_exists() -> None` — No docstring provided.
- `test_ensure_collection_retries_on_transient_failure(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_ensure_collection_handles_conflict() -> None` — No docstring provided.
- `test_reset_collection_invokes_recreate() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- HTTPX async client, pytest unit testing, Qdrant vector database SDK

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_recipes_executor.py

**File path**: `tests/test_recipes_executor.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pathlib, pytest, types, typing; Internal – gateway.mcp.config, gateway.recipes.executor, gateway.recipes.models
**Related modules**: gateway.mcp.config, gateway.recipes.executor, gateway.recipes.models

### Classes
- `FakeToolExecutor` — No docstring provided.
  - Methods: `__init__(self, responses: dict[str, list[Any] | Any]) -> None` — No docstring provided.; `__aenter__(self) -> FakeToolExecutor` — No docstring provided.; `__aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` — No docstring provided.; `call(self, tool: str, params: dict[str, object]) -> object` — No docstring provided.

### Functions
- `test_recipe_runner_success(tmp_path: Path) -> None` — No docstring provided.
- `test_recipe_runner_wait(tmp_path: Path) -> None` — No docstring provided.
- `test_recipe_runner_expect_failure(tmp_path: Path) -> None` — No docstring provided.
- `test_recipe_runner_dry_run(tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_release_scripts.py

**File path**: `tests/test_release_scripts.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, os, pathlib, subprocess; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `_env_with_venv() -> dict[str, str]` — No docstring provided.
- `test_build_wheel_script(tmp_path: Path) -> None` — No docstring provided.
- `test_checksums_script(tmp_path: Path) -> None` — No docstring provided.
- `test_generate_changelog(tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: REPO_ROOT, SCRIPTS_DIR
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Standard library only

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_scheduler.py

**File path**: `tests/test_scheduler.py`
**Purpose**: Unit tests exercising the ingestion scheduler behaviour and metrics.
**Dependencies**: External – __future__, apscheduler.triggers.cron, apscheduler.triggers.interval, collections.abc, filelock, pathlib, prometheus_client, pytest, unittest; Internal – gateway.config.settings, gateway.ingest.pipeline, gateway.scheduler
**Related modules**: gateway.config.settings, gateway.ingest.pipeline, gateway.scheduler

### Classes
- None

### Functions
- `reset_cache() -> Generator[None, None, None]` — Clear cached settings before and after each test.
- `scheduler_settings(tmp_path: Path) -> AppSettings` — Provide scheduler settings pointing at a temporary repo.
- `make_scheduler(settings: AppSettings) -> IngestionScheduler` — Instantiate a scheduler with its APScheduler stubbed out.
- `_metric_value(name: str, labels: dict[str, str] | None = None) -> float` — Fetch a Prometheus sample value with defaults for missing metrics.
- `make_result(head: str) -> IngestionResult` — Construct a minimal ingestion result for scheduler tests.
- `test_scheduler_skips_when_repo_head_unchanged(scheduler_settings: AppSettings) -> None` — Scheduler skips when repository head hash matches the cached value.
- `test_scheduler_runs_when_repo_head_changes(scheduler_settings: AppSettings) -> None` — Scheduler triggers ingestion when the repository head changes.
- `test_scheduler_start_uses_interval_trigger(scheduler_settings: AppSettings) -> None` — Schedulers without cron use the configured interval trigger.
- `test_scheduler_start_uses_cron_trigger(tmp_path: Path) -> None` — Cron expressions configure a cron trigger instead of interval.
- `test_scheduler_skips_when_lock_contended(scheduler_settings: AppSettings) -> None` — Lock contention causes the scheduler to skip runs and record metrics.
- `test_scheduler_requires_maintainer_token(tmp_path: Path) -> None` — Schedulers skip setup when auth is enabled without a maintainer token.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- APScheduler background scheduling, File locking utilities, Prometheus metrics client, pytest unit testing

### Code Quality Notes
- No major issues detected during static review.

## tests/test_search_api.py

**File path**: `tests/test_search_api.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, datetime, fastapi.testclient, json, pathlib, pytest; Internal – gateway.api.app, gateway.search.service
**Related modules**: gateway.api.app, gateway.search.service

### Classes
- `DummySearchService` — No docstring provided.
  - Methods: `__init__(self) -> None` — No docstring provided.; `search(` — No docstring provided.

### Functions
- `test_search_endpoint_returns_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_reuses_incoming_request_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_requires_reader_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_allows_maintainer_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_feedback_logged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_filters_passed_to_service(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_filters_invalid_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_filters_invalid_namespaces(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_filters_invalid_updated_after(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_filters_invalid_max_age(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_search_weights_endpoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_search_cli_show_weights.py

**File path**: `tests/test_search_cli_show_weights.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pathlib, pytest; Internal – gateway.search
**Related modules**: gateway.search

### Classes
- None

### Functions
- `clear_settings_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` — No docstring provided.
- `test_show_weights_command(capsys: pytest.CaptureFixture[str]) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_search_evaluation.py

**File path**: `tests/test_search_evaluation.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, json, math, pathlib, pytest; Internal – gateway.search.cli, gateway.search.dataset, gateway.search.evaluation
**Related modules**: gateway.search.cli, gateway.search.dataset, gateway.search.evaluation

### Classes
- None

### Functions
- `test_evaluate_model(tmp_path: Path) -> None` — No docstring provided.
- `test_evaluate_cli(` — No docstring provided.
- `test_evaluate_model_with_empty_dataset(tmp_path: Path) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_search_exporter.py

**File path**: `tests/test_search_exporter.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, csv, json, pathlib, pytest; Internal – gateway.config.settings, gateway.search.cli, gateway.search.exporter, gateway.search.trainer
**Related modules**: gateway.config.settings, gateway.search.cli, gateway.search.exporter, gateway.search.trainer

### Classes
- None

### Functions
- `_write_events(path: Path, events: list[dict[str, object]]) -> None` — No docstring provided.
- `_sample_event(request_id: str, vote: float | None) -> dict[str, object]` — No docstring provided.
- `test_export_training_dataset_csv(tmp_path: Path) -> None` — No docstring provided.
- `test_export_training_data_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_train_model_from_dataset(tmp_path: Path) -> None` — No docstring provided.
- `test_train_model_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_search_maintenance.py

**File path**: `tests/test_search_maintenance.py`
**Purpose**: Tests for the search maintenance helpers.
**Dependencies**: External – __future__, datetime, json, os, pathlib, pytest, stat; Internal – gateway.search.maintenance
**Related modules**: gateway.search.maintenance

### Classes
- None

### Functions
- `_write_events(path: Path, requests: list[tuple[str, datetime, list[dict[str, object]]]]) -> None` — Write JSON lines representing feedback events for the supplied requests.
- `test_prune_feedback_log_parses_various_timestamp_formats(tmp_path: Path) -> None` — Ensure prune handles numeric, Z-suffixed, and missing timestamps.
- `test_prune_feedback_log_by_age(tmp_path: Path) -> None` — Retains only entries newer than the configured age threshold.
- `test_prune_feedback_log_missing_file(tmp_path: Path) -> None` — Raises if the feedback log file is absent.
- `test_prune_feedback_log_requires_limit(tmp_path: Path) -> None` — Rejects calls without an age or request limit configured.
- `test_prune_feedback_log_empty_file(tmp_path: Path) -> None` — Returns zeroed stats when the log contains no events.
- `test_prune_feedback_log_guard_when_pruning_everything(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None` — Leaves the log intact when filters would drop every request.
- `test_prune_feedback_log_max_requests_prefers_newest(tmp_path: Path) -> None` — Keeps only the newest requests when enforcing a max count.
- `test_redact_dataset_csv(tmp_path: Path) -> None` — Redacts populated CSV fields for queries, contexts, and notes.
- `test_redact_dataset_csv_handles_missing_and_blank_fields(tmp_path: Path) -> None` — Leaves missing or blank CSV fields untouched while redacting non-empty ones.
- `test_redact_dataset_jsonl(tmp_path: Path) -> None` — Redacts JSONL query and context fields when toggled.
- `test_redact_dataset_jsonl_handles_missing_and_blank_fields(tmp_path: Path) -> None` — Leaves absent or empty JSONL fields untouched while redacting populated ones.
- `test_redact_dataset_missing_file(tmp_path: Path) -> None` — Raises if the target dataset file is absent.
- `test_redact_dataset_unsupported_suffix(tmp_path: Path) -> None` — Rejects unsupported dataset extensions.
- `test_redact_dataset_output_path_copies_metadata(tmp_path: Path) -> None` — Preserves metadata when writing to an alternate output path.
- `test_redact_dataset_jsonl_handles_blank_lines(tmp_path: Path) -> None` — Preserves blank lines in JSONL datasets while redacting content.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- No major issues detected during static review.

## tests/test_search_profiles.py

**File path**: `tests/test_search_profiles.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pytest; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

### Classes
- None

### Functions
- `clear_weight_env(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_resolved_search_weights_default() -> None` — No docstring provided.
- `test_resolved_search_weights_profile_selection(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_resolved_search_weights_overrides(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_search_service.py

**File path**: `tests/test_search_service.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, collections.abc, datetime, prometheus_client, pytest, typing; Internal – gateway.graph.service, gateway.search, gateway.search.trainer
**Related modules**: gateway.graph.service, gateway.search, gateway.search.trainer

### Classes
- `FakeEmbedder` — No docstring provided.
  - Methods: `encode(self, texts: Sequence[str]) -> list[list[float]]` — No docstring provided.
- `FakePoint` — No docstring provided.
  - Methods: `__init__(self, payload: dict[str, Any], score: float) -> None` — No docstring provided.
- `FakeQdrantClient` — No docstring provided.
  - Methods: `__init__(self, points: list[FakePoint]) -> None` — No docstring provided.; `search(self, **kwargs: object) -> list[FakePoint]` — No docstring provided.
- `DummyGraphService(GraphService)` — No docstring provided.
  - Methods: `__init__(self, response: dict[str, Any]) -> None` — No docstring provided.; `get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]` — No docstring provided.; `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - not used` — No docstring provided.; `search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - not used` — No docstring provided.; `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover` — No docstring provided.; `shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]` — No docstring provided.
- `MapGraphService(GraphService)` — No docstring provided.
  - Methods: `__init__(self, data: dict[str, dict[str, Any]]) -> None` — No docstring provided.; `get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]` — No docstring provided.; `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - unused` — No docstring provided.; `search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - unused` — No docstring provided.; `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover` — No docstring provided.; `shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]` — No docstring provided.
- `CountingGraphService(GraphService)` — No docstring provided.
  - Methods: `__init__(self, response: dict[str, Any], depth: int = 2) -> None` — No docstring provided.; `get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]` — No docstring provided.; `shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]` — No docstring provided.; `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - unused` — No docstring provided.; `search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - unused` — No docstring provided.; `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover` — No docstring provided.

### Functions
- `_metric_value(name: str, labels: dict[str, str] | None = None) -> float` — No docstring provided.
- `sample_points() -> list[FakePoint]` — No docstring provided.
- `graph_response() -> dict[str, Any]` — No docstring provided.
- `test_search_service_enriches_with_graph(` — No docstring provided.
- `test_search_service_handles_missing_graph(sample_points: list[FakePoint]) -> None` — No docstring provided.
- `test_search_hnsw_search_params(sample_points: list[FakePoint]) -> None` — No docstring provided.
- `test_lexical_score_affects_ranking() -> None` — No docstring provided.
- `test_search_service_orders_by_adjusted_score() -> None` — No docstring provided.
- `test_search_service_caches_graph_lookups(` — No docstring provided.
- `test_search_service_filters_artifact_types() -> None` — No docstring provided.
- `test_search_service_filters_namespaces() -> None` — No docstring provided.
- `test_search_service_filters_tags() -> None` — No docstring provided.
- `test_search_service_filters_recency_updated_after() -> None` — No docstring provided.
- `test_search_service_filters_recency_max_age_days() -> None` — No docstring provided.
- `test_search_service_filters_subsystem_via_graph(graph_response: dict[str, Any]) -> None` — No docstring provided.
- `test_search_service_ml_model_reorders_results() -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- Prometheus metrics client, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.
- Class methods omit docstrings; behaviour inferred from names.

## tests/test_settings_defaults.py

**File path**: `tests/test_settings_defaults.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, pytest; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

### Classes
- None

### Functions
- `test_neo4j_database_defaults_to_knowledge(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.
- `test_neo4j_auth_enabled_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_tracing.py

**File path**: `tests/test_tracing.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, opentelemetry.exporter.otlp.proto.http.trace_exporter, opentelemetry.sdk.trace, opentelemetry.sdk.trace.export, pytest; Internal – gateway.api.app, gateway.config.settings, gateway.observability.tracing
**Related modules**: gateway.api.app, gateway.config.settings, gateway.observability.tracing

### Classes
- None

### Functions
- `test_tracing_disabled_by_default(monkeypatch: MonkeyPatch) -> None` — No docstring provided.
- `test_tracing_enabled_instruments_app(monkeypatch: MonkeyPatch) -> None` — No docstring provided.
- `test_tracing_uses_otlp_exporter(monkeypatch: MonkeyPatch) -> None` — No docstring provided.
- `test_tracing_console_fallback(monkeypatch: MonkeyPatch) -> None` — No docstring provided.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- OpenTelemetry tracing, pytest unit testing

### Code Quality Notes
- Helper functions lack docstrings; rely on type hints for intent.

## tests/test_ui_routes.py

**File path**: `tests/test_ui_routes.py`
**Purpose**: Implementation details not documented; see code for behaviour.
**Dependencies**: External – __future__, fastapi.testclient, pathlib, prometheus_client, pytest; Internal – gateway.api.app, gateway.config.settings
**Related modules**: gateway.api.app, gateway.config.settings

### Classes
- None

### Functions
- `_reset_settings(tmp_path: Path | None = None) -> None` — Clear cached settings and ensure the state directory exists for tests.
- `test_ui_landing_served(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` — The landing page renders successfully and increments the landing metric.
- `test_ui_search_view(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` — The search view renders and increments the search metric.
- `test_ui_subsystems_view(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` — The subsystems view renders and increments the subsystem metric.
- `test_ui_lifecycle_download(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` — Lifecycle report downloads are returned and recorded in metrics.
- `test_ui_events_endpoint(tmp_path: Path, monkeypatch: MonkeyPatch) -> None` — Custom UI events are accepted and reflected in Prometheus metrics.

### Constants and Configuration
- Module-level constants: None
- Environment variables: Not detected in static scan

### Data Flow
- Exercises public behaviours with pytest to prevent regressions.

### Integration Points
- FastAPI web framework, Prometheus metrics client, pytest unit testing

### Code Quality Notes
- No major issues detected during static review.
