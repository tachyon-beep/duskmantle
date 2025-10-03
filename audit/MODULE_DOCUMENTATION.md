# Module Documentation

## gateway/__init__.py

**File path**: `gateway/__init__.py`
**Purpose**: Core package for the Duskmantle knowledge gateway.
**Dependencies**: External – __future__.annotations; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `get_version() -> str` (line 10) — Return the current package version.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- standard library only

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/__main__.py

**File path**: `gateway/__main__.py`
**Purpose**: Console entry point that launches the FastAPI application.
**Dependencies**: External – __future__.annotations, uvicorn; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `main() -> None` (line 8) — Run the gateway API using Uvicorn.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- uvicorn

### Code Quality Notes
- No immediate issues detected from static scan.

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
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- standard library only

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/api/app.py

**File path**: `gateway/api/app.py`
**Purpose**: Primary FastAPI application wiring for the knowledge gateway.
**Dependencies**: External – __future__.annotations, apscheduler.schedulers.base.SchedulerNotRunningError, asyncio, collections.abc.AsyncIterator, collections.abc.Awaitable, collections.abc.Callable, contextlib.AbstractAsyncContextManager, contextlib.asynccontextmanager, contextlib.suppress, fastapi.FastAPI, fastapi.Request, fastapi.Response, fastapi.responses.JSONResponse, fastapi.staticfiles.StaticFiles, json, logging, neo4j.Driver, neo4j.GraphDatabase, neo4j.exceptions.Neo4jError, neo4j.exceptions.ServiceUnavailable, qdrant_client.QdrantClient, slowapi.Limiter, slowapi.errors.RateLimitExceeded, slowapi.middleware.SlowAPIMiddleware, slowapi.util.get_remote_address, time, typing.cast, uuid.uuid4; Internal – gateway.api.connections, gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.api.routes.graph, gateway.api.routes.health, gateway.api.routes.reporting, gateway.api.routes.search, gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.get_version, gateway.graph.get_graph_service, gateway.graph.migrations.MigrationRunner, gateway.observability.GRAPH_MIGRATION_LAST_STATUS, gateway.observability.GRAPH_MIGRATION_LAST_TIMESTAMP, gateway.observability.configure_logging, gateway.observability.configure_tracing, gateway.scheduler.IngestionScheduler, gateway.search.feedback.SearchFeedbackStore, gateway.search.trainer.ModelArtifact, gateway.search.trainer.load_artifact, gateway.ui.get_static_path, gateway.ui.router
**Related modules**: gateway.api.connections, gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.api.routes.graph, gateway.api.routes.health, gateway.api.routes.reporting, gateway.api.routes.search, gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.get_version, gateway.graph.get_graph_service, gateway.graph.migrations.MigrationRunner, gateway.observability.GRAPH_MIGRATION_LAST_STATUS, gateway.observability.GRAPH_MIGRATION_LAST_TIMESTAMP, gateway.observability.configure_logging, gateway.observability.configure_tracing, gateway.scheduler.IngestionScheduler, gateway.search.feedback.SearchFeedbackStore, gateway.search.trainer.ModelArtifact, gateway.search.trainer.load_artifact, gateway.ui.get_static_path, gateway.ui.router

### Classes
- None

### Functions
- `_validate_auth_settings(settings: AppSettings) -> None` (line 53) — No docstring provided.
- `_log_startup_configuration(settings: AppSettings) -> None` (line 83) — No docstring provided.
- `_build_lifespan(settings: AppSettings) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]` (line 106) — No docstring provided.
- `_configure_rate_limits(app: FastAPI, settings: AppSettings) -> Limiter` (line 145) — No docstring provided.
- `_init_feedback_store(settings: AppSettings) -> SearchFeedbackStore | None` (line 156) — No docstring provided.
- `_load_search_model(settings: AppSettings) -> ModelArtifact | None` (line 164) — No docstring provided.
- `_initialise_graph_manager(manager: Neo4jConnectionManager, settings: AppSettings) -> None` (line 182) — No docstring provided.
- `_initialise_qdrant_manager(manager: QdrantConnectionManager) -> None` (line 217) — No docstring provided.
- `async _dependency_heartbeat_loop(app: FastAPI, interval: float) -> None` (line 221) — No docstring provided.
- `_verify_graph_database(driver: Driver, database: str) -> bool` (line 232) — No docstring provided.
- `_ensure_graph_database(settings: AppSettings) -> bool` (line 255) — Ensure the configured Neo4j database exists, creating it if missing.
- `_run_graph_auto_migration(driver: Driver, database: str) -> None` (line 285) — No docstring provided.
- `_fetch_pending_migrations(runner: MigrationRunner) -> list[str] | None` (line 301) — No docstring provided.
- `_log_migration_plan(pending: list[str] | None) -> None` (line 312) — No docstring provided.
- `_log_migration_completion(pending: list[str] | None) -> None` (line 325) — No docstring provided.
- `_set_migration_metrics(status: int, timestamp: float | None) -> None` (line 337) — No docstring provided.
- `create_app() -> FastAPI` (line 342) — Create the FastAPI application instance.
- `_rate_limit_handler(_request: Request, exc: Exception) -> JSONResponse` (line 416) — No docstring provided.

### Constants and Configuration
- DEPENDENCY_HEARTBEAT_INTERVAL_SECONDS = 30.0 (line 50)

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Interacts with Qdrant collections for vector search or persistence.
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Schedules background jobs using APScheduler.

### Integration Points
- apscheduler, asyncio, collections, contextlib, fastapi, json, logging, neo4j, qdrant_client, slowapi, time, typing, uuid

### Code Quality Notes
- 16 public element(s) lack docstrings.

## gateway/api/auth.py

**File path**: `gateway/api/auth.py`
**Purpose**: Authentication dependencies used across the FastAPI surface.
**Dependencies**: External – __future__.annotations, collections.abc.Callable, fastapi.Depends, fastapi.HTTPException, fastapi.security.HTTPAuthorizationCredentials, fastapi.security.HTTPBearer, fastapi.status; Internal – gateway.config.settings.AppSettings, gateway.config.settings.get_settings
**Related modules**: gateway.config.settings.AppSettings, gateway.config.settings.get_settings

### Classes
- None

### Functions
- `require_scope(scope: str) -> Callable[[HTTPAuthorizationCredentials | None], None]` (line 15) — Return a dependency enforcing the given scope.
- `_allowed_tokens_for_scope(settings: AppSettings, scope: str) -> list[str]` (line 43) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- collections, fastapi

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/api/connections.py

**File path**: `gateway/api/connections.py`
**Purpose**: Connection managers for external services (Neo4j and Qdrant).
**Dependencies**: External – __future__.annotations, contextlib, dataclasses.dataclass, logging, neo4j.Driver, neo4j.GraphDatabase, neo4j.READ_ACCESS, neo4j.exceptions.Neo4jError, neo4j.exceptions.ServiceUnavailable, qdrant_client.QdrantClient, threading, time; Internal – gateway.config.settings.AppSettings, gateway.observability.GRAPH_DEPENDENCY_LAST_SUCCESS, gateway.observability.GRAPH_DEPENDENCY_STATUS, gateway.observability.QDRANT_DEPENDENCY_LAST_SUCCESS, gateway.observability.QDRANT_DEPENDENCY_STATUS
**Related modules**: gateway.config.settings.AppSettings, gateway.observability.GRAPH_DEPENDENCY_LAST_SUCCESS, gateway.observability.GRAPH_DEPENDENCY_STATUS, gateway.observability.QDRANT_DEPENDENCY_LAST_SUCCESS, gateway.observability.QDRANT_DEPENDENCY_STATUS

### Classes
- `DependencyStatus` (line 30) — Serializable snapshot of an external dependency. Inherits from object.
  - Attributes: status: str, revision: int, last_success: float | None, last_failure: float | None, last_error: str | None
  - Methods: None
- `Neo4jConnectionManager` (line 40) — Lazy initialisation and health tracking for Neo4j drivers. Inherits from object.
  - Methods:
    - `__init__(self, settings: AppSettings, log: logging.Logger | None = None) -> None` (line 43) — No method docstring provided.
    - `revision(self) -> int` (line 56) — No method docstring provided.
    - `describe(self) -> DependencyStatus` (line 59) — No method docstring provided.
    - `get_write_driver(self) -> Driver` (line 69) — No method docstring provided.
    - `get_readonly_driver(self) -> Driver` (line 83) — No method docstring provided.
    - `mark_failure(self, exc: Exception | None = None) -> None` (line 108) — No method docstring provided.
    - `heartbeat(self) -> bool` (line 123) — No method docstring provided.
    - `_create_driver(self, uri: str, user: str, password: str) -> Driver` (line 139) — No method docstring provided.
    - `_record_success(self) -> None` (line 163) — No method docstring provided.
- `QdrantConnectionManager` (line 171) — Lazy initialisation and health tracking for Qdrant clients. Inherits from object.
  - Methods:
    - `__init__(self, settings: AppSettings, log: logging.Logger | None = None) -> None` (line 174) — No method docstring provided.
    - `revision(self) -> int` (line 186) — No method docstring provided.
    - `describe(self) -> DependencyStatus` (line 189) — No method docstring provided.
    - `get_client(self) -> QdrantClient` (line 199) — No method docstring provided.
    - `mark_failure(self, exc: Exception | None = None) -> None` (line 209) — No method docstring provided.
    - `heartbeat(self) -> bool` (line 219) — No method docstring provided.
    - `_create_client(self) -> QdrantClient` (line 230) — No method docstring provided.
    - `_record_success(self) -> None` (line 245) — No method docstring provided.

### Functions
- None

### Constants and Configuration
- GRAPH_DRIVER_FACTORY = GraphDatabase.driver (line 25)
- QDRANT_CLIENT_FACTORY = QdrantClient (line 26)

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Interacts with Qdrant collections for vector search or persistence.

### Integration Points
- contextlib, dataclasses, logging, neo4j, qdrant_client, threading, time

### Code Quality Notes
- 17 public element(s) lack docstrings.

## gateway/api/dependencies.py

**File path**: `gateway/api/dependencies.py`
**Purpose**: FastAPI dependency helpers for the gateway application.
**Dependencies**: External – __future__.annotations, fastapi.HTTPException, fastapi.Request, logging, slowapi.Limiter; Internal – gateway.config.settings.AppSettings, gateway.graph.GraphService, gateway.graph.get_graph_service, gateway.ingest.embedding.Embedder, gateway.search.SearchOptions, gateway.search.SearchService, gateway.search.SearchWeights, gateway.search.feedback.SearchFeedbackStore, gateway.search.trainer.ModelArtifact
**Related modules**: gateway.config.settings.AppSettings, gateway.graph.GraphService, gateway.graph.get_graph_service, gateway.ingest.embedding.Embedder, gateway.search.SearchOptions, gateway.search.SearchService, gateway.search.SearchWeights, gateway.search.feedback.SearchFeedbackStore, gateway.search.trainer.ModelArtifact

### Classes
- None

### Functions
- `get_app_settings(request: Request) -> AppSettings` (line 20) — Return the application settings attached to the FastAPI app.
- `get_limiter(request: Request) -> Limiter` (line 29) — Return the rate limiter configured on the FastAPI app.
- `get_search_model(request: Request) -> ModelArtifact | None` (line 38) — Return the cached search ranking model from application state.
- `get_graph_service_dependency(request: Request) -> GraphService` (line 43) — Return a memoised graph service bound to the current FastAPI app.
- `get_search_service_dependency(request: Request) -> SearchService | None` (line 74) — Construct (and cache) the hybrid search service for the application.
- `get_feedback_store(request: Request) -> SearchFeedbackStore | None` (line 132) — Return the configured search feedback store, if any.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- fastapi, logging, slowapi

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/api/routes/__init__.py

**File path**: `gateway/api/routes/__init__.py`
**Purpose**: FastAPI route modules for the gateway application.
**Dependencies**: External – graph, health, reporting, search; Internal – None
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
- graph, health, reporting, search

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/api/routes/graph.py

**File path**: `gateway/api/routes/graph.py`
**Purpose**: Graph API routes.
**Dependencies**: External – __future__.annotations, fastapi.APIRouter, fastapi.Body, fastapi.Depends, fastapi.HTTPException, fastapi.Request, fastapi.responses.JSONResponse, slowapi.Limiter, typing.Any; Internal – gateway.api.auth.require_maintainer, gateway.api.auth.require_reader, gateway.api.dependencies.get_graph_service_dependency, gateway.graph.GraphNotFoundError, gateway.graph.GraphQueryError, gateway.graph.GraphService
**Related modules**: gateway.api.auth.require_maintainer, gateway.api.auth.require_reader, gateway.api.dependencies.get_graph_service_dependency, gateway.graph.GraphNotFoundError, gateway.graph.GraphQueryError, gateway.graph.GraphService

### Classes
- None

### Functions
- `create_router(limiter: Limiter, metrics_limit: str) -> APIRouter` (line 16) — Create an API router exposing graph endpoints with shared rate limits.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- fastapi, slowapi, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/api/routes/health.py

**File path**: `gateway/api/routes/health.py`
**Purpose**: Health and observability endpoints.
**Dependencies**: External – __future__.annotations, contextlib.suppress, fastapi.APIRouter, fastapi.Depends, fastapi.FastAPI, fastapi.Request, fastapi.Response, json, prometheus_client.CONTENT_TYPE_LATEST, prometheus_client.generate_latest, slowapi.Limiter, sqlite3, time, typing.Any; Internal – gateway.api.connections.DependencyStatus, gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.api.dependencies.get_app_settings, gateway.config.settings.AppSettings
**Related modules**: gateway.api.connections.DependencyStatus, gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.api.dependencies.get_app_settings, gateway.config.settings.AppSettings

### Classes
- None

### Functions
- `create_router(limiter: Limiter, metrics_limit: str) -> APIRouter` (line 24) — Wire up health, readiness, and metrics endpoints.
- `build_health_report(app: FastAPI, settings: AppSettings) -> dict[str, object]` (line 48) — Assemble the health payload consumed by `/healthz`.
- `_coverage_health(settings: AppSettings) -> dict[str, Any]` (line 76) — No docstring provided.
- `_audit_health(settings: AppSettings) -> dict[str, Any]` (line 126) — No docstring provided.
- `_scheduler_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]` (line 150) — No docstring provided.
- `_graph_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]` (line 167) — No docstring provided.
- `_qdrant_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]` (line 174) — No docstring provided.
- `_dependency_health(manager: Neo4jConnectionManager | QdrantConnectionManager | None) -> dict[str, Any]` (line 182) — No docstring provided.
- `_backup_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]` (line 200) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- contextlib, fastapi, json, prometheus_client, slowapi, sqlite3, time, typing

### Code Quality Notes
- 7 public element(s) lack docstrings.

## gateway/api/routes/reporting.py

**File path**: `gateway/api/routes/reporting.py`
**Purpose**: Observability and reporting routes.
**Dependencies**: External – __future__.annotations, fastapi.APIRouter, fastapi.Depends, fastapi.HTTPException, fastapi.Request, fastapi.responses.JSONResponse, json, pathlib.Path, slowapi.Limiter, typing.Any; Internal – gateway.api.auth.require_maintainer, gateway.api.dependencies.get_app_settings, gateway.config.settings.AppSettings, gateway.ingest.audit.AuditLogger, gateway.ingest.lifecycle.summarize_lifecycle
**Related modules**: gateway.api.auth.require_maintainer, gateway.api.dependencies.get_app_settings, gateway.config.settings.AppSettings, gateway.ingest.audit.AuditLogger, gateway.ingest.lifecycle.summarize_lifecycle

### Classes
- None

### Functions
- `create_router(limiter: Limiter) -> APIRouter` (line 20) — Expose reporting and audit endpoints protected by maintainer auth.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- fastapi, json, pathlib, slowapi, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/api/routes/search.py

**File path**: `gateway/api/routes/search.py`
**Purpose**: Search API routes.
**Dependencies**: External – __future__.annotations, collections.abc.Mapping, datetime.UTC, datetime.datetime, fastapi.APIRouter, fastapi.Body, fastapi.Depends, fastapi.HTTPException, fastapi.Request, fastapi.responses.JSONResponse, logging, qdrant_client.http.exceptions.UnexpectedResponse, slowapi.Limiter, typing.Any, uuid.uuid4; Internal – gateway.api.auth.require_maintainer, gateway.api.auth.require_reader, gateway.api.dependencies.get_app_settings, gateway.api.dependencies.get_feedback_store, gateway.api.dependencies.get_graph_service_dependency, gateway.api.dependencies.get_search_service_dependency, gateway.config.settings.AppSettings, gateway.graph.GraphService, gateway.observability.SEARCH_REQUESTS_TOTAL, gateway.search.SearchService, gateway.search.feedback.SearchFeedbackStore
**Related modules**: gateway.api.auth.require_maintainer, gateway.api.auth.require_reader, gateway.api.dependencies.get_app_settings, gateway.api.dependencies.get_feedback_store, gateway.api.dependencies.get_graph_service_dependency, gateway.api.dependencies.get_search_service_dependency, gateway.config.settings.AppSettings, gateway.graph.GraphService, gateway.observability.SEARCH_REQUESTS_TOTAL, gateway.search.SearchService, gateway.search.feedback.SearchFeedbackStore

### Classes
- None

### Functions
- `create_router(limiter: Limiter, metrics_limit: str) -> APIRouter` (line 32) — Return an API router for the search endpoints with shared rate limits.
- `_parse_iso8601_to_utc(value: str) -> datetime | None` (line 225) — No docstring provided.
- `_has_vote(mapping: Mapping[str, Any] | None) -> bool` (line 240) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Interacts with Qdrant collections for vector search or persistence.
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- collections, datetime, fastapi, logging, qdrant_client, slowapi, typing, uuid

### Code Quality Notes
- 2 public element(s) lack docstrings.

## gateway/backup/__init__.py

**File path**: `gateway/backup/__init__.py`
**Purpose**: Backup utilities for the knowledge gateway.
**Dependencies**: External – exceptions.BackupExecutionError, service.ARCHIVE_ALLOWED_SUFFIXES, service.ARCHIVE_FILENAME_PREFIX, service.BackupResult, service.default_backup_destination, service.is_backup_archive, service.run_backup; Internal – None
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
- exceptions, service

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/backup/exceptions.py

**File path**: `gateway/backup/exceptions.py`
**Purpose**: Custom exceptions for gateway backup operations.
**Dependencies**: External – __future__.annotations; Internal – None
**Related modules**: None

### Classes
- `BackupExecutionError` (line 6) — Raised when the backup helper fails to produce an archive. Inherits from RuntimeError.
  - Methods: None

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

## gateway/backup/service.py

