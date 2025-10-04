# Module Documentation

## gateway/__init__.py
**Purpose**: Core package for the Duskmantle knowledge gateway.

**Dependencies**:
- External: __future__
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `get_version()` – Return the current package version.

### Constants
- None

### Data Flow
- Primary entry points: `get_version`
- Touches external libraries: __future__.

### Integration Points
- External: __future__
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 13


## gateway/__main__.py
**Purpose**: Console entry point that launches the FastAPI application.

**Dependencies**:
- External: __future__, uvicorn
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `main()` – Run the gateway API using Uvicorn.

### Constants
- None

### Data Flow
- Primary entry points: `main`
- Touches external libraries: __future__, uvicorn.

### Integration Points
- External: __future__, uvicorn
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 15


## gateway/api/__init__.py
**Purpose**: API layer for the knowledge gateway.

**Dependencies**:
- External: None
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Lightweight module with minimal data flow; acts as namespace or configuration container.

### Integration Points
- External: None
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 2


## gateway/api/app.py
**Purpose**: Primary FastAPI application wiring for the knowledge gateway.

**Dependencies**:
- External: __future__, apscheduler, asyncio, collections, contextlib, fastapi, json, logging, neo4j, qdrant_client, slowapi, time, typing, uuid
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_validate_auth_settings(settings)` – No docstring.
- `_log_startup_configuration(settings)` – No docstring.
- `_build_lifespan(settings)` – No docstring.
- `_configure_rate_limits(app, settings)` – No docstring.
- `_init_feedback_store(settings)` – No docstring.
- `_load_search_model(settings)` – No docstring.
- `_initialise_graph_manager(manager, settings)` – No docstring.
- `_initialise_qdrant_manager(manager)` – No docstring.
- `async _dependency_heartbeat_loop(app, interval)` – No docstring.
- `_verify_graph_database(driver, database)` – No docstring.
- `_ensure_graph_database(settings)` – Ensure the configured Neo4j database exists, creating it if missing.
- `_run_graph_auto_migration(driver, database)` – No docstring.
- `_fetch_pending_migrations(runner)` – No docstring.
- `_log_migration_plan(pending)` – No docstring.
- `_log_migration_completion(pending)` – No docstring.
- `_set_migration_metrics(status, timestamp)` – No docstring.
- `create_app()` – Create the FastAPI application instance.
- `_rate_limit_handler(_request, exc)` – No docstring.

### Constants
- `DEPENDENCY_HEARTBEAT_INTERVAL_SECONDS` = 30.0

### Data Flow
- Primary entry points: `_validate_auth_settings`, `_log_startup_configuration`, `_build_lifespan`, `_configure_rate_limits`, `_init_feedback_store`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, apscheduler, asyncio, collections, contextlib, fastapi, json, logging, neo4j, qdrant_client, slowapi, time, typing, uuid.

### Integration Points
- External: __future__, apscheduler, asyncio, collections, contextlib, fastapi, json, logging, neo4j, qdrant_client, slowapi, time, typing, uuid
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 18
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 10
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 433


## gateway/api/auth.py
**Purpose**: Authentication dependencies used across the FastAPI surface.

**Dependencies**:
- External: __future__, collections, fastapi
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `require_scope(scope)` – Return a dependency enforcing the given scope.
- `_allowed_tokens_for_scope(settings, scope)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `require_scope`, `_allowed_tokens_for_scope`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, fastapi.

### Integration Points
- External: __future__, collections, fastapi
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 56


## gateway/api/connections.py
**Purpose**: Connection managers for external services (Neo4j and Qdrant).

**Dependencies**:
- External: __future__, contextlib, dataclasses, logging, neo4j, qdrant_client, threading, time
- Internal: gateway
**Related modules**: gateway

### Classes
- `DependencyStatus` (bases: object) – Serializable snapshot of an external dependency.
- `Neo4jConnectionManager` (bases: object) – Lazy initialisation and health tracking for Neo4j drivers.
  - `__init__(self, settings, log=None)` – No docstring.
  - `revision(self)` – No docstring.
  - `describe(self)` – No docstring.
  - `get_write_driver(self)` – No docstring.
  - `get_readonly_driver(self)` – No docstring.
  - `mark_failure(self, exc=None)` – No docstring.
  - `heartbeat(self)` – No docstring.
  - `_create_driver(self, uri, user, password)` – No docstring.
  - `_record_success(self)` – No docstring.
- `QdrantConnectionManager` (bases: object) – Lazy initialisation and health tracking for Qdrant clients.
  - `__init__(self, settings, log=None)` – No docstring.
  - `revision(self)` – No docstring.
  - `describe(self)` – No docstring.
  - `get_client(self)` – No docstring.
  - `mark_failure(self, exc=None)` – No docstring.
  - `heartbeat(self)` – No docstring.
  - `_create_client(self)` – No docstring.
  - `_record_success(self)` – No docstring.

### Functions
- None

### Constants
- `GRAPH_DRIVER_FACTORY` = GraphDatabase.driver
- `QDRANT_CLIENT_FACTORY` = QdrantClient

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, contextlib, dataclasses, logging, neo4j, qdrant_client, threading, time.

### Integration Points
- External: __future__, contextlib, dataclasses, logging, neo4j, qdrant_client, threading, time
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 3 of 3
- Try/except blocks: 5
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 251


## gateway/api/constants.py
**Purpose**: Shared API constants.

**Dependencies**:
- External: __future__
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- `API_V1_PREFIX` = '/api/v1'

### Data Flow
- Touches external libraries: __future__.

### Integration Points
- External: __future__
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 8


## gateway/api/dependencies.py
**Purpose**: FastAPI dependency helpers for the gateway application.

**Dependencies**:
- External: __future__, fastapi, logging, slowapi
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `get_app_settings(request)` – Return the application settings attached to the FastAPI app.
- `get_limiter(request)` – Return the rate limiter configured on the FastAPI app.
- `get_search_model(request)` – Return the cached search ranking model from application state.
- `get_graph_service_dependency(request)` – Return a memoised graph service bound to the current FastAPI app.
- `get_search_service_dependency(request)` – Construct (and cache) the hybrid search service for the application.
- `get_feedback_store(request)` – Return the configured search feedback store, if any.

### Constants
- None

### Data Flow
- Primary entry points: `get_app_settings`, `get_limiter`, `get_search_model`, `get_graph_service_dependency`, `get_search_service_dependency`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, logging, slowapi.

### Integration Points
- External: __future__, fastapi, logging, slowapi
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 6 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 147


## gateway/api/routes/__init__.py
**Purpose**: FastAPI route modules for the gateway application.

**Dependencies**:
- External: graph, health, reporting, search
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: graph, health, reporting, search.

### Integration Points
- External: graph, health, reporting, search
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 6


## gateway/api/routes/graph.py
**Purpose**: Graph API routes.

**Dependencies**:
- External: __future__, fastapi, slowapi, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `create_router(limiter, metrics_limit)` – Create an API router exposing graph endpoints with shared rate limits.

### Constants
- None

### Data Flow
- Primary entry points: `create_router`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, slowapi, typing.

### Integration Points
- External: __future__, fastapi, slowapi, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 5
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 149


## gateway/api/routes/health.py
**Purpose**: Health and observability endpoints.

**Dependencies**:
- External: __future__, contextlib, fastapi, json, prometheus_client, slowapi, sqlite3, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `create_router(limiter, metrics_limit)` – Wire up health, readiness, and metrics endpoints.
- `build_health_report(app, settings)` – Assemble the health payload consumed by `/healthz`.
- `_coverage_health(settings)` – No docstring.
- `_audit_health(settings)` – No docstring.
- `_scheduler_health(app, settings)` – No docstring.
- `_graph_health(app, settings)` – No docstring.
- `_qdrant_health(app, settings)` – No docstring.
- `_dependency_health(manager)` – No docstring.
- `_backup_health(app, settings)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `create_router`, `build_health_report`, `_coverage_health`, `_audit_health`, `_scheduler_health`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, contextlib, fastapi, json, prometheus_client, slowapi, sqlite3, time, typing.

### Integration Points
- External: __future__, contextlib, fastapi, json, prometheus_client, slowapi, sqlite3, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 9
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 2
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 213


## gateway/api/routes/reporting.py
**Purpose**: Observability and reporting routes.

**Dependencies**:
- External: __future__, fastapi, json, logging, pathlib, slowapi, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `create_router(limiter)` – Expose reporting and audit endpoints protected by maintainer auth.

### Constants
- None

### Data Flow
- Primary entry points: `create_router`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, json, logging, pathlib, slowapi, typing.

### Integration Points
- External: __future__, fastapi, json, logging, pathlib, slowapi, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 5
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 139


## gateway/api/routes/search.py
**Purpose**: Search API routes.

**Dependencies**:
- External: __future__, collections, datetime, fastapi, logging, qdrant_client, slowapi, typing, uuid
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `create_router(limiter, metrics_limit)` – Return an API router for the search endpoints with shared rate limits.
- `_parse_iso8601_to_utc(value)` – No docstring.
- `_has_vote(mapping)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `create_router`, `_parse_iso8601_to_utc`, `_has_vote`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, datetime, fastapi, logging, qdrant_client, slowapi, typing, uuid.

### Integration Points
- External: __future__, collections, datetime, fastapi, logging, qdrant_client, slowapi, typing, uuid
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 7
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 256


## gateway/backup/__init__.py
**Purpose**: Backup utilities for the knowledge gateway.

**Dependencies**:
- External: exceptions, service
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: exceptions, service.

### Integration Points
- External: exceptions, service
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 22


## gateway/backup/exceptions.py
**Purpose**: Custom exceptions for gateway backup operations.

**Dependencies**:
- External: __future__
- Internal: None
**Related modules**: None

### Classes
- `BackupExecutionError` (bases: RuntimeError) – Raised when the backup helper fails to produce an archive.

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: __future__.

### Integration Points
- External: __future__
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 11


## gateway/backup/service.py
**Purpose**: Helper functions for orchestrating state backups.

**Dependencies**:
- External: __future__, collections, contextlib, exceptions, os, pathlib, re, subprocess
- Internal: None
**Related modules**: None

### Classes
- `BackupResult` (bases: dict) – Simple mapping describing the archive produced by a backup run.

### Functions
- `default_backup_destination(state_path)` – Return the default directory for storing backup archives.
- `is_backup_archive(path)` – Return ``True`` when ``path`` matches the managed backup filename pattern.
- `run_backup(state_path, script_path, destination_path=None, extra_env=None)` – Execute the backup helper synchronously and return archive metadata.
- `_parse_archive_path(output)` – No docstring.
- `_default_backup_script()` – No docstring.

### Constants
- `_BACKUP_DONE_PATTERN` = re.compile('Backup written to (?P<path>.+)$')
- `ARCHIVE_FILENAME_PREFIX` = 'km-backup-'
- `ARCHIVE_ALLOWED_SUFFIXES` = ('.tgz', '.tar.gz')
- `DEFAULT_BACKUP_DIRNAME` = 'backups'
- `DEFAULT_BACKUP_ARCHIVE_DIRNAME` = 'archives'

### Data Flow
- Primary entry points: `default_backup_destination`, `is_backup_archive`, `run_backup`, `_parse_archive_path`, `_default_backup_script`
- Touches external libraries: __future__, collections, contextlib, exceptions, os, pathlib, re, subprocess.

### Integration Points
- External: __future__, collections, contextlib, exceptions, os, pathlib, re, subprocess
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 5
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 116


## gateway/config/__init__.py
**Purpose**: Configuration helpers for the knowledge gateway.

**Dependencies**:
- External: __future__, settings
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: __future__, settings.

### Integration Points
- External: __future__, settings
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 8


## gateway/config/settings.py
**Purpose**: Pydantic-based configuration for the knowledge gateway.

**Dependencies**:
- External: __future__, functools, pathlib, pydantic, pydantic_settings, typing
- Internal: None
**Related modules**: None

### Classes
- `AppSettings` (bases: BaseSettings) – Runtime configuration for the knowledge gateway.
  - `_clamp_tracing_ratio(cls, value)` – No docstring.
  - `_clamp_search_weights(cls, value)` – No docstring.
  - `_sanitize_hnsw_ef(cls, value)` – No docstring.
  - `_sanitize_graph_cache_ttl(cls, value)` – No docstring.
  - `_sanitize_graph_cache_max(cls, value)` – No docstring.
  - `_sanitize_backup_interval(cls, value)` – No docstring.
  - `_sanitize_backup_retention(cls, value)` – No docstring.
  - `_sanitize_feedback_bytes(cls, value)` – No docstring.
  - `_sanitize_feedback_files(cls, value)` – No docstring.
  - `_sanitize_graph_max_results(cls, value)` – No docstring.
  - `_sanitize_graph_budget(cls, value)` – No docstring.
  - `resolved_search_weights(self)` – No docstring.
  - `backup_trigger_config(self)` – No docstring.
  - `scheduler_trigger_config(self)` – No docstring.
  - `_validate_history_limit(cls, value)` – No docstring.
  - `_validate_audit_history_limit(cls, value)` – No docstring.
  - `_validate_lifecycle_stale(cls, value)` – No docstring.
  - `_ensure_positive_parallelism(cls, value)` – No docstring.

### Functions
- `get_settings()` – Load settings from environment (cached).

### Constants
- `SEARCH_WEIGHT_PROFILES` = {'default': {'weight_subsystem': 0.28, 'weight_relationship': 0.05, 'weight_support': 0.09, 'weight_coverage_penalty': 0.15, 'weight_criticality': 0.12}, 'analysis': {'weight_subsystem': 0.38, 'weight_relationship': 0.1, 'weight_support': 0.08, 'weight_coverage_penalty': 0.18, 'weight_criticality': 0.18}, 'operations': {'weight_subsystem': 0.22, 'weight_relationship': 0.08, 'weight_support': 0.06, 'weight_coverage_penalty': 0.28, 'weight_criticality': 0.1}, 'docs-heavy': {'weight_subsystem': 0.26, 'weight_relationship': 0.04, 'weight_support': 0.22, 'weight_coverage_penalty': 0.12, 'weight_criticality': 0.08}}

### Data Flow
- Primary entry points: `get_settings`
- Touches external libraries: __future__, functools, pathlib, pydantic, pydantic_settings, typing.

### Integration Points
- External: __future__, functools, pathlib, pydantic, pydantic_settings, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 328


## gateway/graph/__init__.py
**Purpose**: Graph query utilities and service layer.

**Dependencies**:
- External: service
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: service.

### Integration Points
- External: service
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 11


## gateway/graph/cli.py
**Purpose**: Command-line utilities for managing the Neo4j graph schema.

**Dependencies**:
- External: __future__, argparse, logging, neo4j
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `build_parser()` – Return the CLI argument parser for graph administration commands.
- `run_migrations(dry_run=False)` – Execute graph schema migrations, optionally printing the pending set.
- `main(argv=None)` – Entrypoint for the `gateway-graph` command-line interface.

### Constants
- None

### Data Flow
- Primary entry points: `build_parser`, `run_migrations`, `main`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, argparse, logging, neo4j.

### Integration Points
- External: __future__, argparse, logging, neo4j
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 68


## gateway/graph/migrations/__init__.py
**Purpose**: Graph schema migrations.

**Dependencies**:
- External: runner
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: runner.

### Integration Points
- External: runner
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 6


## gateway/graph/migrations/runner.py
**Purpose**: Helpers for applying and tracking Neo4j schema migrations.

**Dependencies**:
- External: __future__, collections, dataclasses, logging, neo4j
- Internal: None
**Related modules**: None

### Classes
- `Migration` (bases: object) – Describe a single migration and the Cypher statements it executes.
- `MigrationRunner` (bases: object) – Apply ordered graph migrations using a shared Neo4j driver.
  - `pending_ids(self)` – No docstring.
  - `run(self)` – No docstring.
  - `_is_applied(self, migration_id)` – No docstring.
  - `_apply(self, migration)` – No docstring.

### Functions
- None

### Constants
- `MIGRATIONS` = [Migration(id='001_constraints', statements=['CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (f:SourceFile) REQUIRE f.path IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (d:DesignDoc) REQUIRE d.path IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.path IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE']), Migration(id='002_domain_entities', statements=['CREATE CONSTRAINT IF NOT EXISTS FOR (m:IntegrationMessage) REQUIRE m.name IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (tc:TelemetryChannel) REQUIRE tc.name IS UNIQUE', 'CREATE CONSTRAINT IF NOT EXISTS FOR (cfg:ConfigFile) REQUIRE cfg.path IS UNIQUE'])]

### Data Flow
- Touches external libraries: __future__, collections, dataclasses, logging, neo4j.

### Integration Points
- External: __future__, collections, dataclasses, logging, neo4j
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 2 of 2
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 88


## gateway/graph/service.py
**Purpose**: Read-only graph service utilities backed by Neo4j.

**Dependencies**:
- External: __future__, base64, collections, dataclasses, neo4j, threading, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `GraphServiceError` (bases: RuntimeError) – Base class for graph-related errors.
- `GraphNotFoundError` (bases: GraphServiceError) – Raised when a requested node cannot be found.
- `GraphQueryError` (bases: GraphServiceError) – Raised when a supplied query is invalid or unsafe.
- `SubsystemGraphSnapshot` (bases: object) – Snapshot of a subsystem node and its related graph context.
- `SubsystemGraphCache` (bases: object) – Simple TTL cache for subsystem graph snapshots.
  - `__init__(self, ttl_seconds, max_entries)` – No docstring.
  - `get(self, key)` – No docstring.
  - `set(self, key, snapshot)` – No docstring.
  - `clear(self)` – No docstring.