**File path**: `gateway/backup/service.py`
**Purpose**: Helper functions for orchestrating state backups.
**Dependencies**: External – __future__.annotations, collections.abc.Mapping, contextlib.suppress, exceptions.BackupExecutionError, os, pathlib.Path, re, subprocess; Internal – None
**Related modules**: None

### Classes
- `BackupResult` (line 22) — Simple mapping describing the archive produced by a backup run. Inherits from dict.
  - Attributes: archive: Path
  - Methods: None

### Functions
- `default_backup_destination(state_path: Path) -> Path` (line 28) — Return the default directory for storing backup archives.
- `is_backup_archive(path: Path) -> bool` (line 34) — Return ``True`` when ``path`` matches the managed backup filename pattern.
- `run_backup(state_path: Path, script_path: Path | None, destination_path: Path | None = None, extra_env: Mapping[str, str] | None = None) -> BackupResult` (line 43) — Execute the backup helper synchronously and return archive metadata.
- `_parse_archive_path(output: str) -> str | None` (line 96) — No docstring provided.
- `_default_backup_script() -> Path` (line 104) — No docstring provided.

### Constants and Configuration
- _BACKUP_DONE_PATTERN = re.compile('Backup written to (?P<path>.+)$') (line 14)
- ARCHIVE_FILENAME_PREFIX = 'km-backup-' (line 16)
- ARCHIVE_ALLOWED_SUFFIXES = ('.tgz', '.tar.gz') (line 17)
- DEFAULT_BACKUP_DIRNAME = 'backups' (line 18)
- DEFAULT_BACKUP_ARCHIVE_DIRNAME = 'archives' (line 19)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, contextlib, exceptions, os, pathlib, re, subprocess

### Code Quality Notes
- 2 public element(s) lack docstrings.

## gateway/config/__init__.py

**File path**: `gateway/config/__init__.py`
**Purpose**: Configuration helpers for the knowledge gateway.
**Dependencies**: External – __future__.annotations, settings.AppSettings, settings.get_settings; Internal – None
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
- settings

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/config/settings.py

**File path**: `gateway/config/settings.py`
**Purpose**: Pydantic-based configuration for the knowledge gateway.
**Dependencies**: External – __future__.annotations, functools.lru_cache, pathlib.Path, pydantic.Field, pydantic.field_validator, pydantic_settings.BaseSettings, typing.Literal; Internal – None
**Related modules**: None

### Classes
- `AppSettings` (line 44) — Runtime configuration for the knowledge gateway. Inherits from BaseSettings.
  - Attributes: api_host: str = Field('0.0.0.0', alias='KM_API_HOST'), api_port: int = Field(8000, alias='KM_API_PORT'), auth_mode: Literal['secure', 'insecure'] = Field('secure', alias='KM_AUTH_MODE'), auth_enabled: bool = Field(True, alias='KM_AUTH_ENABLED'), reader_token: str | None = Field(None, alias='KM_READER_TOKEN'), maintainer_token: str | None = Field(None, alias='KM_ADMIN_TOKEN'), rate_limit_requests: int = Field(120, alias='KM_RATE_LIMIT_REQUESTS'), rate_limit_window_seconds: int = Field(60, alias='KM_RATE_LIMIT_WINDOW'), repo_root: Path = Field(Path('/workspace/repo'), alias='KM_REPO_PATH'), state_path: Path = Field(Path('/opt/knowledge/var'), alias='KM_STATE_PATH'), content_root: Path = Field(Path('/workspace/repo'), alias='KM_CONTENT_ROOT'), content_docs_subdir: Path = Field(Path('docs'), alias='KM_CONTENT_DOCS_SUBDIR'), upload_default_overwrite: bool = Field(False, alias='KM_UPLOAD_DEFAULT_OVERWRITE'), upload_default_ingest: bool = Field(False, alias='KM_UPLOAD_DEFAULT_INGEST'), qdrant_url: str = Field('http://localhost:6333', alias='KM_QDRANT_URL'), qdrant_api_key: str | None = Field(None, alias='KM_QDRANT_API_KEY'), qdrant_collection: str = Field('km_knowledge_v1', alias='KM_QDRANT_COLLECTION'), neo4j_uri: str = Field('bolt://localhost:7687', alias='KM_NEO4J_URI'), neo4j_user: str = Field('neo4j', alias='KM_NEO4J_USER'), neo4j_password: str = Field('neo4jadmin', alias='KM_NEO4J_PASSWORD'), neo4j_database: str = Field('neo4j', alias='KM_NEO4J_DATABASE'), neo4j_auth_enabled: bool = Field(True, alias='KM_NEO4J_AUTH_ENABLED'), neo4j_readonly_uri: str | None = Field(None, alias='KM_NEO4J_READONLY_URI'), neo4j_readonly_user: str | None = Field(None, alias='KM_NEO4J_READONLY_USER'), neo4j_readonly_password: str | None = Field(None, alias='KM_NEO4J_READONLY_PASSWORD'), embedding_model: str = Field('sentence-transformers/all-MiniLM-L6-v2', alias='KM_EMBEDDING_MODEL'), ingest_window: int = Field(1000, alias='KM_INGEST_WINDOW'), ingest_overlap: int = Field(200, alias='KM_INGEST_OVERLAP'), ingest_use_dummy_embeddings: bool = Field(False, alias='KM_INGEST_USE_DUMMY'), ingest_incremental_enabled: bool = Field(True, alias='KM_INGEST_INCREMENTAL'), ingest_parallel_workers: int = Field(2, alias='KM_INGEST_PARALLEL_WORKERS'), ingest_max_pending_batches: int = Field(4, alias='KM_INGEST_MAX_PENDING_BATCHES'), scheduler_enabled: bool = Field(False, alias='KM_SCHEDULER_ENABLED'), scheduler_interval_minutes: int = Field(30, alias='KM_SCHEDULER_INTERVAL_MINUTES'), scheduler_cron: str | None = Field(None, alias='KM_SCHEDULER_CRON'), coverage_enabled: bool = Field(True, alias='KM_COVERAGE_ENABLED'), coverage_history_limit: int = Field(5, alias='KM_COVERAGE_HISTORY_LIMIT'), backup_enabled: bool = Field(False, alias='KM_BACKUP_ENABLED'), backup_interval_minutes: int = Field(720, alias='KM_BACKUP_INTERVAL_MINUTES'), backup_cron: str | None = Field(None, alias='KM_BACKUP_CRON'), backup_retention_limit: int = Field(7, alias='KM_BACKUP_RETENTION_LIMIT'), backup_destination: Path | None = Field(None, alias='KM_BACKUP_DEST_PATH'), backup_script_path: Path | None = Field(None, alias='KM_BACKUP_SCRIPT'), lifecycle_report_enabled: bool = Field(True, alias='KM_LIFECYCLE_REPORT_ENABLED'), lifecycle_stale_days: int = Field(30, alias='KM_LIFECYCLE_STALE_DAYS'), lifecycle_history_limit: int = Field(10, alias='KM_LIFECYCLE_HISTORY_LIMIT'), tracing_enabled: bool = Field(False, alias='KM_TRACING_ENABLED'), tracing_endpoint: str | None = Field(None, alias='KM_TRACING_ENDPOINT'), tracing_headers: str | None = Field(None, alias='KM_TRACING_HEADERS'), tracing_service_name: str = Field('duskmantle-knowledge-gateway', alias='KM_TRACING_SERVICE_NAME'), tracing_sample_ratio: float = Field(1.0, alias='KM_TRACING_SAMPLE_RATIO'), tracing_console_export: bool = Field(False, alias='KM_TRACING_CONSOLE_EXPORT'), graph_auto_migrate: bool = Field(False, alias='KM_GRAPH_AUTO_MIGRATE'), graph_subsystem_cache_ttl_seconds: int = Field(30, alias='KM_GRAPH_SUBSYSTEM_CACHE_TTL'), graph_subsystem_cache_max_entries: int = Field(128, alias='KM_GRAPH_SUBSYSTEM_CACHE_MAX'), search_weight_profile: Literal['default', 'analysis', 'operations', 'docs-heavy'] = Field('default', alias='KM_SEARCH_WEIGHT_PROFILE'), search_weight_subsystem: float = Field(0.28, alias='KM_SEARCH_W_SUBSYSTEM'), search_weight_relationship: float = Field(0.05, alias='KM_SEARCH_W_RELATIONSHIP'), search_weight_support: float = Field(0.09, alias='KM_SEARCH_W_SUPPORT'), search_weight_coverage_penalty: float = Field(0.15, alias='KM_SEARCH_W_COVERAGE_PENALTY'), search_weight_criticality: float = Field(0.12, alias='KM_SEARCH_W_CRITICALITY'), search_sort_by_vector: bool = Field(False, alias='KM_SEARCH_SORT_BY_VECTOR'), search_scoring_mode: Literal['heuristic', 'ml'] = Field('heuristic', alias='KM_SEARCH_SCORING_MODE'), search_model_path: Path | None = Field(None, alias='KM_SEARCH_MODEL_PATH'), search_warn_slow_graph_ms: int = Field(250, alias='KM_SEARCH_WARN_GRAPH_MS'), search_vector_weight: float = Field(1.0, alias='KM_SEARCH_VECTOR_WEIGHT'), search_lexical_weight: float = Field(0.25, alias='KM_SEARCH_LEXICAL_WEIGHT'), search_hnsw_ef_search: int | None = Field(128, alias='KM_SEARCH_HNSW_EF_SEARCH'), dry_run: bool = Field(False, alias='KM_INGEST_DRY_RUN'), model_config = {'env_file': '.env', 'extra': 'ignore'}
  - Methods:
    - `_clamp_tracing_ratio(cls, value: float) -> float` (line 137) — Ensure the tracing sampling ratio stays within [0, 1].
    - `_clamp_search_weights(cls, value: float) -> float` (line 156) — Clamp search weights to [0, 1] for stability.
    - `_sanitize_hnsw_ef(cls, value: int | None) -> int | None` (line 167) — No method docstring provided.
    - `_sanitize_graph_cache_ttl(cls, value: int) -> int` (line 176) — No method docstring provided.
    - `_sanitize_graph_cache_max(cls, value: int) -> int` (line 183) — No method docstring provided.
    - `_sanitize_backup_interval(cls, value: int) -> int` (line 190) — No method docstring provided.
    - `_sanitize_backup_retention(cls, value: int) -> int` (line 197) — No method docstring provided.
    - `resolved_search_weights(self) -> tuple[str, dict[str, float]]` (line 202) — Return the active search weight profile name and resolved weights.
    - `backup_trigger_config(self) -> dict[str, object]` (line 229) — Return trigger configuration for the automated backup job.
    - `scheduler_trigger_config(self) -> dict[str, object]` (line 239) — Return trigger configuration for the ingestion scheduler.
    - `_validate_history_limit(cls, value: int) -> int` (line 251) — No method docstring provided.
    - `_validate_lifecycle_stale(cls, value: int) -> int` (line 260) — No method docstring provided.
    - `_ensure_positive_parallelism(cls, value: int) -> int` (line 269) — No method docstring provided.

### Functions
- `get_settings() -> AppSettings` (line 280) — Load settings from environment (cached).

### Constants and Configuration
- SEARCH_WEIGHT_PROFILES : dict[str, dict[str, float]] = {'default': {'weight_subsystem': 0.28, 'weight_relationship': 0.05, 'weight_support': 0.09, 'weight_coverage_penalty': 0.15, 'weight_criticality': 0.12}, 'analysis': {'weight_subsystem': 0.38, 'weight_relationship': 0.1, 'weight_support': 0.08, 'weight_coverage_penalty': 0.18, 'weight_criticality': 0.18}, 'operations': {'weight_subsystem': 0.22, 'weight_relationship': 0.08, 'weight_support': 0.06, 'weight_coverage_penalty': 0.28, 'weight_criticality': 0.1}, 'docs-heavy': {'weight_subsystem': 0.26, 'weight_relationship': 0.04, 'weight_support': 0.22, 'weight_coverage_penalty': 0.12, 'weight_criticality': 0.08}} (line 12)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- functools, pathlib, pydantic, pydantic_settings, typing

### Code Quality Notes
- 8 public element(s) lack docstrings.

## gateway/graph/__init__.py

**File path**: `gateway/graph/__init__.py`
**Purpose**: Graph query utilities and service layer.
**Dependencies**: External – service.GraphNotFoundError, service.GraphQueryError, service.GraphService, service.get_graph_service; Internal – None
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
- service

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/graph/cli.py