- `GraphService` (bases: object) – Service layer for read-only graph queries.
  - `__init__(self, driver_provider, database, cache_ttl=None, cache_max_entries=128, readonly_provider=None, failure_callback=None)` – No docstring.
  - `clear_cache(self)` – No docstring.
  - `_get_driver(self, readonly=False)` – No docstring.
  - `_execute(self, operation, readonly=False)` – No docstring.
  - `_run_with_session(self, operation, readonly=False, **session_kwargs)` – No docstring.
  - `get_subsystem(self, name, depth, limit, cursor, include_artifacts)` – No docstring.
  - `get_subsystem_graph(self, name, depth)` – No docstring.
  - `list_orphan_nodes(self, label, cursor, limit)` – No docstring.
  - `_load_subsystem_snapshot(self, name, depth)` – No docstring.
  - `_build_subsystem_snapshot(self, name, depth)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
  - `search(self, term, limit)` – No docstring.
  - `shortest_path_depth(self, node_id, max_depth=4)` – No docstring.
  - `run_cypher(self, query, parameters=None)` – No docstring.

### Functions
- `get_graph_service(driver, database, cache_ttl=None, cache_max_entries=128, readonly_driver=None, failure_callback=None)` – Factory helper that constructs a `GraphService` with optional caching.
- `_extract_path_components(record)` – No docstring.
- `_record_path_edges(path_nodes, relationships, nodes_by_id, edges_by_key)` – No docstring.
- `_ensure_serialized_node(node, nodes_by_id)` – No docstring.
- `_relationship_direction(relationship, source_node)` – No docstring.
- `_build_related_entry(target_serialized, relationships, path_edges)` – No docstring.
- `_append_related_entry(entry, target_id, related_entries, related_order)` – No docstring.
- `_fetch_subsystem_node(tx, name)` – No docstring.
- `_fetch_subsystem_paths(tx, name, depth)` – No docstring.
- `_fetch_artifacts_for_subsystem(tx, name)` – No docstring.
- `_fetch_orphan_nodes(tx, label, skip, limit)` – No docstring.
- `_fetch_node_by_id(tx, label, key, value)` – No docstring.
- `_fetch_node_relationships(tx, label, key, value, direction, limit)` – No docstring.
- `_search_entities(tx, term, limit)` – No docstring.
- `_serialize_related(record, subsystem_node)` – No docstring.
- `_serialize_node(node)` – No docstring.
- `_serialize_relationship(record)` – No docstring.
- `_serialize_value(value)` – No docstring.
- `_ensure_node(value)` – No docstring.
- `_node_element_id(node)` – No docstring.
- `_canonical_node_id(node)` – No docstring.
- `_parse_node_id(node_id)` – No docstring.
- `_encode_cursor(offset)` – No docstring.
- `_decode_cursor(cursor)` – No docstring.
- `_validate_cypher(query)` – No docstring.
- `_strip_literals_and_comments(query)` – No docstring.
- `_tokenize_query(upper_query)` – No docstring.
- `_extract_procedure_calls(tokens)` – No docstring.
- `_deny_cypher(reason, message)` – No docstring.

### Constants
- `T` = TypeVar('T')
- `ORPHAN_DEFAULT_LABELS` = ('DesignDoc', 'SourceFile', 'Chunk', 'TestCase', 'IntegrationMessage')
- `_ALLOWED_PROCEDURE_PREFIXES` = ('DB.SCHEMA.', 'DB.LABELS', 'DB.RELATIONSHIPTYPES', 'DB.INDEXES', 'DB.CONSTRAINTS', 'DB.PROPERTYKEYS')

### Data Flow
- Primary entry points: `get_graph_service`, `_extract_path_components`, `_record_path_edges`, `_ensure_serialized_node`, `_relationship_direction`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, base64, collections, dataclasses, neo4j, threading, time, typing.

### Integration Points
- External: __future__, base64, collections, dataclasses, neo4j, threading, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 29
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 6 of 6
- Try/except blocks: 6
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 981


## gateway/ingest/__init__.py
**Purpose**: Ingestion pipeline components for the knowledge gateway.

**Dependencies**:
- External: None
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Delegates to internal modules: gateway.

### Integration Points
- External: None
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 6


## gateway/ingest/artifacts.py
**Purpose**: Domain models representing artifacts produced during ingestion.

**Dependencies**:
- External: __future__, dataclasses, pathlib, typing
- Internal: None
**Related modules**: None

### Classes
- `Artifact` (bases: object) – Represents a repository artifact prior to chunking.
- `Chunk` (bases: object) – Represents a chunk ready for embedding and indexing.
- `ChunkEmbedding` (bases: object) – Chunk plus embedding vector.

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: __future__, dataclasses, pathlib, typing.

### Integration Points
- External: __future__, dataclasses, pathlib, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 3 of 3
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 41


## gateway/ingest/audit.py
**Purpose**: SQLite-backed audit log utilities for ingestion runs.

**Dependencies**:
- External: __future__, pathlib, sqlite3, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `AuditLogger` (bases: object) – Persist and retrieve ingestion run metadata in SQLite.
  - `__init__(self, db_path)` – No docstring.
  - `record(self, result)` – No docstring.
  - `recent(self, limit=20)` – No docstring.

### Functions
- None

### Constants
- `_SCHEMA` = '\nCREATE TABLE IF NOT EXISTS ingestion_runs (\n    run_id TEXT PRIMARY KEY,\n    profile TEXT,\n    started_at REAL,\n    duration_seconds REAL,\n    artifact_count INTEGER,\n    chunk_count INTEGER,\n    repo_head TEXT,\n    success INTEGER,\n    created_at REAL\n)\n'
- `_SELECT_RECENT` = '\nSELECT run_id, profile, started_at, duration_seconds, artifact_count, chunk_count, repo_head, success, created_at\nFROM ingestion_runs\nORDER BY created_at DESC\nLIMIT ?\n'
- `_INSERT_RUN` = '\nINSERT INTO ingestion_runs (\n    run_id,\n    profile,\n    started_at,\n    duration_seconds,\n    artifact_count,\n    chunk_count,\n    repo_head,\n    success,\n    created_at\n) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n'

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pathlib, sqlite3, time, typing.

### Integration Points
- External: __future__, pathlib, sqlite3, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 1 of 1
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 101


## gateway/ingest/chunking.py
**Purpose**: Chunk source artifacts into overlapping windows for indexing.

**Dependencies**:
- External: __future__, collections, hashlib, math, pathlib, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `Chunker` (bases: object) – Split artifacts into overlapping textual chunks.
  - `__init__(self, window=DEFAULT_WINDOW, overlap=DEFAULT_OVERLAP)` – No docstring.
  - `split(self, artifact)` – No docstring.
  - `estimate_chunk_count(path, text, window=DEFAULT_WINDOW, overlap=DEFAULT_OVERLAP)` – No docstring.

### Functions
- `_derive_namespace(path)` – Infer a namespace from a file path for tagging chunks.
- `_build_tags(extra_metadata)` – Collect tag-like signals from artifact metadata.

### Constants
- `DEFAULT_WINDOW` = 1000
- `DEFAULT_OVERLAP` = 200

### Data Flow
- Primary entry points: `_derive_namespace`, `_build_tags`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, hashlib, math, pathlib, typing.

### Integration Points
- External: __future__, collections, hashlib, math, pathlib, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 110


## gateway/ingest/cli.py
**Purpose**: Command-line helpers for triggering and inspecting ingestion runs.

**Dependencies**:
- External: __future__, argparse, collections, datetime, logging, pathlib, rich
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_ensure_maintainer_scope(settings)` – Abort execution if maintainer credentials are missing during auth.
- `build_parser()` – Create an argument parser for the ingestion CLI.
- `rebuild(profile, repo, dry_run, dummy_embeddings, incremental, settings=None)` – Execute a full ingestion pass.
- `audit_history(limit, output_json, settings=None)` – Display recent ingestion runs from the audit ledger.
- `_render_audit_table(entries)` – Render recent audit entries as a Rich table.
- `_format_timestamp(raw)` – Format timestamps from the audit ledger for display.
- `_coerce_int(value)` – Attempt to interpret the value as an integer.
- `_coerce_float(value)` – Attempt to interpret the value as a floating point number.
- `main(argv=None)` – Entry point for the CLI.

### Constants
- None

### Data Flow
- Primary entry points: `_ensure_maintainer_scope`, `build_parser`, `rebuild`, `audit_history`, `_render_audit_table`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, argparse, collections, datetime, logging, pathlib, rich.

### Integration Points
- External: __future__, argparse, collections, datetime, logging, pathlib, rich
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 9 of 9
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 249


## gateway/ingest/coverage.py
**Purpose**: Utilities for writing ingestion coverage reports.

**Dependencies**:
- External: __future__, contextlib, datetime, json, pathlib, time
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `write_coverage_report(result, config, output_path, history_limit=None)` – Persist coverage metrics derived from an ingestion result.
- `_write_history_snapshot(payload, reports_dir, history_limit)` – Write coverage history snapshots and prune old entries.

### Constants
- None

### Data Flow
- Primary entry points: `write_coverage_report`, `_write_history_snapshot`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, contextlib, datetime, json, pathlib, time.

### Integration Points
- External: __future__, contextlib, datetime, json, pathlib, time
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 83


## gateway/ingest/discovery.py
**Purpose**: Repository discovery helpers for ingestion pipeline.

**Dependencies**:
- External: __future__, collections, dataclasses, fnmatch, json, logging, pathlib, re, subprocess, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `DiscoveryConfig` (bases: object) – Runtime knobs influencing which artifacts are discovered.

### Functions
- `discover(config)` – Yield textual artifacts from the repository.
- `_should_include(path, repo_root, include_patterns)` – No docstring.
- `_is_textual(path)` – No docstring.
- `_infer_artifact_type(path, repo_root)` – No docstring.
- `_lookup_git_metadata(path, repo_root)` – No docstring.
- `_load_subsystem_catalog(repo_root)` – No docstring.
- `_detect_source_prefixes(repo_root)` – Infer source package prefixes (e.g. ``("src", "gateway")``).
- `_collect_pyproject_prefixes(root, prefixes)` – No docstring.
- `_load_pyproject(path)` – No docstring.
- `_collect_poetry_prefixes(tool_cfg, prefixes)` – No docstring.
- `_collect_project_prefixes(project_cfg, prefixes)` – No docstring.
- `_collect_setuptools_prefixes(tool_cfg, prefixes)` – No docstring.
- `_collect_src_directory_prefixes(root, prefixes)` – No docstring.
- `_add_prefix(prefixes, include, base='src')` – No docstring.
- `_ensure_str_list(value)` – No docstring.
- `_infer_subsystem(path, repo_root, source_prefixes)` – No docstring.
- `_normalize_subsystem_name(value)` – No docstring.
- `_match_catalog_entry(path, repo_root, catalog)` – No docstring.
- `_iter_metadata_patterns(metadata)` – No docstring.
- `_pattern_matches(target, pattern)` – No docstring.
- `dump_artifacts(artifacts)` – Serialize artifacts for debugging or dry-run output.

### Constants
- `_TEXTUAL_SUFFIXES` = {'.md', '.txt', '.py', '.proto', '.yml', '.yaml', '.json', '.ini', '.cfg', '.toml', '.sql'}
- `_MESSAGE_PATTERN` = re.compile('[A-Z]\\w*Message')
- `_TELEMETRY_PATTERN` = re.compile('Telemetry\\w+')
- `_SUBSYSTEM_METADATA_CACHE` = {}
- `_SOURCE_PREFIX_CACHE` = {}

### Data Flow
- Primary entry points: `discover`, `_should_include`, `_is_textual`, `_infer_artifact_type`, `_lookup_git_metadata`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, dataclasses, fnmatch, json, logging, pathlib, re, subprocess, typing.

### Integration Points
- External: __future__, collections, dataclasses, fnmatch, json, logging, pathlib, re, subprocess, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 21
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 6
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 424


## gateway/ingest/embedding.py
**Purpose**: Embedding helpers used during ingestion.

**Dependencies**:
- External: __future__, collections, functools, logging, sentence_transformers
- Internal: None
**Related modules**: None

### Classes
- `Embedder` (bases: object) – Wrapper around sentence-transformers for configurable embeddings.
  - `__init__(self, model_name)` – No docstring.
  - `dimension(self)` – No docstring.
  - `encode(self, texts)` – No docstring.
  - `_load_model(model_name)` – No docstring.
- `DummyEmbedder` (bases: Embedder) – Deterministic embedder for dry-runs and tests.
  - `__init__(self)` – No docstring.
  - `dimension(self)` – No docstring.
  - `encode(self, texts)` – No docstring.

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: __future__, collections, functools, logging, sentence_transformers.

### Integration Points
- External: __future__, collections, functools, logging, sentence_transformers
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 2 of 2
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 63


## gateway/ingest/lifecycle.py
**Purpose**: Lifecycle reporting helpers for ingestion outputs.

**Dependencies**:
- External: __future__, collections, contextlib, dataclasses, datetime, json, neo4j, pathlib, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `LifecycleConfig` (bases: object) – Configuration values that influence lifecycle report generation.

### Functions
- `write_lifecycle_report(result, config, graph_service)` – Persist lifecycle insights derived from the most recent ingest run.
- `build_graph_service(driver, database, cache_ttl)` – Construct a graph service with sensible defaults for lifecycle usage.
- `summarize_lifecycle(payload)` – Produce a summarized view of lifecycle data for reporting.
- `_fetch_isolated_nodes(graph_service)` – Collect isolated graph nodes grouped by label.
- `_find_stale_docs(artifacts, stale_days, now)` – Identify design documents that are older than the stale threshold.
- `_find_missing_tests(artifacts)` – Determine subsystems lacking corresponding tests.
- `_write_history_snapshot(payload, reports_dir, history_limit)` – Write lifecycle history to disk while enforcing retention.
- `_coerce_float(value)` – Coerce numeric-like values to float when possible.
- `_lifecycle_counts(isolated, stale_docs, missing_tests, removed)` – Aggregate lifecycle metrics into counters.

### Constants
- `SECONDS_PER_DAY` = 60 * 60 * 24

### Data Flow
- Primary entry points: `write_lifecycle_report`, `build_graph_service`, `summarize_lifecycle`, `_fetch_isolated_nodes`, `_find_stale_docs`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, contextlib, dataclasses, datetime, json, neo4j, pathlib, time, typing.

### Integration Points
- External: __future__, collections, contextlib, dataclasses, datetime, json, neo4j, pathlib, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 9 of 9
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 244


## gateway/ingest/neo4j_writer.py
**Purpose**: Write ingestion artifacts and chunks into Neo4j.

**Dependencies**:
- External: __future__, collections, logging, neo4j
- Internal: gateway
**Related modules**: gateway

### Classes
- `Neo4jWriter` (bases: object) – Persist artifacts and derived data into a Neo4j database.
  - `__init__(self, driver, database='knowledge')` – No docstring.
  - `ensure_constraints(self)` – No docstring.
  - `sync_artifact(self, artifact)` – No docstring.
  - `sync_chunks(self, chunk_embeddings)` – No docstring.
  - `delete_artifact(self, path)` – No docstring.

### Functions
- `_artifact_label(artifact)` – Map artifact types to Neo4j labels.
- `_label_for_type(artifact_type)` – Return the default label for the given artifact type.
- `_relationship_for_label(label)` – Return the relationship used to link artifacts to subsystems.
- `_clean_string_list(values)` – No docstring.
- `_normalize_subsystem_name(value)` – No docstring.
- `_extract_dependencies(metadata)` – No docstring.
- `_subsystem_properties(metadata)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_artifact_label`, `_label_for_type`, `_relationship_for_label`, `_clean_string_list`, `_normalize_subsystem_name`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, logging, neo4j.

### Integration Points
- External: __future__, collections, logging, neo4j
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 7
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 250


## gateway/ingest/pipeline.py
**Purpose**: Pipeline orchestrations for ingestion, chunking, and persistence.

**Dependencies**:
- External: __future__, collections, concurrent, contextlib, dataclasses, filelock, hashlib, json, logging, opentelemetry, os, pathlib, subprocess, time, uuid
- Internal: gateway
**Related modules**: gateway

### Classes
- `IngestionConfig` (bases: object) – Configuration options controlling ingestion behaviour.
- `IngestionResult` (bases: object) – Summary of outputs emitted by an ingestion run.
- `IngestionPipeline` (bases: object) – Execute the ingestion workflow end-to-end.
  - `__init__(self, qdrant_writer, neo4j_writer, config)` – No docstring.
  - `run(self)` – No docstring.
  - `_build_embedder(self)` – No docstring.
  - `_encode_batch(self, embedder, chunks)` – No docstring.
  - `_build_embeddings(self, chunks, vectors)` – No docstring.
  - `_persist_embeddings(self, embeddings)` – No docstring.
  - `_handle_stale_artifacts(self, previous, current, profile)` – No docstring.
  - `_delete_artifact_from_backends(self, path)` – No docstring.
  - `_load_artifact_ledger(self)` – No docstring.
  - `_read_ledger_file(self, ledger_path)` – No docstring.
  - `_write_artifact_ledger(self, entries)` – No docstring.
  - `_atomic_write(self, ledger_path, payload)` – No docstring.

### Functions
- `_current_repo_head(repo_root)` – No docstring.
- `_coerce_int(value)` – No docstring.
- `_coerce_float(value)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_current_repo_head`, `_coerce_int`, `_coerce_float`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, concurrent, contextlib, dataclasses, filelock, hashlib, json, logging, opentelemetry, os, pathlib, subprocess, time, uuid.

### Integration Points
- External: __future__, collections, concurrent, contextlib, dataclasses, filelock, hashlib, json, logging, opentelemetry, os, pathlib, subprocess, time, uuid
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 3 of 3
- Try/except blocks: 12
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 529


## gateway/ingest/qdrant_writer.py
**Purpose**: Helpers for writing chunk embeddings into Qdrant collections.

**Dependencies**:
- External: __future__, collections, logging, qdrant_client, time, uuid
- Internal: gateway
**Related modules**: gateway

### Classes
- `QdrantWriter` (bases: object) – Lightweight adapter around the Qdrant client.
  - `__init__(self, client, collection_name)` – No docstring.
  - `ensure_collection(self, vector_size, retries=3, retry_backoff=0.5)` – No docstring.
  - `reset_collection(self, vector_size)` – No docstring.
  - `upsert_chunks(self, chunks)` – No docstring.
  - `delete_artifact(self, artifact_path)` – No docstring.
  - `_collection_exists(self)` – No docstring.
  - `_create_collection(self, vector_size)` – No docstring.

### Functions
- None

### Constants
- None

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, logging, qdrant_client, time, uuid.

### Integration Points
- External: __future__, collections, logging, qdrant_client, time, uuid
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 1 of 1
- Try/except blocks: 3
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 163


## gateway/ingest/service.py
**Purpose**: High-level orchestration routines for running ingestion.

**Dependencies**:
- External: __future__, logging, neo4j, pathlib, qdrant_client
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `execute_ingestion(settings, profile, repo_override=None, dry_run=None, use_dummy_embeddings=None, incremental=None, graph_manager=None, qdrant_manager=None)` – Run ingestion using shared settings and return result.

### Constants
- None

### Data Flow
- Primary entry points: `execute_ingestion`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, logging, neo4j, pathlib, qdrant_client.

### Integration Points
- External: __future__, logging, neo4j, pathlib, qdrant_client
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 145


## gateway/lifecycle/__init__.py
**Purpose**: Lifecycle reporting package.

**Dependencies**:
- External: None
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Lightweight module with minimal data flow; acts as namespace or configuration container.

### Integration Points
- External: None
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 4


## gateway/lifecycle/cli.py
**Purpose**: Command-line utilities for inspecting lifecycle health reports.

**Dependencies**:
- External: __future__, argparse, collections, datetime, json, pathlib, rich
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `build_parser()` – Create the CLI argument parser shared across entrypoints.
- `render_table(payload)` – Pretty-print the lifecycle report payload using Rich tables.
- `_render_isolated_nodes(value)` – Render the isolated node section when data is present.
- `_render_stale_docs(value)` – Render the stale documentation summary rows.
- `_render_missing_tests(value)` – Render subsystems missing tests in a tabular format.
- `_format_timestamp(value)` – Convert a timestamp-like input into an ISO formatted string.
- `main(argv=None)` – CLI entry point for lifecycle reporting.

### Constants
- None

### Data Flow
- Primary entry points: `build_parser`, `render_table`, `_render_isolated_nodes`, `_render_stale_docs`, `_render_missing_tests`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, argparse, collections, datetime, json, pathlib, rich.

### Integration Points
- External: __future__, argparse, collections, datetime, json, pathlib, rich
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 7 of 7
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 134


## gateway/mcp/__init__.py
**Purpose**: Model Context Protocol server integration for the knowledge gateway.

**Dependencies**:
- External: config, server
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: config, server.

### Integration Points
- External: config, server
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 7


## gateway/mcp/backup.py
**Purpose**: Backup helpers for the MCP server.

**Dependencies**:
- External: __future__, asyncio, config, pathlib, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `async trigger_backup(settings)` – Invoke the km-backup helper and return the resulting archive metadata.

### Constants
- None

### Data Flow
- Primary entry points: `trigger_backup`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, asyncio, config, pathlib, typing.

### Integration Points
- External: __future__, asyncio, config, pathlib, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 31


## gateway/mcp/cli.py
**Purpose**: Command-line entry point for the MCP server.

**Dependencies**:
- External: __future__, argparse, collections, config, logging, server, sys
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `build_parser()` – Return the CLI parser for launching the MCP server.
- `main(argv=None)` – Entry point for the MCP server management CLI.

### Constants
- `_TRANSPORT_CHOICES` = ['stdio', 'http', 'sse', 'streamable-http']

### Data Flow
- Primary entry points: `build_parser`, `main`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, argparse, collections, config, logging, server, sys.

### Integration Points
- External: __future__, argparse, collections, config, logging, server, sys
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 96


## gateway/mcp/client.py
**Purpose**: HTTP client for interacting with the gateway API.

**Dependencies**:
- External: __future__, collections, config, exceptions, httpx, json, logging, types, typing, urllib
- Internal: gateway
**Related modules**: gateway

### Classes
- `GatewayClient` (bases: object) – Thin async wrapper over the gateway REST API.
  - `__init__(self, settings)` – No docstring.
  - `async __aenter__(self)` – No docstring.
  - `async __aexit__(self, exc_type, exc, tb)` – No docstring.
  - `settings(self)` – No docstring.
  - `async search(self, payload)` – No docstring.
  - `async graph_node(self, node_id, relationships, limit)` – No docstring.
  - `async graph_subsystem(self, name, depth, include_artifacts, cursor, limit)` – No docstring.
  - `async graph_search(self, term, limit)` – No docstring.
  - `async coverage_summary(self)` – No docstring.
  - `async lifecycle_report(self)` – No docstring.
  - `async audit_history(self, limit=10)` – No docstring.
  - `async _request(self, method, path, json_payload=None, params=None, require_admin=False, require_reader=False)` – No docstring.

### Functions
- `_extract_error_detail(response)` – Extract a human-readable error detail from an HTTP response.
- `_safe_json(response)` – Safely decode a JSON response, returning ``None`` on failure.
- `_quote_segment(value)` – No docstring.
- `_expect_dict(data, operation)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_extract_error_detail`, `_safe_json`, `_quote_segment`, `_expect_dict`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, config, exceptions, httpx, json, logging, types, typing, urllib.

### Integration Points
- External: __future__, collections, config, exceptions, httpx, json, logging, types, typing, urllib
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 234


## gateway/mcp/config.py
**Purpose**: Configuration for the MCP adapter.

**Dependencies**:
- External: __future__, pathlib, pydantic, pydantic_settings, typing
- Internal: None
**Related modules**: None

### Classes
- `MCPSettings` (bases: BaseSettings) – Settings controlling the MCP server runtime.

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: __future__, pathlib, pydantic, pydantic_settings, typing.

### Integration Points
- External: __future__, pathlib, pydantic, pydantic_settings, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 99


## gateway/mcp/exceptions.py
**Purpose**: Custom exceptions for the MCP adapter.

**Dependencies**:
- External: __future__
- Internal: gateway
**Related modules**: gateway

### Classes
- `MCPAdapterError` (bases: Exception) – Base error raised by the MCP bridge.
- `GatewayRequestError` (bases: MCPAdapterError) – Raised when the gateway API returns an error response.
  - `__init__(self, status_code, detail, payload=None)` – No docstring.
- `MissingTokenError` (bases: MCPAdapterError) – Raised when a privileged operation lacks an authentication token.
  - `__init__(self, scope)` – No docstring.
- `BackupExecutionError` (bases: _BackupExecutionError, MCPAdapterError) – Raised when the backup helper fails to produce an archive.

### Functions
- None

### Constants
- None

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__.

### Integration Points
- External: __future__
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 4 of 4
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 41


## gateway/mcp/feedback.py
**Purpose**: Feedback logging utilities used by MCP tools.

**Dependencies**:
- External: __future__, asyncio, collections, config, datetime, json, pathlib, typing
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `async record_feedback(settings, request_id, chunk_id, vote, note, context)` – Append a manual feedback entry to the state directory.
- `_append_line(path, line)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `record_feedback`, `_append_line`
- Touches external libraries: __future__, asyncio, collections, config, datetime, json, pathlib, typing.

### Integration Points
- External: __future__, asyncio, collections, config, datetime, json, pathlib, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 50


## gateway/mcp/ingest.py
**Purpose**: Helpers for managing ingestion workflows via MCP.

**Dependencies**:
- External: __future__, asyncio, config, dataclasses, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `async trigger_ingest(settings, profile, dry_run, use_dummy_embeddings)` – Execute an ingestion run in a worker thread and return a serialisable summary.
- `async latest_ingest_status(history, profile)` – Return the newest ingest record optionally filtered by profile.

### Constants
- None

### Data Flow
- Primary entry points: `trigger_ingest`, `latest_ingest_status`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, asyncio, config, dataclasses, typing.

### Integration Points
- External: __future__, asyncio, config, dataclasses, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 57


## gateway/mcp/server.py
**Purpose**: FastMCP server exposing the knowledge gateway.

**Dependencies**:
- External: __future__, backup, client, collections, config, contextlib, datetime, exceptions, fastmcp, feedback, functools, ingest, json, pathlib, storetext, textwrap, time, typing, upload
- Internal: gateway
**Related modules**: gateway

### Classes
- `MCPServerState` (bases: object) – Holds shared state for the MCP server lifespan.
  - `__init__(self, settings)` – No docstring.
  - `require_client(self)` – No docstring.
  - `lifespan(self)` – No docstring.

### Functions
- `build_server(settings=None)` – Create a FastMCP server wired to the gateway API.
- `async _report_info(context, message)` – No docstring.
- `async _report_error(context, message)` – No docstring.
- `_record_success(tool, start)` – No docstring.
- `_record_failure(tool, exc, start)` – No docstring.
- `_clamp(value, minimum, maximum)` – No docstring.
- `_normalise_filters(payload)` – No docstring.
- `_resolve_usage(tool)` – No docstring.
- `_ensure_maintainer_scope(settings)` – No docstring.
- `_append_audit_entry(settings, tool, payload)` – No docstring.
- `_load_help_document()` – No docstring.
- `_initialise_metric_labels()` – No docstring.

### Constants
- `TOOL_USAGE` = {'km-search': {'description': 'Hybrid search across the knowledge base with optional filters and graph context', 'details': dedent('\n            Required: `query` text. Optional: `limit` (default 10, max 25), `include_graph`, structured `filters`, `sort_by_vector`.\n            Example: `/sys mcp run duskmantle km-search --query "ingest pipeline" --limit 5`.\n            Returns scored chunks with metadata and optional graph enrichments.\n            ').strip()}, 'km-graph-node': {'description': 'Fetch a graph node by ID and inspect incoming/outgoing relationships', 'details': dedent('\n            Required: `node_id` such as `DesignDoc:docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md`.\n            Optional: `relationships` (`outgoing`, `incoming`, `all`, `none`) and `limit` (default 50, max 200).\n            Example: `/sys mcp run duskmantle km-graph-node --node-id "Code:gateway/mcp/server.py"`.\n            ').strip()}, 'km-graph-subsystem': {'description': 'Review a subsystem, related artifacts, and connected subsystems', 'details': dedent('\n            Required: `name` of the subsystem.\n            Optional: `depth` (default 1, max 5), `include_artifacts`, pagination `cursor`, `limit` (default 25, max 100).\n            Example: `/sys mcp run duskmantle km-graph-subsystem --name Kasmina --depth 2`.\n            ').strip()}, 'km-graph-search': {'description': 'Search graph entities (artifacts, subsystems, teams) by term', 'details': dedent('\n            Required: `term` to match against graph nodes.\n            Optional: `limit` (default 20, max 50).\n            Example: `/sys mcp run duskmantle km-graph-search --term coverage`.\n            ').strip()}, 'km-coverage-summary': {'description': 'Summarise ingestion coverage (artifact and chunk counts, freshness)', 'details': dedent('\n            No parameters. Returns the same payload as `/coverage` including summary counts and stale thresholds.\n            Example: `/sys mcp run duskmantle km-coverage-summary`.\n            ').strip()}, 'km-lifecycle-report': {'description': 'Summarise isolated nodes, stale docs, and missing tests', 'details': dedent('\n            No parameters. Mirrors the `/lifecycle` endpoint and highlights isolated graph nodes, stale design docs, and subsystems missing tests.\n            Example: `/sys mcp run duskmantle km-lifecycle-report`.\n            ').strip()}, 'km-ingest-status': {'description': 'Show the most recent ingest run (profile, status, timestamps)', 'details': dedent('\n            Optional: `profile` to scope results to a specific ingest profile.\n            Example: `/sys mcp run duskmantle km-ingest-status --profile demo`.\n            Returns `status: ok` with run metadata or `status: not_found` when history is empty.\n            ').strip()}, 'km-ingest-trigger': {'description': 'Kick off a manual ingest run (full rebuild via gateway-ingest)', 'details': dedent('\n            Optional: `profile` (defaults to MCP settings), `dry_run`, `use_dummy_embeddings`.\n            Example: `/sys mcp run duskmantle km-ingest-trigger --profile local --dry-run true`.\n            Requires maintainer token (`KM_ADMIN_TOKEN`).\n            ').strip()}, 'km-backup-trigger': {'description': 'Create a compressed backup of gateway state (Neo4j/Qdrant data)', 'details': dedent('\n            No parameters. Returns archive path and metadata.\n            Example: `/sys mcp run duskmantle km-backup-trigger`.\n            Requires maintainer token; mirrors the `bin/km-backup` helper.\n            ').strip()}, 'km-feedback-submit': {'description': 'Vote on a search result and attach optional notes for training data', 'details': dedent('\n            Required: `request_id` (search request) and `chunk_id` (result identifier).\n            Optional: numeric `vote` (-1.0 to 1.0) and freeform `note`.\n            Example: `/sys mcp run duskmantle km-feedback-submit --request-id req123 --chunk-id chunk456 --vote 1`.\n            Maintainer token required when auth is enforced.\n            ').strip()}, 'km-upload': {'description': 'Copy an existing file into the knowledge workspace and optionally trigger ingest', 'details': dedent('\n            Required: `source_path` (file visible to the MCP host). Optional: `destination` (relative path inside the\n            content root), `overwrite`, `ingest`. Default behaviour stores the file under the configured docs directory.\n            Example: `/sys mcp run duskmantle km-upload --source-path ./notes/design.md --destination docs/uploads/`.\n            Maintainer scope recommended because this writes to the repository volume and may trigger ingestion.\n            ').strip()}, 'km-storetext': {'description': 'Persist raw text as a document within the knowledge workspace', 'details': dedent('\n            Required: `content` (text body). Optional: `title`, `destination`, `subsystem`, `tags`, `metadata` map,\n            `overwrite`, `ingest`. Defaults write markdown into the configured docs directory with YAML front matter\n            derived from the provided metadata.\n            Example: `/sys mcp run duskmantle km-storetext --title "Release Notes" --content "## Summary"`.\n            Maintainer scope recommended because this writes to the repository volume.\n            ').strip()}}
- `HELP_DOC_PATH` = Path(__file__).resolve().parents[2] / 'docs' / 'MCP_INTERFACE_SPEC.md'

### Data Flow
- Primary entry points: `build_server`, `_report_info`, `_report_error`, `_record_success`, `_record_failure`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, backup, client, collections, config, contextlib, datetime, exceptions, fastmcp, feedback, functools, ingest, json, pathlib, storetext, textwrap, time, typing, upload.

### Integration Points
- External: __future__, backup, client, collections, config, contextlib, datetime, exceptions, fastmcp, feedback, functools, ingest, json, pathlib, storetext, textwrap, time, typing, upload
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 12
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 16
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 670


## gateway/mcp/storetext.py
**Purpose**: Handlers for storing text via MCP.

**Dependencies**:
- External: __future__, datetime, ingest, pathlib, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_build_filename(title)` – No docstring.
- `_normalise_destination(destination, default_dir, filename)` – No docstring.
- `_compose_content(title, subsystem, tags, metadata, body)` – No docstring.
- `async handle_storetext(settings, content, title, destination, subsystem, tags, metadata, overwrite, ingest)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_build_filename`, `_normalise_destination`, `_compose_content`, `handle_storetext`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, ingest, pathlib, typing.

### Integration Points
- External: __future__, datetime, ingest, pathlib, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 126


## gateway/mcp/upload.py
**Purpose**: Handlers for MCP file uploads.