**File path**: `gateway/graph/cli.py`
**Purpose**: Command-line utilities for managing the Neo4j graph schema.
**Dependencies**: External – __future__.annotations, argparse, logging, neo4j.GraphDatabase; Internal – gateway.config.settings.get_settings, gateway.graph.migrations.MigrationRunner
**Related modules**: gateway.config.settings.get_settings, gateway.graph.migrations.MigrationRunner

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` (line 16) — Return the CLI argument parser for graph administration commands.
- `run_migrations(dry_run: bool = False) -> None` (line 31) — Execute graph schema migrations, optionally printing the pending set.
- `main(argv: list[str] | None = None) -> None` (line 54) — Entrypoint for the `gateway-graph` command-line interface.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- argparse, logging, neo4j

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/graph/migrations/__init__.py

**File path**: `gateway/graph/migrations/__init__.py`
**Purpose**: Graph schema migrations.
**Dependencies**: External – runner.MigrationRunner; Internal – None
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
- runner

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/graph/migrations/runner.py

**File path**: `gateway/graph/migrations/runner.py`
**Purpose**: Helpers for applying and tracking Neo4j schema migrations.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, dataclasses.dataclass, logging, neo4j.Driver; Internal – None
**Related modules**: None

### Classes
- `Migration` (line 15) — Describe a single migration and the Cypher statements it executes. Inherits from object.
  - Attributes: id: str, statements: Iterable[str]
  - Methods: None
- `MigrationRunner` (line 45) — Apply ordered graph migrations using a shared Neo4j driver. Inherits from object.
  - Attributes: driver: Driver, database: str = 'knowledge'
  - Methods:
    - `pending_ids(self) -> list[str]` (line 51) — Return the identifiers of migrations that have not yet been applied.
    - `run(self) -> None` (line 59) — Apply all pending migrations to the configured Neo4j database.
    - `_is_applied(self, migration_id: str) -> bool` (line 69) — Return whether the given migration has already been recorded.
    - `_apply(self, migration: Migration) -> None` (line 78) — Execute migration statements and record completion.

### Functions
- None

### Constants and Configuration
- MIGRATIONS : list[Migration] = [Migration(id='001_constraints', statements=['CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (f:SourceFile) REQUIRE f.path IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (d:DesignDoc) REQUIRE d.path IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.path IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE']), Migration(id='002_domain_entities', statements=['CREATE CONSTRAINT IF NOT EXISTS FOR (m:IntegrationMessage) REQUIRE m.name IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (tc:TelemetryChannel) REQUIRE tc.name IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (cfg:ConfigFile) REQUIRE cfg.path IS UNIQUE'])] (line 22)

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- collections, dataclasses, logging, neo4j

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/graph/service.py

**File path**: `gateway/graph/service.py`
**Purpose**: Read-only graph service utilities backed by Neo4j.
**Dependencies**: External – __future__.annotations, base64, collections.OrderedDict, collections.abc.Callable, collections.abc.Mapping, collections.abc.Sequence, dataclasses.dataclass, neo4j.Driver, neo4j.ManagedTransaction, neo4j.Session, neo4j.exceptions.Neo4jError, neo4j.exceptions.ServiceUnavailable, neo4j.graph.Node, neo4j.graph.Relationship, threading.Lock, time.monotonic, typing.Any, typing.TypeVar, typing.cast; Internal – gateway.observability.metrics.GRAPH_CYPHER_DENIED_TOTAL
**Related modules**: gateway.observability.metrics.GRAPH_CYPHER_DENIED_TOTAL

### Classes
- `GraphServiceError` (line 22) — Base class for graph-related errors. Inherits from RuntimeError.
  - Methods: None
- `GraphNotFoundError` (line 26) — Raised when a requested node cannot be found. Inherits from GraphServiceError.
  - Methods: None
- `GraphQueryError` (line 30) — Raised when a supplied query is invalid or unsafe. Inherits from GraphServiceError.
  - Methods: None
- `SubsystemGraphSnapshot` (line 35) — Snapshot of a subsystem node and its related graph context. Inherits from object.
  - Attributes: subsystem: dict[str, Any], related: list[dict[str, Any]], nodes: list[dict[str, Any]], edges: list[dict[str, Any]], artifacts: list[dict[str, Any]]
  - Methods: None
- `SubsystemGraphCache` (line 54) — Simple TTL cache for subsystem graph snapshots. Inherits from object.
  - Methods:
    - `__init__(self, ttl_seconds: float, max_entries: int) -> None` (line 57) — Create a cache with an expiry window and bounded size.
    - `get(self, key: tuple[str, int]) -> SubsystemGraphSnapshot | None` (line 64) — Return a cached snapshot if it exists and has not expired.
    - `set(self, key: tuple[str, int], snapshot: SubsystemGraphSnapshot) -> None` (line 80) — Cache a snapshot for the given key, evicting oldest entries if needed.
    - `clear(self) -> None` (line 91) — Remove all cached subsystem snapshots.
- `GraphService` (line 97) — Service layer for read-only graph queries. Inherits from object.
  - Attributes: __slots__ = ('_driver_provider', '_readonly_provider', '_failure_callback', 'database', 'subsystem_cache')
  - Methods:
    - `__init__(self, driver_provider: Callable[[], Driver], database: str, cache_ttl: float | None = None, cache_max_entries: int = 128, readonly_provider: Callable[[], Driver] | None = None, failure_callback: Callable[[Exception], None] | None = None) -> None` (line 108) — No method docstring provided.
    - `clear_cache(self) -> None` (line 124) — Wipe the subsystem snapshot cache if caching is enabled.
    - `_get_driver(self, readonly: bool = False) -> Driver` (line 129) — No method docstring provided.
    - `_execute(self, operation: Callable[[Driver], T], readonly: bool = False) -> T` (line 134) — No method docstring provided.
    - `_run_with_session(self, operation: Callable[[Session], T], readonly: bool = False, **session_kwargs: object) -> T` (line 149) — No method docstring provided.
    - `get_subsystem(self, name: str, depth: int, limit: int, cursor: str | None, include_artifacts: bool) -> dict[str, Any]` (line 164) — Return a windowed view of related nodes for the requested subsystem.
    - `get_subsystem_graph(self, name: str, depth: int) -> dict[str, Any]` (line 197) — Return the full node/edge snapshot for a subsystem.
    - `list_orphan_nodes(self, label: str | None, cursor: str | None, limit: int) -> dict[str, Any]` (line 207) — List nodes that have no relationships of the allowed labels.
    - `_load_subsystem_snapshot(self, name: str, depth: int) -> SubsystemGraphSnapshot` (line 235) — No method docstring provided.
    - `_build_subsystem_snapshot(self, name: str, depth: int) -> SubsystemGraphSnapshot` (line 247) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 297) — Return a node and a limited set of relationships using Cypher lookups.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 327) — Search the graph for nodes matching the provided term.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 347) — Return the length of the shortest path from the node to any subsystem.  The search is bounded by ``max_depth`` hops across the knowledge graph relationship types used by ingestion. ``None`` is returned when no subsystem can be reached within the given depth limit.
    - `run_cypher(self, query: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]` (line 385) — Execute an arbitrary Cypher query and serialize the response.

### Functions
- `get_graph_service(driver: Driver | Callable[[], Driver], database: str, cache_ttl: float | None = None, cache_max_entries: int = 128, readonly_driver: Driver | Callable[[], Driver] | None = None, failure_callback: Callable[[Exception], None] | None = None) -> GraphService` (line 460) — Factory helper that constructs a `GraphService` with optional caching.
- `_extract_path_components(record: Mapping[str, Any]) -> tuple[Node, Sequence[Node], Sequence[Relationship]] | None` (line 492) — No docstring provided.
- `_record_path_edges(path_nodes: Sequence[Node], relationships: Sequence[Relationship], nodes_by_id: OrderedDict[str, dict[str, Any]], edges_by_key: OrderedDict[tuple[str, str, str], dict[str, Any]]) -> list[dict[str, Any]]` (line 518) — No docstring provided.
- `_ensure_serialized_node(node: Node, nodes_by_id: OrderedDict[str, dict[str, Any]]) -> dict[str, Any]` (line 548) — No docstring provided.
- `_relationship_direction(relationship: Relationship, source_node: Node) -> str` (line 558) — No docstring provided.
- `_build_related_entry(target_serialized: dict[str, Any], relationships: Sequence[Relationship], path_edges: Sequence[dict[str, Any]]) -> dict[str, Any]` (line 563) — No docstring provided.
- `_append_related_entry(entry: dict[str, Any], target_id: str, related_entries: list[dict[str, Any]], related_order: list[str]) -> None` (line 577) — No docstring provided.
- `_fetch_subsystem_node(name: str) -> Node | None` (line 592) — No docstring provided.
- `_fetch_subsystem_paths(name: str, depth: int) -> list[dict[str, Any]]` (line 598) — No docstring provided.
- `_fetch_artifacts_for_subsystem(name: str) -> list[Node]` (line 629) — No docstring provided.
- `_fetch_orphan_nodes(label: str | None, skip: int, limit: int) -> list[Node]` (line 639) — No docstring provided.
- `_fetch_node_by_id(label: str, key: str, value: object) -> Node | None` (line 665) — No docstring provided.
- `_fetch_node_relationships(label: str, key: str, value: object, direction: str, limit: int) -> list[dict[str, Any]]` (line 671) — No docstring provided.
- `_search_entities(term: str, limit: int) -> list[dict[str, Any]]` (line 690) — No docstring provided.
- `_serialize_related(record: dict[str, Any], subsystem_node: Node) -> dict[str, Any]` (line 723) — No docstring provided.
- `_serialize_node(node: Node) -> dict[str, Any]` (line 741) — No docstring provided.
- `_serialize_relationship(record: dict[str, Any]) -> dict[str, Any]` (line 749) — No docstring provided.
- `_serialize_value(value: object) -> object` (line 773) — No docstring provided.
- `_ensure_node(value: object) -> Node` (line 788) — No docstring provided.
- `_node_element_id(node: Node | None) -> str` (line 794) — No docstring provided.
- `_canonical_node_id(node: Node) -> str` (line 800) — No docstring provided.
- `_parse_node_id(node_id: str) -> tuple[str, str, str]` (line 816) — No docstring provided.
- `_encode_cursor(offset: int) -> str` (line 835) — No docstring provided.
- `_decode_cursor(cursor: str | None) -> int` (line 839) — No docstring provided.
- `_validate_cypher(query: str) -> None` (line 848) — No docstring provided.
- `_strip_literals_and_comments(query: str) -> str` (line 881) — No docstring provided.
- `_tokenize_query(upper_query: str) -> list[str]` (line 927) — No docstring provided.
- `_extract_procedure_calls(tokens: list[str]) -> list[str]` (line 942) — No docstring provided.
- `_deny_cypher(reason: str, message: str) -> None` (line 975) — No docstring provided.

### Constants and Configuration
- T = TypeVar('T') (line 19)
- ORPHAN_DEFAULT_LABELS : tuple[str, ...] = ('DesignDoc', 'SourceFile', 'Chunk', 'TestCase', 'IntegrationMessage') (line 45)
- _ALLOWED_PROCEDURE_PREFIXES = ('DB.SCHEMA.', 'DB.LABELS', 'DB.RELATIONSHIPTYPES', 'DB.INDEXES', 'DB.CONSTRAINTS', 'DB.PROPERTYKEYS') (line 965)

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- base64, collections, dataclasses, neo4j, threading, time, typing

### Code Quality Notes
- 34 public element(s) lack docstrings.

## gateway/ingest/__init__.py

**File path**: `gateway/ingest/__init__.py`
**Purpose**: Ingestion pipeline components for the knowledge gateway.
**Dependencies**: External – None; Internal – gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline
**Related modules**: gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline

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

## gateway/ingest/artifacts.py

**File path**: `gateway/ingest/artifacts.py`
**Purpose**: Domain models representing artifacts produced during ingestion.
**Dependencies**: External – __future__.annotations, dataclasses.dataclass, dataclasses.field, pathlib.Path, typing.Any; Internal – None
**Related modules**: None

### Classes
- `Artifact` (line 11) — Represents a repository artifact prior to chunking. Inherits from object.
  - Attributes: path: Path, artifact_type: str, subsystem: str | None, content: str, git_commit: str | None, git_timestamp: int | None, extra_metadata: dict[str, Any] = field(default_factory=dict)
  - Methods: None
- `Chunk` (line 24) — Represents a chunk ready for embedding and indexing. Inherits from object.
  - Attributes: artifact: Artifact, chunk_id: str, text: str, sequence: int, content_digest: str, metadata: dict[str, Any]
  - Methods: None
- `ChunkEmbedding` (line 36) — Chunk plus embedding vector. Inherits from object.
  - Attributes: chunk: Chunk, vector: list[float]
  - Methods: None

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- dataclasses, pathlib, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/audit.py

**File path**: `gateway/ingest/audit.py`
**Purpose**: SQLite-backed audit log utilities for ingestion runs.
**Dependencies**: External – __future__.annotations, pathlib.Path, sqlite3, time, typing.Any; Internal – gateway.ingest.pipeline.IngestionResult
**Related modules**: gateway.ingest.pipeline.IngestionResult

### Classes
- `AuditLogger` (line 48) — Persist and retrieve ingestion run metadata in SQLite. Inherits from object.
  - Methods:
    - `__init__(self, db_path: Path) -> None` (line 51) — Initialise the audit database and ensure the schema exists.
    - `record(self, result: IngestionResult) -> None` (line 58) — Insert a new ingestion run entry.
    - `recent(self, limit: int = 20) -> list[dict[str, Any]]` (line 77) — Return the most recent ingestion runs up to ``limit`` entries.

### Functions
- None

### Constants and Configuration
- _SCHEMA = '\nCREATE TABLE IF NOT EXISTS ingestion_runs (\n    run_id TEXT PRIMARY KEY,\n    profile TEXT,\n    started_at REAL,\n    duration_seconds REAL,\n    artifact_count INTEGER,\n    chunk_count INTEGER,\n    repo_head TEXT,\n    success INTEGER,\n    created_at REAL\n)\n' (line 12)
- _SELECT_RECENT = '\nSELECT run_id, profile, started_at, duration_seconds, artifact_count, chunk_count, repo_head, success, created_at\nFROM ingestion_runs\nORDER BY created_at DESC\nLIMIT ?\n' (line 26)
- _INSERT_RUN = '\nINSERT INTO ingestion_runs (\n    run_id,\n    profile,\n    started_at,\n    duration_seconds,\n    artifact_count,\n    chunk_count,\n    repo_head,\n    success,\n    created_at\n) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n' (line 33)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- pathlib, sqlite3, time, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/chunking.py

**File path**: `gateway/ingest/chunking.py`
**Purpose**: Chunk source artifacts into overlapping windows for indexing.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, hashlib, math, pathlib.Path, typing.Any; Internal – gateway.ingest.artifacts.Artifact, gateway.ingest.artifacts.Chunk
**Related modules**: gateway.ingest.artifacts.Artifact, gateway.ingest.artifacts.Chunk

### Classes
- `Chunker` (line 17) — Split artifacts into overlapping textual chunks. Inherits from object.
  - Methods:
    - `__init__(self, window: int = DEFAULT_WINDOW, overlap: int = DEFAULT_OVERLAP) -> None` (line 20) — Configure chunk sizes and overlap.
    - `split(self, artifact: Artifact) -> Iterable[Chunk]` (line 29) — Split the artifact content into `Chunk` instances.
    - `estimate_chunk_count(path: Path, text: str, window: int = DEFAULT_WINDOW, overlap: int = DEFAULT_OVERLAP) -> int` (line 69) — Estimate how many chunks a text would produce with the configured window.

### Functions
- `_derive_namespace(path: Path) -> str` (line 78) — Infer a namespace from a file path for tagging chunks.
- `_build_tags(extra_metadata: dict[str, Any]) -> list[str]` (line 88) — Collect tag-like signals from artifact metadata.

### Constants and Configuration
- DEFAULT_WINDOW = 1000 (line 13)
- DEFAULT_OVERLAP = 200 (line 14)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, hashlib, math, pathlib, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/cli.py

**File path**: `gateway/ingest/cli.py`
**Purpose**: Command-line helpers for triggering and inspecting ingestion runs.
**Dependencies**: External – __future__.annotations, argparse, collections.abc.Iterable, datetime.datetime, logging, pathlib.Path, rich.console.Console, rich.table.Table; Internal – gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.ingest.audit.AuditLogger, gateway.ingest.service.execute_ingestion, gateway.observability.configure_logging, gateway.observability.configure_tracing
**Related modules**: gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.ingest.audit.AuditLogger, gateway.ingest.service.execute_ingestion, gateway.observability.configure_logging, gateway.observability.configure_tracing

### Classes
- None

### Functions
- `_ensure_maintainer_scope(settings: AppSettings) -> None` (line 23) — Abort execution if maintainer credentials are missing during auth.
- `build_parser() -> argparse.ArgumentParser` (line 29) — Create an argument parser for the ingestion CLI.
- `rebuild(profile: str, repo: Path | None, dry_run: bool, dummy_embeddings: bool, incremental: bool | None, settings: AppSettings | None = None) -> None` (line 89) — Execute a full ingestion pass.
- `audit_history(limit: int, output_json: bool, settings: AppSettings | None = None) -> None` (line 122) — Display recent ingestion runs from the audit ledger.
- `_render_audit_table(entries: Iterable[dict[str, object]]) -> Table` (line 148) — Render recent audit entries as a Rich table.
- `_format_timestamp(raw: object) -> str` (line 180) — Format timestamps from the audit ledger for display.
- `_coerce_int(value: object) -> int | None` (line 188) — Attempt to interpret the value as an integer.
- `_coerce_float(value: object) -> float | None` (line 200) — Attempt to interpret the value as a floating point number.
- `main(argv: list[str] | None = None) -> None` (line 215) — Entry point for the CLI.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- argparse, collections, datetime, logging, pathlib, rich

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/coverage.py

**File path**: `gateway/ingest/coverage.py`
**Purpose**: Utilities for writing ingestion coverage reports.
**Dependencies**: External – __future__.annotations, contextlib.suppress, datetime.UTC, datetime.datetime, json, pathlib.Path, time; Internal – gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.COVERAGE_HISTORY_SNAPSHOTS, gateway.observability.metrics.COVERAGE_LAST_RUN_STATUS, gateway.observability.metrics.COVERAGE_LAST_RUN_TIMESTAMP, gateway.observability.metrics.COVERAGE_MISSING_ARTIFACTS, gateway.observability.metrics.COVERAGE_STALE_ARTIFACTS
**Related modules**: gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.COVERAGE_HISTORY_SNAPSHOTS, gateway.observability.metrics.COVERAGE_LAST_RUN_STATUS, gateway.observability.metrics.COVERAGE_LAST_RUN_TIMESTAMP, gateway.observability.metrics.COVERAGE_MISSING_ARTIFACTS, gateway.observability.metrics.COVERAGE_STALE_ARTIFACTS

### Classes
- None

### Functions
- `write_coverage_report(result: IngestionResult, config: IngestionConfig, output_path: Path, history_limit: int | None = None) -> None` (line 21) — Persist coverage metrics derived from an ingestion result.
- `_write_history_snapshot(payload: dict[str, object], reports_dir: Path, history_limit: int) -> list[Path]` (line 67) — Write coverage history snapshots and prune old entries.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- contextlib, datetime, json, pathlib, time

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/discovery.py

**File path**: `gateway/ingest/discovery.py`
**Purpose**: Repository discovery helpers for ingestion pipeline.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.abc.Mapping, dataclasses.dataclass, fnmatch.fnmatch, json, logging, pathlib.Path, re, subprocess, typing.Any; Internal – gateway.ingest.artifacts.Artifact
**Related modules**: gateway.ingest.artifacts.Artifact

### Classes
- `DiscoveryConfig` (line 43) — Runtime knobs influencing which artifacts are discovered. Inherits from object.
  - Attributes: repo_root: Path, include_patterns: tuple[str, ...] = ('docs', 'src', 'tests', '.codacy')
  - Methods: None

### Functions
- `discover(config: DiscoveryConfig) -> Iterable[Artifact]` (line 59) — Yield textual artifacts from the repository.
- `_should_include(path: Path, repo_root: Path, include_patterns: tuple[str, ...]) -> bool` (line 117) — No docstring provided.
- `_is_textual(path: Path) -> bool` (line 125) — No docstring provided.
- `_infer_artifact_type(path: Path, repo_root: Path) -> str` (line 135) — No docstring provided.
- `_lookup_git_metadata(path: Path, repo_root: Path) -> tuple[str | None, int | None]` (line 151) — No docstring provided.
- `_load_subsystem_catalog(repo_root: Path) -> dict[str, Any]` (line 179) — No docstring provided.
- `_detect_source_prefixes(repo_root: Path) -> list[tuple[str, ...]]` (line 207) — Infer source package prefixes (e.g. ``("src", "gateway")``).
- `_collect_pyproject_prefixes(root: Path, prefixes: set[tuple[str, ...]]) -> None` (line 224) — No docstring provided.
- `_load_pyproject(path: Path) -> Mapping[str, Any] | dict[str, Any]` (line 243) — No docstring provided.
- `_collect_poetry_prefixes(tool_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None` (line 251) — No docstring provided.
- `_collect_project_prefixes(project_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None` (line 266) — No docstring provided.
- `_collect_setuptools_prefixes(tool_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None` (line 278) — No docstring provided.
- `_collect_src_directory_prefixes(root: Path, prefixes: set[tuple[str, ...]]) -> None` (line 299) — No docstring provided.
- `_add_prefix(prefixes: set[tuple[str, ...]], include: str | None, base: str | None = 'src') -> None` (line 308) — No docstring provided.
- `_ensure_str_list(value: object) -> list[str]` (line 322) — No docstring provided.
- `_infer_subsystem(path: Path, repo_root: Path, source_prefixes: list[tuple[str, ...]]) -> str | None` (line 330) — No docstring provided.
- `_normalize_subsystem_name(value: str | None) -> str | None` (line 356) — No docstring provided.
- `_match_catalog_entry(path: Path, repo_root: Path, catalog: dict[str, dict[str, Any]]) -> dict[str, Any] | None` (line 367) — No docstring provided.
- `_iter_metadata_patterns(metadata: Mapping[str, Any]) -> Iterable[str]` (line 380) — No docstring provided.
- `_pattern_matches(target: str, pattern: str) -> bool` (line 400) — No docstring provided.
- `dump_artifacts(artifacts: Iterable[Artifact]) -> str` (line 407) — Serialize artifacts for debugging or dry-run output.

### Constants and Configuration
- _TEXTUAL_SUFFIXES = {'.md', '.txt', '.py', '.proto', '.yml', '.yaml', '.json', '.ini', '.cfg', '.toml', '.sql'} (line 24)
- _MESSAGE_PATTERN = re.compile('[A-Z]\\w*Message') (line 38)
- _TELEMETRY_PATTERN = re.compile('Telemetry\\w+') (line 39)
- _SUBSYSTEM_METADATA_CACHE : dict[Path, dict[str, Any]] = {} (line 55)
- _SOURCE_PREFIX_CACHE : dict[Path, list[tuple[str, ...]]] = {} (line 56)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, dataclasses, fnmatch, json, logging, pathlib, re, subprocess, typing

### Code Quality Notes
- 18 public element(s) lack docstrings.

## gateway/ingest/embedding.py

**File path**: `gateway/ingest/embedding.py`
**Purpose**: Embedding helpers used during ingestion.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, functools.lru_cache, logging, sentence_transformers.SentenceTransformer; Internal – None
**Related modules**: None

### Classes
- `Embedder` (line 14) — Wrapper around sentence-transformers for configurable embeddings. Inherits from object.
  - Methods:
    - `__init__(self, model_name: str) -> None` (line 17) — Load the requested sentence-transformer model.
    - `dimension(self) -> int` (line 24) — Return the embedding dimensionality for the underlying model.
    - `encode(self, texts: Iterable[str]) -> list[list[float]]` (line 31) — Embed an iterable of texts using the configured transformer.
    - `_load_model(model_name: str) -> SentenceTransformer` (line 37) — Load and cache the requested sentence transformer model.
- `DummyEmbedder` (line 43) — Deterministic embedder for dry-runs and tests. Inherits from Embedder.
  - Methods:
    - `__init__(self) -> None` (line 46) — Initialise the deterministic embedder for testing.
    - `dimension(self) -> int` (line 51) — Return the fixed dimension used by the dummy embedder.
    - `encode(self, texts: Iterable[str]) -> list[list[float]]` (line 55) — Produce deterministic vectors for the provided texts.

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, functools, logging, sentence_transformers

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/lifecycle.py

**File path**: `gateway/ingest/lifecycle.py`
**Purpose**: Lifecycle reporting helpers for ingestion outputs.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.defaultdict, contextlib.suppress, dataclasses.dataclass, datetime.UTC, datetime.datetime, json, neo4j.Driver, pathlib.Path, time, typing.Any; Internal – gateway.graph.GraphService, gateway.graph.get_graph_service, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.LIFECYCLE_HISTORY_SNAPSHOTS, gateway.observability.metrics.LIFECYCLE_ISOLATED_NODES_TOTAL, gateway.observability.metrics.LIFECYCLE_LAST_RUN_STATUS, gateway.observability.metrics.LIFECYCLE_LAST_RUN_TIMESTAMP, gateway.observability.metrics.LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL, gateway.observability.metrics.LIFECYCLE_REMOVED_ARTIFACTS_TOTAL, gateway.observability.metrics.LIFECYCLE_STALE_DOCS_TOTAL
**Related modules**: gateway.graph.GraphService, gateway.graph.get_graph_service, gateway.ingest.pipeline.IngestionResult, gateway.observability.metrics.LIFECYCLE_HISTORY_SNAPSHOTS, gateway.observability.metrics.LIFECYCLE_ISOLATED_NODES_TOTAL, gateway.observability.metrics.LIFECYCLE_LAST_RUN_STATUS, gateway.observability.metrics.LIFECYCLE_LAST_RUN_TIMESTAMP, gateway.observability.metrics.LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL, gateway.observability.metrics.LIFECYCLE_REMOVED_ARTIFACTS_TOTAL, gateway.observability.metrics.LIFECYCLE_STALE_DOCS_TOTAL

### Classes
- `LifecycleConfig` (line 33) — Configuration values that influence lifecycle report generation. Inherits from object.
  - Attributes: output_path: Path, stale_days: int, graph_enabled: bool, history_limit: int | None = None
  - Methods: None

### Functions
- `write_lifecycle_report(result: IngestionResult, config: LifecycleConfig, graph_service: GraphService | None) -> None` (line 42) — Persist lifecycle insights derived from the most recent ingest run.
- `build_graph_service(driver: Driver, database: str, cache_ttl: float) -> GraphService` (line 107) — Construct a graph service with sensible defaults for lifecycle usage.
- `summarize_lifecycle(payload: dict[str, Any]) -> dict[str, Any]` (line 112) — Produce a summarized view of lifecycle data for reporting.
- `_fetch_isolated_nodes(graph_service: GraphService | None) -> dict[str, list[dict[str, Any]]]` (line 129) — Collect isolated graph nodes grouped by label.
- `_find_stale_docs(artifacts: Iterable[dict[str, Any]], stale_days: int, now: float) -> list[dict[str, Any]]` (line 158) — Identify design documents that are older than the stale threshold.
- `_find_missing_tests(artifacts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]` (line 179) — Determine subsystems lacking corresponding tests.
- `_write_history_snapshot(payload: dict[str, Any], reports_dir: Path, history_limit: int) -> list[Path]` (line 202) — Write lifecycle history to disk while enforcing retention.
- `_coerce_float(value: object) -> float | None` (line 221) — Coerce numeric-like values to float when possible.
- `_lifecycle_counts(isolated: dict[str, list[dict[str, Any]]], stale_docs: list[dict[str, Any]], missing_tests: list[dict[str, Any]], removed: list[dict[str, Any]]) -> dict[str, int]` (line 229) — Aggregate lifecycle metrics into counters.

### Constants and Configuration
- SECONDS_PER_DAY = 60 * 60 * 24 (line 29)

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- collections, contextlib, dataclasses, datetime, json, neo4j, pathlib, time, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/ingest/neo4j_writer.py

**File path**: `gateway/ingest/neo4j_writer.py`
**Purpose**: Write ingestion artifacts and chunks into Neo4j.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.abc.Mapping, collections.abc.Sequence, logging, neo4j.Driver; Internal – gateway.ingest.artifacts.Artifact, gateway.ingest.artifacts.ChunkEmbedding
**Related modules**: gateway.ingest.artifacts.Artifact, gateway.ingest.artifacts.ChunkEmbedding

### Classes
- `Neo4jWriter` (line 15) — Persist artifacts and derived data into a Neo4j database. Inherits from object.
  - Methods:
    - `__init__(self, driver: Driver, database: str = 'knowledge') -> None` (line 18) — Initialise the writer with a driver and target database.
    - `ensure_constraints(self) -> None` (line 23) — Create required uniqueness constraints if they do not exist.
    - `sync_artifact(self, artifact: Artifact) -> None` (line 39) — Upsert the artifact node and related subsystem relationships.
    - `sync_chunks(self, chunk_embeddings: Iterable[ChunkEmbedding]) -> None` (line 125) — Upsert chunk nodes and connect them to their owning artifacts.
    - `delete_artifact(self, path: str) -> None` (line 146) — Remove an artifact node and its chunks.

### Functions
- `_artifact_label(artifact: Artifact) -> str` (line 160) — Map artifact types to Neo4j labels.
- `_label_for_type(artifact_type: str) -> str` (line 172) — Return the default label for the given artifact type.
- `_relationship_for_label(label: str) -> str | None` (line 183) — Return the relationship used to link artifacts to subsystems.
- `_clean_string_list(values: object) -> list[str]` (line 192) — No docstring provided.
- `_normalize_subsystem_name(value: str | None) -> str | None` (line 206) — No docstring provided.
- `_extract_dependencies(metadata: Mapping[str, object] | None) -> list[str]` (line 217) — No docstring provided.
- `_subsystem_properties(metadata: Mapping[str, object] | None) -> dict[str, object]` (line 236) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.

### Integration Points
- collections, logging, neo4j

### Code Quality Notes
- 4 public element(s) lack docstrings.

## gateway/ingest/pipeline.py

**File path**: `gateway/ingest/pipeline.py`
**Purpose**: Pipeline orchestrations for ingestion, chunking, and persistence.
**Dependencies**: External – __future__.annotations, collections.abc.Sequence, collections.deque, concurrent.futures.Future, concurrent.futures.ThreadPoolExecutor, dataclasses.dataclass, dataclasses.field, hashlib, json, logging, opentelemetry.trace, opentelemetry.trace.Status, opentelemetry.trace.StatusCode, pathlib.Path, subprocess, time, uuid; Internal – gateway.ingest.artifacts.Chunk, gateway.ingest.artifacts.ChunkEmbedding, gateway.ingest.chunking.Chunker, gateway.ingest.discovery.DiscoveryConfig, gateway.ingest.discovery.discover, gateway.ingest.embedding.DummyEmbedder, gateway.ingest.embedding.Embedder, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.qdrant_writer.QdrantWriter, gateway.observability.metrics.INGEST_ARTIFACTS_TOTAL, gateway.observability.metrics.INGEST_CHUNKS_TOTAL, gateway.observability.metrics.INGEST_DURATION_SECONDS, gateway.observability.metrics.INGEST_LAST_RUN_STATUS, gateway.observability.metrics.INGEST_LAST_RUN_TIMESTAMP, gateway.observability.metrics.INGEST_SKIPS_TOTAL, gateway.observability.metrics.INGEST_STALE_RESOLVED_TOTAL
**Related modules**: gateway.ingest.artifacts.Chunk, gateway.ingest.artifacts.ChunkEmbedding, gateway.ingest.chunking.Chunker, gateway.ingest.discovery.DiscoveryConfig, gateway.ingest.discovery.discover, gateway.ingest.embedding.DummyEmbedder, gateway.ingest.embedding.Embedder, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.qdrant_writer.QdrantWriter, gateway.observability.metrics.INGEST_ARTIFACTS_TOTAL, gateway.observability.metrics.INGEST_CHUNKS_TOTAL, gateway.observability.metrics.INGEST_DURATION_SECONDS, gateway.observability.metrics.INGEST_LAST_RUN_STATUS, gateway.observability.metrics.INGEST_LAST_RUN_TIMESTAMP, gateway.observability.metrics.INGEST_SKIPS_TOTAL, gateway.observability.metrics.INGEST_STALE_RESOLVED_TOTAL

### Classes
- `IngestionConfig` (line 40) — Configuration options controlling ingestion behaviour. Inherits from object.
  - Attributes: repo_root: Path, dry_run: bool = False, chunk_window: int = 1000, chunk_overlap: int = 200, embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2', use_dummy_embeddings: bool = False, environment: str = 'local', include_patterns: tuple[str, ...] = ('docs', 'src', 'tests', '.codacy'), audit_path: Path | None = None, coverage_path: Path | None = None, coverage_history_limit: int = 5, ledger_path: Path | None = None, incremental: bool = True, embed_parallel_workers: int = 2, max_pending_batches: int = 4
  - Methods: None
- `IngestionResult` (line 66) — Summary of outputs emitted by an ingestion run. Inherits from object.
  - Attributes: run_id: str, profile: str, started_at: float, duration_seconds: float, artifact_counts: dict[str, int] = field(default_factory=dict), chunk_count: int = 0, repo_head: str | None = None, success: bool = True, artifacts: list[dict[str, object]] = field(default_factory=list), removed_artifacts: list[dict[str, object]] = field(default_factory=list)
  - Methods: None
- `IngestionPipeline` (line 81) — Execute the ingestion workflow end-to-end. Inherits from object.
  - Methods:
    - `__init__(self, qdrant_writer: QdrantWriter | None, neo4j_writer: Neo4jWriter | None, config: IngestionConfig) -> None` (line 84) — Initialise the pipeline with writer backends and configuration.
    - `run(self) -> IngestionResult` (line 95) — Execute discovery, chunking, embedding, and persistence for a repo.
    - `_build_embedder(self) -> Embedder` (line 324) — No method docstring provided.
    - `_encode_batch(self, embedder: Embedder, chunks: Sequence[Chunk]) -> list[list[float]]` (line 330) — No method docstring provided.
    - `_build_embeddings(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> list[ChunkEmbedding]` (line 333) — No method docstring provided.
    - `_persist_embeddings(self, embeddings: Sequence[ChunkEmbedding]) -> int` (line 339) — No method docstring provided.
    - `_handle_stale_artifacts(self, previous: dict[str, dict[str, object]], current: dict[str, dict[str, object]], profile: str) -> list[dict[str, object]]` (line 348) — No method docstring provided.
    - `_delete_artifact_from_backends(self, path: str) -> str` (line 390) — No method docstring provided.
    - `_load_artifact_ledger(self) -> dict[str, dict[str, object]]` (line 413) — No method docstring provided.
    - `_write_artifact_ledger(self, entries: dict[str, dict[str, object]]) -> None` (line 434) — No method docstring provided.

### Functions
- `_current_repo_head(repo_root: Path) -> str | None` (line 447) — No docstring provided.
- `_coerce_int(value: object) -> int | None` (line 462) — No docstring provided.
- `_coerce_float(value: object) -> float | None` (line 473) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, concurrent, dataclasses, hashlib, json, logging, opentelemetry, pathlib, subprocess, time, uuid

### Code Quality Notes
- 11 public element(s) lack docstrings.

## gateway/ingest/qdrant_writer.py

**File path**: `gateway/ingest/qdrant_writer.py`
**Purpose**: Helpers for writing chunk embeddings into Qdrant collections.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, logging, qdrant_client.QdrantClient, qdrant_client.http.exceptions.UnexpectedResponse, qdrant_client.http.models, time, uuid; Internal – gateway.ingest.artifacts.ChunkEmbedding
**Related modules**: gateway.ingest.artifacts.ChunkEmbedding

### Classes
- `QdrantWriter` (line 19) — Lightweight adapter around the Qdrant client. Inherits from object.
  - Methods:
    - `__init__(self, client: QdrantClient, collection_name: str) -> None` (line 22) — Initialise the writer with a target collection.
    - `ensure_collection(self, vector_size: int, retries: int = 3, retry_backoff: float = 0.5) -> None` (line 27) — Ensure the collection exists without destructive recreation.  The method prefers non-destructive `create_collection` calls. Transient errors trigger bounded retries with exponential backoff; conflicts are treated as success. Destructive resets are exposed separately via :meth:`reset_collection` to make data loss an explicit operator choice.
    - `reset_collection(self, vector_size: int) -> None` (line 79) — Destructively recreate the collection, wiping all stored vectors.
    - `upsert_chunks(self, chunks: Iterable[ChunkEmbedding]) -> None` (line 93) — Upsert chunk embeddings into the configured collection.
    - `delete_artifact(self, artifact_path: str) -> None` (line 111) — Delete all points belonging to an artifact path.
    - `_collection_exists(self) -> bool` (line 128) — Return True when the collection already exists in Qdrant.
    - `_create_collection(self, vector_size: int) -> None` (line 149) — No method docstring provided.

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Interacts with Qdrant collections for vector search or persistence.

### Integration Points
- collections, logging, qdrant_client, time, uuid

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/ingest/service.py

**File path**: `gateway/ingest/service.py`
**Purpose**: High-level orchestration routines for running ingestion.
**Dependencies**: External – __future__.annotations, logging, neo4j.GraphDatabase, neo4j.exceptions.Neo4jError, pathlib.Path, qdrant_client.QdrantClient, qdrant_client.http.exceptions.UnexpectedResponse; Internal – gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.config.settings.AppSettings, gateway.ingest.audit.AuditLogger, gateway.ingest.coverage.write_coverage_report, gateway.ingest.lifecycle.LifecycleConfig, gateway.ingest.lifecycle.build_graph_service, gateway.ingest.lifecycle.write_lifecycle_report, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.ingest.pipeline.IngestionResult, gateway.ingest.qdrant_writer.QdrantWriter
**Related modules**: gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.config.settings.AppSettings, gateway.ingest.audit.AuditLogger, gateway.ingest.coverage.write_coverage_report, gateway.ingest.lifecycle.LifecycleConfig, gateway.ingest.lifecycle.build_graph_service, gateway.ingest.lifecycle.write_lifecycle_report, gateway.ingest.neo4j_writer.Neo4jWriter, gateway.ingest.pipeline.IngestionConfig, gateway.ingest.pipeline.IngestionPipeline, gateway.ingest.pipeline.IngestionResult, gateway.ingest.qdrant_writer.QdrantWriter

### Classes
- None

### Functions
- `execute_ingestion(settings: AppSettings, profile: str, repo_override: Path | None = None, dry_run: bool | None = None, use_dummy_embeddings: bool | None = None, incremental: bool | None = None, graph_manager: Neo4jConnectionManager | None = None, qdrant_manager: QdrantConnectionManager | None = None) -> IngestionResult` (line 25) — Run ingestion using shared settings and return result.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Interacts with Qdrant collections for vector search or persistence.

### Integration Points
- logging, neo4j, pathlib, qdrant_client

### Code Quality Notes
- No immediate issues detected from static scan.

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
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- standard library only

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/lifecycle/cli.py

**File path**: `gateway/lifecycle/cli.py`
**Purpose**: Command-line utilities for inspecting lifecycle health reports.
**Dependencies**: External – __future__.annotations, argparse, collections.abc.Iterable, collections.abc.Mapping, datetime.datetime, json, pathlib.Path, rich.console.Console, rich.table.Table; Internal – gateway.config.settings.get_settings, gateway.observability.configure_logging, gateway.observability.configure_tracing
**Related modules**: gateway.config.settings.get_settings, gateway.observability.configure_logging, gateway.observability.configure_tracing

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` (line 20) — Create the CLI argument parser shared across entrypoints.
- `render_table(payload: dict[str, object]) -> None` (line 36) — Pretty-print the lifecycle report payload using Rich tables.
- `_render_isolated_nodes(value: object) -> None` (line 47) — Render the isolated node section when data is present.
- `_render_stale_docs(value: object) -> None` (line 63) — Render the stale documentation summary rows.
- `_render_missing_tests(value: object) -> None` (line 84) — Render subsystems missing tests in a tabular format.
- `_format_timestamp(value: object) -> str` (line 105) — Convert a timestamp-like input into an ISO formatted string.
- `main(argv: list[str] | None = None) -> None` (line 112) — CLI entry point for lifecycle reporting.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- argparse, collections, datetime, json, pathlib, rich

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/mcp/__init__.py

**File path**: `gateway/mcp/__init__.py`
**Purpose**: Model Context Protocol server integration for the knowledge gateway.
**Dependencies**: External – config.MCPSettings, server.build_server; Internal – None
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
- config, server

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/mcp/backup.py

**File path**: `gateway/mcp/backup.py`
**Purpose**: Backup helpers for the MCP server.
**Dependencies**: External – __future__.annotations, asyncio, config.MCPSettings, pathlib.Path, typing.Any; Internal – gateway.backup.service.run_backup
**Related modules**: gateway.backup.service.run_backup

### Classes
- None

### Functions
- `async trigger_backup(settings: MCPSettings) -> dict[str, Any]` (line 14) — Invoke the km-backup helper and return the resulting archive metadata.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- asyncio, config, pathlib, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/mcp/cli.py

**File path**: `gateway/mcp/cli.py`
**Purpose**: Command-line entry point for the MCP server.
**Dependencies**: External – __future__.annotations, argparse, collections.abc.Sequence, config.MCPSettings, logging, server.build_server, sys; Internal – gateway.get_version
**Related modules**: gateway.get_version

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` (line 18) — Return the CLI parser for launching the MCP server.
- `main(argv: Sequence[str] | None = None) -> int` (line 55) — Entry point for the MCP server management CLI.

### Constants and Configuration
- _TRANSPORT_CHOICES = ['stdio', 'http', 'sse', 'streamable-http'] (line 15)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- argparse, collections, config, logging, server, sys

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/mcp/client.py

**File path**: `gateway/mcp/client.py`
**Purpose**: HTTP client for interacting with the gateway API.
**Dependencies**: External – __future__.annotations, collections.abc.Mapping, config.MCPSettings, exceptions.GatewayRequestError, exceptions.MissingTokenError, httpx, json, logging, types.TracebackType, typing.Any, urllib.parse.quote; Internal – None
**Related modules**: None

### Classes
- `GatewayClient` (line 20) — Thin async wrapper over the gateway REST API. Inherits from object.
  - Methods:
    - `__init__(self, settings: MCPSettings) -> None` (line 23) — No method docstring provided.
    - `async __aenter__(self) -> GatewayClient` (line 27) — Open the underlying HTTP client.
    - `async __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 39) — No method docstring provided.
    - `settings(self) -> MCPSettings` (line 50) — Return the settings used to configure the client.
    - `async search(self, payload: dict[str, Any]) -> dict[str, Any]` (line 54) — Perform a search request against the gateway.
    - `async graph_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 64) — Fetch a graph node by ID.
    - `async graph_subsystem(self, name: str, depth: int, include_artifacts: bool, cursor: str | None, limit: int) -> dict[str, Any]` (line 74) — Retrieve subsystem details and related artifacts.
    - `async graph_search(self, term: str, limit: int) -> dict[str, Any]` (line 99) — Perform a graph search by term.
    - `async coverage_summary(self) -> dict[str, Any]` (line 109) — Fetch the coverage summary endpoint as a dict.
    - `async lifecycle_report(self) -> dict[str, Any]` (line 118) — Fetch the lifecycle report payload.
    - `async audit_history(self, limit: int = 10) -> list[dict[str, Any]]` (line 127) — Return recent audit history entries.
    - `async _request(self, method: str, path: str, json_payload: Mapping[str, object] | list[object] | None = None, params: Mapping[str, _ParamValue] | None = None, require_admin: bool = False, require_reader: bool = False) -> object` (line 139) — Issue an HTTP request with token management and error handling.

### Functions
- `_extract_error_detail(response: httpx.Response) -> str` (line 192) — Extract a human-readable error detail from an HTTP response.
- `_safe_json(response: httpx.Response) -> Mapping[str, object] | list[object] | None` (line 205) — Safely decode a JSON response, returning ``None`` on failure.
- `_quote_segment(value: str) -> str` (line 218) — No docstring provided.
- `_expect_dict(data: object, operation: str) -> dict[str, Any]` (line 225) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, config, exceptions, httpx, json, logging, types, typing, urllib

### Code Quality Notes
- 4 public element(s) lack docstrings.

## gateway/mcp/config.py

**File path**: `gateway/mcp/config.py`
**Purpose**: Configuration for the MCP adapter.
**Dependencies**: External – __future__.annotations, pathlib.Path, pydantic.Field, pydantic_settings.BaseSettings, typing.Literal; Internal – None
**Related modules**: None

### Classes
- `MCPSettings` (line 12) — Settings controlling the MCP server runtime. Inherits from BaseSettings.
  - Attributes: gateway_url: str = Field('http://localhost:8000', alias='KM_GATEWAY_URL', description='Base URL of the gateway API'), reader_token: str | None = Field(default=None, alias='KM_READER_TOKEN', description='Bearer token for reader-scoped operations'), admin_token: str | None = Field(default=None, alias='KM_ADMIN_TOKEN', description='Bearer token for maintainer-scoped operations'), request_timeout_seconds: float = Field(default=30.0, alias='KM_MCP_TIMEOUT_SECONDS', description='HTTP request timeout when talking to the gateway'), verify_ssl: bool = Field(default=True, alias='KM_MCP_VERIFY_SSL', description='Whether to verify TLS certificates when contacting the gateway'), state_path: Path = Field(default=Path('/opt/knowledge/var'), alias='KM_STATE_PATH', description='Path containing gateway state files (audit logs, backups, feedback)'), content_root: Path = Field(default=Path('/workspace/repo'), alias='KM_CONTENT_ROOT', description='Root directory where MCP upload/storetext helpers write content'), content_docs_subdir: Path = Field(default=Path('docs'), alias='KM_CONTENT_DOCS_SUBDIR', description='Default subdirectory under the content root for text documents'), upload_default_overwrite: bool = Field(default=False, alias='KM_UPLOAD_DEFAULT_OVERWRITE', description='Allow MCP uploads to overwrite existing files by default'), upload_default_ingest: bool = Field(default=False, alias='KM_UPLOAD_DEFAULT_INGEST', description='Trigger an ingest run immediately after MCP uploads by default'), ingest_profile_default: str = Field(default='manual', alias='KM_MCP_DEFAULT_INGEST_PROFILE', description='Default profile label applied to manual ingest runs'), ingest_repo_override: Path | None = Field(default=None, alias='KM_MCP_REPO_ROOT', description='Optional repository root override for MCP-triggered ingest runs'), backup_script: Path | None = Field(default=None, alias='KM_MCP_BACKUP_SCRIPT', description='Override path to the km-backup helper script'), log_requests: bool = Field(default=False, alias='KM_MCP_LOG_REQUESTS', description='Enable verbose logging for outbound HTTP requests'), transport: Literal['stdio', 'http', 'sse', 'streamable-http'] = Field(default='stdio', alias='KM_MCP_TRANSPORT', description='Default transport used when launching the MCP server'), model_config = {'env_file': None, 'case_sensitive': False, 'extra': 'ignore'}
  - Methods: None

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- pathlib, pydantic, pydantic_settings, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/mcp/exceptions.py

**File path**: `gateway/mcp/exceptions.py`
**Purpose**: Custom exceptions for the MCP adapter.
**Dependencies**: External – __future__.annotations; Internal – gateway.backup.exceptions.BackupExecutionError
**Related modules**: gateway.backup.exceptions.BackupExecutionError

### Classes
- `MCPAdapterError` (line 8) — Base error raised by the MCP bridge. Inherits from Exception.
  - Methods: None
- `GatewayRequestError` (line 12) — Raised when the gateway API returns an error response. Inherits from MCPAdapterError.
  - Methods:
    - `__init__(self, status_code: int, detail: str, payload: object | None = None) -> None` (line 15) — No method docstring provided.
- `MissingTokenError` (line 23) — Raised when a privileged operation lacks an authentication token. Inherits from MCPAdapterError.
  - Methods:
    - `__init__(self, scope: str) -> None` (line 26) — No method docstring provided.
- `BackupExecutionError` (line 31) — Raised when the backup helper fails to produce an archive. Inherits from _BackupExecutionError, MCPAdapterError.
  - Methods: None

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- standard library only

### Code Quality Notes
- 2 public element(s) lack docstrings.

## gateway/mcp/feedback.py

**File path**: `gateway/mcp/feedback.py`
**Purpose**: Feedback logging utilities used by MCP tools.
**Dependencies**: External – __future__.annotations, asyncio, collections.abc.Mapping, config.MCPSettings, datetime.UTC, datetime.datetime, json, pathlib.Path, typing.Any; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- `async record_feedback(settings: MCPSettings, request_id: str, chunk_id: str, vote: float | None, note: str | None, context: Mapping[str, Any] | None) -> dict[str, Any]` (line 15) — Append a manual feedback entry to the state directory.
- `_append_line(path: Path, line: str) -> None` (line 43) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- asyncio, collections, config, datetime, json, pathlib, typing

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/mcp/ingest.py

**File path**: `gateway/mcp/ingest.py`
**Purpose**: Helpers for managing ingestion workflows via MCP.
**Dependencies**: External – __future__.annotations, asyncio, config.MCPSettings, dataclasses.asdict, typing.Any; Internal – gateway.config.settings.get_settings, gateway.ingest.service.execute_ingestion
**Related modules**: gateway.config.settings.get_settings, gateway.ingest.service.execute_ingestion

### Classes
- None

### Functions
- `async trigger_ingest(settings: MCPSettings, profile: str, dry_run: bool, use_dummy_embeddings: bool | None) -> dict[str, Any]` (line 15) — Execute an ingestion run in a worker thread and return a serialisable summary.
- `async latest_ingest_status(history: list[dict[str, Any]], profile: str | None) -> dict[str, Any] | None` (line 39) — Return the newest ingest record optionally filtered by profile.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- asyncio, config, dataclasses, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/mcp/server.py

**File path**: `gateway/mcp/server.py`
**Purpose**: FastMCP server exposing the knowledge gateway.
**Dependencies**: External – __future__.annotations, backup.trigger_backup, client.GatewayClient, collections.abc.AsyncIterator, collections.abc.Callable, config.MCPSettings, contextlib.AbstractAsyncContextManager, contextlib.asynccontextmanager, datetime.UTC, datetime.datetime, exceptions.GatewayRequestError, fastmcp.Context, fastmcp.FastMCP, feedback.record_feedback, functools.lru_cache, ingest.latest_ingest_status, ingest.trigger_ingest, json, pathlib.Path, storetext.handle_storetext, textwrap.dedent, time.perf_counter, typing.Any, typing.cast, upload.handle_upload; Internal – gateway.get_version, gateway.observability.metrics.MCP_FAILURES_TOTAL, gateway.observability.metrics.MCP_REQUESTS_TOTAL, gateway.observability.metrics.MCP_REQUEST_SECONDS, gateway.observability.metrics.MCP_STORETEXT_TOTAL, gateway.observability.metrics.MCP_UPLOAD_TOTAL
**Related modules**: gateway.get_version, gateway.observability.metrics.MCP_FAILURES_TOTAL, gateway.observability.metrics.MCP_REQUESTS_TOTAL, gateway.observability.metrics.MCP_REQUEST_SECONDS, gateway.observability.metrics.MCP_STORETEXT_TOTAL, gateway.observability.metrics.MCP_UPLOAD_TOTAL

### Classes
- `MCPServerState` (line 160) — Holds shared state for the MCP server lifespan. Inherits from object.
  - Methods:
    - `__init__(self, settings: MCPSettings) -> None` (line 163) — No method docstring provided.
    - `require_client(self) -> GatewayClient` (line 167) — No method docstring provided.
    - `lifespan(self) -> LifespanCallable` (line 172) — No method docstring provided.

### Functions
- `build_server(settings: MCPSettings | None = None) -> FastMCP` (line 185) — Create a FastMCP server wired to the gateway API.
- `async _report_info(context: Context | None, message: str) -> None` (line 564) — No docstring provided.
- `async _report_error(context: Context | None, message: str) -> None` (line 569) — No docstring provided.
- `_record_success(tool: str, start: float) -> None` (line 574) — No docstring provided.
- `_record_failure(tool: str, exc: Exception, start: float) -> None` (line 580) — No docstring provided.
- `_clamp(value: int, minimum: int, maximum: int) -> int` (line 587) — No docstring provided.
- `_normalise_filters(payload: dict[str, Any]) -> dict[str, Any]` (line 591) — No docstring provided.
- `_resolve_usage(tool: str | None) -> dict[str, Any]` (line 610) — No docstring provided.
- `_ensure_maintainer_scope(settings: MCPSettings) -> None` (line 623) — No docstring provided.
- `_append_audit_entry(settings: MCPSettings, tool: str, payload: dict[str, Any]) -> None` (line 629) — No docstring provided.
- `_load_help_document() -> str` (line 647) — No docstring provided.
- `_initialise_metric_labels() -> None` (line 660) — No docstring provided.

### Constants and Configuration
- TOOL_USAGE = {'km-search': {'description': 'Hybrid search across the knowledge base with optional filters and graph context', 'details': dedent('\n            Required: `query` text. Optional: `limit` (default 10, max 25), `include_graph`, structured `filters`, `sort_by_vector`.\n            Example: `/sys mcp run duskmantle km-search --query "ingest pipeline" --limit 5`.\n            Returns scored chunks with metadata and optional graph enrichments.\n            ').strip()}, 'km-graph-node': {'description': 'Fetch a graph node by ID and inspect incoming/outgoing relationships', 'details': dedent('\n            Required: `node_id` such as `DesignDoc:docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md`.\n            Optional: `relationships` (`outgoing`, `incoming`, `all`, `none`) and `limit` (default 50, max 200).\n            Example: `/sys mcp run duskmantle km-graph-node --node-id "Code:gateway/mcp/server.py"`.\n            ').strip()}, 'km-graph-subsystem': {'description': 'Review a subsystem, related artifacts, and connected subsystems', 'details': dedent('\n            Required: `name` of the subsystem.\n            Optional: `depth` (default 1, max 5), `include_artifacts`, pagination `cursor`, `limit` (default 25, max 100).\n            Example: `/sys mcp run duskmantle km-graph-subsystem --name Kasmina --depth 2`.\n            ').strip()}, 'km-graph-search': {'description': 'Search graph entities (artifacts, subsystems, teams) by term', 'details': dedent('\n            Required: `term` to match against graph nodes.\n            Optional: `limit` (default 20, max 50).\n            Example: `/sys mcp run duskmantle km-graph-search --term coverage`.\n            ').strip()}, 'km-coverage-summary': {'description': 'Summarise ingestion coverage (artifact and chunk counts, freshness)', 'details': dedent('\n            No parameters. Returns the same payload as `/coverage` including summary counts and stale thresholds.\n            Example: `/sys mcp run duskmantle km-coverage-summary`.\n            ').strip()}, 'km-lifecycle-report': {'description': 'Summarise isolated nodes, stale docs, and missing tests', 'details': dedent('\n            No parameters. Mirrors the `/lifecycle` endpoint and highlights isolated graph nodes, stale design docs, and subsystems missing tests.\n            Example: `/sys mcp run duskmantle km-lifecycle-report`.\n            ').strip()}, 'km-ingest-status': {'description': 'Show the most recent ingest run (profile, status, timestamps)', 'details': dedent('\n            Optional: `profile` to scope results to a specific ingest profile.\n            Example: `/sys mcp run duskmantle km-ingest-status --profile demo`.\n            Returns `status: ok` with run metadata or `status: not_found` when history is empty.\n            ').strip()}, 'km-ingest-trigger': {'description': 'Kick off a manual ingest run (full rebuild via gateway-ingest)', 'details': dedent('\n            Optional: `profile` (defaults to MCP settings), `dry_run`, `use_dummy_embeddings`.\n            Example: `/sys mcp run duskmantle km-ingest-trigger --profile local --dry-run true`.\n            Requires maintainer token (`KM_ADMIN_TOKEN`).\n            ').strip()}, 'km-backup-trigger': {'description': 'Create a compressed backup of gateway state (Neo4j/Qdrant data)', 'details': dedent('\n            No parameters. Returns archive path and metadata.\n            Example: `/sys mcp run duskmantle km-backup-trigger`.\n            Requires maintainer token; mirrors the `bin/km-backup` helper.\n            ').strip()}, 'km-feedback-submit': {'description': 'Vote on a search result and attach optional notes for training data', 'details': dedent('\n            Required: `request_id` (search request) and `chunk_id` (result identifier).\n            Optional: numeric `vote` (-1.0 to 1.0) and freeform `note`.\n            Example: `/sys mcp run duskmantle km-feedback-submit --request-id req123 --chunk-id chunk456 --vote 1`.\n            Maintainer token required when auth is enforced.\n            ').strip()}, 'km-upload': {'description': 'Copy an existing file into the knowledge workspace and optionally trigger ingest', 'details': dedent('\n            Required: `source_path` (file visible to the MCP host). Optional: `destination` (relative path inside the\n            content root), `overwrite`, `ingest`. Default behaviour stores the file under the configured docs directory.\n            Example: `/sys mcp run duskmantle km-upload --source-path ./notes/design.md --destination docs/uploads/`.\n            Maintainer scope recommended because this writes to the repository volume and may trigger ingestion.\n            ').strip()}, 'km-storetext': {'description': 'Persist raw text as a document within the knowledge workspace', 'details': dedent('\n            Required: `content` (text body). Optional: `title`, `destination`, `subsystem`, `tags`, `metadata` map,\n            `overwrite`, `ingest`. Defaults write markdown into the configured docs directory with YAML front matter\n            derived from the provided metadata.\n            Example: `/sys mcp run duskmantle km-storetext --title "Release Notes" --content "## Summary"`.\n            Maintainer scope recommended because this writes to the repository volume.\n            ').strip()}} (line 29)
- HELP_DOC_PATH = Path(__file__).resolve().parents[2] / 'docs' / 'MCP_INTERFACE_SPEC.md' (line 154)

### Data Flow
- Implements MCP tools or message handlers invoked by MCP clients.

### Integration Points
- backup, client, collections, config, contextlib, datetime, exceptions, fastmcp, feedback, functools, ingest, json, pathlib, storetext, textwrap, time, typing, upload

### Code Quality Notes
- 14 public element(s) lack docstrings.

## gateway/mcp/storetext.py

**File path**: `gateway/mcp/storetext.py`
**Purpose**: Handlers for storing text via MCP.
**Dependencies**: External – __future__.annotations, datetime.datetime, ingest.trigger_ingest, pathlib.Path, typing.Any; Internal – gateway.mcp.config.MCPSettings, gateway.mcp.utils.files.DocumentCopyError, gateway.mcp.utils.files.slugify, gateway.mcp.utils.files.write_text_document
**Related modules**: gateway.mcp.config.MCPSettings, gateway.mcp.utils.files.DocumentCopyError, gateway.mcp.utils.files.slugify, gateway.mcp.utils.files.write_text_document

### Classes
- None

### Functions
- `_build_filename(title: str | None) -> str` (line 15) — No docstring provided.
- `_normalise_destination(destination: str | None, default_dir: Path, filename: str) -> Path` (line 23) — No docstring provided.
- `_compose_content(title: str | None, subsystem: str | None, tags: list[str] | None, metadata: dict[str, Any] | None, body: str) -> str` (line 32) — No docstring provided.
- `async handle_storetext(settings: MCPSettings, content: str, title: str | None, destination: str | None, subsystem: str | None, tags: list[str] | None, metadata: dict[str, Any] | None, overwrite: bool, ingest: bool) -> dict[str, Any]` (line 69) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- datetime, ingest, pathlib, typing

### Code Quality Notes
- 4 public element(s) lack docstrings.

## gateway/mcp/upload.py

**File path**: `gateway/mcp/upload.py`
**Purpose**: Handlers for MCP file uploads.
**Dependencies**: External – __future__.annotations, ingest.trigger_ingest, pathlib.Path, typing.Any; Internal – gateway.mcp.config.MCPSettings, gateway.mcp.utils.files.DocumentCopyError, gateway.mcp.utils.files.copy_into_root
**Related modules**: gateway.mcp.config.MCPSettings, gateway.mcp.utils.files.DocumentCopyError, gateway.mcp.utils.files.copy_into_root

### Classes
- None

### Functions
- `async handle_upload(settings: MCPSettings, source_path: str, destination: str | None, overwrite: bool, ingest: bool) -> dict[str, Any]` (line 14) — Copy ``source_path`` into the configured content root and optionally trigger ingest.
- `_resolve_destination(destination: str | None, default_dir: Path, filename: str) -> Path` (line 68) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- ingest, pathlib, typing

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/mcp/utils/__init__.py

**File path**: `gateway/mcp/utils/__init__.py`
**Purpose**: Module gateway/mcp/utils/__init__.py lacks docstring; review source for intent.
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

## gateway/mcp/utils/files.py

**File path**: `gateway/mcp/utils/files.py`
**Purpose**: Shared helpers for MCP content management.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, dataclasses.dataclass, os, pathlib.Path, re, shutil, unicodedata; Internal – None
**Related modules**: None

### Classes
- `DocumentCopyResult` (line 17) — Result of an attempted document copy. Inherits from object.
  - Attributes: source: Path, destination: Path, copied: bool, overwritten: bool = False, reason: str | None = None
  - Methods: None
- `DocumentCopyError` (line 27) — Raised when a copy operation fails fatally. Inherits from Exception.
  - Methods: None

### Functions
- `slugify(value: str, fallback: str = 'document') -> str` (line 34) — Create a filesystem-friendly slug.
- `is_supported_document(path: Path) -> bool` (line 43) — Return ``True`` if the path has a supported document extension.
- `_assert_within_root(root: Path, candidate: Path) -> None` (line 49) — Ensure ``candidate`` is within ``root`` to prevent path traversal.
- `sweep_documents(root: Path, target: Path, dry_run: bool = False, overwrite: bool = False) -> Iterable[DocumentCopyResult]` (line 64) — Copy supported documents under ``root`` into ``target``.
- `copy_into_root(source: Path, root: Path, destination: Path | None = None, overwrite: bool = False) -> DocumentCopyResult` (line 145) — Copy ``source`` into ``root``.
- `write_text_document(content: str, root: Path, relative_path: Path, overwrite: bool = False, encoding: str = 'utf-8') -> Path` (line 176) — Write ``content`` to ``root / relative_path`` ensuring safety.

### Constants and Configuration
- SUPPORTED_EXTENSIONS = {'.md', '.docx', '.txt', '.doc', '.pdf'} (line 13)
- _SLUG_REGEX = re.compile('[^a-z0-9]+') (line 31)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, dataclasses, os, pathlib, re, shutil, unicodedata

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/observability/__init__.py

**File path**: `gateway/observability/__init__.py`
**Purpose**: Observability utilities (metrics, logging, tracing).
**Dependencies**: External – logging.configure_logging, metrics.BACKUP_LAST_STATUS, metrics.BACKUP_LAST_SUCCESS_TIMESTAMP, metrics.BACKUP_RUNS_TOTAL, metrics.COVERAGE_LAST_RUN_STATUS, metrics.COVERAGE_LAST_RUN_TIMESTAMP, metrics.COVERAGE_MISSING_ARTIFACTS, metrics.GRAPH_DEPENDENCY_LAST_SUCCESS, metrics.GRAPH_DEPENDENCY_STATUS, metrics.GRAPH_MIGRATION_LAST_STATUS, metrics.GRAPH_MIGRATION_LAST_TIMESTAMP, metrics.INGEST_ARTIFACTS_TOTAL, metrics.INGEST_CHUNKS_TOTAL, metrics.INGEST_DURATION_SECONDS, metrics.INGEST_LAST_RUN_STATUS, metrics.INGEST_LAST_RUN_TIMESTAMP, metrics.LIFECYCLE_HISTORY_SNAPSHOTS, metrics.LIFECYCLE_ISOLATED_NODES_TOTAL, metrics.LIFECYCLE_LAST_RUN_STATUS, metrics.LIFECYCLE_LAST_RUN_TIMESTAMP, metrics.LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL, metrics.LIFECYCLE_REMOVED_ARTIFACTS_TOTAL, metrics.LIFECYCLE_STALE_DOCS_TOTAL, metrics.QDRANT_DEPENDENCY_LAST_SUCCESS, metrics.QDRANT_DEPENDENCY_STATUS, metrics.SEARCH_GRAPH_CACHE_EVENTS, metrics.SEARCH_GRAPH_LOOKUP_SECONDS, metrics.SEARCH_REQUESTS_TOTAL, metrics.SEARCH_SCORE_DELTA, metrics.UI_EVENTS_TOTAL, metrics.UI_REQUESTS_TOTAL, tracing.configure_tracing; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Interacts with Qdrant collections for vector search or persistence.

### Integration Points
- logging, metrics, tracing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/observability/logging.py

**File path**: `gateway/observability/logging.py`
**Purpose**: Structured logging configuration for the gateway.
**Dependencies**: External – __future__.annotations, logging, pythonjsonlogger.json, sys, typing.Any; Internal – None
**Related modules**: None

### Classes
- `IngestAwareFormatter` (line 14) — JSON formatter that enforces consistent keys. Inherits from json.JsonFormatter.
  - Methods:
    - `add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None` (line 17) — No method docstring provided.

### Functions
- `configure_logging() -> None` (line 29) — Configure root logging with a JSON formatter once per process.

### Constants and Configuration
- _LOG_CONFIGURED = False (line 11)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- logging, pythonjsonlogger, sys, typing

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/observability/metrics.py

**File path**: `gateway/observability/metrics.py`
**Purpose**: Prometheus metric definitions for the knowledge gateway.
**Dependencies**: External – __future__.annotations, prometheus_client.Counter, prometheus_client.Gauge, prometheus_client.Histogram; Internal – None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants and Configuration
- BACKUP_RUNS_TOTAL = Counter('km_backup_runs_total', 'Backup job outcomes partitioned by result', labelnames=['result']) (line 7)
- BACKUP_LAST_STATUS = Gauge('km_backup_last_status', 'Last backup status (1=success,0=failure)') (line 13)
- BACKUP_LAST_SUCCESS_TIMESTAMP = Gauge('km_backup_last_success_timestamp', 'Unix timestamp of the last successful backup run') (line 18)
- BACKUP_RETENTION_DELETES_TOTAL = Counter('km_backup_retention_deletes_total', 'Number of backup archives removed by retention pruning') (line 23)
- GRAPH_DEPENDENCY_STATUS = Gauge('km_graph_dependency_status', 'Neo4j connectivity status (1=healthy,0=unavailable)') (line 28)
- GRAPH_DEPENDENCY_LAST_SUCCESS = Gauge('km_graph_dependency_last_success_timestamp', 'Unix timestamp of the last successful Neo4j heartbeat') (line 33)
- QDRANT_DEPENDENCY_STATUS = Gauge('km_qdrant_dependency_status', 'Qdrant connectivity status (1=healthy,0=unavailable)') (line 38)
- QDRANT_DEPENDENCY_LAST_SUCCESS = Gauge('km_qdrant_dependency_last_success_timestamp', 'Unix timestamp of the last successful Qdrant heartbeat') (line 43)
- INGEST_DURATION_SECONDS = Histogram('km_ingest_duration_seconds', 'Duration of ingestion runs', labelnames=['profile', 'status']) (line 48)
- INGEST_ARTIFACTS_TOTAL = Counter('km_ingest_artifacts_total', 'Number of artifacts processed', labelnames=['profile', 'artifact_type']) (line 54)
- INGEST_CHUNKS_TOTAL = Counter('km_ingest_chunks_total', 'Number of chunks generated', labelnames=['profile']) (line 60)
- INGEST_LAST_RUN_STATUS = Gauge('km_ingest_last_run_status', 'Last ingestion status (1=success,0=failure)', labelnames=['profile']) (line 66)
- INGEST_LAST_RUN_TIMESTAMP = Gauge('km_ingest_last_run_timestamp', 'Unix timestamp of last ingestion run', labelnames=['profile']) (line 72)
- COVERAGE_LAST_RUN_STATUS = Gauge('km_coverage_last_run_status', 'Last coverage report generation status (1=success,0=failure)', labelnames=['profile']) (line 78)
- COVERAGE_LAST_RUN_TIMESTAMP = Gauge('km_coverage_last_run_timestamp', 'Unix timestamp of last coverage report', labelnames=['profile']) (line 84)
- COVERAGE_MISSING_ARTIFACTS = Gauge('km_coverage_missing_artifacts_total', 'Number of artifacts without chunks discovered in last coverage report', labelnames=['profile']) (line 90)
- COVERAGE_STALE_ARTIFACTS = Gauge('km_coverage_stale_artifacts_total', 'Number of stale or removed artifacts recorded in last coverage report', labelnames=['profile']) (line 96)
- INGEST_STALE_RESOLVED_TOTAL = Counter('km_ingest_stale_resolved_total', 'Count of stale artifacts removed from backends during ingestion', labelnames=['profile']) (line 103)
- INGEST_SKIPS_TOTAL = Counter('km_ingest_skips_total', 'Ingestion runs skipped partitioned by reason', labelnames=['reason']) (line 109)
- SEARCH_REQUESTS_TOTAL = Counter('km_search_requests_total', 'Search API requests partitioned by outcome', labelnames=['status']) (line 115)
- SEARCH_GRAPH_CACHE_EVENTS = Counter('km_search_graph_cache_events_total', 'Graph context cache events during search', labelnames=['status']) (line 121)
- SEARCH_GRAPH_LOOKUP_SECONDS = Histogram('km_search_graph_lookup_seconds', 'Latency of graph lookups for search enrichment') (line 127)
- SEARCH_SCORE_DELTA = Histogram('km_search_adjusted_minus_vector', 'Distribution of adjusted minus vector scores') (line 132)
- GRAPH_CYPHER_DENIED_TOTAL = Counter('km_graph_cypher_denied_total', 'Maintainer Cypher requests blocked by read-only safeguards', labelnames=['reason']) (line 137)
- GRAPH_MIGRATION_LAST_STATUS = Gauge('km_graph_migration_last_status', 'Graph migration result (1=success, 0=failure, -1=skipped)') (line 143)
- GRAPH_MIGRATION_LAST_TIMESTAMP = Gauge('km_graph_migration_last_timestamp', 'Unix timestamp of the last graph migration attempt') (line 148)
- SCHEDULER_RUNS_TOTAL = Counter('km_scheduler_runs_total', 'Scheduled ingestion job outcomes partitioned by result', labelnames=['result']) (line 153)
- SCHEDULER_LAST_SUCCESS_TIMESTAMP = Gauge('km_scheduler_last_success_timestamp', 'Unix timestamp of the last successful scheduled ingestion run') (line 159)
- COVERAGE_HISTORY_SNAPSHOTS = Gauge('km_coverage_history_snapshots', 'Number of retained coverage history snapshots', labelnames=['profile']) (line 164)
- WATCH_RUNS_TOTAL = Counter('km_watch_runs_total', 'Watcher outcomes partitioned by result', labelnames=['result']) (line 170)
- LIFECYCLE_LAST_RUN_STATUS = Gauge('km_lifecycle_last_run_status', 'Lifecycle report generation status (1=success,0=failure)', labelnames=['profile']) (line 177)
- LIFECYCLE_LAST_RUN_TIMESTAMP = Gauge('km_lifecycle_last_run_timestamp', 'Unix timestamp of the last lifecycle report', labelnames=['profile']) (line 183)
- LIFECYCLE_STALE_DOCS_TOTAL = Gauge('km_lifecycle_stale_docs_total', 'Number of stale design docs in the latest lifecycle report', labelnames=['profile']) (line 189)
- LIFECYCLE_ISOLATED_NODES_TOTAL = Gauge('km_lifecycle_isolated_nodes_total', 'Number of isolated graph nodes recorded in the latest lifecycle report', labelnames=['profile']) (line 195)
- LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL = Gauge('km_lifecycle_missing_test_subsystems_total', 'Number of subsystems missing tests in the latest lifecycle report', labelnames=['profile']) (line 201)
- LIFECYCLE_REMOVED_ARTIFACTS_TOTAL = Gauge('km_lifecycle_removed_artifacts_total', 'Number of recently removed artifacts recorded in the latest lifecycle report', labelnames=['profile']) (line 207)
- LIFECYCLE_HISTORY_SNAPSHOTS = Gauge('km_lifecycle_history_snapshots', 'Number of retained lifecycle history snapshots', labelnames=['profile']) (line 213)
- MCP_REQUESTS_TOTAL = Counter('km_mcp_requests_total', 'MCP tool invocations partitioned by result', labelnames=['tool', 'result']) (line 219)
- MCP_REQUEST_SECONDS = Histogram('km_mcp_request_seconds', 'Latency of MCP tool handlers', labelnames=['tool']) (line 225)
- MCP_FAILURES_TOTAL = Counter('km_mcp_failures_total', 'MCP tool failures partitioned by error type', labelnames=['tool', 'error']) (line 231)
- MCP_UPLOAD_TOTAL = Counter('km_mcp_upload_total', 'MCP upload tool invocations partitioned by result', labelnames=['result']) (line 237)
- MCP_STORETEXT_TOTAL = Counter('km_mcp_storetext_total', 'MCP storetext tool invocations partitioned by result', labelnames=['result']) (line 243)
- UI_REQUESTS_TOTAL = Counter('km_ui_requests_total', 'Embedded UI visits partitioned by view', labelnames=['view']) (line 250)
- UI_EVENTS_TOTAL = Counter('km_ui_events_total', 'Embedded UI events partitioned by event label', labelnames=['event']) (line 257)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- prometheus_client

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/observability/tracing.py

**File path**: `gateway/observability/tracing.py`
**Purpose**: Tracing helpers for wiring OpenTelemetry exporters.
**Dependencies**: External – __future__.annotations, fastapi.FastAPI, opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter, opentelemetry.instrumentation.fastapi.FastAPIInstrumentor, opentelemetry.instrumentation.requests.RequestsInstrumentor, opentelemetry.sdk.resources.Resource, opentelemetry.sdk.trace.TracerProvider, opentelemetry.sdk.trace.export.BatchSpanProcessor, opentelemetry.sdk.trace.export.ConsoleSpanExporter, opentelemetry.sdk.trace.export.SimpleSpanProcessor, opentelemetry.sdk.trace.export.SpanExporter, opentelemetry.sdk.trace.sampling.ParentBased, opentelemetry.sdk.trace.sampling.TraceIdRatioBased, opentelemetry.trace; Internal – gateway.config.settings.AppSettings
**Related modules**: gateway.config.settings.AppSettings

### Classes
- None

### Functions
- `configure_tracing(app: FastAPI | None, settings: AppSettings) -> None` (line 20) — Configure OpenTelemetry tracing based on runtime settings.
- `_select_exporter(settings: AppSettings) -> SpanExporter` (line 49) — Choose the span exporter based on settings.
- `_parse_headers(header_string: str | None) -> dict[str, str] | None` (line 60) — Parse comma-separated OTLP header strings into a dict.
- `reset_tracing_for_tests() -> None` (line 77) — Reset module-level state so tests can reconfigure tracing cleanly.

### Constants and Configuration
- _TRACING_CONFIGURED = False (line 17)

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.

### Integration Points
- fastapi, opentelemetry

### Code Quality Notes
- No immediate issues detected from static scan.

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
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- standard library only

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/recipes/__init__.py

**File path**: `gateway/recipes/__init__.py`
**Purpose**: Utilities for running knowledge recipes.
**Dependencies**: External – executor.RecipeRunResult, executor.RecipeRunner, models.Recipe, models.RecipeStep; Internal – None
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
- executor, models

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/recipes/cli.py

**File path**: `gateway/recipes/cli.py`
**Purpose**: Command-line utilities for inspecting and running MCP recipes.
**Dependencies**: External – __future__.annotations, argparse, asyncio, collections.abc.Callable, executor.GatewayToolExecutor, executor.RecipeExecutionError, executor.RecipeRunner, executor.list_recipes, executor.load_recipe, json, logging, models.Recipe, pathlib.Path, pydantic.ValidationError, rich.console.Console, rich.table.Table, typing.Any; Internal – gateway.mcp.config.MCPSettings
**Related modules**: gateway.mcp.config.MCPSettings

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` (line 28) — Construct the top-level argument parser for the CLI.
- `load_recipe_by_name(recipes_dir: Path, name: str) -> Recipe` (line 75) — Load a recipe by stem name from the given directory.
- `parse_variables(pairs: list[str]) -> dict[str, str]` (line 83) — Parse ``key=value`` overrides supplied on the command line.
- `command_list(args: argparse.Namespace) -> None` (line 94) — List recipes available in the configured directory.
- `command_show(args: argparse.Namespace) -> None` (line 108) — Print a single recipe definition in JSON form.
- `command_validate(args: argparse.Namespace) -> None` (line 117) — Validate one or all recipes and report the outcome.
- `recipe_executor_factory(settings: MCPSettings) -> Callable[[], GatewayToolExecutor]` (line 143) — Create a factory that instantiates a gateway-backed tool executor.
- `command_run(args: argparse.Namespace, settings: MCPSettings) -> None` (line 148) — Execute a recipe and render the results.
- `_render_run_result(result: dict[str, Any]) -> None` (line 177) — Pretty-print a recipe execution result in tabular form.
- `main(argv: list[str] | None = None) -> None` (line 197) — Entry point for the recipes CLI.

### Constants and Configuration
- DEFAULT_RECIPES_DIR = Path(__file__).resolve().parents[2] / 'recipes' (line 25)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- argparse, asyncio, collections, executor, json, logging, models, pathlib, pydantic, rich, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/recipes/executor.py

**File path**: `gateway/recipes/executor.py`
**Purpose**: Recipe execution layer for automating MCP-driven workflows.
**Dependencies**: External – __future__.annotations, asyncio, collections.abc.AsyncIterator, collections.abc.Callable, collections.abc.Mapping, contextlib.asynccontextmanager, dataclasses.dataclass, dataclasses.field, json, logging, models.Capture, models.Condition, models.Recipe, models.WaitConfig, pathlib.Path, re, time, types.TracebackType, yaml; Internal – gateway.mcp.backup.trigger_backup, gateway.mcp.client.GatewayClient, gateway.mcp.config.MCPSettings, gateway.mcp.exceptions.GatewayRequestError, gateway.mcp.ingest.latest_ingest_status, gateway.mcp.ingest.trigger_ingest
**Related modules**: gateway.mcp.backup.trigger_backup, gateway.mcp.client.GatewayClient, gateway.mcp.config.MCPSettings, gateway.mcp.exceptions.GatewayRequestError, gateway.mcp.ingest.latest_ingest_status, gateway.mcp.ingest.trigger_ingest

### Classes
- `RecipeExecutionError` (line 29) — Raised when a recipe step fails. Inherits from RuntimeError.
  - Methods: None
- `StepResult` (line 34) — Lightweight representation of a single recipe step outcome. Inherits from object.
  - Attributes: step_id: str, status: str, duration_seconds: float, result: object | None = None, message: str | None = None
  - Methods: None
- `RecipeRunResult` (line 45) — Aggregate outcome for a recipe execution, including captured outputs. Inherits from object.
  - Attributes: recipe: Recipe, started_at: float, finished_at: float, success: bool, steps: list[StepResult] = field(default_factory=list), outputs: dict[str, object] = field(default_factory=dict)
  - Methods:
    - `to_dict(self) -> dict[str, object]` (line 55) — Serialise the run result to a JSON-friendly mapping.
- `ToolExecutor` (line 77) — Abstract tool executor interface. Inherits from object.
  - Methods:
    - `async call(self, tool: str, params: dict[str, object]) -> object` (line 80) — Invoke a named tool with the given parameters.
    - `async __aenter__(self) -> ToolExecutor` (line 84) — Allow derived executors to perform async setup.
    - `async __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 88) — Allow derived executors to perform async teardown.
- `GatewayToolExecutor` (line 95) — Execute tools by reusing gateway HTTP/MCP helpers. Inherits from ToolExecutor.
  - Methods:
    - `__init__(self, settings: MCPSettings) -> None` (line 98) — No method docstring provided.
    - `async __aenter__(self) -> GatewayToolExecutor` (line 103) — Open the shared gateway client for tool execution.
    - `async __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None` (line 109) — Close the shared gateway client when execution completes.
    - `async call(self, tool: str, params: dict[str, object]) -> object` (line 116) — Route tool invocations to the appropriate gateway operation.
- `RecipeRunner` (line 284) — Run recipes using the configured MCP settings. Inherits from object.
  - Methods:
    - `__init__(self, settings: MCPSettings, executor_factory: Callable[[], ToolExecutor] | None = None, audit_path: Path | None = None) -> None` (line 287) — No method docstring provided.
    - `make_executor(self) -> ToolExecutor` (line 297) — Instantiate a tool executor using the configured factory.
    - `async run(self, recipe: Recipe, variables: dict[str, object] | None = None, dry_run: bool = False) -> RecipeRunResult` (line 301) — Execute a recipe end-to-end and return the collected results.
    - `async _execute_wait(self, executor: ToolExecutor, context: dict[str, object], wait: WaitConfig) -> object` (line 431) — Repeatedly invoke a wait tool until the condition passes or times out.
    - `_append_audit(self, result: RecipeRunResult, context: dict[str, object]) -> None` (line 454) — Append the recipe outcome to the on-disk audit log.

### Functions
- `_resolve_template(value: object, context: Mapping[str, object]) -> object` (line 186) — No docstring provided.
- `_lookup_expression(expr: str, context: Mapping[str, object]) -> object` (line 206) — No docstring provided.
- `_descend(current: object, part: str) -> object` (line 239) — No docstring provided.
- `_evaluate_condition(result: object, condition: Condition) -> None` (line 266) — No docstring provided.
- `_compute_capture(result: object, capture: Capture) -> object` (line 278) — No docstring provided.
- `async _executor_cm(factory: Callable[[], ToolExecutor]) -> AsyncIterator[ToolExecutor]` (line 481) — Context manager that yields a tool executor from the provided factory.
- `load_recipe(path: Path) -> Recipe` (line 488) — Load a recipe file from disk and validate the schema.
- `_ensure_object_map(value: object, label: str) -> dict[str, object]` (line 497) — Ensure template resolution returned a mapping, raising otherwise.
- `_require_str(params: Mapping[str, object], key: str) -> str` (line 504) — Fetch a required string parameter from a mapping of arguments.
- `_coerce_optional_str(value: object | None) -> str | None` (line 513) — Convert optional string-like values to trimmed strings.
- `_coerce_positive_int(value: object | None, default: int) -> int` (line 521) — Convert inputs to a positive integer, falling back to the default.
- `_coerce_int(value: object | None) -> int | None` (line 529) — Coerce common primitive values to an integer when possible.
- `_coerce_bool(value: object | None, default: bool | None = None) -> bool | None` (line 548) — Interpret truthy/falsey string values and return a boolean.
- `list_recipes(recipes_dir: Path) -> list[Path]` (line 561) — Return all recipe definition files within the directory.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- asyncio, collections, contextlib, dataclasses, json, logging, models, pathlib, re, time, types, yaml

### Code Quality Notes
- 7 public element(s) lack docstrings.

## gateway/recipes/models.py

**File path**: `gateway/recipes/models.py`
**Purpose**: Pydantic models describing MCP recipe configuration.
**Dependencies**: External – __future__.annotations, pydantic.BaseModel, pydantic.Field, pydantic.model_validator, typing.Any; Internal – None
**Related modules**: None

### Classes
- `Condition` (line 10) — Assertion condition evaluated against a step result. Inherits from BaseModel.
  - Attributes: path: str = Field(description='Dot path into the result payload'), equals: Any | None = None, not_equals: Any | None = None, exists: bool | None = None
  - Methods: None
- `Capture` (line 19) — Capture part of a step result into the execution context. Inherits from BaseModel.
  - Attributes: name: str, path: str | None = None
  - Methods: None
- `WaitConfig` (line 26) — Poll a tool until a condition is satisfied. Inherits from BaseModel.
  - Attributes: tool: str = Field(description='Tool to invoke while waiting'), params: dict[str, Any] = Field(default_factory=dict), until: Condition = Field(description='Condition that terminates the wait'), interval_seconds: float = Field(default=5.0, ge=0.5, description='Polling interval'), timeout_seconds: float = Field(default=300.0, ge=1.0, description='Timeout before failing')
  - Methods: None
- `RecipeStep` (line 36) — Single step inside a recipe. Inherits from BaseModel.
  - Attributes: id: str, description: str | None = None, tool: str | None = None, params: dict[str, Any] = Field(default_factory=dict), expect: dict[str, Any] | None = None, asserts: list[Condition] | None = Field(default=None, alias='assert'), capture: list[Capture] | None = None, wait: WaitConfig | None = None, prompt: str | None = None
  - Methods:
    - `validate_mode(self) -> RecipeStep` (line 50) — Ensure mutually exclusive tool/wait configuration is respected.
- `Recipe` (line 59) — Top level recipe definition. Inherits from BaseModel.
  - Attributes: version: int = Field(1, description='Schema version'), name: str, summary: str | None = None, variables: dict[str, Any] = Field(default_factory=dict), steps: list[RecipeStep], outputs: dict[str, str] = Field(default_factory=dict)
  - Methods:
    - `ensure_unique_step_ids(self) -> Recipe` (line 70) — Verify step identifiers are unique within the recipe.

### Functions
- None

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- pydantic, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/scheduler.py

**File path**: `gateway/scheduler.py`
**Purpose**: Background scheduler that drives periodic ingestion runs.
**Dependencies**: External – __future__.annotations, apscheduler.schedulers.background.BackgroundScheduler, apscheduler.schedulers.base.SchedulerNotRunningError, apscheduler.triggers.cron.CronTrigger, apscheduler.triggers.interval.IntervalTrigger, collections.abc.Mapping, contextlib.suppress, filelock.FileLock, filelock.Timeout, logging, pathlib.Path, subprocess, time; Internal – gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.backup.BackupExecutionError, gateway.backup.service.default_backup_destination, gateway.backup.service.is_backup_archive, gateway.backup.service.run_backup, gateway.config.settings.AppSettings, gateway.ingest.service.execute_ingestion, gateway.observability.metrics.BACKUP_LAST_STATUS, gateway.observability.metrics.BACKUP_LAST_SUCCESS_TIMESTAMP, gateway.observability.metrics.BACKUP_RETENTION_DELETES_TOTAL, gateway.observability.metrics.BACKUP_RUNS_TOTAL, gateway.observability.metrics.INGEST_SKIPS_TOTAL, gateway.observability.metrics.SCHEDULER_LAST_SUCCESS_TIMESTAMP, gateway.observability.metrics.SCHEDULER_RUNS_TOTAL
**Related modules**: gateway.api.connections.Neo4jConnectionManager, gateway.api.connections.QdrantConnectionManager, gateway.backup.BackupExecutionError, gateway.backup.service.default_backup_destination, gateway.backup.service.is_backup_archive, gateway.backup.service.run_backup, gateway.config.settings.AppSettings, gateway.ingest.service.execute_ingestion, gateway.observability.metrics.BACKUP_LAST_STATUS, gateway.observability.metrics.BACKUP_LAST_SUCCESS_TIMESTAMP, gateway.observability.metrics.BACKUP_RETENTION_DELETES_TOTAL, gateway.observability.metrics.BACKUP_RUNS_TOTAL, gateway.observability.metrics.INGEST_SKIPS_TOTAL, gateway.observability.metrics.SCHEDULER_LAST_SUCCESS_TIMESTAMP, gateway.observability.metrics.SCHEDULER_RUNS_TOTAL

### Classes
- `IngestionScheduler` (line 36) — APScheduler wrapper that coordinates repo-aware ingestion jobs. Inherits from object.
  - Methods:
    - `__init__(self, settings: AppSettings, graph_manager: Neo4jConnectionManager | None = None, qdrant_manager: QdrantConnectionManager | None = None) -> None` (line 39) — Initialise scheduler state and ensure the scratch directory exists.
    - `start(self) -> None` (line 64) — Register the ingestion job and begin scheduling if enabled.
    - `shutdown(self) -> None` (line 107) — Stop the scheduler and release APScheduler resources.
    - `_run_ingestion(self) -> None` (line 114) — Execute a single ingestion cycle, guarding with a file lock.
    - `_run_backup(self) -> None` (line 169) — Run the backup job and record metrics/retention.
    - `_read_last_head(self) -> str | None` (line 223) — No method docstring provided.
    - `_write_last_head(self, head: str) -> None` (line 229) — No method docstring provided.
    - `_prune_backups(self) -> int` (line 232) — No method docstring provided.
    - `backup_health(self) -> dict[str, object]` (line 274) — No method docstring provided.

### Functions
- `_current_repo_head(repo_root: Path) -> str | None` (line 280) — Return the git HEAD sha for the repo, or ``None`` when unavailable.
- `_build_trigger(config: Mapping[str, object]) -> CronTrigger | IntervalTrigger` (line 296) — Construct the APScheduler trigger based on user configuration.
- `_describe_trigger(config: Mapping[str, object]) -> str` (line 311) — Provide a human readable summary of the configured trigger.
- `_coerce_positive_int(value: object, default: int) -> int` (line 320) — Best-effort conversion to a positive integer with sane defaults.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Schedules background jobs using APScheduler.

### Integration Points
- apscheduler, collections, contextlib, filelock, logging, pathlib, subprocess, time

### Code Quality Notes
- 4 public element(s) lack docstrings.

## gateway/search/__init__.py

**File path**: `gateway/search/__init__.py`
**Purpose**: Search service exposing vector search with graph context.
**Dependencies**: External – dataset.DatasetLoadError, dataset.build_feature_matrix, dataset.load_dataset_records, evaluation.EvaluationMetrics, evaluation.evaluate_model, exporter.ExportOptions, exporter.ExportStats, exporter.export_training_dataset, feedback.SearchFeedbackStore, maintenance.PruneOptions, maintenance.PruneStats, maintenance.RedactOptions, maintenance.RedactStats, maintenance.prune_feedback_log, maintenance.redact_dataset, service.SearchOptions, service.SearchResponse, service.SearchResult, service.SearchService, service.SearchWeights; Internal – None
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
- dataset, evaluation, exporter, feedback, maintenance, service

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/search/cli.py

**File path**: `gateway/search/cli.py`
**Purpose**: Command-line helpers for search training, exports, and maintenance.
**Dependencies**: External – __future__.annotations, argparse, datetime.UTC, datetime.datetime, logging, pathlib.Path, rich.console.Console; Internal – gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.observability.configure_logging, gateway.observability.configure_tracing, gateway.search.evaluation.evaluate_model, gateway.search.exporter.ExportOptions, gateway.search.exporter.export_training_dataset, gateway.search.maintenance.PruneOptions, gateway.search.maintenance.RedactOptions, gateway.search.maintenance.prune_feedback_log, gateway.search.maintenance.redact_dataset, gateway.search.trainer.DatasetLoadError, gateway.search.trainer.save_artifact, gateway.search.trainer.train_from_dataset
**Related modules**: gateway.config.settings.AppSettings, gateway.config.settings.get_settings, gateway.observability.configure_logging, gateway.observability.configure_tracing, gateway.search.evaluation.evaluate_model, gateway.search.exporter.ExportOptions, gateway.search.exporter.export_training_dataset, gateway.search.maintenance.PruneOptions, gateway.search.maintenance.RedactOptions, gateway.search.maintenance.prune_feedback_log, gateway.search.maintenance.redact_dataset, gateway.search.trainer.DatasetLoadError, gateway.search.trainer.save_artifact, gateway.search.trainer.train_from_dataset

### Classes
- None

### Functions
- `build_parser() -> argparse.ArgumentParser` (line 23) — Return an argument parser covering all search CLI commands.
- `export_training_data(output: Path | None, fmt: str, require_vote: bool, limit: int | None, settings: AppSettings | None = None) -> None` (line 142) — Materialise feedback events into a training dataset file.
- `train_model(dataset: Path, output: Path | None, settings: AppSettings) -> None` (line 188) — Train a ranking model from a prepared dataset and save the artifact.
- `show_weights(settings: AppSettings) -> None` (line 222) — Print the active search weight profile to the console.
- `prune_feedback(settings: AppSettings, max_age_days: int | None, max_requests: int | None, output: Path | None) -> None` (line 239) — Trim feedback logs by age/request count and optionally archive removals.
- `redact_training_dataset(dataset: Path, output: Path | None, drop_query: bool, drop_context: bool, drop_note: bool) -> None` (line 268) — Strip sensitive fields and emit a sanitized dataset.
- `evaluate_trained_model(dataset: Path, model: Path) -> None` (line 297) — Run offline evaluation of a trained model against a labelled dataset.
- `main(argv: list[str] | None = None) -> None` (line 326) — Entry point for the `gateway-search` command-line interface.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- argparse, datetime, logging, pathlib, rich

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/search/dataset.py

**File path**: `gateway/search/dataset.py`
**Purpose**: Utilities for reading and preparing search training datasets.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.abc.Mapping, collections.abc.Sequence, csv, json, pathlib.Path; Internal – gateway.search.exporter.FIELDNAMES
**Related modules**: gateway.search.exporter.FIELDNAMES

### Classes
- `DatasetLoadError` (line 15) — Raised when a dataset cannot be parsed. Inherits from RuntimeError.
  - Methods: None

### Functions
- `load_dataset_records(path: Path) -> list[Mapping[str, object]]` (line 19) — Load dataset rows from disk, raising when the file is missing.
- `build_feature_matrix(records: Iterable[Mapping[str, object]], feature_names: Sequence[str]) -> tuple[list[list[float]], list[float], list[str]]` (line 55) — Convert dataset rows into numeric feature vectors and targets.
- `_parse_float(value: object) -> float | None` (line 82) — No docstring provided.

### Constants and Configuration
- TARGET_FIELD = 'feedback_vote' (line 12)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, csv, json, pathlib

### Code Quality Notes
- 1 public element(s) lack docstrings.

## gateway/search/evaluation.py

**File path**: `gateway/search/evaluation.py`
**Purpose**: Model evaluation utilities for the search ranking pipeline.
**Dependencies**: External – __future__.annotations, collections.abc.Sequence, dataclasses.dataclass, math, numpy, numpy.typing, pathlib.Path, statistics.mean, typing.cast; Internal – gateway.search.dataset.DatasetLoadError, gateway.search.dataset.build_feature_matrix, gateway.search.dataset.load_dataset_records, gateway.search.trainer.load_artifact
**Related modules**: gateway.search.dataset.DatasetLoadError, gateway.search.dataset.build_feature_matrix, gateway.search.dataset.load_dataset_records, gateway.search.trainer.load_artifact

### Classes
- `EvaluationMetrics` (line 20) — Aggregate metrics produced after evaluating a ranking model. Inherits from object.
  - Attributes: mse: float, r2: float, ndcg_at_5: float, ndcg_at_10: float, spearman: float | None
  - Methods: None

### Functions
- `evaluate_model(dataset_path: Path, model_path: Path) -> EvaluationMetrics` (line 30) — Load a dataset and model artifact, returning evaluation metrics.
- `_mean_ndcg(request_ids: Sequence[str], relevance: FloatArray, scores: FloatArray, k: int) -> float` (line 63) — Compute mean NDCG@k for groups identified by request ids.
- `_dcg(relevances: FloatArray, k: int) -> float` (line 87) — Compute discounted cumulative gain at rank ``k``.
- `_spearman_correlation(y_true: FloatArray, y_pred: FloatArray) -> float | None` (line 96) — Return Spearman rank correlation between true and predicted values.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, dataclasses, math, numpy, pathlib, statistics, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/search/exporter.py

**File path**: `gateway/search/exporter.py`
**Purpose**: Utilities for exporting feedback logs into training datasets.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.abc.Iterator, collections.abc.Sequence, csv, dataclasses.dataclass, json, logging, pathlib.Path, typing.Any, typing.Literal; Internal – None
**Related modules**: None

### Classes
- `ExportOptions` (line 19) — User-configurable options controlling dataset export. Inherits from object.
  - Attributes: output_path: Path, output_format: FeedbackFormat, require_vote: bool = False, limit: int | None = None
  - Methods: None
- `ExportStats` (line 29) — Basic statistics about the export process. Inherits from object.
  - Attributes: total_events: int, written_rows: int, skipped_without_vote: int
  - Methods: None

### Functions
- `export_training_dataset(events_path: Path, options: ExportOptions) -> ExportStats` (line 63) — Write feedback events into the requested dataset format.
- `iter_feedback_events(path: Path) -> Iterator[dict[str, Any]]` (line 79) — Yield feedback events from a JSON lines log file.
- `_write_csv(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats` (line 101) — Write feedback events into a CSV file.
- `_write_jsonl(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats` (line 124) — Write feedback events into a JSONL file.
- `_flatten_event(event: dict[str, Any]) -> dict[str, Any]` (line 146) — Flatten nested event data into scalar fields.

### Constants and Configuration
- FIELDNAMES : Sequence[str] = ('request_id', 'timestamp', 'rank', 'query', 'result_count', 'chunk_id', 'artifact_path', 'artifact_type', 'subsystem', 'vector_score', 'adjusted_score', 'signal_subsystem_affinity', 'signal_relationship_count', 'signal_supporting_bonus', 'signal_coverage_missing', 'graph_context_present', 'feedback_vote', 'feedback_note', 'context_json', 'metadata_request_id', 'metadata_graph_context_included', 'metadata_warnings_count') (line 37)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, csv, dataclasses, json, logging, pathlib, typing

### Code Quality Notes
- No immediate issues detected from static scan.

## gateway/search/feedback.py

**File path**: `gateway/search/feedback.py`
**Purpose**: Persistent storage helpers for search feedback events.
**Dependencies**: External – __future__.annotations, collections.abc.Mapping, collections.abc.Sequence, datetime.UTC, datetime.datetime, json, pathlib.Path, threading, uuid; Internal – gateway.search.service.SearchResponse
**Related modules**: gateway.search.service.SearchResponse

### Classes
- `SearchFeedbackStore` (line 15) — Append-only store for search telemetry and feedback. Inherits from object.
  - Methods:
    - `__init__(self, root: Path) -> None` (line 18) — Initialise the feedback store beneath the given directory.
    - `record(self, response: SearchResponse, feedback: Mapping[str, object] | None, context: object = None, request_id: str | None = None) -> None` (line 25) — Persist a feedback event for the supplied search response.
    - `_append(self, rows: Sequence[Mapping[str, object]]) -> None` (line 68) — No method docstring provided.

### Functions
- `_serialize_results(response: SearchResponse, request_id: str, timestamp: str, vote: float | None, note: str | None, context: object, feedback: Mapping[str, object] | None) -> list[dict[str, object]]` (line 78) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, datetime, json, pathlib, threading, uuid

### Code Quality Notes
- 2 public element(s) lack docstrings.

## gateway/search/maintenance.py

**File path**: `gateway/search/maintenance.py`
**Purpose**: Maintenance routines for pruning feedback logs and redacting datasets.
**Dependencies**: External – __future__.annotations, collections.abc.Iterable, collections.abc.MutableMapping, csv, dataclasses.dataclass, datetime.UTC, datetime.datetime, datetime.timedelta, json, logging, pathlib.Path, shutil; Internal – gateway.search.exporter.iter_feedback_events
**Related modules**: gateway.search.exporter.iter_feedback_events

### Classes
- `PruneOptions` (line 22) — Configures retention rules for the feedback log pruning routine. Inherits from object.
  - Attributes: max_age_days: int | None = None, max_requests: int | None = None, output_path: Path | None = None, current_time: datetime | None = None
  - Methods: None
- `PruneStats` (line 32) — Summary of how many feedback requests were kept versus removed. Inherits from object.
  - Attributes: total_requests: int, retained_requests: int, removed_requests: int
  - Methods: None
- `RedactOptions` (line 41) — Toggles that control which sensitive fields should be redacted. Inherits from object.
  - Attributes: output_path: Path | None = None, drop_query: bool = False, drop_context: bool = False, drop_note: bool = False
  - Methods: None
- `RedactStats` (line 51) — Summary of how many dataset rows required redaction. Inherits from object.
  - Attributes: total_rows: int, redacted_rows: int
  - Methods: None

### Functions
- `prune_feedback_log(events_path: Path, options: PruneOptions) -> PruneStats` (line 58) — Prune feedback requests based on age and count thresholds.
- `redact_dataset(dataset_path: Path, options: RedactOptions) -> RedactStats` (line 96) — Redact sensitive fields from datasets stored as CSV or JSON Lines.
- `_parse_timestamp(value: object) -> datetime | None` (line 118) — Parse timestamps stored as numbers or ISO 8601 strings.
- `_collect_events(events_path: Path) -> tuple[MutableMapping[str, list[dict[str, object]]], list[str]]` (line 134) — No docstring provided.
- `_build_timestamps(events_by_request: MutableMapping[str, list[dict[str, object]]]) -> dict[str, datetime]` (line 152) — No docstring provided.
- `_apply_prune_filters(request_order: list[str], timestamps: dict[str, datetime], options: PruneOptions, now: datetime) -> list[str]` (line 161) — No docstring provided.
- `_preserve_original_order(order: list[str], selected_ids: Iterable[str]) -> list[str]` (line 180) — No docstring provided.
- `_write_retained_events(destination: Path, retained_order: Iterable[str], events_by_request: MutableMapping[str, list[dict[str, object]]]) -> None` (line 185) — No docstring provided.
- `_redact_csv(source: Path, destination: Path, options: RedactOptions) -> RedactStats` (line 199) — Redact sensitive columns from a CSV dataset.
- `_redact_csv_row(row: MutableMapping[str, str], options: RedactOptions) -> bool` (line 217) — No docstring provided.
- `_clear_field(row: MutableMapping[str, str], field: str, replacement: str) -> bool` (line 228) — No docstring provided.
- `_redact_jsonl(source: Path, destination: Path, options: RedactOptions) -> RedactStats` (line 237) — Redact sensitive fields from JSON lines datasets.
- `_redact_json_record(record: MutableMapping[str, object], options: RedactOptions) -> bool` (line 257) — No docstring provided.
- `_null_field(record: MutableMapping[str, object], field: str) -> bool` (line 268) — No docstring provided.

### Constants and Configuration
- _FALLBACK_TIMESTAMP = datetime.fromordinal(1).replace(tzinfo=UTC) (line 18)

### Data Flow
- Handles in-process data transformations defined in this module.

### Integration Points
- collections, csv, dataclasses, datetime, json, logging, pathlib, shutil

### Code Quality Notes
- 9 public element(s) lack docstrings.

## gateway/search/service.py

**File path**: `gateway/search/service.py`
**Purpose**: Hybrid search orchestration for Duskmantle's knowledge gateway.
**Dependencies**: External – __future__.annotations, collections.abc.Callable, collections.abc.Iterable, collections.abc.Sequence, dataclasses.dataclass, datetime.UTC, datetime.datetime, datetime.timedelta, logging, neo4j.exceptions.Neo4jError, qdrant_client.QdrantClient, qdrant_client.http.models.ScoredPoint, qdrant_client.http.models.SearchParams, re, time, typing.Any, typing.Literal; Internal – gateway.graph.service.GraphService, gateway.graph.service.GraphServiceError, gateway.ingest.embedding.Embedder, gateway.observability.SEARCH_GRAPH_CACHE_EVENTS, gateway.observability.SEARCH_GRAPH_LOOKUP_SECONDS, gateway.observability.SEARCH_SCORE_DELTA, gateway.search.trainer.ModelArtifact
**Related modules**: gateway.graph.service.GraphService, gateway.graph.service.GraphServiceError, gateway.ingest.embedding.Embedder, gateway.observability.SEARCH_GRAPH_CACHE_EVENTS, gateway.observability.SEARCH_GRAPH_LOOKUP_SECONDS, gateway.observability.SEARCH_SCORE_DELTA, gateway.search.trainer.ModelArtifact

### Classes
- `SearchResult` (line 26) — Single ranked chunk returned from the search pipeline. Inherits from object.
  - Attributes: chunk: dict[str, Any], graph_context: dict[str, Any] | None, scoring: dict[str, Any]
  - Methods: None
- `SearchResponse` (line 35) — API-friendly container for search results and metadata. Inherits from object.
  - Attributes: query: str, results: list[SearchResult], metadata: dict[str, Any]
  - Methods: None
- `SearchOptions` (line 44) — Runtime options controlling the search service behaviour. Inherits from object.
  - Attributes: max_limit: int = 25, graph_timeout_seconds: float = 0.25, hnsw_ef_search: int | None = None, scoring_mode: Literal['heuristic', 'ml'] = 'heuristic', weight_profile: str = 'custom', slow_graph_warn_seconds: float = 0.25
  - Methods: None
- `SearchWeights` (line 56) — Weighting configuration for hybrid scoring. Inherits from object.
  - Attributes: subsystem: float = 0.3, relationship: float = 0.05, support: float = 0.1, coverage_penalty: float = 0.15, criticality: float = 0.12, vector: float = 1.0, lexical: float = 0.25
  - Methods: None
- `FilterState` (line 69) — Preprocessed filter collections derived from request parameters. Inherits from object.
  - Attributes: allowed_subsystems: set[str], allowed_types: set[str], allowed_namespaces: set[str], allowed_tags: set[str], filters_applied: dict[str, Any], recency_cutoff: datetime | None, recency_warning_emitted: bool = False
  - Methods: None
- `CoverageInfo` (line 82) — Coverage characteristics used during scoring. Inherits from object.
  - Attributes: ratio: float, penalty: float, missing_flag: float
  - Methods: None
- `SearchService` (line 90) — Execute hybrid vector/graph search with heuristic or ML scoring. Inherits from object.
  - Methods:
    - `__init__(self, qdrant_client: QdrantClient, collection_name: str, embedder: Embedder, options: SearchOptions | None = None, weights: SearchWeights | None = None, model_artifact: ModelArtifact | None = None, failure_callback: Callable[[Exception], None] | None = None) -> None` (line 93) — Initialise the search service with vector and scoring options.
    - `search(self, query: str, limit: int, include_graph: bool, graph_service: GraphService | None, sort_by_vector: bool = False, request_id: str | None = None, filters: dict[str, Any] | None = None) -> SearchResponse` (line 155) — Execute a hybrid search request and return ranked results.
    - `_resolve_graph_context(self, payload: dict[str, Any], graph_service: GraphService | None, include_graph: bool, graph_cache: dict[str, dict[str, Any]], recency_required: bool, allowed_subsystems: set[str], subsystem_match: bool, request_id: str | None, warnings: list[str]) -> tuple[dict[str, Any] | None, float | None]` (line 339) — Fetch and cache graph context for a search result chunk.
    - `_build_model_features(self, scoring: dict[str, Any], graph_context: dict[str, Any] | None, graph_context_included: bool, warnings_count: int) -> dict[str, float]` (line 469) — No method docstring provided.
    - `_apply_model(self, features: dict[str, float]) -> tuple[float, dict[str, float]]` (line 496) — No method docstring provided.

### Functions
- `_label_for_artifact(artifact_type: str | None) -> str` (line 510) — No docstring provided.
- `_summarize_graph_context(data: dict[str, Any]) -> dict[str, Any]` (line 521) — No docstring provided.
- `_subsystems_from_context(graph_context: dict[str, Any] | None) -> set[str]` (line 551) — No docstring provided.
- `_detect_query_subsystems(query: str) -> set[str]` (line 569) — No docstring provided.
- `_normalise_hybrid_weights(vector_weight: float, lexical_weight: float) -> tuple[float, float]` (line 574) — No docstring provided.
- `_prepare_filter_state(filters: dict[str, Any]) -> FilterState` (line 582) — No docstring provided.
- `_passes_payload_filters(payload: dict[str, Any], state: FilterState) -> bool` (line 652) — No docstring provided.
- `_normalise_payload_tags(raw_tags: Sequence[object] | set[object] | None) -> set[str]` (line 669) — No docstring provided.
- `_build_chunk(payload: dict[str, Any], score: float) -> dict[str, Any]` (line 675) — No docstring provided.
- `_calculate_subsystem_affinity(subsystem: str, query_tokens: set[str]) -> float` (line 692) — No docstring provided.
- `_calculate_supporting_bonus(related_artifacts: Iterable[dict[str, Any]]) -> float` (line 702) — No docstring provided.
- `_calculate_coverage_info(chunk: dict[str, Any], weight_coverage_penalty: float) -> CoverageInfo` (line 714) — No docstring provided.
- `_coerce_ratio_value(value: object) -> float | None` (line 724) — No docstring provided.
- `_calculate_criticality_score(chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> float` (line 742) — No docstring provided.
- `_update_path_depth_signal(signals: dict[str, Any], path_depth: float | None, graph_context: dict[str, Any] | None) -> None` (line 749) — No docstring provided.
- `_ensure_criticality_signal(signals: dict[str, Any], chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> None` (line 764) — No docstring provided.
- `_ensure_freshness_signal(signals: dict[str, Any], chunk: dict[str, Any], graph_context: dict[str, Any] | None, freshness_days: float | None) -> None` (line 774) — No docstring provided.
- `_ensure_coverage_ratio_signal(signals: dict[str, Any], chunk: dict[str, Any]) -> None` (line 785) — No docstring provided.
- `_lexical_score(query: str, chunk: dict[str, Any]) -> float` (line 800) — No docstring provided.
- `_base_scoring(vector_score: float, lexical_score: float, vector_weight: float, lexical_weight: float) -> dict[str, Any]` (line 833) — No docstring provided.
- `_compute_scoring(base_scoring: dict[str, Any], vector_score: float, lexical_score: float, vector_weight: float, lexical_weight: float, query_tokens: set[str], chunk: dict[str, Any], graph_context: dict[str, Any], weight_subsystem: float, weight_relationship: float, weight_support: float, weight_coverage_penalty: float, weight_criticality: float) -> dict[str, Any]` (line 856) — No docstring provided.
- `_populate_additional_signals(scoring: dict[str, Any], chunk: dict[str, Any], graph_context: dict[str, Any] | None, path_depth: float | None, freshness_days: float | None) -> dict[str, Any]` (line 914) — No docstring provided.
- `_estimate_path_depth(graph_context: dict[str, Any] | None) -> float` (line 932) — No docstring provided.
- `_extract_subsystem_criticality(graph_context: dict[str, Any] | None) -> str | None` (line 941) — No docstring provided.
- `_normalise_criticality(value: str | float | None) -> float` (line 956) — No docstring provided.
- `_compute_freshness_days(chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> float | None` (line 970) — No docstring provided.
- `_resolve_chunk_datetime(chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> datetime | None` (line 986) — No docstring provided.
- `_parse_iso_datetime(value: object) -> datetime | None` (line 1013) — No docstring provided.

### Constants and Configuration
- _TOKEN_PATTERN = re.compile('\\w+', flags=re.ASCII) (line 797)

### Data Flow
- Issues Cypher queries against Neo4j and returns structured dictionaries.
- Interacts with Qdrant collections for vector search or persistence.

### Integration Points
- collections, dataclasses, datetime, logging, neo4j, qdrant_client, re, time, typing

### Code Quality Notes
- 30 public element(s) lack docstrings.

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
**Dependencies**: External – __future__.annotations, fastapi.testclient.TestClient, json, logging, pathlib.Path, pytest, typing.Any; Internal – gateway.api.app.create_app, gateway.config.settings.get_settings, gateway.get_version, gateway.graph.service.GraphService, gateway.search.service.SearchResponse
**Related modules**: gateway.api.app.create_app, gateway.config.settings.get_settings, gateway.get_version, gateway.graph.service.GraphService, gateway.search.service.SearchResponse

### Classes
- None

### Functions
- `reset_settings_cache() -> None` (line 19) — No docstring provided.
- `test_audit_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 25) — No docstring provided.
- `test_coverage_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 52) — No docstring provided.
- `test_coverage_missing_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 82) — No docstring provided.
- `test_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None` (line 99) — No docstring provided.
- `test_startup_logs_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None` (line 113) — No docstring provided.
- `test_secure_mode_without_admin_token_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 129) — No docstring provided.
- `test_secure_mode_requires_custom_neo4j_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 139) — No docstring provided.
- `test_rate_limiting_search(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None` (line 149) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Defines FastAPI routes or dependencies responding to HTTP requests.
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- fastapi, json, logging, pathlib, pytest, typing

### Code Quality Notes
- 9 public element(s) lack docstrings.

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
- `sample_repo(tmp_path: Path) -> Path` (line 23) — No docstring provided.
- `test_cli_rebuild_dry_run(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 31) — No docstring provided.
- `test_cli_rebuild_requires_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 50) — No docstring provided.
- `test_cli_rebuild_with_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 60) — No docstring provided.
- `test_cli_rebuild_full_rebuild_flag(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 75) — No docstring provided.
- `test_cli_rebuild_incremental_flag(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None` (line 85) — No docstring provided.
- `test_cli_audit_history_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 99) — No docstring provided.
- `test_cli_audit_history_no_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None` (line 123) — No docstring provided.

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
**Dependencies**: External – __future__.annotations, collections.abc.Sequence, datetime.UTC, datetime.datetime, datetime.timedelta, prometheus_client.REGISTRY, pytest, typing.Any; Internal – gateway.graph.service.GraphService, gateway.search.SearchOptions, gateway.search.SearchService, gateway.search.SearchWeights, gateway.search.trainer.ModelArtifact
**Related modules**: gateway.graph.service.GraphService, gateway.search.SearchOptions, gateway.search.SearchService, gateway.search.SearchWeights, gateway.search.trainer.ModelArtifact

### Classes
- `FakeEmbedder` (line 20) — No class docstring provided. Inherits from object.
  - Methods:
    - `encode(self, texts: Sequence[str]) -> list[list[float]]` (line 21) — No method docstring provided.
- `FakePoint` (line 25) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, payload: dict[str, Any], score: float) -> None` (line 26) — No method docstring provided.
- `FakeQdrantClient` (line 31) — No class docstring provided. Inherits from object.
  - Methods:
    - `__init__(self, points: list[FakePoint]) -> None` (line 32) — No method docstring provided.
    - `search(self, **kwargs: object) -> list[FakePoint]` (line 36) — No method docstring provided.
- `DummyGraphService` (line 41) — No class docstring provided. Inherits from GraphService.
  - Methods:
    - `__init__(self, response: dict[str, Any]) -> None` (line 42) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 45) — No method docstring provided.
    - `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]` (line 48) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 51) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 54) — No method docstring provided.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 57) — No method docstring provided.
- `MapGraphService` (line 178) — No class docstring provided. Inherits from GraphService.
  - Methods:
    - `__init__(self, data: dict[str, dict[str, Any]]) -> None` (line 179) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 182) — No method docstring provided.
    - `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]` (line 185) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 188) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 191) — No method docstring provided.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 194) — No method docstring provided.