**Dependencies**:
- External: __future__, ingest, pathlib, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `async handle_upload(settings, source_path, destination, overwrite, ingest)` – Copy ``source_path`` into the configured content root and optionally trigger ingest.
- `_resolve_destination(destination, default_dir, filename)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `handle_upload`, `_resolve_destination`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, ingest, pathlib, typing.

### Integration Points
- External: __future__, ingest, pathlib, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 78


## gateway/mcp/utils/__init__.py
**Purpose**: Implements   init  

**Dependencies**:
- External: None
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Lightweight module with minimal data flow; acts as namespace or configuration container.

### Integration Points
- External: None
- Internal: None

### Code Quality Notes
- Module docstring present: no
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 1


## gateway/mcp/utils/files.py
**Purpose**: Shared helpers for MCP content management.

**Dependencies**:
- External: __future__, collections, dataclasses, os, pathlib, re, shutil, unicodedata
- Internal: None
**Related modules**: None

### Classes
- `DocumentCopyResult` (bases: object) – Result of an attempted document copy.
- `DocumentCopyError` (bases: Exception) – Raised when a copy operation fails fatally.

### Functions
- `slugify(value, fallback='document')` – Create a filesystem-friendly slug.
- `is_supported_document(path)` – Return ``True`` if the path has a supported document extension.
- `_assert_within_root(root, candidate)` – Ensure ``candidate`` is within ``root`` to prevent path traversal.
- `sweep_documents(root, target, dry_run=False, overwrite=False)` – Copy supported documents under ``root`` into ``target``.
- `copy_into_root(source, root, destination=None, overwrite=False)` – Copy ``source`` into ``root``.
- `write_text_document(content, root, relative_path, overwrite=False, encoding='utf-8')` – Write ``content`` to ``root / relative_path`` ensuring safety.

### Constants
- `SUPPORTED_EXTENSIONS` = {'.md', '.docx', '.txt', '.doc', '.pdf'}
- `_SLUG_REGEX` = re.compile('[^a-z0-9]+')

### Data Flow
- Primary entry points: `slugify`, `is_supported_document`, `_assert_within_root`, `sweep_documents`, `copy_into_root`
- Touches external libraries: __future__, collections, dataclasses, os, pathlib, re, shutil, unicodedata.

### Integration Points
- External: __future__, collections, dataclasses, os, pathlib, re, shutil, unicodedata
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 6 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 2 of 2
- Try/except blocks: 2
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 199


## gateway/observability/__init__.py
**Purpose**: Observability utilities (metrics, logging, tracing).

**Dependencies**:
- External: logging, metrics, tracing
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: logging, metrics, tracing.

### Integration Points
- External: logging, metrics, tracing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 74


## gateway/observability/logging.py
**Purpose**: Structured logging configuration for the gateway.

**Dependencies**:
- External: __future__, logging, pythonjsonlogger, sys, typing
- Internal: None
**Related modules**: None

### Classes
- `IngestAwareFormatter` (bases: JsonFormatter) – JSON formatter that enforces consistent keys.
  - `add_fields(self, log_record, record, message_dict)` – No docstring.

### Functions
- `configure_logging()` – Configure root logging with a JSON formatter once per process.

### Constants
- `_LOG_CONFIGURED` = False

### Data Flow
- Primary entry points: `configure_logging`
- Touches external libraries: __future__, logging, pythonjsonlogger, sys, typing.

### Integration Points
- External: __future__, logging, pythonjsonlogger, sys, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 48


## gateway/observability/metrics.py
**Purpose**: Prometheus metric definitions for the knowledge gateway.

**Dependencies**:
- External: __future__, prometheus_client
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- `BACKUP_RUNS_TOTAL` = Counter('km_backup_runs_total', 'Backup job outcomes partitioned by result', labelnames=['result'])
- `BACKUP_LAST_STATUS` = Gauge('km_backup_last_status', 'Last backup status (1=success,0=failure)')
- `BACKUP_LAST_SUCCESS_TIMESTAMP` = Gauge('km_backup_last_success_timestamp', 'Unix timestamp of the last successful backup run')
- `BACKUP_RETENTION_DELETES_TOTAL` = Counter('km_backup_retention_deletes_total', 'Number of backup archives removed by retention pruning')
- `GRAPH_DEPENDENCY_STATUS` = Gauge('km_graph_dependency_status', 'Neo4j connectivity status (1=healthy,0=unavailable)')
- `GRAPH_DEPENDENCY_LAST_SUCCESS` = Gauge('km_graph_dependency_last_success_timestamp', 'Unix timestamp of the last successful Neo4j heartbeat')
- `QDRANT_DEPENDENCY_STATUS` = Gauge('km_qdrant_dependency_status', 'Qdrant connectivity status (1=healthy,0=unavailable)')
- `QDRANT_DEPENDENCY_LAST_SUCCESS` = Gauge('km_qdrant_dependency_last_success_timestamp', 'Unix timestamp of the last successful Qdrant heartbeat')
- `INGEST_DURATION_SECONDS` = Histogram('km_ingest_duration_seconds', 'Duration of ingestion runs', labelnames=['profile', 'status'])
- `INGEST_ARTIFACTS_TOTAL` = Counter('km_ingest_artifacts_total', 'Number of artifacts processed', labelnames=['profile', 'artifact_type'])
- `INGEST_CHUNKS_TOTAL` = Counter('km_ingest_chunks_total', 'Number of chunks generated', labelnames=['profile'])
- `INGEST_LAST_RUN_STATUS` = Gauge('km_ingest_last_run_status', 'Last ingestion status (1=success,0=failure)', labelnames=['profile'])
- `INGEST_LAST_RUN_TIMESTAMP` = Gauge('km_ingest_last_run_timestamp', 'Unix timestamp of last ingestion run', labelnames=['profile'])
- `COVERAGE_LAST_RUN_STATUS` = Gauge('km_coverage_last_run_status', 'Last coverage report generation status (1=success,0=failure)', labelnames=['profile'])
- `COVERAGE_LAST_RUN_TIMESTAMP` = Gauge('km_coverage_last_run_timestamp', 'Unix timestamp of last coverage report', labelnames=['profile'])
- `COVERAGE_MISSING_ARTIFACTS` = Gauge('km_coverage_missing_artifacts_total', 'Number of artifacts without chunks discovered in last coverage report', labelnames=['profile'])
- `COVERAGE_STALE_ARTIFACTS` = Gauge('km_coverage_stale_artifacts_total', 'Number of stale or removed artifacts recorded in last coverage report', labelnames=['profile'])
- `INGEST_STALE_RESOLVED_TOTAL` = Counter('km_ingest_stale_resolved_total', 'Count of stale artifacts removed from backends during ingestion', labelnames=['profile'])
- `INGEST_SKIPS_TOTAL` = Counter('km_ingest_skips_total', 'Ingestion runs skipped partitioned by reason', labelnames=['reason'])
- `SEARCH_REQUESTS_TOTAL` = Counter('km_search_requests_total', 'Search API requests partitioned by outcome', labelnames=['status'])
- `SEARCH_GRAPH_CACHE_EVENTS` = Counter('km_search_graph_cache_events_total', 'Graph context cache events during search', labelnames=['status'])
- `SEARCH_GRAPH_SKIPPED_TOTAL` = Counter('km_search_graph_skipped_total', 'Number of search results where graph enrichment was skipped', labelnames=['reason'])
- `SEARCH_FEEDBACK_ROTATIONS_TOTAL` = Counter('km_feedback_rotations_total', 'Number of times the search feedback log rotated due to size limits')
- `SEARCH_FEEDBACK_LOG_BYTES` = Gauge('km_feedback_log_bytes', 'Current size of the primary search feedback log in bytes')
- `SEARCH_GRAPH_LOOKUP_SECONDS` = Histogram('km_search_graph_lookup_seconds', 'Latency of graph lookups for search enrichment')
- `SEARCH_SCORE_DELTA` = Histogram('km_search_adjusted_minus_vector', 'Distribution of adjusted minus vector scores')
- `GRAPH_CYPHER_DENIED_TOTAL` = Counter('km_graph_cypher_denied_total', 'Maintainer Cypher requests blocked by read-only safeguards', labelnames=['reason'])
- `GRAPH_MIGRATION_LAST_STATUS` = Gauge('km_graph_migration_last_status', 'Graph migration result (1=success, 0=failure, -1=skipped)')
- `GRAPH_MIGRATION_LAST_TIMESTAMP` = Gauge('km_graph_migration_last_timestamp', 'Unix timestamp of the last graph migration attempt')
- `SCHEDULER_RUNS_TOTAL` = Counter('km_scheduler_runs_total', 'Scheduled ingestion job outcomes partitioned by result', labelnames=['result'])
- `SCHEDULER_LAST_SUCCESS_TIMESTAMP` = Gauge('km_scheduler_last_success_timestamp', 'Unix timestamp of the last successful scheduled ingestion run')
- `COVERAGE_HISTORY_SNAPSHOTS` = Gauge('km_coverage_history_snapshots', 'Number of retained coverage history snapshots', labelnames=['profile'])
- `WATCH_RUNS_TOTAL` = Counter('km_watch_runs_total', 'Watcher outcomes partitioned by result', labelnames=['result'])
- `LIFECYCLE_LAST_RUN_STATUS` = Gauge('km_lifecycle_last_run_status', 'Lifecycle report generation status (1=success,0=failure)', labelnames=['profile'])
- `LIFECYCLE_LAST_RUN_TIMESTAMP` = Gauge('km_lifecycle_last_run_timestamp', 'Unix timestamp of the last lifecycle report', labelnames=['profile'])
- `LIFECYCLE_STALE_DOCS_TOTAL` = Gauge('km_lifecycle_stale_docs_total', 'Number of stale design docs in the latest lifecycle report', labelnames=['profile'])
- `LIFECYCLE_ISOLATED_NODES_TOTAL` = Gauge('km_lifecycle_isolated_nodes_total', 'Number of isolated graph nodes recorded in the latest lifecycle report', labelnames=['profile'])
- `LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL` = Gauge('km_lifecycle_missing_test_subsystems_total', 'Number of subsystems missing tests in the latest lifecycle report', labelnames=['profile'])
- `LIFECYCLE_REMOVED_ARTIFACTS_TOTAL` = Gauge('km_lifecycle_removed_artifacts_total', 'Number of recently removed artifacts recorded in the latest lifecycle report', labelnames=['profile'])
- `LIFECYCLE_HISTORY_SNAPSHOTS` = Gauge('km_lifecycle_history_snapshots', 'Number of retained lifecycle history snapshots', labelnames=['profile'])
- `MCP_REQUESTS_TOTAL` = Counter('km_mcp_requests_total', 'MCP tool invocations partitioned by result', labelnames=['tool', 'result'])
- `MCP_REQUEST_SECONDS` = Histogram('km_mcp_request_seconds', 'Latency of MCP tool handlers', labelnames=['tool'])
- `MCP_FAILURES_TOTAL` = Counter('km_mcp_failures_total', 'MCP tool failures partitioned by error type', labelnames=['tool', 'error'])
- `MCP_UPLOAD_TOTAL` = Counter('km_mcp_upload_total', 'MCP upload tool invocations partitioned by result', labelnames=['result'])
- `MCP_STORETEXT_TOTAL` = Counter('km_mcp_storetext_total', 'MCP storetext tool invocations partitioned by result', labelnames=['result'])
- `UI_REQUESTS_TOTAL` = Counter('km_ui_requests_total', 'Embedded UI visits partitioned by view', labelnames=['view'])
- `UI_EVENTS_TOTAL` = Counter('km_ui_events_total', 'Embedded UI events partitioned by event label', labelnames=['event'])

### Data Flow
- Touches external libraries: __future__, prometheus_client.

### Integration Points
- External: __future__, prometheus_client
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 278


## gateway/observability/tracing.py
**Purpose**: Tracing helpers for wiring OpenTelemetry exporters.

**Dependencies**:
- External: __future__, fastapi, opentelemetry
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `configure_tracing(app, settings)` – Configure OpenTelemetry tracing based on runtime settings.
- `_select_exporter(settings)` – Choose the span exporter based on settings.
- `_parse_headers(header_string)` – Parse comma-separated OTLP header strings into a dict.
- `reset_tracing_for_tests()` – Reset module-level state so tests can reconfigure tracing cleanly.

### Constants
- `_TRACING_CONFIGURED` = False

### Data Flow
- Primary entry points: `configure_tracing`, `_select_exporter`, `_parse_headers`, `reset_tracing_for_tests`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, opentelemetry.

### Integration Points
- External: __future__, fastapi, opentelemetry
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 4 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 84


## gateway/plugins/__init__.py
**Purpose**: Plugin namespace for future ingestion extensions.

**Dependencies**:
- External: None
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Lightweight module with minimal data flow; acts as namespace or configuration container.

### Integration Points
- External: None
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 2


## gateway/recipes/__init__.py
**Purpose**: Utilities for running knowledge recipes.

**Dependencies**:
- External: executor, models
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: executor, models.

### Integration Points
- External: executor, models
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 7


## gateway/recipes/cli.py
**Purpose**: Command-line utilities for inspecting and running MCP recipes.

**Dependencies**:
- External: __future__, argparse, asyncio, collections, executor, json, logging, models, pathlib, pydantic, rich, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `build_parser()` – Construct the top-level argument parser for the CLI.
- `load_recipe_by_name(recipes_dir, name)` – Load a recipe by stem name from the given directory.
- `parse_variables(pairs)` – Parse ``key=value`` overrides supplied on the command line.
- `command_list(args)` – List recipes available in the configured directory.
- `command_show(args)` – Print a single recipe definition in JSON form.
- `command_validate(args)` – Validate one or all recipes and report the outcome.
- `recipe_executor_factory(settings)` – Create a factory that instantiates a gateway-backed tool executor.
- `command_run(args, settings)` – Execute a recipe and render the results.
- `_render_run_result(result)` – Pretty-print a recipe execution result in tabular form.
- `main(argv=None)` – Entry point for the recipes CLI.

### Constants
- `DEFAULT_RECIPES_DIR` = Path(__file__).resolve().parents[2] / 'recipes'

### Data Flow
- Primary entry points: `build_parser`, `load_recipe_by_name`, `parse_variables`, `command_list`, `command_show`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, argparse, asyncio, collections, executor, json, logging, models, pathlib, pydantic, rich, typing.

### Integration Points
- External: __future__, argparse, asyncio, collections, executor, json, logging, models, pathlib, pydantic, rich, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 10 of 10
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 220


## gateway/recipes/executor.py
**Purpose**: Recipe execution layer for automating MCP-driven workflows.

**Dependencies**:
- External: __future__, asyncio, collections, contextlib, dataclasses, json, logging, models, pathlib, re, time, types, yaml
- Internal: gateway
**Related modules**: gateway

### Classes
- `RecipeExecutionError` (bases: RuntimeError) – Raised when a recipe step fails.
- `StepResult` (bases: object) – Lightweight representation of a single recipe step outcome.
- `RecipeRunResult` (bases: object) – Aggregate outcome for a recipe execution, including captured outputs.
  - `to_dict(self)` – No docstring.
- `ToolExecutor` (bases: object) – Abstract tool executor interface.
  - `async call(self, tool, params)` – No docstring.
  - `async __aenter__(self)` – No docstring.
  - `async __aexit__(self, exc_type, exc, tb)` – No docstring.
- `GatewayToolExecutor` (bases: ToolExecutor) – Execute tools by reusing gateway HTTP/MCP helpers.
  - `__init__(self, settings)` – No docstring.
  - `async __aenter__(self)` – No docstring.
  - `async __aexit__(self, exc_type, exc, tb)` – No docstring.
  - `async call(self, tool, params)` – No docstring.
- `RecipeRunner` (bases: object) – Run recipes using the configured MCP settings.
  - `__init__(self, settings, executor_factory=None, audit_path=None)` – No docstring.
  - `make_executor(self)` – No docstring.
  - `async run(self, recipe, variables=None, dry_run=False)` – No docstring.
  - `async _execute_wait(self, executor, context, wait)` – No docstring.
  - `_append_audit(self, result, context)` – No docstring.

### Functions
- `_resolve_template(value, context)` – No docstring.
- `_lookup_expression(expr, context)` – No docstring.
- `_descend(current, part)` – No docstring.
- `_evaluate_condition(result, condition)` – No docstring.
- `_compute_capture(result, capture)` – No docstring.
- `async _executor_cm(factory)` – Context manager that yields a tool executor from the provided factory.
- `load_recipe(path)` – Load a recipe file from disk and validate the schema.
- `_ensure_object_map(value, label)` – Ensure template resolution returned a mapping, raising otherwise.
- `_require_str(params, key)` – Fetch a required string parameter from a mapping of arguments.
- `_coerce_optional_str(value)` – Convert optional string-like values to trimmed strings.
- `_coerce_positive_int(value, default)` – Convert inputs to a positive integer, falling back to the default.
- `_coerce_int(value)` – Coerce common primitive values to an integer when possible.
- `_coerce_bool(value, default=None)` – Interpret truthy/falsey string values and return a boolean.
- `list_recipes(recipes_dir)` – Return all recipe definition files within the directory.

### Constants
- None

### Data Flow
- Primary entry points: `_resolve_template`, `_lookup_expression`, `_descend`, `_evaluate_condition`, `_compute_capture`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, asyncio, collections, contextlib, dataclasses, json, logging, models, pathlib, re, time, types, yaml.

### Integration Points
- External: __future__, asyncio, collections, contextlib, dataclasses, json, logging, models, pathlib, re, time, types, yaml
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 9 of 14
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 6 of 6
- Try/except blocks: 4
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 574


## gateway/recipes/models.py
**Purpose**: Pydantic models describing MCP recipe configuration.

**Dependencies**:
- External: __future__, pydantic, typing
- Internal: None
**Related modules**: None

### Classes
- `Condition` (bases: BaseModel) – Assertion condition evaluated against a step result.
- `Capture` (bases: BaseModel) – Capture part of a step result into the execution context.
- `WaitConfig` (bases: BaseModel) – Poll a tool until a condition is satisfied.
- `RecipeStep` (bases: BaseModel) – Single step inside a recipe.
  - `validate_mode(self)` – No docstring.
- `Recipe` (bases: BaseModel) – Top level recipe definition.
  - `ensure_unique_step_ids(self)` – No docstring.

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: __future__, pydantic, typing.

### Integration Points
- External: __future__, pydantic, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 5 of 5
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 81


## gateway/scheduler.py
**Purpose**: Background scheduler that drives periodic ingestion runs.

**Dependencies**:
- External: __future__, apscheduler, collections, contextlib, filelock, logging, pathlib, subprocess, time
- Internal: gateway
**Related modules**: gateway

### Classes
- `IngestionScheduler` (bases: object) – APScheduler wrapper that coordinates repo-aware ingestion jobs.
  - `__init__(self, settings, graph_manager=None, qdrant_manager=None)` – No docstring.
  - `start(self)` – No docstring.
  - `shutdown(self)` – No docstring.
  - `_run_ingestion(self)` – No docstring.
  - `_run_backup(self)` – No docstring.
  - `_read_last_head(self)` – No docstring.
  - `_write_last_head(self, head)` – No docstring.
  - `_prune_backups(self)` – No docstring.
  - `backup_health(self)` – No docstring.

### Functions
- `_current_repo_head(repo_root)` – Return the git HEAD sha for the repo, or ``None`` when unavailable.
- `_build_trigger(config)` – Construct the APScheduler trigger based on user configuration.
- `_describe_trigger(config)` – Provide a human readable summary of the configured trigger.
- `_coerce_positive_int(value, default)` – Best-effort conversion to a positive integer with sane defaults.

### Constants
- None

### Data Flow
- Primary entry points: `_current_repo_head`, `_build_trigger`, `_describe_trigger`, `_coerce_positive_int`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, apscheduler, collections, contextlib, filelock, logging, pathlib, subprocess, time.

### Integration Points
- External: __future__, apscheduler, collections, contextlib, filelock, logging, pathlib, subprocess, time
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 4 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 11
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 343


## gateway/search/__init__.py
**Purpose**: Search service exposing vector search with graph context.

**Dependencies**:
- External: dataset, evaluation, exporter, feedback, maintenance, models, service
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: dataset, evaluation, exporter, feedback, maintenance, models, service.

### Integration Points
- External: dataset, evaluation, exporter, feedback, maintenance, models, service
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 42


## gateway/search/cli.py
**Purpose**: Command-line helpers for search training, exports, and maintenance.

**Dependencies**:
- External: __future__, argparse, datetime, logging, pathlib, rich
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `build_parser()` – Return an argument parser covering all search CLI commands.
- `export_training_data(output, fmt, require_vote, limit, include_rotations, settings=None)` – Materialise feedback events into a training dataset file.
- `train_model(dataset, output, settings)` – Train a ranking model from a prepared dataset and save the artifact.
- `show_weights(settings)` – Print the active search weight profile to the console.
- `prune_feedback(settings, max_age_days, max_requests, output)` – Trim feedback logs by age/request count and optionally archive removals.
- `redact_training_dataset(dataset, output, drop_query, drop_context, drop_note)` – Strip sensitive fields and emit a sanitized dataset.
- `evaluate_trained_model(dataset, model)` – Run offline evaluation of a trained model against a labelled dataset.
- `main(argv=None)` – Entry point for the `gateway-search` command-line interface.

### Constants
- None

### Data Flow
- Primary entry points: `build_parser`, `export_training_data`, `train_model`, `show_weights`, `prune_feedback`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, argparse, datetime, logging, pathlib, rich.

### Integration Points
- External: __future__, argparse, datetime, logging, pathlib, rich
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 8 of 8
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 4
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 398


## gateway/search/dataset.py
**Purpose**: Utilities for reading and preparing search training datasets.

**Dependencies**:
- External: __future__, collections, csv, json, pathlib
- Internal: gateway
**Related modules**: gateway

### Classes
- `DatasetLoadError` (bases: RuntimeError) – Raised when a dataset cannot be parsed.

### Functions
- `load_dataset_records(path)` – Load dataset rows from disk, raising when the file is missing.
- `build_feature_matrix(records, feature_names)` – Convert dataset rows into numeric feature vectors and targets.
- `_parse_float(value)` – No docstring.

### Constants
- `TARGET_FIELD` = 'feedback_vote'

### Data Flow
- Primary entry points: `load_dataset_records`, `build_feature_matrix`, `_parse_float`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, csv, json, pathlib.

### Integration Points
- External: __future__, collections, csv, json, pathlib
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 2
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 104


## gateway/search/evaluation.py
**Purpose**: Model evaluation utilities for the search ranking pipeline.

**Dependencies**:
- External: __future__, collections, dataclasses, math, numpy, pathlib, statistics, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `EvaluationMetrics` (bases: object) – Aggregate metrics produced after evaluating a ranking model.

### Functions
- `evaluate_model(dataset_path, model_path)` – Load a dataset and model artifact, returning evaluation metrics.
- `_mean_ndcg(request_ids, relevance, scores, k)` – Compute mean NDCG@k for groups identified by request ids.
- `_dcg(relevances, k)` – Compute discounted cumulative gain at rank ``k``.
- `_spearman_correlation(y_true, y_pred)` – Return Spearman rank correlation between true and predicted values.

### Constants
- None

### Data Flow
- Primary entry points: `evaluate_model`, `_mean_ndcg`, `_dcg`, `_spearman_correlation`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, dataclasses, math, numpy, pathlib, statistics, typing.

### Integration Points
- External: __future__, collections, dataclasses, math, numpy, pathlib, statistics, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 4 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 113


## gateway/search/exporter.py
**Purpose**: Utilities for exporting feedback logs into training datasets.

**Dependencies**:
- External: __future__, collections, csv, dataclasses, json, logging, pathlib, re, typing
- Internal: None
**Related modules**: None

### Classes
- `ExportOptions` (bases: object) – User-configurable options controlling dataset export.
- `ExportStats` (bases: object) – Basic statistics about the export process.

### Functions
- `export_training_dataset(events_path, options)` – Write feedback events from a single log into the requested dataset format.
- `export_feedback_logs(log_paths, options)` – Write feedback events from one or more log files into the requested dataset format.
- `iter_feedback_events(path)` – Yield feedback events from a JSON lines log file.
- `discover_feedback_logs(root, include_rotations)` – Return feedback log files in chronological order (oldest to newest).
- `_iter_feedback_logs(paths)` – Yield events from a sequence of log files.
- `_write_csv(events, options)` – Write feedback events into a CSV file.
- `_write_jsonl(events, options)` – Write feedback events into a JSONL file.
- `_flatten_event(event)` – Flatten nested event data into scalar fields.

### Constants
- `FIELDNAMES` = ('request_id', 'timestamp', 'rank', 'query', 'result_count', 'chunk_id', 'artifact_path', 'artifact_type', 'subsystem', 'vector_score', 'adjusted_score', 'signal_subsystem_affinity', 'signal_relationship_count', 'signal_supporting_bonus', 'signal_coverage_missing', 'graph_context_present', 'feedback_vote', 'feedback_note', 'context_json', 'metadata_request_id', 'metadata_graph_context_included', 'metadata_warnings_count')
- `LOG_SUFFIX_PATTERN` = re.compile('events\\.log(?:\\.(?P<index>\\d+))?$')

### Data Flow
- Primary entry points: `export_training_dataset`, `export_feedback_logs`, `iter_feedback_events`, `discover_feedback_logs`, `_iter_feedback_logs`
- Touches external libraries: __future__, collections, csv, dataclasses, json, logging, pathlib, re, typing.

### Integration Points
- External: __future__, collections, csv, dataclasses, json, logging, pathlib, re, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 8 of 8
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 2 of 2
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 250


## gateway/search/feedback.py
**Purpose**: Persistent storage helpers for search feedback events.

**Dependencies**:
- External: __future__, collections, datetime, json, pathlib, threading, typing, uuid
- Internal: gateway
**Related modules**: gateway

### Classes
- `SearchFeedbackStore` (bases: object) – Append-only store for search telemetry and feedback.
  - `__init__(self, root, max_bytes, max_files)` – No docstring.
  - `record(self, response, feedback, context=None, request_id=None)` – No docstring.
  - `_append(self, rows)` – No docstring.
  - `_rotate_if_needed(self, incoming_size)` – No docstring.
  - `_perform_rotation(self)` – No docstring.
  - `_suffix_path(self, index)` – No docstring.
  - `_current_size(self)` – No docstring.
  - `_update_metrics(self)` – No docstring.

### Functions
- `_serialize_results(response, request_id, timestamp, vote, note, context, feedback)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_serialize_results`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, datetime, json, pathlib, threading, typing, uuid.

### Integration Points
- External: __future__, collections, datetime, json, pathlib, threading, typing, uuid
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 0 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 3
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 182


## gateway/search/filtering.py
**Purpose**: Filter processing helpers for search queries.

**Dependencies**:
- External: __future__, collections, datetime, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `build_filter_state(filters)` – Normalise raw filter payloads into a `FilterState`.
- `payload_passes_filters(payload, state)` – Return True when the payload matches the provided filter state.
- `parse_iso_datetime(value)` – Parse integers, floats, or ISO-8601 strings into timezone-aware datetimes.
- `_normalise_payload_tags(raw_tags)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `build_filter_state`, `payload_passes_filters`, `parse_iso_datetime`, `_normalise_payload_tags`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, datetime, typing.

### Integration Points
- External: __future__, collections, datetime, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 4
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 130


## gateway/search/graph_enricher.py
**Purpose**: Graph enrichment helpers for search results.

**Dependencies**:
- External: __future__, dataclasses, logging, neo4j, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `GraphEnrichmentResult` (bases: object) – Graph enrichment output for a single search hit.
- `GraphEnricher` (bases: object) – Manage graph lookups with caching, budgets, and telemetry.
  - `__init__(self, graph_service, include_graph, filter_state, graph_max_results, time_budget_seconds, slow_warn_seconds, request_id)` – No docstring.
  - `slots_exhausted(self)` – No docstring.
  - `time_exhausted(self)` – No docstring.
  - `resolve(self, payload, subsystem_match, warnings)` – No docstring.

### Functions
- `_label_for_artifact(artifact_type)` – No docstring.
- `_summarize_graph_context(data)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_label_for_artifact`, `_summarize_graph_context`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, dataclasses, logging, neo4j, time, typing.

### Integration Points
- External: __future__, dataclasses, logging, neo4j, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 2 of 2
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 267


## gateway/search/maintenance.py
**Purpose**: Maintenance routines for pruning feedback logs and redacting datasets.

**Dependencies**:
- External: __future__, collections, csv, dataclasses, datetime, json, logging, pathlib, shutil
- Internal: gateway
**Related modules**: gateway

### Classes
- `PruneOptions` (bases: object) – Configures retention rules for the feedback log pruning routine.
- `PruneStats` (bases: object) – Summary of how many feedback requests were kept versus removed.
- `RedactOptions` (bases: object) – Toggles that control which sensitive fields should be redacted.
- `RedactStats` (bases: object) – Summary of how many dataset rows required redaction.

### Functions
- `prune_feedback_log(events_path, options)` – Prune feedback requests based on age and count thresholds.
- `redact_dataset(dataset_path, options)` – Redact sensitive fields from datasets stored as CSV or JSON Lines.
- `_parse_timestamp(value)` – Parse timestamps stored as numbers or ISO 8601 strings.
- `_collect_events(events_path)` – No docstring.
- `_build_timestamps(events_by_request)` – No docstring.
- `_apply_prune_filters(request_order, timestamps, options, now)` – No docstring.
- `_preserve_original_order(order, selected_ids)` – No docstring.
- `_write_retained_events(destination, retained_order, events_by_request)` – No docstring.
- `_redact_csv(source, destination, options)` – Redact sensitive columns from a CSV dataset.
- `_redact_csv_row(row, options)` – No docstring.
- `_clear_field(row, field, replacement)` – No docstring.
- `_redact_jsonl(source, destination, options)` – Redact sensitive fields from JSON lines datasets.
- `_redact_json_record(record, options)` – No docstring.
- `_null_field(record, field)` – No docstring.

### Constants
- `_FALLBACK_TIMESTAMP` = datetime.fromordinal(1).replace(tzinfo=UTC)

### Data Flow
- Primary entry points: `prune_feedback_log`, `redact_dataset`, `_parse_timestamp`, `_collect_events`, `_build_timestamps`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, csv, dataclasses, datetime, json, logging, pathlib, shutil.

### Integration Points
- External: __future__, collections, csv, dataclasses, datetime, json, logging, pathlib, shutil
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 5 of 14
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 4 of 4
- Try/except blocks: 1
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 285


## gateway/search/ml.py
**Purpose**: Machine-learning scoring helpers for search results.

**Dependencies**:
- External: __future__, dataclasses, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `ModelScore` (bases: object) – Container for ML score and per-feature contributions.
- `ModelScorer` (bases: object) – Apply linear model artifacts to enrich search scoring.
  - `__init__(self, artifact)` – No docstring.
  - `available(self)` – No docstring.
  - `intercept(self)` – No docstring.
  - `score(self, scoring, graph_context, graph_context_included, warnings_count)` – No docstring.
  - `_build_features(self, scoring, graph_context, graph_context_included, warnings_count)` – No docstring.
  - `_apply(self, features)` – No docstring.

### Functions
- None

### Constants
- None

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, dataclasses, typing.

### Integration Points
- External: __future__, dataclasses, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 2 of 2
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 101


## gateway/search/models.py
**Purpose**: Shared dataclasses and type helpers for search components.

**Dependencies**:
- External: __future__, dataclasses, datetime, typing
- Internal: None
**Related modules**: None

### Classes
- `SearchResult` (bases: object) – Single ranked chunk returned from the search pipeline.
- `SearchResponse` (bases: object) – API-friendly container for search results and metadata.
- `SearchOptions` (bases: object) – Runtime options controlling the search service behaviour.
- `SearchWeights` (bases: object) – Weighting configuration for hybrid scoring.
- `FilterState` (bases: object) – Preprocessed filter collections derived from request parameters.
- `CoverageInfo` (bases: object) – Coverage characteristics used during scoring.

### Functions
- `ensure_utc(dt)` – Normalise datetimes to UTC for serialisation.

### Constants
- None

### Data Flow
- Primary entry points: `ensure_utc`
- Touches external libraries: __future__, dataclasses, datetime, typing.

### Integration Points
- External: __future__, dataclasses, datetime, typing
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 1 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 6 of 6
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 94


## gateway/search/scoring.py
**Purpose**: Heuristic scoring helpers used by the search service.

**Dependencies**:
- External: __future__, datetime, re, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `HeuristicScorer` (bases: object) – Apply hybrid heuristic signals and aggregate scoring metadata.
  - `__init__(self, weights, vector_weight, lexical_weight)` – No docstring.
  - `build_chunk(self, payload, score)` – No docstring.
  - `lexical_score(self, query, chunk)` – No docstring.
  - `base_scoring(self, vector_score, lexical_score)` – No docstring.
  - `apply_graph_scoring(self, base_scoring, vector_score, lexical_score, query_tokens, chunk, graph_context)` – No docstring.
  - `populate_additional_signals(self, scoring, chunk, graph_context, path_depth, freshness_days)` – No docstring.
  - `compute_freshness_days(self, chunk, graph_context)` – No docstring.
  - `_calculate_subsystem_affinity(subsystem, query_tokens)` – No docstring.
  - `_calculate_supporting_bonus(related_artifacts)` – No docstring.
  - `_calculate_coverage_info(self, chunk)` – No docstring.
  - `_coerce_ratio_value(value)` – No docstring.
  - `_calculate_criticality_score(chunk, graph_context)` – No docstring.
  - `_extract_subsystem_criticality(graph_context)` – No docstring.
  - `_normalise_criticality(value)` – No docstring.
  - `_estimate_path_depth(graph_context)` – No docstring.

### Functions
- None

### Constants
- None

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, re, typing.

### Integration Points
- External: __future__, datetime, re, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 1 of 1
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 261


## gateway/search/service.py
**Purpose**: Hybrid search orchestration for Duskmantle's knowledge gateway.

**Dependencies**:
- External: __future__, collections, datetime, logging, qdrant_client, re, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `SearchService` (bases: object) – Execute hybrid vector/graph search with heuristic or ML scoring.
  - `__init__(self, qdrant_client, collection_name, embedder, options=None, weights=None, model_artifact=None, failure_callback=None)` – No docstring.
  - `search(self, query, limit, include_graph, graph_service, sort_by_vector=False, request_id=None, filters=None)` – No docstring.

### Functions
- `_subsystems_from_context(graph_context)` – Extract subsystem identifiers from cached graph context.
- `_detect_query_subsystems(query)` – Tokenise the query to detect subsystem keywords for affinity scoring.
- `_normalise_hybrid_weights(vector_weight, lexical_weight)` – No docstring.
- `_resolve_chunk_datetime(chunk, graph_context)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_subsystems_from_context`, `_detect_query_subsystems`, `_normalise_hybrid_weights`, `_resolve_chunk_datetime`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, datetime, logging, qdrant_client, re, typing.

### Integration Points
- External: __future__, collections, datetime, logging, qdrant_client, re, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 3
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 346


## gateway/search/trainer.py
**Purpose**: Training utilities for search ranking models.

**Dependencies**:
- External: __future__, collections, dataclasses, datetime, json, math, numpy, pathlib
- Internal: gateway
**Related modules**: gateway

### Classes
- `TrainingResult` (bases: object) – Capture optimiser output for debug or inspection.
- `ModelArtifact` (bases: object) – Persisted search model metadata and coefficients.

### Functions
- `train_from_dataset(path)` – Train a logistic regression model from the labelled dataset.
- `save_artifact(artifact, path)` – Write the model artifact to disk as JSON.
- `load_artifact(path)` – Load a saved model artifact from disk.
- `_linear_regression(X, y)` – No docstring.

### Constants
- `FEATURE_FIELDS` = ('vector_score', 'signal_subsystem_affinity', 'signal_relationship_count', 'signal_supporting_bonus', 'signal_coverage_missing', 'graph_context_present', 'metadata_graph_context_included', 'metadata_warnings_count')

### Data Flow
- Primary entry points: `train_from_dataset`, `save_artifact`, `load_artifact`, `_linear_regression`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, dataclasses, datetime, json, math, numpy, pathlib.

### Integration Points
- External: __future__, collections, dataclasses, datetime, json, math, numpy, pathlib
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 2 of 2
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 129


## gateway/search/vector_retriever.py
**Purpose**: Utilities for running vector retrieval against Qdrant.

**Dependencies**:
- External: __future__, collections, logging, qdrant_client
- Internal: gateway
**Related modules**: gateway

### Classes
- `VectorRetrievalError` (bases: RuntimeError) – Raised when vector search fails before results are returned.
- `VectorRetriever` (bases: object) – Encode a query and execute Qdrant search with optional tuning.
  - `__init__(self, embedder, qdrant_client, collection_name, hnsw_ef_search=None, failure_callback=None)` – No docstring.
  - `search(self, query, limit, request_id=None)` – No docstring.

### Functions
- None

### Constants
- None

### Data Flow
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, logging, qdrant_client.

### Integration Points
- External: __future__, collections, logging, qdrant_client
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Class docstrings: 2 of 2
- Try/except blocks: 2
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 84


## gateway/ui/__init__.py
**Purpose**: UI utilities and routers.

**Dependencies**:
- External: routes
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Touches external libraries: routes.

### Integration Points
- External: routes
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 6


## gateway/ui/routes.py
**Purpose**: UI router exposing static assets and HTML entry points.