- `CountingGraphService` (line 198) — No class docstring provided. Inherits from GraphService.
  - Methods:
    - `__init__(self, response: dict[str, Any], depth: int = 2) -> None` (line 199) — No method docstring provided.
    - `get_node(self, node_id: str, relationships: str, limit: int) -> dict[str, Any]` (line 205) — No method docstring provided.
    - `shortest_path_depth(self, node_id: str, max_depth: int = 4) -> int | None` (line 209) — No method docstring provided.
    - `get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]` (line 213) — No method docstring provided.
    - `search(self, term: str, limit: int) -> dict[str, Any]` (line 216) — No method docstring provided.
    - `run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]` (line 219) — No method docstring provided.

### Functions
- `_metric_value(name: str, labels: dict[str, str] | None = None) -> float` (line 15) — No docstring provided.
- `sample_points() -> list[FakePoint]` (line 62) — No docstring provided.
- `graph_response() -> dict[str, Any]` (line 81) — No docstring provided.
- `test_search_service_enriches_with_graph(sample_points: list[FakePoint], graph_response: dict[str, Any]) -> None` (line 112) — No docstring provided.
- `test_search_service_handles_missing_graph(sample_points: list[FakePoint]) -> None` (line 150) — No docstring provided.
- `test_search_hnsw_search_params(sample_points: list[FakePoint]) -> None` (line 223) — No docstring provided.
- `test_lexical_score_affects_ranking() -> None` (line 245) — No docstring provided.
- `test_search_service_orders_by_adjusted_score() -> None` (line 289) — No docstring provided.
- `test_search_service_caches_graph_lookups(sample_points: list[FakePoint], graph_response: dict[str, Any]) -> None` (line 373) — No docstring provided.
- `test_search_service_filters_artifact_types() -> None` (line 434) — No docstring provided.
- `test_search_service_filters_namespaces() -> None` (line 483) — No docstring provided.
- `test_search_service_filters_tags() -> None` (line 532) — No docstring provided.
- `test_search_service_filters_recency_updated_after() -> None` (line 581) — No docstring provided.
- `test_search_service_filters_recency_max_age_days() -> None` (line 636) — No docstring provided.
- `test_search_service_filters_subsystem_via_graph(graph_response: dict[str, Any]) -> None` (line 686) — No docstring provided.
- `test_search_service_ml_model_reorders_results() -> None` (line 741) — No docstring provided.

### Constants and Configuration
- No module-level constants detected.

### Data Flow
- Executes pytest fixtures or assertions to validate behaviour.

### Integration Points
- collections, datetime, prometheus_client, pytest, typing

### Code Quality Notes
- 44 public element(s) lack docstrings.

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