**Dependencies**:
- External: __future__, fastapi, json, logging, pathlib
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `get_static_path()` – Return the absolute path to UI static assets.
- `async ui_index(request)` – Render the landing page for the embedded UI.
- `async ui_search(request)` – Render the search console view.
- `async ui_subsystems(request)` – Render the subsystem explorer view.
- `async ui_lifecycle(request)` – Render the lifecycle dashboard view.
- `async ui_lifecycle_report(request)` – Serve the lifecycle report JSON while recording UI metrics.
- `async ui_event(request, payload)` – Record a UI event for observability purposes.

### Constants
- `STATIC_DIR` = Path(__file__).resolve().parent / 'static'
- `TEMPLATES_DIR` = Path(__file__).resolve().parent / 'templates'

### Data Flow
- Primary entry points: `get_static_path`, `ui_index`, `ui_search`, `ui_subsystems`, `ui_lifecycle`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, json, logging, pathlib.

### Integration Points
- External: __future__, fastapi, json, logging, pathlib
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 7 of 7
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 133


## scripts/generate-changelog.py
**Purpose**: Generate changelog entries from Conventional Commits.

**Dependencies**:
- External: __future__, argparse, collections, datetime, pathlib, subprocess, sys
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `_run_git(args)` – No docstring.
- `discover_commits(since)` – No docstring.
- `categorize(commits)` – No docstring.
- `update_changelog(version, released, entries)` – No docstring.
- `main()` – No docstring.

### Constants
- `ROOT` = Path(__file__).resolve().parents[1]
- `CHANGELOG` = ROOT / 'CHANGELOG.md'
- `CATEGORY_MAP` = {'feat': 'Added', 'fix': 'Fixed', 'docs': 'Documentation', 'perf': 'Performance', 'refactor': 'Changed', 'chore': 'Chore', 'test': 'Tests'}

### Data Flow
- Primary entry points: `_run_git`, `discover_commits`, `categorize`, `update_changelog`, `main`
- Touches external libraries: __future__, argparse, collections, datetime, pathlib, subprocess, sys.

### Integration Points
- External: __future__, argparse, collections, datetime, pathlib, subprocess, sys
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 0 of 5
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 83


## tests/__init__.py
**Purpose**: Test package for the knowledge gateway.

**Dependencies**:
- External: None
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- None

### Constants
- None

### Data Flow
- Lightweight module with minimal data flow; acts as namespace or configuration container.

### Integration Points
- External: None
- Internal: None

### Code Quality Notes
- Module docstring present: yes
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 2


## tests/conftest.py
**Purpose**: Implements conftest

**Dependencies**:
- External: __future__, collections, neo4j, os, pytest, shutil, subprocess, sys, time, types, typing, uuid, warnings
- Internal: None
**Related modules**: None

### Classes
- `_NullSession` (bases: object) – No docstring.
  - `__init__(self)` – No docstring.
  - `__enter__(self)` – No docstring.
  - `__exit__(self, exc_type, exc, tb)` – No docstring.
  - `close(self)` – No docstring.
  - `execute_read(self, func, *args, **kwargs)` – No docstring.
  - `run(self, *args, **kwargs)` – No docstring.
- `_NullDriver` (bases: object) – No docstring.
  - `session(self, **kwargs)` – No docstring.
  - `close(self)` – No docstring.

### Functions
- `disable_real_graph_driver(monkeypatch, request)` – No docstring.
- `default_authentication_env(monkeypatch)` – Provide secure default credentials so create_app() can boot under auth-on defaults.
- `neo4j_test_environment()` – No docstring.
- `pytest_collection_modifyitems(config, items)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `disable_real_graph_driver`, `default_authentication_env`, `neo4j_test_environment`, `pytest_collection_modifyitems`
- Touches external libraries: __future__, collections, neo4j, os, pytest, shutil, subprocess, sys, time, types, typing, uuid, warnings.

### Integration Points
- External: __future__, collections, neo4j, os, pytest, shutil, subprocess, sys, time, types, typing, uuid, warnings
- Internal: None

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 1 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 2
- Try/except blocks: 5
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 268


## tests/mcp/test_server_tools.py
**Purpose**: Integration tests for MCP server tools and metrics wiring.

**Dependencies**:
- External: __future__, asyncio, collections, pathlib, prometheus_client, pytest, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_reset_mcp_metrics()` – No docstring.
- `mcp_server()` – No docstring.
- `_counter_value(counter, *labels)` – No docstring.
- `_histogram_sum(histogram, *labels)` – No docstring.
- `_upload_counter(result)` – No docstring.
- `_storetext_counter(result)` – No docstring.
- `_tool_fn(tool)` – No docstring.
- `async test_km_help_lists_tools_and_provides_details(monkeypatch, mcp_server)` – No docstring.
- `async test_metrics_export_includes_tool_labels(monkeypatch, mcp_server)` – No docstring.
- `async test_km_search_success_records_metrics(mcp_server)` – No docstring.
- `async test_km_search_gateway_error_records_failure(mcp_server)` – No docstring.
- `async test_graph_tools_delegate_to_client_and_record_metrics(mcp_server)` – No docstring.
- `async test_lifecycle_report_records_metrics(mcp_server)` – No docstring.
- `async test_coverage_summary_records_metrics(mcp_server)` – No docstring.
- `async test_ingest_status_handles_missing_history(mcp_server)` – No docstring.
- `async test_ingest_trigger_succeeds(monkeypatch, mcp_server)` – No docstring.
- `async test_ingest_trigger_failure_records_metrics(monkeypatch, mcp_server)` – No docstring.
- `async test_backup_trigger(monkeypatch, mcp_server)` – No docstring.
- `async test_feedback_submit(monkeypatch, mcp_server)` – No docstring.
- `async test_km_upload_copies_file_and_records_metrics(tmp_path)` – No docstring.
- `async test_km_upload_missing_source_raises(tmp_path)` – No docstring.
- `async test_km_upload_requires_admin_token(tmp_path)` – No docstring.
- `async test_km_upload_triggers_ingest_when_requested(monkeypatch, tmp_path)` – No docstring.
- `async test_km_storetext_creates_document_with_front_matter(tmp_path)` – No docstring.
- `async test_km_storetext_requires_content(tmp_path)` – No docstring.
- `async test_km_storetext_triggers_ingest_when_requested(monkeypatch, tmp_path)` – No docstring.
- `async test_km_storetext_requires_admin_token(tmp_path)` – No docstring.
- `async test_mcp_smoke_run(monkeypatch, mcp_server)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_reset_mcp_metrics`, `mcp_server`, `_counter_value`, `_histogram_sum`, `_upload_counter`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, asyncio, collections, pathlib, prometheus_client, pytest, typing.

### Integration Points
- External: __future__, asyncio, collections, pathlib, prometheus_client, pytest, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 0 of 28
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 776


## tests/mcp/test_utils_files.py
**Purpose**: Implements test utils files

**Dependencies**:
- External: __future__, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_sweep_documents_copies_supported_files(tmp_path)` – No docstring.
- `test_sweep_documents_dry_run_reports_actions(tmp_path)` – No docstring.
- `test_copy_into_root_prevents_traversal(tmp_path)` – No docstring.
- `test_write_text_document_requires_content(tmp_path)` – No docstring.
- `test_slugify_generates_fallback_when_empty()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_sweep_documents_copies_supported_files`, `test_sweep_documents_dry_run_reports_actions`, `test_copy_into_root_prevents_traversal`, `test_write_text_document_requires_content`, `test_slugify_generates_fallback_when_empty`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pathlib, pytest.

### Integration Points
- External: __future__, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 5
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 57


## tests/playwright_server.py
**Purpose**: Implements playwright server

**Dependencies**:
- External: __future__, datetime, json, os, pathlib, shutil, signal, uvicorn
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_write_json(path, payload)` – No docstring.
- `_prepare_state(state_path)` – No docstring.
- `_configure_environment(state_path)` – No docstring.
- `main()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_write_json`, `_prepare_state`, `_configure_environment`, `main`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, json, os, pathlib, shutil, signal, uvicorn.

### Integration Points
- External: __future__, datetime, json, os, pathlib, shutil, signal, uvicorn
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 182


## tests/search/test_exporter.py
**Purpose**: Implements test exporter

**Dependencies**:
- External: __future__, csv, json, pathlib, types
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_discover_feedback_logs_orders_oldest_first(tmp_path)` – No docstring.
- `test_export_feedback_logs_combines_rotations(tmp_path)` – No docstring.
- `test_export_training_data_includes_rotations(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_discover_feedback_logs_orders_oldest_first`, `test_export_feedback_logs_combines_rotations`, `test_export_training_data_includes_rotations`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, csv, json, pathlib, types.

### Integration Points
- External: __future__, csv, json, pathlib, types
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 192


## tests/search/test_filtering.py
**Purpose**: Implements test filtering

**Dependencies**:
- External: __future__, datetime
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_build_filter_state_normalises_filters()` – No docstring.
- `test_payload_passes_filters_checks_all_fields()` – No docstring.
- `test_parse_iso_datetime_handles_multiple_formats()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_build_filter_state_normalises_filters`, `test_payload_passes_filters_checks_all_fields`, `test_parse_iso_datetime_handles_multiple_formats`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime.

### Integration Points
- External: __future__, datetime
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 60


## tests/search/test_graph_enricher.py
**Purpose**: Implements test graph enricher

**Dependencies**:
- External: __future__, pytest, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummyGraphService` (bases: GraphService) – No docstring.
  - `__init__(self, response, delay=0.0)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
  - `shortest_path_depth(self, node_id, max_depth=4)` – No docstring.
  - `get_subsystem(self, *args, **kwargs)` – No docstring.
  - `search(self, term, limit)` – No docstring.
  - `run_cypher(self, query, parameters)` – No docstring.

### Functions
- `_metric_value(name, labels=None)` – No docstring.
- `graph_payload()` – No docstring.
- `graph_response()` – No docstring.
- `test_graph_enricher_caches_results(graph_payload, graph_response)` – No docstring.
- `test_graph_enricher_respects_result_budget(graph_payload, graph_response)` – No docstring.
- `test_graph_enricher_respects_time_budget(graph_payload, graph_response)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_metric_value`, `graph_payload`, `graph_response`, `test_graph_enricher_caches_results`, `test_graph_enricher_respects_result_budget`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pytest, time, typing.

### Integration Points
- External: __future__, pytest, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 146


## tests/search/test_ml_scorer.py
**Purpose**: Implements test ml scorer

**Dependencies**:
- External: __future__, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_artifact()` – No docstring.
- `test_model_scorer_produces_contributions()` – No docstring.
- `test_model_scorer_handles_missing_features_with_defaults()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_artifact`, `test_model_scorer_produces_contributions`, `test_model_scorer_handles_missing_features_with_defaults`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pytest.

### Integration Points
- External: __future__, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 60


## tests/search/test_scoring.py
**Purpose**: Implements test scoring

**Dependencies**:
- External: __future__, datetime, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_heuristic_scorer_applies_graph_signals()` – No docstring.
- `test_compute_freshness_days_prefers_chunk_timestamp()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_heuristic_scorer_applies_graph_signals`, `test_compute_freshness_days_prefers_chunk_timestamp`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, pytest.

### Integration Points
- External: __future__, datetime, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 82


## tests/search/test_vector_retriever.py
**Purpose**: Implements test vector retriever

**Dependencies**:
- External: __future__, collections, pytest, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummyEmbedder` (bases: object) – No docstring.
  - `__init__(self, raise_on_encode=None)` – No docstring.
  - `encode(self, texts)` – No docstring.
- `DummyQdrantClient` (bases: object) – No docstring.
  - `__init__(self, raise_on_search=None)` – No docstring.
  - `search(self, **kwargs)` – No docstring.

### Functions
- `test_vector_retriever_returns_hits()` – No docstring.
- `test_vector_retriever_failure_calls_callback()` – No docstring.
- `test_vector_retriever_encode_failure_propagates()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_vector_retriever_returns_hits`, `test_vector_retriever_failure_calls_callback`, `test_vector_retriever_encode_failure_propagates`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, pytest, typing.

### Integration Points
- External: __future__, collections, pytest, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 2
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 85


## tests/test_api_security.py
**Purpose**: Implements test api security

**Dependencies**:
- External: __future__, fastapi, json, logging, pathlib, pytest, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `reset_settings_cache()` – No docstring.
- `test_audit_requires_token(tmp_path, monkeypatch)` – No docstring.
- `test_audit_history_limit_clamped(tmp_path, monkeypatch)` – No docstring.
- `test_audit_history_limit_too_low_normalized(tmp_path, monkeypatch)` – No docstring.
- `test_coverage_endpoint(tmp_path, monkeypatch)` – No docstring.
- `test_coverage_missing_report(tmp_path, monkeypatch)` – No docstring.
- `test_rate_limiting(monkeypatch)` – No docstring.
- `test_startup_logs_configuration(monkeypatch, tmp_path, caplog)` – No docstring.
- `test_secure_mode_without_admin_token_fails(tmp_path, monkeypatch)` – No docstring.
- `test_secure_mode_requires_custom_neo4j_password(tmp_path, monkeypatch)` – No docstring.
- `test_rate_limiting_search(monkeypatch, tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `reset_settings_cache`, `test_audit_requires_token`, `test_audit_history_limit_clamped`, `test_audit_history_limit_too_low_normalized`, `test_coverage_endpoint`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, json, logging, pathlib, pytest, typing.

### Integration Points
- External: __future__, fastapi, json, logging, pathlib, pytest, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 11
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 272


## tests/test_app_smoke.py
**Purpose**: Implements test app smoke

**Dependencies**:
- External: __future__, fastapi, json, logging, os, pathlib, pytest, time, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `reset_settings_cache()` – No docstring.
- `_stub_connection_managers(monkeypatch)` – No docstring.
- `test_health_endpoint_reports_diagnostics(tmp_path, monkeypatch)` – No docstring.
- `test_health_endpoint_ok_when_artifacts_present(tmp_path, monkeypatch)` – No docstring.
- `test_ready_endpoint_returns_ready()` – No docstring.
- `test_lifecycle_history_endpoint(tmp_path, monkeypatch)` – No docstring.
- `test_requires_non_default_neo4j_password_when_auth_enabled(monkeypatch, tmp_path)` – No docstring.
- `test_requires_non_empty_neo4j_password_when_auth_enabled(monkeypatch, tmp_path)` – No docstring.
- `test_logs_warning_when_neo4j_auth_disabled(monkeypatch, tmp_path, caplog)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `reset_settings_cache`, `_stub_connection_managers`, `test_health_endpoint_reports_diagnostics`, `test_health_endpoint_ok_when_artifacts_present`, `test_ready_endpoint_returns_ready`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, json, logging, os, pathlib, pytest, time, unittest.

### Integration Points
- External: __future__, fastapi, json, logging, os, pathlib, pytest, time, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 9
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: yes
- TODO/FIXME markers: 0
- Approximate lines: 214


## tests/test_connection_managers.py
**Purpose**: Implements test connection managers

**Dependencies**:
- External: __future__, prometheus_client, pytest, types, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_reset_metric(metric)` – No docstring.
- `reset_metrics()` – No docstring.
- `make_settings(**overrides)` – No docstring.
- `_make_dummy_driver()` – No docstring.
- `test_neo4j_manager_records_success_and_failure(monkeypatch)` – No docstring.
- `test_qdrant_manager_handles_health_failures(monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_reset_metric`, `reset_metrics`, `make_settings`, `_make_dummy_driver`, `test_neo4j_manager_records_success_and_failure`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, prometheus_client, pytest, types, unittest.

### Integration Points
- External: __future__, prometheus_client, pytest, types, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 125


## tests/test_coverage_report.py
**Purpose**: Implements test coverage report

**Dependencies**:
- External: __future__, collections, fastapi, json, pathlib, prometheus_client, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- `StubQdrantWriter` (bases: object) – No docstring.
  - `ensure_collection(self, vector_size)` – No docstring.
  - `upsert_chunks(self, chunks)` – No docstring.
- `StubNeo4jWriter` (bases: object) – No docstring.
  - `ensure_constraints(self)` – No docstring.
  - `sync_artifact(self, artifact)` – No docstring.
  - `sync_chunks(self, chunk_embeddings)` – No docstring.

### Functions
- `test_write_coverage_report(tmp_path)` – No docstring.
- `test_coverage_endpoint_after_report_generation(tmp_path, monkeypatch)` – No docstring.
- `test_coverage_history_rotation(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_write_coverage_report`, `test_coverage_endpoint_after_report_generation`, `test_coverage_history_rotation`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, fastapi, json, pathlib, prometheus_client, pytest.

### Integration Points
- External: __future__, collections, fastapi, json, pathlib, prometheus_client, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 2
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 159


## tests/test_graph_api.py
**Purpose**: Implements test graph api

**Dependencies**:
- External: __future__, fastapi, neo4j, os, pathlib, pytest, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummyGraphService` (bases: object) – No docstring.
  - `__init__(self, responses)` – No docstring.
  - `get_subsystem(self, name, **kwargs)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
  - `search(self, term, limit)` – No docstring.
  - `get_subsystem_graph(self, name, depth)` – No docstring.
  - `list_orphan_nodes(self, label, cursor, limit)` – No docstring.
  - `run_cypher(self, query, parameters)` – No docstring.

### Functions
- `app(monkeypatch)` – No docstring.
- `test_graph_subsystem_returns_payload(app)` – No docstring.
- `test_graph_subsystem_legacy_path_missing(app)` – No docstring.
- `test_graph_subsystem_not_found(app)` – No docstring.
- `test_graph_subsystem_graph_endpoint(app)` – No docstring.
- `test_graph_orphans_endpoint(app)` – No docstring.
- `test_graph_node_endpoint(app)` – No docstring.
- `test_graph_node_accepts_slash_encoded_ids(app)` – No docstring.
- `test_graph_node_endpoint_live(monkeypatch, tmp_path)` – No docstring.
- `test_graph_search_endpoint_live(monkeypatch, tmp_path)` – No docstring.
- `test_graph_search_endpoint(app)` – No docstring.
- `test_graph_cypher_requires_maintainer_token(monkeypatch)` – No docstring.
- `test_graph_reader_scope(monkeypatch)` – No docstring.

### Constants
- `GRAPH_PREFIX` = f'{API_V1_PREFIX}/graph'

### Data Flow
- Primary entry points: `app`, `test_graph_subsystem_returns_payload`, `test_graph_subsystem_legacy_path_missing`, `test_graph_subsystem_not_found`, `test_graph_subsystem_graph_endpoint`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, neo4j, os, pathlib, pytest, typing.

### Integration Points
- External: __future__, fastapi, neo4j, os, pathlib, pytest, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 13
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 407


## tests/test_graph_auto_migrate.py
**Purpose**: Implements test graph auto migrate

**Dependencies**:
- External: __future__, neo4j, prometheus_client, pytest, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `reset_settings_cache()` – No docstring.
- `reset_migration_metrics()` – No docstring.
- `_metric(name)` – No docstring.
- `_stub_managers(monkeypatch, driver=None, qdrant_client=None, write_driver_error=None)` – No docstring.
- `test_auto_migrate_runs_when_enabled(monkeypatch)` – No docstring.
- `test_auto_migrate_skipped_when_disabled(monkeypatch)` – No docstring.
- `test_auto_migrate_records_failure(monkeypatch)` – No docstring.
- `test_missing_database_disables_graph_driver(monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `reset_settings_cache`, `reset_migration_metrics`, `_metric`, `_stub_managers`, `test_auto_migrate_runs_when_enabled`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, neo4j, prometheus_client, pytest, unittest.

### Integration Points
- External: __future__, neo4j, prometheus_client, pytest, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 8
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 202


## tests/test_graph_cli.py
**Purpose**: Implements test graph cli

**Dependencies**:
- External: __future__, pytest, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummySettings` (bases: object) – No docstring.

### Functions
- `test_graph_cli_migrate_runs_runner(monkeypatch)` – No docstring.
- `test_graph_cli_dry_run_prints_pending(monkeypatch, capsys)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_graph_cli_migrate_runs_runner`, `test_graph_cli_dry_run_prints_pending`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pytest, unittest.

### Integration Points
- External: __future__, pytest, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 52


## tests/test_graph_database_validation.py
**Purpose**: Implements test graph database validation

**Dependencies**:
- External: __future__, neo4j, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_verify_graph_database_returns_false_when_database_missing()` – No docstring.
- `test_verify_graph_database_returns_true_on_success()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_verify_graph_database_returns_false_when_database_missing`, `test_verify_graph_database_returns_true_on_success`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, neo4j, unittest.

### Integration Points
- External: __future__, neo4j, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 39


## tests/test_graph_migrations.py
**Purpose**: Implements test graph migrations

**Dependencies**:
- External: __future__, collections, types
- Internal: gateway
**Related modules**: gateway

### Classes
- `FakeResult` (bases: object) – No docstring.
  - `__init__(self, record=None)` – No docstring.
  - `single(self)` – No docstring.
- `FakeTransaction` (bases: object) – No docstring.
  - `__init__(self, applied_ids, results)` – No docstring.
  - `run(self, query, **params)` – No docstring.
  - `commit(self)` – No docstring.
  - `rollback(self)` – No docstring.
  - `__enter__(self)` – No docstring.
  - `__exit__(self, exc_type, exc_val, exc_tb)` – No docstring.
- `FakeSession` (bases: object) – No docstring.
  - `__init__(self, applied_ids, records)` – No docstring.
  - `run(self, query, **params)` – No docstring.
  - `begin_transaction(self)` – No docstring.
  - `close(self)` – No docstring.
  - `__enter__(self)` – No docstring.
  - `__exit__(self, exc_type, exc_val, exc_tb)` – No docstring.
- `FakeDriver` (bases: object) – No docstring.
  - `__init__(self)` – No docstring.
  - `session(self, database)` – No docstring.
  - `close(self)` – No docstring.

### Functions
- `test_migration_runner_applies_pending_migrations()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_migration_runner_applies_pending_migrations`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, types.

### Integration Points
- External: __future__, collections, types
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 4
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 106


## tests/test_graph_service_startup.py
**Purpose**: Implements test graph service startup

**Dependencies**:
- External: __future__, fastapi, pytest, starlette, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `reset_settings_cache()` – No docstring.
- `set_state_path(tmp_path_factory, monkeypatch)` – No docstring.
- `async _receive()` – No docstring.
- `_make_request(app)` – No docstring.
- `test_graph_dependency_returns_503_when_database_missing(monkeypatch)` – No docstring.
- `test_graph_dependency_returns_service_when_available(monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `reset_settings_cache`, `set_state_path`, `_receive`, `_make_request`, `test_graph_dependency_returns_503_when_database_missing`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, pytest, starlette, unittest.

### Integration Points
- External: __future__, fastapi, pytest, starlette, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 95


## tests/test_graph_service_unit.py
**Purpose**: Implements test graph service unit

**Dependencies**:
- External: __future__, collections, pytest, types, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummyNode` (bases: dict[str, object]) – No docstring.
  - `__init__(self, labels, element_id, **props)` – No docstring.
- `DummyRelationship` (bases: dict[str, object]) – No docstring.
  - `__init__(self, start_node, end_node, rel_type, **props)` – No docstring.
- `DummySession` (bases: object) – No docstring.
  - `__init__(self)` – No docstring.
  - `__enter__(self)` – No docstring.
  - `__exit__(self, exc_type, exc, tb)` – No docstring.
  - `execute_read(self, func, *args, **kwargs)` – No docstring.
  - `run(self, query, **params)` – No docstring.
- `DummyDriver` (bases: object) – No docstring.
  - `__init__(self, session)` – No docstring.
  - `session(self, **kwargs)` – No docstring.
  - `execute_query(self, query, parameters, database_)` – No docstring.

### Functions
- `_reset_metric(reason)` – No docstring.
- `_metric_value(reason)` – No docstring.
- `patch_graph_types(monkeypatch)` – No docstring.
- `dummy_driver()` – No docstring.
- `test_get_subsystem_paginates_and_includes_artifacts(monkeypatch, dummy_driver)` – No docstring.
- `test_get_subsystem_missing_raises(monkeypatch, dummy_driver)` – No docstring.
- `test_get_subsystem_graph_returns_nodes_and_edges(monkeypatch, dummy_driver)` – No docstring.
- `test_fetch_subsystem_paths_inlines_depth_literal(monkeypatch)` – No docstring.
- `test_get_node_with_relationships(monkeypatch, dummy_driver)` – No docstring.
- `test_list_orphan_nodes_rejects_unknown_label(dummy_driver)` – No docstring.
- `test_list_orphan_nodes_serializes_results(monkeypatch, dummy_driver)` – No docstring.
- `test_get_node_missing_raises(monkeypatch, dummy_driver)` – No docstring.
- `test_search_serializes_results(monkeypatch, dummy_driver)` – No docstring.
- `test_shortest_path_depth(monkeypatch, dummy_driver)` – No docstring.
- `test_shortest_path_depth_none(monkeypatch, dummy_driver)` – No docstring.
- `test_run_cypher_serializes_records(monkeypatch, dummy_driver)` – No docstring.
- `test_run_cypher_rejects_non_read_queries(dummy_driver)` – No docstring.
- `test_run_cypher_rejects_updates_detected_in_counters(dummy_driver)` – No docstring.
- `test_run_cypher_allows_whitelisted_procedure(dummy_driver)` – No docstring.
- `test_run_cypher_rejects_disallowed_procedure(dummy_driver)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_reset_metric`, `_metric_value`, `patch_graph_types`, `dummy_driver`, `test_get_subsystem_paginates_and_includes_artifacts`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, pytest, types, unittest.

### Integration Points
- External: __future__, collections, pytest, types, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 20
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 4
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 448


## tests/test_graph_validation.py
**Purpose**: End-to-end validation of ingestion and graph-backed search.

**Dependencies**:
- External: __future__, collections, neo4j, os, pathlib, pytest, qdrant_client, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `_DummyEmbedder` (bases: Embedder) – Minimal embedder returning deterministic vectors for tests.
  - `__init__(self)` – No docstring.
  - `dimension(self)` – No docstring.
  - `encode(self, texts)` – No docstring.
- `_FakePoint` (bases: object) – No docstring.
  - `__init__(self, payload, score)` – No docstring.
- `_DummyQdrantClient` (bases: object) – Stub Qdrant client that returns pre-seeded points.
  - `__init__(self, points)` – No docstring.
  - `search(self, **_kwargs)` – No docstring.

### Functions
- `test_ingestion_populates_graph(tmp_path)` – Run ingestion and verify graph nodes, edges, and metadata.
- `test_search_replay_against_real_graph(tmp_path)` – Replay saved search results against the populated knowledge graph.

### Constants
- None

### Data Flow
- Primary entry points: `test_ingestion_populates_graph`, `test_search_replay_against_real_graph`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, neo4j, os, pathlib, pytest, qdrant_client, typing.

### Integration Points
- External: __future__, collections, neo4j, os, pathlib, pytest, qdrant_client, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 2 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 2 of 3
- Try/except blocks: 2
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 249


## tests/test_ingest_cli.py
**Purpose**: Implements test ingest cli

**Dependencies**:
- External: __future__, pathlib, pytest, time, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `reset_settings_cache()` – No docstring.
- `sample_repo(tmp_path)` – No docstring.
- `test_cli_rebuild_dry_run(sample_repo, monkeypatch)` – No docstring.
- `test_cli_rebuild_requires_maintainer_token(sample_repo, monkeypatch)` – No docstring.
- `test_cli_rebuild_with_maintainer_token(sample_repo, monkeypatch)` – No docstring.
- `test_cli_rebuild_full_rebuild_flag(sample_repo, monkeypatch)` – No docstring.
- `test_cli_rebuild_incremental_flag(sample_repo, monkeypatch)` – No docstring.
- `test_cli_audit_history_json(tmp_path, monkeypatch, capsys)` – No docstring.
- `test_cli_audit_history_limit_clamped(tmp_path, monkeypatch, capsys)` – No docstring.
- `test_cli_audit_history_no_entries(tmp_path, monkeypatch, capsys)` – No docstring.
- `test_audit_logger_recent_normalizes_limit(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `reset_settings_cache`, `sample_repo`, `test_cli_rebuild_dry_run`, `test_cli_rebuild_requires_maintainer_token`, `test_cli_rebuild_with_maintainer_token`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pathlib, pytest, time, unittest.

### Integration Points
- External: __future__, pathlib, pytest, time, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 11
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 182


## tests/test_ingest_pipeline.py
**Purpose**: Implements test ingest pipeline

**Dependencies**:
- External: __future__, collections, json, pathlib, prometheus_client, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- `StubQdrantWriter` (bases: object) – No docstring.
  - `__init__(self)` – No docstring.
  - `ensure_collection(self, vector_size)` – No docstring.
  - `upsert_chunks(self, chunks)` – No docstring.
  - `delete_artifact(self, artifact_path)` – No docstring.
- `StubNeo4jWriter` (bases: object) – No docstring.
  - `__init__(self)` – No docstring.
  - `ensure_constraints(self)` – No docstring.
  - `sync_artifact(self, artifact)` – No docstring.
  - `sync_chunks(self, chunk_embeddings)` – No docstring.
  - `delete_artifact(self, path)` – No docstring.

### Functions
- `_metric_value(name, labels)` – No docstring.
- `sample_repo(tmp_path)` – No docstring.
- `test_pipeline_generates_chunks(sample_repo)` – No docstring.
- `test_pipeline_removes_stale_artifacts(tmp_path)` – No docstring.
- `test_pipeline_skips_unchanged_artifacts(tmp_path)` – No docstring.
- `test_artifact_ledger_writes_atomically(tmp_path)` – No docstring.
- `test_artifact_ledger_loads_gracefully_on_corruption(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_metric_value`, `sample_repo`, `test_pipeline_generates_chunks`, `test_pipeline_removes_stale_artifacts`, `test_pipeline_skips_unchanged_artifacts`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, json, pathlib, prometheus_client, pytest.

### Integration Points
- External: __future__, collections, json, pathlib, prometheus_client, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 7
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 2
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 229


## tests/test_km_watch.py
**Purpose**: Implements test km watch

**Dependencies**:
- External: __future__, os, pathlib, prometheus_client, runpy, sys
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `_metric_value(name, labels)` – No docstring.
- `test_compute_fingerprints(tmp_path)` – No docstring.
- `test_diff_fingerprints_detects_changes()` – No docstring.
- `test_watch_metrics_increment(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_metric_value`, `test_compute_fingerprints`, `test_diff_fingerprints_detects_changes`, `test_watch_metrics_increment`
- Touches external libraries: __future__, os, pathlib, prometheus_client, runpy, sys.

### Integration Points
- External: __future__, os, pathlib, prometheus_client, runpy, sys
- Internal: None

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 105


## tests/test_lifecycle_cli.py
**Purpose**: Implements test lifecycle cli

**Dependencies**:
- External: __future__, json, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_lifecycle_cli_json(tmp_path, capsys)` – No docstring.
- `test_lifecycle_cli_missing_file(tmp_path, capsys)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_lifecycle_cli_json`, `test_lifecycle_cli_missing_file`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, json, pathlib, pytest.

### Integration Points
- External: __future__, json, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 32


## tests/test_lifecycle_report.py
**Purpose**: Unit tests for lifecycle report generation and graph enrichment.

**Dependencies**:
- External: __future__, datetime, json, pathlib, prometheus_client, pytest, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummyGraphService` (bases: object) – Test double that returns pre-seeded orphan graph nodes.
  - `__init__(self, pages)` – No docstring.
  - `list_orphan_nodes(self, label, cursor, limit)` – No docstring.

### Functions
- `_ingestion_result()` – Build a representative ingestion result for lifecycle reporting tests.
- `test_write_lifecycle_report_without_graph(tmp_path, ingestion_result)` – Reports render correctly when graph enrichment is disabled.
- `test_write_lifecycle_report_with_graph(tmp_path, ingestion_result)` – Graph enrichment populates isolated node information in the payload.

### Constants
- None

### Data Flow
- Primary entry points: `_ingestion_result`, `test_write_lifecycle_report_without_graph`, `test_write_lifecycle_report_with_graph`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, json, pathlib, prometheus_client, pytest, typing.

### Integration Points
- External: __future__, datetime, json, pathlib, prometheus_client, pytest, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 3 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 1 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 154


## tests/test_mcp_recipes.py
**Purpose**: Implements test mcp recipes

**Dependencies**:
- External: __future__, json, pathlib, pytest
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `test_snippets_are_valid_json(snippet)` – No docstring.

### Constants
- `RECIPES` = Path('docs/MCP_RECIPES.md').read_text()

### Data Flow
- Primary entry points: `test_snippets_are_valid_json`
- Touches external libraries: __future__, json, pathlib, pytest.

### Integration Points
- External: __future__, json, pathlib, pytest
- Internal: None

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 1
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 25


## tests/test_mcp_smoke_recipes.py
**Purpose**: Implements test mcp smoke recipes

**Dependencies**:
- External: __future__, json, pathlib, pytest
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `_recipe_params()` – No docstring.
- `test_recipe_lines_are_valid_json(line)` – No docstring.

### Constants
- `RECIPES` = Path('docs/MCP_RECIPES.md').read_text().splitlines()

### Data Flow
- Primary entry points: `_recipe_params`, `test_recipe_lines_are_valid_json`
- Touches external libraries: __future__, json, pathlib, pytest.

### Integration Points
- External: __future__, json, pathlib, pytest
- Internal: None

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 30


## tests/test_neo4j_writer.py
**Purpose**: Unit tests for the lightweight Neo4j writer integration layer.

**Dependencies**:
- External: __future__, neo4j, pathlib, types, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `RecordingSession` (bases: object) – Stubbed session that records Cypher queries for assertions.
  - `__init__(self)` – No docstring.
  - `run(self, query, **params)` – No docstring.
  - `__enter__(self)` – No docstring.
  - `__exit__(self, exc_type, exc, tb)` – No docstring.
- `RecordingDriver` (bases: object) – Stubbed driver that yields recording sessions.
  - `__init__(self)` – No docstring.
  - `session(self, database=None)` – No docstring.

### Functions
- `_make_writer()` – Create a writer bound to a recording driver for inspection.
- `test_sync_artifact_creates_domain_relationships()` – Artifacts trigger the expected Cypher commands and relationships.
- `test_sync_artifact_merges_subsystem_edge_once()` – Syncing an artifact does not duplicate the subsystem relationship.
- `test_sync_chunks_links_chunk_to_artifact()` – Chunk synchronization creates chunk nodes and linking edges.

### Constants
- None

### Data Flow
- Primary entry points: `_make_writer`, `test_sync_artifact_creates_domain_relationships`, `test_sync_artifact_merges_subsystem_edge_once`, `test_sync_chunks_links_chunk_to_artifact`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, neo4j, pathlib, types, typing.

### Integration Points
- External: __future__, neo4j, pathlib, types, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 4 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 2 of 2
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 159


## tests/test_qdrant_writer.py
**Purpose**: Implements test qdrant writer

**Dependencies**:
- External: __future__, httpx, pytest, qdrant_client, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `stub_qdrant_models(monkeypatch)` – No docstring.
- `build_client(**kwargs)` – No docstring.
- `test_ensure_collection_creates_when_missing(monkeypatch)` – No docstring.
- `test_ensure_collection_noop_when_collection_exists()` – No docstring.
- `test_ensure_collection_retries_on_transient_failure(monkeypatch)` – No docstring.
- `test_ensure_collection_handles_conflict()` – No docstring.
- `test_reset_collection_invokes_recreate()` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `stub_qdrant_models`, `build_client`, `test_ensure_collection_creates_when_missing`, `test_ensure_collection_noop_when_collection_exists`, `test_ensure_collection_retries_on_transient_failure`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, httpx, pytest, qdrant_client, unittest.

### Integration Points
- External: __future__, httpx, pytest, qdrant_client, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 7
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 91


## tests/test_recipes_executor.py
**Purpose**: Implements test recipes executor

**Dependencies**:
- External: __future__, pathlib, pytest, types, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `FakeToolExecutor` (bases: object) – No docstring.
  - `__init__(self, responses)` – No docstring.
  - `async __aenter__(self)` – No docstring.
  - `async __aexit__(self, exc_type, exc, tb)` – No docstring.
  - `async call(self, tool, params)` – No docstring.

### Functions
- `async test_recipe_runner_success(tmp_path)` – No docstring.
- `async test_recipe_runner_wait(tmp_path)` – No docstring.
- `async test_recipe_runner_expect_failure(tmp_path)` – No docstring.
- `async test_recipe_runner_dry_run(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_recipe_runner_success`, `test_recipe_runner_wait`, `test_recipe_runner_expect_failure`, `test_recipe_runner_dry_run`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pathlib, pytest, types, typing.

### Integration Points
- External: __future__, pathlib, pytest, types, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 143


## tests/test_release_scripts.py
**Purpose**: Implements test release scripts

**Dependencies**:
- External: __future__, os, pathlib, subprocess
- Internal: None
**Related modules**: None

### Classes
- None

### Functions
- `_env_with_venv()` – No docstring.
- `test_build_wheel_script(tmp_path)` – No docstring.
- `test_checksums_script(tmp_path)` – No docstring.
- `test_generate_changelog(tmp_path)` – No docstring.

### Constants
- `REPO_ROOT` = Path(__file__).resolve().parents[1]
- `SCRIPTS_DIR` = REPO_ROOT / 'scripts'

### Data Flow
- Primary entry points: `_env_with_venv`, `test_build_wheel_script`, `test_checksums_script`, `test_generate_changelog`
- Touches external libraries: __future__, os, pathlib, subprocess.

### Integration Points
- External: __future__, os, pathlib, subprocess
- Internal: None

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 95


## tests/test_scheduler.py
**Purpose**: Unit tests exercising the ingestion scheduler behaviour and metrics.

**Dependencies**:
- External: __future__, apscheduler, collections, filelock, os, pathlib, prometheus_client, pytest, unittest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `reset_cache()` – Clear cached settings before and after each test.
- `scheduler_settings(tmp_path)` – Provide scheduler settings pointing at a temporary repo.
- `make_scheduler(settings)` – Instantiate a scheduler with its APScheduler stubbed out.
- `_metric_value(name, labels=None)` – Fetch a Prometheus sample value with defaults for missing metrics.
- `make_result(head)` – Construct a minimal ingestion result for scheduler tests.
- `test_scheduler_skips_when_repo_head_unchanged(scheduler_settings)` – Scheduler skips when repository head hash matches the cached value.
- `test_scheduler_runs_when_repo_head_changes(scheduler_settings)` – Scheduler triggers ingestion when the repository head changes.
- `test_scheduler_start_uses_interval_trigger(scheduler_settings)` – Schedulers without cron use the configured interval trigger.
- `test_scheduler_start_uses_cron_trigger(tmp_path)` – Cron expressions configure a cron trigger instead of interval.
- `test_scheduler_schedules_backup_job(tmp_path)` – Standalone backup schedules a job even when ingestion is disabled.
- `test_scheduler_backup_run_records_metrics(tmp_path, monkeypatch)` – Backup job updates metrics and retention tracking.
- `test_scheduler_backup_failure_records_metrics(tmp_path, monkeypatch)` – Failures set the status gauge and increment failure counters.
- `test_scheduler_skips_when_lock_contended(scheduler_settings)` – Lock contention causes the scheduler to skip runs and record metrics.
- `test_scheduler_requires_maintainer_token(tmp_path)` – Schedulers skip setup when auth is enabled without a maintainer token.

### Constants
- None

### Data Flow
- Primary entry points: `reset_cache`, `scheduler_settings`, `make_scheduler`, `_metric_value`, `make_result`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, apscheduler, collections, filelock, os, pathlib, prometheus_client, pytest, unittest.

### Integration Points
- External: __future__, apscheduler, collections, filelock, os, pathlib, prometheus_client, pytest, unittest
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 14 of 14
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 291


## tests/test_search_api.py
**Purpose**: Implements test search api

**Dependencies**:
- External: __future__, datetime, fastapi, json, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- `DummySearchService` (bases: object) – No docstring.
  - `__init__(self)` – No docstring.
  - `search(self, query, limit, include_graph, graph_service, sort_by_vector=False, request_id=None, filters=None)` – No docstring.

### Functions
- `test_search_endpoint_returns_results(monkeypatch, tmp_path)` – No docstring.
- `test_search_reuses_incoming_request_id(monkeypatch, tmp_path)` – No docstring.
- `test_search_requires_reader_token(monkeypatch, tmp_path)` – No docstring.
- `test_search_allows_maintainer_token(monkeypatch, tmp_path)` – No docstring.
- `test_search_feedback_logged(monkeypatch, tmp_path)` – No docstring.
- `test_search_filters_passed_to_service(monkeypatch, tmp_path)` – No docstring.
- `test_search_filters_invalid_type(monkeypatch, tmp_path)` – No docstring.
- `test_search_filters_invalid_namespaces(monkeypatch, tmp_path)` – No docstring.
- `test_search_filters_invalid_updated_after(monkeypatch, tmp_path)` – No docstring.
- `test_search_filters_invalid_max_age(monkeypatch, tmp_path)` – No docstring.
- `test_search_weights_endpoint(monkeypatch, tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_search_endpoint_returns_results`, `test_search_reuses_incoming_request_id`, `test_search_requires_reader_token`, `test_search_allows_maintainer_token`, `test_search_feedback_logged`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, fastapi, json, pathlib, pytest.

### Integration Points
- External: __future__, datetime, fastapi, json, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 11
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 1
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 329


## tests/test_search_cli_show_weights.py
**Purpose**: Implements test search cli show weights

**Dependencies**:
- External: __future__, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `clear_settings_cache(monkeypatch, tmp_path)` – No docstring.
- `test_show_weights_command(capsys)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `clear_settings_cache`, `test_show_weights_command`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pathlib, pytest.

### Integration Points
- External: __future__, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 2
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 25


## tests/test_search_evaluation.py
**Purpose**: Implements test search evaluation

**Dependencies**:
- External: __future__, json, math, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_evaluate_model(tmp_path)` – No docstring.
- `test_evaluate_cli(tmp_path, monkeypatch, capsys)` – No docstring.
- `test_evaluate_model_with_empty_dataset(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_evaluate_model`, `test_evaluate_cli`, `test_evaluate_model_with_empty_dataset`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, json, math, pathlib, pytest.

### Integration Points
- External: __future__, json, math, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 1
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 60


## tests/test_search_exporter.py
**Purpose**: Implements test search exporter

**Dependencies**:
- External: __future__, csv, json, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_write_events(path, events)` – No docstring.
- `_sample_event(request_id, vote)` – No docstring.
- `test_export_training_dataset_csv(tmp_path)` – No docstring.
- `test_export_training_data_cli(tmp_path, monkeypatch)` – No docstring.
- `test_train_model_from_dataset(tmp_path)` – No docstring.
- `test_train_model_cli(tmp_path, monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_write_events`, `_sample_event`, `test_export_training_dataset_csv`, `test_export_training_data_cli`, `test_train_model_from_dataset`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, csv, json, pathlib, pytest.

### Integration Points
- External: __future__, csv, json, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 144


## tests/test_search_feedback.py
**Purpose**: Implements test search feedback

**Dependencies**:
- External: __future__, pathlib, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_make_response(query, note)` – No docstring.
- `test_feedback_store_writes_entries(tmp_path)` – No docstring.
- `test_feedback_store_rotates_when_threshold_exceeded(tmp_path)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_make_response`, `test_feedback_store_writes_entries`, `test_feedback_store_rotates_when_threshold_exceeded`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pathlib, pytest.

### Integration Points
- External: __future__, pathlib, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 68


## tests/test_search_maintenance.py
**Purpose**: Tests for the search maintenance helpers.

**Dependencies**:
- External: __future__, datetime, json, os, pathlib, pytest, stat
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_write_events(path, requests)` – Write JSON lines representing feedback events for the supplied requests.
- `test_prune_feedback_log_parses_various_timestamp_formats(tmp_path)` – Ensure prune handles numeric, Z-suffixed, and missing timestamps.
- `test_prune_feedback_log_by_age(tmp_path)` – Retains only entries newer than the configured age threshold.
- `test_prune_feedback_log_missing_file(tmp_path)` – Raises if the feedback log file is absent.
- `test_prune_feedback_log_requires_limit(tmp_path)` – Rejects calls without an age or request limit configured.
- `test_prune_feedback_log_empty_file(tmp_path)` – Returns zeroed stats when the log contains no events.
- `test_prune_feedback_log_guard_when_pruning_everything(tmp_path, caplog)` – Leaves the log intact when filters would drop every request.
- `test_prune_feedback_log_max_requests_prefers_newest(tmp_path)` – Keeps only the newest requests when enforcing a max count.
- `test_redact_dataset_csv(tmp_path)` – Redacts populated CSV fields for queries, contexts, and notes.
- `test_redact_dataset_csv_handles_missing_and_blank_fields(tmp_path)` – Leaves missing or blank CSV fields untouched while redacting non-empty ones.
- `test_redact_dataset_jsonl(tmp_path)` – Redacts JSONL query and context fields when toggled.
- `test_redact_dataset_jsonl_handles_missing_and_blank_fields(tmp_path)` – Leaves absent or empty JSONL fields untouched while redacting populated ones.
- `test_redact_dataset_missing_file(tmp_path)` – Raises if the target dataset file is absent.
- `test_redact_dataset_unsupported_suffix(tmp_path)` – Rejects unsupported dataset extensions.
- `test_redact_dataset_output_path_copies_metadata(tmp_path)` – Preserves metadata when writing to an alternate output path.
- `test_redact_dataset_jsonl_handles_blank_lines(tmp_path)` – Preserves blank lines in JSONL datasets while redacting content.

### Constants
- None

### Data Flow
- Primary entry points: `_write_events`, `test_prune_feedback_log_parses_various_timestamp_formats`, `test_prune_feedback_log_by_age`, `test_prune_feedback_log_missing_file`, `test_prune_feedback_log_requires_limit`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, datetime, json, os, pathlib, pytest, stat.

### Integration Points
- External: __future__, datetime, json, os, pathlib, pytest, stat
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 16 of 16
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 371


## tests/test_search_profiles.py
**Purpose**: Implements test search profiles

**Dependencies**:
- External: __future__, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `clear_weight_env(monkeypatch)` – No docstring.
- `test_resolved_search_weights_default()` – No docstring.
- `test_resolved_search_weights_profile_selection(monkeypatch)` – No docstring.
- `test_resolved_search_weights_overrides(monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `clear_weight_env`, `test_resolved_search_weights_default`, `test_resolved_search_weights_profile_selection`, `test_resolved_search_weights_overrides`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pytest.

### Integration Points
- External: __future__, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 45


## tests/test_search_service.py
**Purpose**: Implements test search service

**Dependencies**:
- External: __future__, collections, datetime, prometheus_client, pytest, time, typing
- Internal: gateway
**Related modules**: gateway

### Classes
- `FakeEmbedder` (bases: object) – No docstring.
  - `encode(self, texts)` – No docstring.
- `FakePoint` (bases: object) – No docstring.
  - `__init__(self, payload, score)` – No docstring.
- `FakeQdrantClient` (bases: object) – No docstring.
  - `__init__(self, points)` – No docstring.
  - `search(self, **kwargs)` – No docstring.
- `DummyGraphService` (bases: GraphService) – No docstring.
  - `__init__(self, response)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
  - `get_subsystem(self, *args, **kwargs)` – No docstring.
  - `search(self, term, limit)` – No docstring.
  - `run_cypher(self, query, parameters)` – No docstring.
  - `shortest_path_depth(self, node_id, max_depth=4)` – No docstring.
- `SlowGraphService` (bases: DummyGraphService) – No docstring.
  - `__init__(self, response, delay)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
- `MapGraphService` (bases: GraphService) – No docstring.
  - `__init__(self, data)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
  - `get_subsystem(self, *args, **kwargs)` – No docstring.
  - `search(self, term, limit)` – No docstring.
  - `run_cypher(self, query, parameters)` – No docstring.
  - `shortest_path_depth(self, node_id, max_depth=4)` – No docstring.
- `CountingGraphService` (bases: GraphService) – No docstring.
  - `__init__(self, response, depth=2)` – No docstring.
  - `get_node(self, node_id, relationships, limit)` – No docstring.
  - `shortest_path_depth(self, node_id, max_depth=4)` – No docstring.
  - `get_subsystem(self, *args, **kwargs)` – No docstring.
  - `search(self, term, limit)` – No docstring.
  - `run_cypher(self, query, parameters)` – No docstring.

### Functions
- `_metric_value(name, labels=None)` – No docstring.
- `sample_points()` – No docstring.
- `graph_response()` – No docstring.
- `test_search_service_enriches_with_graph(sample_points, graph_response)` – No docstring.
- `test_search_service_handles_missing_graph(sample_points)` – No docstring.
- `test_search_hnsw_search_params(sample_points)` – No docstring.
- `test_lexical_score_affects_ranking()` – No docstring.
- `test_search_service_orders_by_adjusted_score()` – No docstring.
- `test_search_service_caches_graph_lookups(sample_points, graph_response)` – No docstring.
- `test_search_service_filters_artifact_types()` – No docstring.
- `test_search_service_filters_namespaces()` – No docstring.
- `test_search_service_filters_tags()` – No docstring.
- `test_search_service_filters_recency_updated_after()` – No docstring.
- `test_search_service_filters_recency_max_age_days()` – No docstring.
- `test_search_service_filters_subsystem_via_graph(graph_response)` – No docstring.
- `test_search_service_ml_model_reorders_results()` – No docstring.
- `test_search_service_limits_graph_results(graph_response)` – No docstring.
- `test_search_service_respects_graph_time_budget(graph_response)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `_metric_value`, `sample_points`, `graph_response`, `test_search_service_enriches_with_graph`, `test_search_service_handles_missing_graph`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, collections, datetime, prometheus_client, pytest, time, typing.

### Integration Points
- External: __future__, collections, datetime, prometheus_client, pytest, time, typing
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 18
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Class docstrings: 0 of 7
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 891


## tests/test_settings_defaults.py
**Purpose**: Implements test settings defaults

**Dependencies**:
- External: __future__, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_neo4j_database_defaults_to_neo4j(monkeypatch)` – No docstring.
- `test_neo4j_auth_enabled_defaults_true(monkeypatch)` – No docstring.
- `test_auth_enabled_defaults_true(monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_neo4j_database_defaults_to_neo4j`, `test_neo4j_auth_enabled_defaults_true`, `test_auth_enabled_defaults_true`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, pytest.

### Integration Points
- External: __future__, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 3
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 24


## tests/test_tracing.py
**Purpose**: Implements test tracing

**Dependencies**:
- External: __future__, opentelemetry, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `test_tracing_disabled_by_default(monkeypatch)` – No docstring.
- `test_tracing_enabled_instruments_app(monkeypatch)` – No docstring.
- `test_tracing_uses_otlp_exporter(monkeypatch)` – No docstring.
- `test_tracing_console_fallback(monkeypatch)` – No docstring.

### Constants
- None

### Data Flow
- Primary entry points: `test_tracing_disabled_by_default`, `test_tracing_enabled_instruments_app`, `test_tracing_uses_otlp_exporter`, `test_tracing_console_fallback`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, opentelemetry, pytest.

### Integration Points
- External: __future__, opentelemetry, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: no
- Function docstrings: 0 of 4
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 124


## tests/test_ui_routes.py
**Purpose**: Smoke tests covering the HTML console routes exposed by the gateway API.

**Dependencies**:
- External: __future__, fastapi, pathlib, prometheus_client, pytest
- Internal: gateway
**Related modules**: gateway

### Classes
- None

### Functions
- `_reset_settings(tmp_path=None)` – Clear cached settings and ensure the state directory exists for tests.
- `test_ui_landing_served(tmp_path, monkeypatch)` – The landing page renders successfully and increments the landing metric.
- `test_ui_search_view(tmp_path, monkeypatch)` – The search view renders and increments the search metric.
- `test_ui_subsystems_view(tmp_path, monkeypatch)` – The subsystems view renders and increments the subsystem metric.
- `test_ui_lifecycle_download(tmp_path, monkeypatch)` – Lifecycle report downloads are returned and recorded in metrics.
- `test_ui_events_endpoint(tmp_path, monkeypatch)` – Custom UI events are accepted and reflected in Prometheus metrics.

### Constants
- None

### Data Flow
- Primary entry points: `_reset_settings`, `test_ui_landing_served`, `test_ui_search_view`, `test_ui_subsystems_view`, `test_ui_lifecycle_download`
- Delegates to internal modules: gateway.
- Touches external libraries: __future__, fastapi, pathlib, prometheus_client, pytest.

### Integration Points
- External: __future__, fastapi, pathlib, prometheus_client, pytest
- Internal: gateway

### Code Quality Notes
- Module docstring present: yes
- Function docstrings: 6 of 6
- Parameter annotations coverage: 100%
- Return annotations coverage: 100%
- Try/except blocks: 0
- Logging used: no
- TODO/FIXME markers: 0
- Approximate lines: 138

