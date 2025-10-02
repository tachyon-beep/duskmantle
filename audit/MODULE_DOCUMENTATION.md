# Module Documentation

## gateway/__init__.py

**File path**: `gateway/__init__.py`
**Purpose**: Core package for the Duskmantle knowledge gateway.
**Dependencies**: External – __future__; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `get_version() — Return the current package version.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/__main__.py

**File path**: `gateway/__main__.py`
**Purpose**: Console entry point that launches the FastAPI application.
**Dependencies**: External – __future__, uvicorn; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `main() — Run the gateway API using Uvicorn.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/api/__init__.py

**File path**: `gateway/api/__init__.py`
**Purpose**: API layer for the knowledge gateway.
**Dependencies**: External – None; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/api/app.py

**File path**: `gateway/api/app.py`
**Purpose**: Primary FastAPI application wiring for the knowledge gateway.
**Dependencies**: External – __future__, apscheduler.schedulers.base, collections, contextlib, fastapi, fastapi.responses, fastapi.staticfiles, json, logging, neo4j, neo4j.exceptions, qdrant_client, slowapi, slowapi.errors, slowapi.middleware, slowapi.util, time, typing, uuid; Internal – gateway, gateway.api.dependencies, gateway.api.routes, gateway.config.settings, gateway.graph, gateway.graph.migrations, gateway.observability, gateway.scheduler, gateway.search.feedback, gateway.search.trainer, gateway.ui
**Related modules**: gateway, gateway.api.dependencies, gateway.api.routes, gateway.config.settings, gateway.graph, gateway.graph.migrations, gateway.observability, gateway.scheduler, gateway.search.feedback, gateway.search.trainer, gateway.ui

**Classes**
- None

**Functions**
- `_validate_auth_settings(settings) — No docstring.`
- `_log_startup_configuration(settings) — No docstring.`
- `_build_lifespan(settings) — No docstring.`
- `_configure_rate_limits(app, settings) — No docstring.`
- `_init_feedback_store(settings) — No docstring.`
- `_load_search_model(settings) — No docstring.`
- `_init_graph_driver(settings) — No docstring.`
- `_init_qdrant_client(settings) — No docstring.`
- `_create_graph_driver(settings) — No docstring.`
- `_verify_graph_database(driver, database) — No docstring.`
- `_run_graph_auto_migration(driver, database) — No docstring.`
- `_fetch_pending_migrations(runner) — No docstring.`
- `_log_migration_plan(pending) — No docstring.`
- `_log_migration_completion(pending) — No docstring.`
- `_set_migration_metrics(status) — No docstring.`
- `create_app() — Create the FastAPI application instance.`
- `_rate_limit_handler(_request, exc) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Bootstraps FastAPI, initialises shared state, and wires route dependencies.

**Integration Points**
- FastAPI
- Neo4j driver
- Qdrant client
- SlowAPI rate limiting

**Code Quality Notes**
- Functions missing docstrings.

## gateway/api/auth.py

**File path**: `gateway/api/auth.py`
**Purpose**: Authentication dependencies used across the FastAPI surface.
**Dependencies**: External – __future__, collections, fastapi, fastapi.security; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

**Classes**
- None

**Functions**
- `require_scope(scope) — Return a dependency enforcing the given scope.`
- `_allowed_tokens_for_scope(settings, scope) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI

**Code Quality Notes**
- Functions missing docstrings.

## gateway/api/dependencies.py

**File path**: `gateway/api/dependencies.py`
**Purpose**: FastAPI dependency helpers for the gateway application.
**Dependencies**: External – __future__, fastapi, logging, slowapi; Internal – gateway.config.settings, gateway.graph, gateway.ingest.embedding, gateway.search, gateway.search.feedback, gateway.search.trainer
**Related modules**: gateway.config.settings, gateway.graph, gateway.ingest.embedding, gateway.search, gateway.search.feedback, gateway.search.trainer

**Classes**
- None

**Functions**
- `get_app_settings(request) — Return the application settings attached to the FastAPI app.`
- `get_limiter(request) — Return the rate limiter configured on the FastAPI app.`
- `get_search_model(request) — Return the cached search ranking model from application state.`
- `get_graph_service_dependency(request) — Return a memoised graph service bound to the current FastAPI app.`
- `get_search_service_dependency(request) — Construct (and cache) the hybrid search service for the application.`
- `get_feedback_store(request) — Return the configured search feedback store, if any.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- SlowAPI rate limiting

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/api/routes/__init__.py

**File path**: `gateway/api/routes/__init__.py`
**Purpose**: FastAPI route modules for the gateway application.
**Dependencies**: External – None; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/api/routes/graph.py

**File path**: `gateway/api/routes/graph.py`
**Purpose**: Graph API routes.
**Dependencies**: External – __future__, fastapi, fastapi.responses, slowapi, typing; Internal – gateway.api.auth, gateway.api.dependencies, gateway.graph
**Related modules**: gateway.api.auth, gateway.api.dependencies, gateway.graph

**Classes**
- None

**Functions**
- `create_router(limiter, metrics_limit) — Create an API router exposing graph endpoints with shared rate limits.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- SlowAPI rate limiting

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/api/routes/health.py

**File path**: `gateway/api/routes/health.py`
**Purpose**: Health and observability endpoints.
**Dependencies**: External – __future__, contextlib, fastapi, json, prometheus_client, slowapi, sqlite3, time, typing; Internal – gateway.api.dependencies, gateway.config.settings
**Related modules**: gateway.api.dependencies, gateway.config.settings

**Classes**
- None

**Functions**
- `create_router(limiter, metrics_limit) — Wire up health, readiness, and metrics endpoints.`
- `build_health_report(app, settings) — Assemble the health payload consumed by `/healthz`.`
- `_coverage_health(settings) — No docstring.`
- `_audit_health(settings) — No docstring.`
- `_scheduler_health(app, settings) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- SlowAPI rate limiting

**Code Quality Notes**
- Functions missing docstrings.

## gateway/api/routes/reporting.py

**File path**: `gateway/api/routes/reporting.py`
**Purpose**: Observability and reporting routes.
**Dependencies**: External – __future__, fastapi, fastapi.responses, json, pathlib, slowapi, typing; Internal – gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.ingest.audit, gateway.ingest.lifecycle
**Related modules**: gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.ingest.audit, gateway.ingest.lifecycle

**Classes**
- None

**Functions**
- `create_router(limiter) — Expose reporting and audit endpoints protected by maintainer auth.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- SlowAPI rate limiting

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/api/routes/search.py

**File path**: `gateway/api/routes/search.py`
**Purpose**: Search API routes.
**Dependencies**: External – __future__, collections, datetime, fastapi, fastapi.responses, logging, qdrant_client.http.exceptions, slowapi, typing, uuid; Internal – gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.graph, gateway.observability, gateway.search, gateway.search.feedback
**Related modules**: gateway.api.auth, gateway.api.dependencies, gateway.config.settings, gateway.graph, gateway.observability, gateway.search, gateway.search.feedback

**Classes**
- None

**Functions**
- `create_router(limiter, metrics_limit) — Return an API router for the search endpoints with shared rate limits.`
- `_parse_iso8601_to_utc(value) — No docstring.`
- `_has_vote(mapping) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- SlowAPI rate limiting

**Code Quality Notes**
- Functions missing docstrings.

## gateway/config/__init__.py

**File path**: `gateway/config/__init__.py`
**Purpose**: Configuration helpers for the knowledge gateway.
**Dependencies**: External – __future__, settings; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/config/settings.py

**File path**: `gateway/config/settings.py`
**Purpose**: Pydantic-based configuration for the knowledge gateway.
**Dependencies**: External – __future__, functools, pathlib, pydantic, pydantic_settings, typing; Internal – None
**Related modules**: None

**Classes**
- AppSettings (bases: BaseSettings) — Runtime configuration for the knowledge gateway. Methods: _clamp_tracing_ratio(cls, value), _clamp_search_weights(cls, value), _sanitize_hnsw_ef(cls, value), _sanitize_graph_cache_ttl(cls, value), _sanitize_graph_cache_max(cls, value), resolved_search_weights(self), scheduler_trigger_config(self), _validate_history_limit(cls, value), _validate_lifecycle_stale(cls, value), _ensure_positive_parallelism(cls, value).

**Functions**
- `get_settings() — Load settings from environment (cached).`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/graph/__init__.py

**File path**: `gateway/graph/__init__.py`
**Purpose**: Graph query utilities and service layer.
**Dependencies**: External – service; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/graph/cli.py

**File path**: `gateway/graph/cli.py`
**Purpose**: Command-line utilities for managing the Neo4j graph schema.
**Dependencies**: External – __future__, argparse, logging, neo4j; Internal – gateway.config.settings, gateway.graph.migrations
**Related modules**: gateway.config.settings, gateway.graph.migrations

**Classes**
- None

**Functions**
- `build_parser() — Return the CLI argument parser for graph administration commands.`
- `run_migrations() — Execute graph schema migrations, optionally printing the pending set.`
- `main(argv) — Entrypoint for the `gateway-graph` command-line interface.`

**Constants and Configuration**
- None

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/graph/migrations/__init__.py

**File path**: `gateway/graph/migrations/__init__.py`
**Purpose**: Graph schema migrations.
**Dependencies**: External – runner; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/graph/migrations/runner.py

**File path**: `gateway/graph/migrations/runner.py`
**Purpose**: Helpers for applying and tracking Neo4j schema migrations.
**Dependencies**: External – __future__, collections, dataclasses, logging, neo4j; Internal – None
**Related modules**: None

**Classes**
- Migration (bases: object) — Describe a single migration and the Cypher statements it executes. Methods: None.
- MigrationRunner (bases: object) — Apply ordered graph migrations using a shared Neo4j driver. Methods: pending_ids(self), run(self), _is_applied(self, migration_id), _apply(self, migration).

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/graph/service.py

**File path**: `gateway/graph/service.py`
**Purpose**: Read-only graph service utilities backed by Neo4j.
**Dependencies**: External – __future__, base64, collections, dataclasses, neo4j, neo4j.graph, threading, time, typing; Internal – None
**Related modules**: None

**Classes**
- GraphServiceError (bases: RuntimeError) — Base class for graph-related errors. Methods: None.
- GraphNotFoundError (bases: GraphServiceError) — Raised when a requested node cannot be found. Methods: None.
- GraphQueryError (bases: GraphServiceError) — Raised when a supplied query is invalid or unsafe. Methods: None.
- SubsystemGraphSnapshot (bases: object) — Snapshot of a subsystem node and its related graph context. Methods: None.
- SubsystemGraphCache (bases: object) — Simple TTL cache for subsystem graph snapshots. Methods: __init__(self, ttl_seconds, max_entries), get(self, key), set(self, key, snapshot), clear(self).
- GraphService (bases: object) — Service layer for read-only graph queries. Methods: get_subsystem(self, name), get_subsystem_graph(self, name), list_orphan_nodes(self), clear_cache(self), _load_subsystem_snapshot(self, name, depth), _build_subsystem_snapshot(self, name, depth), get_node(self, node_id), search(self, term), shortest_path_depth(self, node_id), run_cypher(self, query, parameters).

**Functions**
- `get_graph_service(driver, database) — Factory helper that constructs a `GraphService` with optional caching.`
- `_extract_path_components(record) — No docstring.`
- `_record_path_edges(path_nodes, relationships, nodes_by_id, edges_by_key) — No docstring.`
- `_ensure_serialized_node(node, nodes_by_id) — No docstring.`
- `_relationship_direction(relationship, source_node) — No docstring.`
- `_build_related_entry(target_serialized, relationships, path_edges) — No docstring.`
- `_append_related_entry(entry, target_id, related_entries, related_order) — No docstring.`
- `_fetch_subsystem_node(name) — No docstring.`
- `_fetch_subsystem_paths(name, depth) — No docstring.`
- `_fetch_artifacts_for_subsystem(name) — No docstring.`
- `_fetch_orphan_nodes(label, skip, limit) — No docstring.`
- `_fetch_node_by_id(label, key, value) — No docstring.`
- `_fetch_node_relationships(label, key, value, direction, limit) — No docstring.`
- `_search_entities(term, limit) — No docstring.`
- `_serialize_related(record, subsystem_node) — No docstring.`
- `_serialize_node(node) — No docstring.`
- `_serialize_relationship(record) — No docstring.`
- `_serialize_value(value) — No docstring.`
- `_ensure_node(value) — No docstring.`
- `_node_element_id(node) — No docstring.`
- `_canonical_node_id(node) — No docstring.`
- `_parse_node_id(node_id) — No docstring.`
- `_encode_cursor(offset) — No docstring.`
- `_decode_cursor(cursor) — No docstring.`
- `_validate_cypher(query) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- Functions missing docstrings.

## gateway/ingest/__init__.py

**File path**: `gateway/ingest/__init__.py`
**Purpose**: Ingestion pipeline components for the knowledge gateway.
**Dependencies**: External – None; Internal – gateway.ingest.pipeline
**Related modules**: gateway.ingest.pipeline

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/artifacts.py

**File path**: `gateway/ingest/artifacts.py`
**Purpose**: Domain models representing artifacts produced during ingestion.
**Dependencies**: External – __future__, dataclasses, pathlib, typing; Internal – None
**Related modules**: None

**Classes**
- Artifact (bases: object) — Represents a repository artifact prior to chunking. Methods: None.
- Chunk (bases: object) — Represents a chunk ready for embedding and indexing. Methods: None.
- ChunkEmbedding (bases: object) — Chunk plus embedding vector. Methods: None.

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/audit.py

**File path**: `gateway/ingest/audit.py`
**Purpose**: SQLite-backed audit log utilities for ingestion runs.
**Dependencies**: External – __future__, pathlib, sqlite3, time, typing; Internal – gateway.ingest.pipeline
**Related modules**: gateway.ingest.pipeline

**Classes**
- AuditLogger (bases: object) — Persist and retrieve ingestion run metadata in SQLite. Methods: __init__(self, db_path), record(self, result), recent(self, limit).

**Functions**
- None

**Constants and Configuration**
- _SCHEMA = """
- _SELECT_RECENT = """
- _INSERT_RUN = """

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/chunking.py

**File path**: `gateway/ingest/chunking.py`
**Purpose**: Chunk source artifacts into overlapping windows for indexing.
**Dependencies**: External – __future__, collections, hashlib, math, pathlib, typing; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

**Classes**
- Chunker (bases: object) — Split artifacts into overlapping textual chunks. Methods: __init__(self, window, overlap), split(self, artifact), estimate_chunk_count(path, text).

**Functions**
- `_derive_namespace(path) — Infer a namespace from a file path for tagging chunks.`
- `_build_tags(extra_metadata) — Collect tag-like signals from artifact metadata.`

**Constants and Configuration**
- DEFAULT_WINDOW = 1000
- DEFAULT_OVERLAP = 200

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/cli.py

**File path**: `gateway/ingest/cli.py`
**Purpose**: Command-line helpers for triggering and inspecting ingestion runs.
**Dependencies**: External – __future__, argparse, collections, datetime, logging, pathlib, rich.console, rich.table; Internal – gateway.config.settings, gateway.ingest.audit, gateway.ingest.service, gateway.observability
**Related modules**: gateway.config.settings, gateway.ingest.audit, gateway.ingest.service, gateway.observability

**Classes**
- None

**Functions**
- `_ensure_maintainer_scope(settings) — Abort execution if maintainer credentials are missing during auth.`
- `build_parser() — Create an argument parser for the ingestion CLI.`
- `rebuild() — Execute a full ingestion pass.`
- `audit_history() — Display recent ingestion runs from the audit ledger.`
- `_render_audit_table(entries) — Render recent audit entries as a Rich table.`
- `_format_timestamp(raw) — Format timestamps from the audit ledger for display.`
- `_coerce_int(value) — Attempt to interpret the value as an integer.`
- `_coerce_float(value) — Attempt to interpret the value as a floating point number.`
- `main(argv) — Entry point for the CLI.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/coverage.py

**File path**: `gateway/ingest/coverage.py`
**Purpose**: Utilities for writing ingestion coverage reports.
**Dependencies**: External – __future__, contextlib, datetime, json, pathlib, time; Internal – gateway.ingest.pipeline, gateway.observability.metrics
**Related modules**: gateway.ingest.pipeline, gateway.observability.metrics

**Classes**
- None

**Functions**
- `write_coverage_report(result, config) — Persist coverage metrics derived from an ingestion result.`
- `_write_history_snapshot(payload, reports_dir, history_limit) — Write coverage history snapshots and prune old entries.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/discovery.py

**File path**: `gateway/ingest/discovery.py`
**Purpose**: Repository discovery helpers for ingestion pipeline.
**Dependencies**: External – __future__, collections, dataclasses, fnmatch, json, logging, pathlib, re, subprocess, tomli, tomllib, typing; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

**Classes**
- DiscoveryConfig (bases: object) — Runtime knobs influencing which artifacts are discovered. Methods: None.

**Functions**
- `discover(config) — Yield textual artifacts from the repository.`
- `_should_include(path, repo_root, include_patterns) — No docstring.`
- `_is_textual(path) — No docstring.`
- `_infer_artifact_type(path, repo_root) — No docstring.`
- `_lookup_git_metadata(path, repo_root) — No docstring.`
- `_load_subsystem_catalog(repo_root) — No docstring.`
- `_detect_source_prefixes(repo_root) — Infer source package prefixes (e.g. ``("src", "gateway")``).`
- `_collect_pyproject_prefixes(root, prefixes) — No docstring.`
- `_load_pyproject(path) — No docstring.`
- `_collect_poetry_prefixes(tool_cfg, prefixes) — No docstring.`
- `_collect_project_prefixes(project_cfg, prefixes) — No docstring.`
- `_collect_setuptools_prefixes(tool_cfg, prefixes) — No docstring.`
- `_collect_src_directory_prefixes(root, prefixes) — No docstring.`
- `_add_prefix(prefixes, include, base) — No docstring.`
- `_ensure_str_list(value) — No docstring.`
- `_infer_subsystem(path, repo_root, source_prefixes) — No docstring.`
- `_normalize_subsystem_name(value) — No docstring.`
- `_match_catalog_entry(path, repo_root, catalog) — No docstring.`
- `_iter_metadata_patterns(metadata) — No docstring.`
- `_pattern_matches(target, pattern) — No docstring.`
- `dump_artifacts(artifacts) — Serialize artifacts for debugging or dry-run output.`

**Constants and Configuration**
- _TEXTUAL_SUFFIXES = {
- _MESSAGE_PATTERN = re.compile(r"[A-Z]\w*Message")
- _TELEMETRY_PATTERN = re.compile(r"Telemetry\w+")

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/ingest/embedding.py

**File path**: `gateway/ingest/embedding.py`
**Purpose**: Embedding helpers used during ingestion.
**Dependencies**: External – __future__, collections, functools, logging, sentence_transformers; Internal – None
**Related modules**: None

**Classes**
- Embedder (bases: object) — Wrapper around sentence-transformers for configurable embeddings. Methods: __init__(self, model_name), dimension(self), encode(self, texts), _load_model(model_name).
- DummyEmbedder (bases: Embedder) — Deterministic embedder for dry-runs and tests. Methods: __init__(self), dimension(self), encode(self, texts).

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/lifecycle.py

**File path**: `gateway/ingest/lifecycle.py`
**Purpose**: Lifecycle reporting helpers for ingestion outputs.
**Dependencies**: External – __future__, collections, contextlib, dataclasses, datetime, json, neo4j, pathlib, time, typing; Internal – gateway.graph, gateway.ingest.pipeline, gateway.observability.metrics
**Related modules**: gateway.graph, gateway.ingest.pipeline, gateway.observability.metrics

**Classes**
- LifecycleConfig (bases: object) — Configuration values that influence lifecycle report generation. Methods: None.

**Functions**
- `write_lifecycle_report(result) — Persist lifecycle insights derived from the most recent ingest run.`
- `build_graph_service() — Construct a graph service with sensible defaults for lifecycle usage.`
- `summarize_lifecycle(payload) — Produce a summarized view of lifecycle data for reporting.`
- `_fetch_isolated_nodes(graph_service) — Collect isolated graph nodes grouped by label.`
- `_find_stale_docs(artifacts, stale_days, now) — Identify design documents that are older than the stale threshold.`
- `_find_missing_tests(artifacts) — Determine subsystems lacking corresponding tests.`
- `_write_history_snapshot(payload, reports_dir, history_limit) — Write lifecycle history to disk while enforcing retention.`
- `_coerce_float(value) — Coerce numeric-like values to float when possible.`
- `_lifecycle_counts() — Aggregate lifecycle metrics into counters.`

**Constants and Configuration**
- SECONDS_PER_DAY = 60 * 60 * 24

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/neo4j_writer.py

**File path**: `gateway/ingest/neo4j_writer.py`
**Purpose**: Write ingestion artifacts and chunks into Neo4j.
**Dependencies**: External – __future__, collections, logging, neo4j; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

**Classes**
- Neo4jWriter (bases: object) — Persist artifacts and derived data into a Neo4j database. Methods: __init__(self, driver, database), ensure_constraints(self), sync_artifact(self, artifact), sync_chunks(self, chunk_embeddings), delete_artifact(self, path).

**Functions**
- `_artifact_label(artifact) — Map artifact types to Neo4j labels.`
- `_label_for_type(artifact_type) — Return the default label for the given artifact type.`
- `_relationship_for_label(label) — Return the relationship used to link artifacts to subsystems.`
- `_clean_string_list(values) — No docstring.`
- `_normalize_subsystem_name(value) — No docstring.`
- `_extract_dependencies(metadata) — No docstring.`
- `_subsystem_properties(metadata) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- Functions missing docstrings.

## gateway/ingest/pipeline.py

**File path**: `gateway/ingest/pipeline.py`
**Purpose**: Pipeline orchestrations for ingestion, chunking, and persistence.
**Dependencies**: External – __future__, collections, concurrent.futures, dataclasses, hashlib, json, logging, opentelemetry, opentelemetry.trace, pathlib, subprocess, time, uuid; Internal – gateway.ingest.artifacts, gateway.ingest.chunking, gateway.ingest.discovery, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.qdrant_writer, gateway.observability.metrics
**Related modules**: gateway.ingest.artifacts, gateway.ingest.chunking, gateway.ingest.discovery, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.qdrant_writer, gateway.observability.metrics

**Classes**
- IngestionConfig (bases: object) — Configuration options controlling ingestion behaviour. Methods: None.
- IngestionResult (bases: object) — Summary of outputs emitted by an ingestion run. Methods: None.
- IngestionPipeline (bases: object) — Execute the ingestion workflow end-to-end. Methods: __init__(self, qdrant_writer, neo4j_writer, config), run(self), _build_embedder(self), _encode_batch(self, embedder, chunks), _build_embeddings(self, chunks, vectors), _persist_embeddings(self, embeddings), _handle_stale_artifacts(self, previous, current, profile), _delete_artifact_from_backends(self, path), _load_artifact_ledger(self), _write_artifact_ledger(self, entries).

**Functions**
- `_current_repo_head(repo_root) — No docstring.`
- `_coerce_int(value) — No docstring.`
- `_coerce_float(value) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Streams discovered artifacts through chunking, embedding, and persistence to Neo4j/Qdrant.

**Integration Points**
- OpenTelemetry

**Code Quality Notes**
- Functions missing docstrings.

## gateway/ingest/qdrant_writer.py

**File path**: `gateway/ingest/qdrant_writer.py`
**Purpose**: Helpers for writing chunk embeddings into Qdrant collections.
**Dependencies**: External – __future__, collections, logging, qdrant_client, qdrant_client.http, qdrant_client.http.exceptions, uuid; Internal – gateway.ingest.artifacts
**Related modules**: gateway.ingest.artifacts

**Classes**
- QdrantWriter (bases: object) — Lightweight adapter around the Qdrant client. Methods: __init__(self, client, collection_name), ensure_collection(self, vector_size), upsert_chunks(self, chunks), delete_artifact(self, artifact_path).

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Interacts with Qdrant collections for vector storage and retrieval.

**Integration Points**
- Qdrant client

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ingest/service.py

**File path**: `gateway/ingest/service.py`
**Purpose**: High-level orchestration routines for running ingestion.
**Dependencies**: External – __future__, logging, neo4j, pathlib, qdrant_client; Internal – gateway.config.settings, gateway.ingest.audit, gateway.ingest.coverage, gateway.ingest.lifecycle, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.ingest.qdrant_writer
**Related modules**: gateway.config.settings, gateway.ingest.audit, gateway.ingest.coverage, gateway.ingest.lifecycle, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.ingest.qdrant_writer

**Classes**
- None

**Functions**
- `execute_ingestion() — Run ingestion using shared settings and return result.`

**Constants and Configuration**
- None

**Data Flow**
- Interacts with Qdrant collections for vector storage and retrieval.

**Integration Points**
- Neo4j driver
- Qdrant client

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/lifecycle/__init__.py

**File path**: `gateway/lifecycle/__init__.py`
**Purpose**: Lifecycle reporting package.
**Dependencies**: External – None; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/lifecycle/cli.py

**File path**: `gateway/lifecycle/cli.py`
**Purpose**: Command-line utilities for inspecting lifecycle health reports.
**Dependencies**: External – __future__, argparse, collections, datetime, json, pathlib, rich.console, rich.table; Internal – gateway.config.settings, gateway.observability
**Related modules**: gateway.config.settings, gateway.observability

**Classes**
- None

**Functions**
- `build_parser() — Create the CLI argument parser shared across entrypoints.`
- `render_table(payload) — Pretty-print the lifecycle report payload using Rich tables.`
- `_render_isolated_nodes(value) — Render the isolated node section when data is present.`
- `_render_stale_docs(value) — Render the stale documentation summary rows.`
- `_render_missing_tests(value) — Render subsystems missing tests in a tabular format.`
- `_format_timestamp(value) — Convert a timestamp-like input into an ISO formatted string.`
- `main(argv) — CLI entry point for lifecycle reporting.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/__init__.py

**File path**: `gateway/mcp/__init__.py`
**Purpose**: Model Context Protocol server integration for the knowledge gateway.
**Dependencies**: External – config, server; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/backup.py

**File path**: `gateway/mcp/backup.py`
**Purpose**: Backup helpers for the MCP server.
**Dependencies**: External – __future__, asyncio, config, exceptions, os, pathlib, re, typing; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `_parse_archive_path(output) — No docstring.`
- `_default_backup_script() — No docstring.`

**Constants and Configuration**
- _BACKUP_DONE_PATTERN = re.compile(r"Backup written to (?P<path>.+)$")

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/mcp/cli.py

**File path**: `gateway/mcp/cli.py`
**Purpose**: Command-line entry point for the MCP server.
**Dependencies**: External – __future__, argparse, collections, config, logging, server, sys; Internal – gateway
**Related modules**: gateway

**Classes**
- None

**Functions**
- `build_parser() — Return the CLI parser for launching the MCP server.`
- `main(argv) — Entry point for the MCP server management CLI.`

**Constants and Configuration**
- _TRANSPORT_CHOICES = ["stdio", "http", "sse", "streamable-http"]

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/client.py

**File path**: `gateway/mcp/client.py`
**Purpose**: HTTP client for interacting with the gateway API.
**Dependencies**: External – __future__, collections, config, exceptions, httpx, json, logging, types, typing, urllib.parse; Internal – None
**Related modules**: None

**Classes**
- GatewayClient (bases: object) — Thin async wrapper over the gateway REST API. Methods: __init__(self, settings), settings(self).

**Functions**
- `_extract_error_detail(response) — Extract a human-readable error detail from an HTTP response.`
- `_safe_json(response) — Safely decode a JSON response, returning ``None`` on failure.`
- `_quote_segment(value) — No docstring.`
- `_expect_dict(data, operation) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/mcp/config.py

**File path**: `gateway/mcp/config.py`
**Purpose**: Configuration for the MCP adapter.
**Dependencies**: External – __future__, pathlib, pydantic, pydantic_settings, typing; Internal – None
**Related modules**: None

**Classes**
- MCPSettings (bases: BaseSettings) — Settings controlling the MCP server runtime. Methods: None.

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/exceptions.py

**File path**: `gateway/mcp/exceptions.py`
**Purpose**: Custom exceptions for the MCP adapter.
**Dependencies**: External – __future__; Internal – None
**Related modules**: None

**Classes**
- MCPAdapterError (bases: Exception) — Base error raised by the MCP bridge. Methods: None.
- GatewayRequestError (bases: MCPAdapterError) — Raised when the gateway API returns an error response. Methods: __init__(self).
- MissingTokenError (bases: MCPAdapterError) — Raised when a privileged operation lacks an authentication token. Methods: __init__(self, scope).
- BackupExecutionError (bases: MCPAdapterError) — Raised when the backup helper fails to produce an archive. Methods: None.

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/feedback.py

**File path**: `gateway/mcp/feedback.py`
**Purpose**: Feedback logging utilities used by MCP tools.
**Dependencies**: External – __future__, asyncio, collections, config, datetime, json, pathlib, typing; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `_append_line(path, line) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/mcp/ingest.py

**File path**: `gateway/mcp/ingest.py`
**Purpose**: Helpers for managing ingestion workflows via MCP.
**Dependencies**: External – __future__, asyncio, config, dataclasses, typing; Internal – gateway.config.settings, gateway.ingest.service
**Related modules**: gateway.config.settings, gateway.ingest.service

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/server.py

**File path**: `gateway/mcp/server.py`
**Purpose**: FastMCP server exposing the knowledge gateway.
**Dependencies**: External – __future__, backup, client, collections, config, contextlib, datetime, exceptions, fastmcp, feedback, functools, ingest, json, pathlib, storetext, textwrap, time, typing, upload; Internal – gateway, gateway.observability.metrics
**Related modules**: gateway, gateway.observability.metrics

**Classes**
- MCPServerState (bases: object) — Holds shared state for the MCP server lifespan. Methods: __init__(self, settings), require_client(self), lifespan(self).

**Functions**
- `build_server(settings) — Create a FastMCP server wired to the gateway API.`
- `_record_success(tool, start) — No docstring.`
- `_record_failure(tool, exc, start) — No docstring.`
- `_clamp(value) — No docstring.`
- `_normalise_filters(payload) — No docstring.`
- `_resolve_usage(tool) — No docstring.`
- `_ensure_maintainer_scope(settings) — No docstring.`
- `_append_audit_entry(settings) — No docstring.`
- `_load_help_document() — No docstring.`
- `_initialise_metric_labels() — No docstring.`

**Constants and Configuration**
- TOOL_USAGE = {
- HELP_DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "MCP_INTERFACE_SPEC.md"

**Data Flow**
- Implements FastMCP tools that proxy requests into the gateway API.

**Integration Points**
- FastMCP

**Code Quality Notes**
- Functions missing docstrings.

## gateway/mcp/storetext.py

**File path**: `gateway/mcp/storetext.py`
**Purpose**: Handlers for storing text via MCP.
**Dependencies**: External – __future__, datetime, ingest, pathlib, typing; Internal – gateway.mcp.config, gateway.mcp.utils.files
**Related modules**: gateway.mcp.config, gateway.mcp.utils.files

**Classes**
- None

**Functions**
- `_build_filename(title) — No docstring.`
- `_normalise_destination(destination, default_dir, filename) — No docstring.`
- `_compose_content() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/mcp/upload.py

**File path**: `gateway/mcp/upload.py`
**Purpose**: Handlers for MCP file uploads.
**Dependencies**: External – __future__, ingest, pathlib, typing; Internal – gateway.mcp.config, gateway.mcp.utils.files
**Related modules**: gateway.mcp.config, gateway.mcp.utils.files

**Classes**
- None

**Functions**
- `_resolve_destination(destination, default_dir, filename) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/mcp/utils/__init__.py

**File path**: `gateway/mcp/utils/__init__.py`
**Purpose**: Initialise the utils package namespace.
**Dependencies**: External – None; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/mcp/utils/files.py

**File path**: `gateway/mcp/utils/files.py`
**Purpose**: Shared helpers for MCP content management.
**Dependencies**: External – __future__, collections, dataclasses, os, pathlib, re, shutil, unicodedata; Internal – None
**Related modules**: None

**Classes**
- DocumentCopyResult (bases: object) — Result of an attempted document copy. Methods: None.
- DocumentCopyError (bases: Exception) — Raised when a copy operation fails fatally. Methods: None.

**Functions**
- `slugify(value) — Create a filesystem-friendly slug.`
- `is_supported_document(path) — Return ``True`` if the path has a supported document extension.`
- `_assert_within_root(root, candidate) — Ensure ``candidate`` is within ``root`` to prevent path traversal.`
- `sweep_documents(root, target) — Copy supported documents under ``root`` into ``target``.`
- `copy_into_root(source, root, destination) — Copy ``source`` into ``root``.`
- `write_text_document(content, root, relative_path) — Write ``content`` to ``root / relative_path`` ensuring safety.`

**Constants and Configuration**
- SUPPORTED_EXTENSIONS = {".md", ".docx", ".txt", ".doc", ".pdf"}
- _SLUG_REGEX = re.compile(r"[^a-z0-9]+")

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/observability/__init__.py

**File path**: `gateway/observability/__init__.py`
**Purpose**: Observability utilities (metrics, logging, tracing).
**Dependencies**: External – logging, metrics, tracing; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/observability/logging.py

**File path**: `gateway/observability/logging.py`
**Purpose**: Structured logging configuration for the gateway.
**Dependencies**: External – __future__, logging, pythonjsonlogger, sys, typing; Internal – None
**Related modules**: None

**Classes**
- IngestAwareFormatter (bases: json.JsonFormatter) — JSON formatter that enforces consistent keys. Methods: add_fields(self, log_record, record, message_dict).

**Functions**
- `configure_logging() — Configure root logging with a JSON formatter once per process.`

**Constants and Configuration**
- _LOG_CONFIGURED = False

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/observability/metrics.py

**File path**: `gateway/observability/metrics.py`
**Purpose**: Prometheus metric definitions for the knowledge gateway.
**Dependencies**: External – __future__, prometheus_client; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- INGEST_DURATION_SECONDS = Histogram(
- INGEST_ARTIFACTS_TOTAL = Counter(
- INGEST_CHUNKS_TOTAL = Counter(
- INGEST_LAST_RUN_STATUS = Gauge(
- INGEST_LAST_RUN_TIMESTAMP = Gauge(
- COVERAGE_LAST_RUN_STATUS = Gauge(
- COVERAGE_LAST_RUN_TIMESTAMP = Gauge(
- COVERAGE_MISSING_ARTIFACTS = Gauge(
- COVERAGE_STALE_ARTIFACTS = Gauge(
- INGEST_STALE_RESOLVED_TOTAL = Counter(
- INGEST_SKIPS_TOTAL = Counter(
- SEARCH_REQUESTS_TOTAL = Counter(
- SEARCH_GRAPH_CACHE_EVENTS = Counter(
- SEARCH_GRAPH_LOOKUP_SECONDS = Histogram(
- SEARCH_SCORE_DELTA = Histogram(
- GRAPH_MIGRATION_LAST_STATUS = Gauge(
- GRAPH_MIGRATION_LAST_TIMESTAMP = Gauge(
- SCHEDULER_RUNS_TOTAL = Counter(
- SCHEDULER_LAST_SUCCESS_TIMESTAMP = Gauge(
- COVERAGE_HISTORY_SNAPSHOTS = Gauge(
- WATCH_RUNS_TOTAL = Counter(
- LIFECYCLE_LAST_RUN_STATUS = Gauge(
- LIFECYCLE_LAST_RUN_TIMESTAMP = Gauge(
- LIFECYCLE_STALE_DOCS_TOTAL = Gauge(
- LIFECYCLE_ISOLATED_NODES_TOTAL = Gauge(
- LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL = Gauge(
- LIFECYCLE_REMOVED_ARTIFACTS_TOTAL = Gauge(
- LIFECYCLE_HISTORY_SNAPSHOTS = Gauge(
- MCP_REQUESTS_TOTAL = Counter(
- MCP_REQUEST_SECONDS = Histogram(
- MCP_FAILURES_TOTAL = Counter(
- MCP_UPLOAD_TOTAL = Counter(
- MCP_STORETEXT_TOTAL = Counter(
- UI_REQUESTS_TOTAL = Counter(
- UI_EVENTS_TOTAL = Counter(

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/observability/tracing.py

**File path**: `gateway/observability/tracing.py`
**Purpose**: Tracing helpers for wiring OpenTelemetry exporters.
**Dependencies**: External – __future__, fastapi, opentelemetry, opentelemetry.exporter.otlp.proto.http.trace_exporter, opentelemetry.instrumentation.fastapi, opentelemetry.instrumentation.requests, opentelemetry.sdk.resources, opentelemetry.sdk.trace, opentelemetry.sdk.trace.export, opentelemetry.sdk.trace.sampling; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

**Classes**
- None

**Functions**
- `configure_tracing(app, settings) — Configure OpenTelemetry tracing based on runtime settings.`
- `_select_exporter(settings) — Choose the span exporter based on settings.`
- `_parse_headers(header_string) — Parse comma-separated OTLP header strings into a dict.`
- `reset_tracing_for_tests() — Reset module-level state so tests can reconfigure tracing cleanly.`

**Constants and Configuration**
- _TRACING_CONFIGURED = False

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- OpenTelemetry

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/plugins/__init__.py

**File path**: `gateway/plugins/__init__.py`
**Purpose**: Plugin namespace for future ingestion extensions.
**Dependencies**: External – None; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/recipes/__init__.py

**File path**: `gateway/recipes/__init__.py`
**Purpose**: Utilities for running knowledge recipes.
**Dependencies**: External – executor, models; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/recipes/cli.py

**File path**: `gateway/recipes/cli.py`
**Purpose**: Command-line utilities for inspecting and running MCP recipes.
**Dependencies**: External – __future__, argparse, asyncio, collections, executor, json, logging, models, pathlib, pydantic, rich.console, rich.table, typing; Internal – gateway.mcp.config
**Related modules**: gateway.mcp.config

**Classes**
- None

**Functions**
- `build_parser() — Construct the top-level argument parser for the CLI.`
- `load_recipe_by_name(recipes_dir, name) — Load a recipe by stem name from the given directory.`
- `parse_variables(pairs) — Parse ``key=value`` overrides supplied on the command line.`
- `command_list(args) — List recipes available in the configured directory.`
- `command_show(args) — Print a single recipe definition in JSON form.`
- `command_validate(args) — Validate one or all recipes and report the outcome.`
- `recipe_executor_factory(settings) — Create a factory that instantiates a gateway-backed tool executor.`
- `command_run(args, settings) — Execute a recipe and render the results.`
- `_render_run_result(result) — Pretty-print a recipe execution result in tabular form.`
- `main(argv) — Entry point for the recipes CLI.`

**Constants and Configuration**
- DEFAULT_RECIPES_DIR = Path(__file__).resolve().parents[2] / "recipes"

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/recipes/executor.py

**File path**: `gateway/recipes/executor.py`
**Purpose**: Recipe execution layer for automating MCP-driven workflows.
**Dependencies**: External – __future__, asyncio, collections, contextlib, dataclasses, json, logging, models, pathlib, re, time, types, yaml; Internal – gateway.mcp.backup, gateway.mcp.client, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.ingest
**Related modules**: gateway.mcp.backup, gateway.mcp.client, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.ingest

**Classes**
- RecipeExecutionError (bases: RuntimeError) — Raised when a recipe step fails. Methods: None.
- StepResult (bases: object) — Lightweight representation of a single recipe step outcome. Methods: None.
- RecipeRunResult (bases: object) — Aggregate outcome for a recipe execution, including captured outputs. Methods: to_dict(self).
- ToolExecutor (bases: object) — Abstract tool executor interface. Methods: None.
- GatewayToolExecutor (bases: ToolExecutor) — Execute tools by reusing gateway HTTP/MCP helpers. Methods: __init__(self, settings).
- RecipeRunner (bases: object) — Run recipes using the configured MCP settings. Methods: __init__(self, settings, executor_factory, audit_path), make_executor(self), _append_audit(self, result, context).

**Functions**
- `_resolve_template(value, context) — No docstring.`
- `_lookup_expression(expr, context) — No docstring.`
- `_descend(current, part) — No docstring.`
- `_evaluate_condition(result, condition) — No docstring.`
- `_compute_capture(result, capture) — No docstring.`
- `load_recipe(path) — Load a recipe file from disk and validate the schema.`
- `_ensure_object_map(value, label) — Ensure template resolution returned a mapping, raising otherwise.`
- `_require_str(params, key) — Fetch a required string parameter from a mapping of arguments.`
- `_coerce_optional_str(value) — Convert optional string-like values to trimmed strings.`
- `_coerce_positive_int(value) — Convert inputs to a positive integer, falling back to the default.`
- `_coerce_int(value) — Coerce common primitive values to an integer when possible.`
- `_coerce_bool(value) — Interpret truthy/falsey string values and return a boolean.`
- `list_recipes(recipes_dir) — Return all recipe definition files within the directory.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/recipes/models.py

**File path**: `gateway/recipes/models.py`
**Purpose**: Pydantic models describing MCP recipe configuration.
**Dependencies**: External – __future__, pydantic, typing; Internal – None
**Related modules**: None

**Classes**
- Condition (bases: BaseModel) — Assertion condition evaluated against a step result. Methods: None.
- Capture (bases: BaseModel) — Capture part of a step result into the execution context. Methods: None.
- WaitConfig (bases: BaseModel) — Poll a tool until a condition is satisfied. Methods: None.
- RecipeStep (bases: BaseModel) — Single step inside a recipe. Methods: validate_mode(self).
- Recipe (bases: BaseModel) — Top level recipe definition. Methods: ensure_unique_step_ids(self).

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/scheduler.py

**File path**: `gateway/scheduler.py`
**Purpose**: Background scheduler that drives periodic ingestion runs.
**Dependencies**: External – __future__, apscheduler.schedulers.background, apscheduler.schedulers.base, apscheduler.triggers.cron, apscheduler.triggers.interval, collections, contextlib, filelock, logging, pathlib, subprocess, time; Internal – gateway.config.settings, gateway.ingest.service, gateway.observability.metrics
**Related modules**: gateway.config.settings, gateway.ingest.service, gateway.observability.metrics

**Classes**
- IngestionScheduler (bases: object) — APScheduler wrapper that coordinates repo-aware ingestion jobs. Methods: __init__(self, settings), start(self), shutdown(self), _run_ingestion(self), _read_last_head(self), _write_last_head(self, head).

**Functions**
- `_current_repo_head(repo_root) — Return the git HEAD sha for the repo, or ``None`` when unavailable.`
- `_build_trigger(config) — Construct the APScheduler trigger based on user configuration.`
- `_describe_trigger(config) — Provide a human readable summary of the configured trigger.`
- `_coerce_positive_int(value) — Best-effort conversion to a positive integer with sane defaults.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/search/__init__.py

**File path**: `gateway/search/__init__.py`
**Purpose**: Search service exposing vector search with graph context.
**Dependencies**: External – dataset, evaluation, exporter, feedback, maintenance, service; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/search/cli.py

**File path**: `gateway/search/cli.py`
**Purpose**: Command-line helpers for search training, exports, and maintenance.
**Dependencies**: External – __future__, argparse, datetime, logging, pathlib, rich.console; Internal – gateway.config.settings, gateway.observability, gateway.search.evaluation, gateway.search.exporter, gateway.search.maintenance, gateway.search.trainer
**Related modules**: gateway.config.settings, gateway.observability, gateway.search.evaluation, gateway.search.exporter, gateway.search.maintenance, gateway.search.trainer

**Classes**
- None

**Functions**
- `build_parser() — Return an argument parser covering all search CLI commands.`
- `export_training_data() — Materialise feedback events into a training dataset file.`
- `train_model() — Train a ranking model from a prepared dataset and save the artifact.`
- `show_weights() — Print the active search weight profile to the console.`
- `prune_feedback() — Trim feedback logs by age/request count and optionally archive removals.`
- `redact_training_dataset() — Strip sensitive fields and emit a sanitized dataset.`
- `evaluate_trained_model() — Run offline evaluation of a trained model against a labelled dataset.`
- `main(argv) — Entry point for the `gateway-search` command-line interface.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/search/dataset.py

**File path**: `gateway/search/dataset.py`
**Purpose**: Utilities for reading and preparing search training datasets.
**Dependencies**: External – __future__, collections, csv, json, pathlib; Internal – gateway.search.exporter
**Related modules**: gateway.search.exporter

**Classes**
- DatasetLoadError (bases: RuntimeError) — Raised when a dataset cannot be parsed. Methods: None.

**Functions**
- `load_dataset_records(path) — Load dataset rows from disk, raising when the file is missing.`
- `build_feature_matrix(records, feature_names) — Convert dataset rows into numeric feature vectors and targets.`
- `_parse_float(value) — No docstring.`

**Constants and Configuration**
- TARGET_FIELD = "feedback_vote"

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/search/evaluation.py

**File path**: `gateway/search/evaluation.py`
**Purpose**: Model evaluation utilities for the search ranking pipeline.
**Dependencies**: External – __future__, collections, dataclasses, math, numpy, numpy.typing, pathlib, statistics, typing; Internal – gateway.search.dataset, gateway.search.trainer
**Related modules**: gateway.search.dataset, gateway.search.trainer

**Classes**
- EvaluationMetrics (bases: object) — Aggregate metrics produced after evaluating a ranking model. Methods: None.

**Functions**
- `evaluate_model(dataset_path, model_path) — Load a dataset and model artifact, returning evaluation metrics.`
- `_mean_ndcg(request_ids, relevance, scores) — Compute mean NDCG@k for groups identified by request ids.`
- `_dcg(relevances, k) — Compute discounted cumulative gain at rank ``k``.`
- `_spearman_correlation(y_true, y_pred) — Return Spearman rank correlation between true and predicted values.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/search/exporter.py

**File path**: `gateway/search/exporter.py`
**Purpose**: Utilities for exporting feedback logs into training datasets.
**Dependencies**: External – __future__, collections, csv, dataclasses, json, logging, pathlib, typing; Internal – None
**Related modules**: None

**Classes**
- ExportOptions (bases: object) — User-configurable options controlling dataset export. Methods: None.
- ExportStats (bases: object) — Basic statistics about the export process. Methods: None.

**Functions**
- `export_training_dataset(events_path) — Write feedback events into the requested dataset format.`
- `iter_feedback_events(path) — Yield feedback events from a JSON lines log file.`
- `_write_csv(events, options) — Write feedback events into a CSV file.`
- `_write_jsonl(events, options) — Write feedback events into a JSONL file.`
- `_flatten_event(event) — Flatten nested event data into scalar fields.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/search/feedback.py

**File path**: `gateway/search/feedback.py`
**Purpose**: Persistent storage helpers for search feedback events.
**Dependencies**: External – __future__, collections, datetime, json, pathlib, threading, uuid; Internal – gateway.search.service
**Related modules**: gateway.search.service

**Classes**
- SearchFeedbackStore (bases: object) — Append-only store for search telemetry and feedback. Methods: __init__(self, root), record(self), _append(self, rows).

**Functions**
- `_serialize_results() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/search/maintenance.py

**File path**: `gateway/search/maintenance.py`
**Purpose**: Maintenance routines for pruning feedback logs and redacting datasets.
**Dependencies**: External – __future__, collections, csv, dataclasses, datetime, json, logging, pathlib, shutil; Internal – gateway.search.exporter
**Related modules**: gateway.search.exporter

**Classes**
- PruneOptions (bases: object) — Configures retention rules for the feedback log pruning routine. Methods: None.
- PruneStats (bases: object) — Summary of how many feedback requests were kept versus removed. Methods: None.
- RedactOptions (bases: object) — Toggles that control which sensitive fields should be redacted. Methods: None.
- RedactStats (bases: object) — Summary of how many dataset rows required redaction. Methods: None.

**Functions**
- `prune_feedback_log(events_path) — Prune feedback requests based on age and count thresholds.`
- `redact_dataset(dataset_path) — Redact sensitive fields from datasets stored as CSV or JSON Lines.`
- `_parse_timestamp(value) — Parse timestamps stored as numbers or ISO 8601 strings.`
- `_collect_events(events_path) — No docstring.`
- `_build_timestamps(events_by_request) — No docstring.`
- `_apply_prune_filters(request_order, timestamps, options, now) — No docstring.`
- `_preserve_original_order(order, selected_ids) — No docstring.`
- `_write_retained_events(destination, retained_order, events_by_request) — No docstring.`
- `_redact_csv(source, destination, options) — Redact sensitive columns from a CSV dataset.`
- `_redact_csv_row(row, options) — No docstring.`
- `_clear_field(row, field, replacement) — No docstring.`
- `_redact_jsonl(source, destination, options) — Redact sensitive fields from JSON lines datasets.`
- `_redact_json_record(record, options) — No docstring.`
- `_null_field(record, field) — No docstring.`

**Constants and Configuration**
- _FALLBACK_TIMESTAMP = datetime.fromordinal(1).replace(tzinfo=UTC)

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/search/service.py

**File path**: `gateway/search/service.py`
**Purpose**: Hybrid search orchestration for Duskmantle's knowledge gateway.
**Dependencies**: External – __future__, collections, dataclasses, datetime, logging, neo4j.exceptions, qdrant_client, qdrant_client.http.models, re, time, typing; Internal – gateway.graph.service, gateway.ingest.embedding, gateway.observability, gateway.search.trainer
**Related modules**: gateway.graph.service, gateway.ingest.embedding, gateway.observability, gateway.search.trainer

**Classes**
- SearchResult (bases: object) — Single ranked chunk returned from the search pipeline. Methods: None.
- SearchResponse (bases: object) — API-friendly container for search results and metadata. Methods: None.
- SearchOptions (bases: object) — Runtime options controlling the search service behaviour. Methods: None.
- SearchWeights (bases: object) — Weighting configuration for hybrid scoring. Methods: None.
- FilterState (bases: object) — Preprocessed filter collections derived from request parameters. Methods: None.
- CoverageInfo (bases: object) — Coverage characteristics used during scoring. Methods: None.
- SearchService (bases: object) — Execute hybrid vector/graph search with heuristic or ML scoring. Methods: __init__(self, qdrant_client, collection_name, embedder), search(self), _resolve_graph_context(self), _build_model_features(self), _apply_model(self, features).

**Functions**
- `_label_for_artifact(artifact_type) — No docstring.`
- `_summarize_graph_context(data) — No docstring.`
- `_subsystems_from_context(graph_context) — No docstring.`
- `_detect_query_subsystems(query) — No docstring.`
- `_normalise_hybrid_weights(vector_weight, lexical_weight) — No docstring.`
- `_prepare_filter_state(filters) — No docstring.`
- `_passes_payload_filters(payload, state) — No docstring.`
- `_normalise_payload_tags(raw_tags) — No docstring.`
- `_build_chunk(payload, score) — No docstring.`
- `_calculate_subsystem_affinity(subsystem, query_tokens) — No docstring.`
- `_calculate_supporting_bonus(related_artifacts) — No docstring.`
- `_calculate_coverage_info(chunk, weight_coverage_penalty) — No docstring.`
- `_coerce_ratio_value(value) — No docstring.`
- `_calculate_criticality_score(chunk, graph_context) — No docstring.`
- `_update_path_depth_signal(signals, path_depth, graph_context) — No docstring.`
- `_ensure_criticality_signal(signals, chunk, graph_context) — No docstring.`
- `_ensure_freshness_signal(signals, chunk, graph_context, freshness_days) — No docstring.`
- `_ensure_coverage_ratio_signal(signals, chunk) — No docstring.`
- `_lexical_score(query, chunk) — No docstring.`
- `_base_scoring(vector_score, lexical_score, vector_weight, lexical_weight) — No docstring.`
- `_compute_scoring() — No docstring.`
- `_populate_additional_signals() — No docstring.`
- `_estimate_path_depth(graph_context) — No docstring.`
- `_extract_subsystem_criticality(graph_context) — No docstring.`
- `_normalise_criticality(value) — No docstring.`
- `_compute_freshness_days(chunk, graph_context) — No docstring.`
- `_resolve_chunk_datetime(chunk, graph_context) — No docstring.`
- `_parse_iso_datetime(value) — No docstring.`

**Constants and Configuration**
- _TOKEN_PATTERN = re.compile(r"\w+", flags=re.ASCII)

**Data Flow**
- Performs hybrid vector search, applies heuristics, and enriches results with optional graph context.

**Integration Points**
- Qdrant client

**Code Quality Notes**
- Functions missing docstrings.

## gateway/search/trainer.py

**File path**: `gateway/search/trainer.py`
**Purpose**: Training utilities for search ranking models.
**Dependencies**: External – __future__, collections, dataclasses, datetime, json, math, numpy, pathlib; Internal – gateway.search.dataset
**Related modules**: gateway.search.dataset

**Classes**
- TrainingResult (bases: object) — Capture optimiser output for debug or inspection. Methods: None.
- ModelArtifact (bases: object) — Persisted search model metadata and coefficients. Methods: None.

**Functions**
- `train_from_dataset(path) — Train a logistic regression model from the labelled dataset.`
- `save_artifact(artifact, path) — Write the model artifact to disk as JSON.`
- `load_artifact(path) — Load a saved model artifact from disk.`
- `_linear_regression(X, y) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## gateway/ui/__init__.py

**File path**: `gateway/ui/__init__.py`
**Purpose**: UI utilities and routers.
**Dependencies**: External – routes; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## gateway/ui/routes.py

**File path**: `gateway/ui/routes.py`
**Purpose**: UI router exposing static assets and HTML entry points.
**Dependencies**: External – __future__, fastapi, fastapi.responses, fastapi.templating, json, logging, pathlib; Internal – gateway.config.settings, gateway.observability
**Related modules**: gateway.config.settings, gateway.observability

**Classes**
- None

**Functions**
- `get_static_path() — Return the absolute path to UI static assets.`

**Constants and Configuration**
- STATIC_DIR = Path(__file__).resolve().parent / "static"
- TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## scripts/generate-changelog.py

**File path**: `scripts/generate-changelog.py`
**Purpose**: Generate changelog entries from Conventional Commits.
**Dependencies**: External – __future__, argparse, collections, datetime, pathlib, subprocess, sys; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `_run_git(args) — No docstring.`
- `discover_commits(since) — No docstring.`
- `categorize(commits) — No docstring.`
- `update_changelog(version, released, entries) — No docstring.`
- `main() — No docstring.`

**Constants and Configuration**
- ROOT = Path(__file__).resolve().parents[1]
- CHANGELOG = ROOT / "CHANGELOG.md"
- CATEGORY_MAP = {

**Data Flow**
- Transforms inputs through helper functions and returns Python data structures.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/__init__.py

**File path**: `tests/__init__.py`
**Purpose**: Test package for the knowledge gateway.
**Dependencies**: External – None; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## tests/conftest.py

**File path**: `tests/conftest.py`
**Purpose**: Pytest coverage for conftest.
**Dependencies**: External – __future__, collections, neo4j, os, pytest, sentence_transformers, shutil, subprocess, sys, time, types, typing, uuid, warnings; Internal – None
**Related modules**: None

**Classes**
- _NullSession (bases: object) — No docstring. Methods: __enter__(self), __exit__(self, exc_type, exc, tb), execute_read(self, func), run(self).
- _NullDriver (bases: object) — No docstring. Methods: session(self), close(self).

**Functions**
- `disable_real_graph_driver(monkeypatch, request) — No docstring.`
- `neo4j_test_environment() — No docstring.`
- `pytest_collection_modifyitems(config, items) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/mcp/test_server_tools.py

**File path**: `tests/mcp/test_server_tools.py`
**Purpose**: Integration tests for MCP server tools and metrics wiring.
**Dependencies**: External – __future__, asyncio, collections, pathlib, prometheus_client, pytest, typing; Internal – gateway.mcp, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.server, gateway.observability.metrics
**Related modules**: gateway.mcp, gateway.mcp.config, gateway.mcp.exceptions, gateway.mcp.server, gateway.observability.metrics

**Classes**
- None

**Functions**
- `_reset_mcp_metrics() — No docstring.`
- `mcp_server() — No docstring.`
- `_counter_value(counter) — No docstring.`
- `_histogram_sum(histogram) — No docstring.`
- `_upload_counter(result) — No docstring.`
- `_storetext_counter(result) — No docstring.`
- `_tool_fn(tool) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/mcp/test_utils_files.py

**File path**: `tests/mcp/test_utils_files.py`
**Purpose**: Pytest coverage for utils files.
**Dependencies**: External – __future__, pathlib, pytest; Internal – gateway.mcp.utils
**Related modules**: gateway.mcp.utils

**Classes**
- None

**Functions**
- `test_sweep_documents_copies_supported_files(tmp_path) — No docstring.`
- `test_sweep_documents_dry_run_reports_actions(tmp_path) — No docstring.`
- `test_copy_into_root_prevents_traversal(tmp_path) — No docstring.`
- `test_write_text_document_requires_content(tmp_path) — No docstring.`
- `test_slugify_generates_fallback_when_empty() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/playwright_server.py

**File path**: `tests/playwright_server.py`
**Purpose**: Pytest coverage for playwright server.
**Dependencies**: External – __future__, datetime, json, os, pathlib, shutil, signal, uvicorn; Internal – gateway.api.app
**Related modules**: gateway.api.app

**Classes**
- None

**Functions**
- `_write_json(path, payload) — No docstring.`
- `_prepare_state(state_path) — No docstring.`
- `_configure_environment(state_path) — No docstring.`
- `main() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_api_security.py

**File path**: `tests/test_api_security.py`
**Purpose**: Pytest coverage for api security.
**Dependencies**: External – __future__, fastapi.testclient, json, logging, pathlib, pytest, typing; Internal – gateway, gateway.api.app, gateway.config.settings, gateway.graph.service, gateway.search.service
**Related modules**: gateway, gateway.api.app, gateway.config.settings, gateway.graph.service, gateway.search.service

**Classes**
- None

**Functions**
- `reset_settings_cache() — No docstring.`
- `test_audit_requires_token(tmp_path, monkeypatch) — No docstring.`
- `test_coverage_endpoint(tmp_path, monkeypatch) — No docstring.`
- `test_coverage_missing_report(tmp_path, monkeypatch) — No docstring.`
- `test_rate_limiting(monkeypatch) — No docstring.`
- `test_startup_logs_configuration(monkeypatch, tmp_path, caplog) — No docstring.`
- `test_secure_mode_without_admin_token_fails(tmp_path, monkeypatch) — No docstring.`
- `test_secure_mode_requires_custom_neo4j_password(tmp_path, monkeypatch) — No docstring.`
- `test_rate_limiting_search(monkeypatch, tmp_path) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_app_smoke.py

**File path**: `tests/test_app_smoke.py`
**Purpose**: Pytest coverage for app smoke.
**Dependencies**: External – __future__, fastapi.testclient, json, logging, pathlib, pytest, time, unittest; Internal – gateway.api.app, gateway.config.settings, gateway.ingest.audit
**Related modules**: gateway.api.app, gateway.config.settings, gateway.ingest.audit

**Classes**
- None

**Functions**
- `reset_settings_cache() — No docstring.`
- `test_health_endpoint_reports_diagnostics(tmp_path, monkeypatch) — No docstring.`
- `test_health_endpoint_ok_when_artifacts_present(tmp_path, monkeypatch) — No docstring.`
- `test_ready_endpoint_returns_ready() — No docstring.`
- `test_lifecycle_history_endpoint(tmp_path, monkeypatch) — No docstring.`
- `test_requires_non_default_neo4j_password_when_auth_enabled(monkeypatch, tmp_path) — No docstring.`
- `test_requires_non_empty_neo4j_password_when_auth_enabled(monkeypatch, tmp_path) — No docstring.`
- `test_logs_warning_when_neo4j_auth_disabled(monkeypatch, tmp_path, caplog) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_coverage_report.py

**File path**: `tests/test_coverage_report.py`
**Purpose**: Pytest coverage for coverage report.
**Dependencies**: External – __future__, collections, fastapi.testclient, json, pathlib, prometheus_client, pytest; Internal – gateway.api.app, gateway.config.settings, gateway.ingest.coverage, gateway.ingest.pipeline, gateway.observability.metrics
**Related modules**: gateway.api.app, gateway.config.settings, gateway.ingest.coverage, gateway.ingest.pipeline, gateway.observability.metrics

**Classes**
- StubQdrantWriter (bases: object) — No docstring. Methods: ensure_collection(self, vector_size), upsert_chunks(self, chunks).
- StubNeo4jWriter (bases: object) — No docstring. Methods: ensure_constraints(self), sync_artifact(self, artifact), sync_chunks(self, chunk_embeddings).

**Functions**
- `test_write_coverage_report(tmp_path) — No docstring.`
- `test_coverage_endpoint_after_report_generation(tmp_path, monkeypatch) — No docstring.`
- `test_coverage_history_rotation(tmp_path) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_graph_api.py

**File path**: `tests/test_graph_api.py`
**Purpose**: Pytest coverage for graph api.
**Dependencies**: External – __future__, fastapi, fastapi.testclient, neo4j, os, pathlib, pytest, typing; Internal – gateway.api.app, gateway.config.settings, gateway.graph, gateway.graph.migrations.runner, gateway.ingest.neo4j_writer, gateway.ingest.pipeline
**Related modules**: gateway.api.app, gateway.config.settings, gateway.graph, gateway.graph.migrations.runner, gateway.ingest.neo4j_writer, gateway.ingest.pipeline

**Classes**
- DummyGraphService (bases: object) — No docstring. Methods: __init__(self, responses), get_subsystem(self, name), get_node(self, node_id), search(self, term), get_subsystem_graph(self, name), list_orphan_nodes(self), run_cypher(self, query, parameters).

**Functions**
- `app(monkeypatch) — No docstring.`
- `test_graph_subsystem_returns_payload(app) — No docstring.`
- `test_graph_subsystem_not_found(app) — No docstring.`
- `test_graph_subsystem_graph_endpoint(app) — No docstring.`
- `test_graph_orphans_endpoint(app) — No docstring.`
- `test_graph_node_endpoint(app) — No docstring.`
- `test_graph_node_accepts_slash_encoded_ids(app) — No docstring.`
- `test_graph_node_endpoint_live(monkeypatch, tmp_path) — No docstring.`
- `test_graph_search_endpoint_live(monkeypatch, tmp_path) — No docstring.`
- `test_graph_search_endpoint(app) — No docstring.`
- `test_graph_cypher_requires_maintainer_token(monkeypatch) — No docstring.`
- `test_graph_reader_scope(monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI
- Neo4j driver

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_graph_auto_migrate.py

**File path**: `tests/test_graph_auto_migrate.py`
**Purpose**: Pytest coverage for graph auto migrate.
**Dependencies**: External – __future__, prometheus_client, pytest, unittest; Internal – gateway.api.app, gateway.config.settings, gateway.observability.metrics
**Related modules**: gateway.api.app, gateway.config.settings, gateway.observability.metrics

**Classes**
- None

**Functions**
- `reset_settings_cache() — No docstring.`
- `reset_migration_metrics() — No docstring.`
- `_metric(name) — No docstring.`
- `test_auto_migrate_runs_when_enabled(monkeypatch) — No docstring.`
- `test_auto_migrate_skipped_when_disabled(monkeypatch) — No docstring.`
- `test_auto_migrate_records_failure(monkeypatch) — No docstring.`
- `test_missing_database_disables_graph_driver(monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_graph_cli.py

**File path**: `tests/test_graph_cli.py`
**Purpose**: Pytest coverage for graph cli.
**Dependencies**: External – __future__, pytest, unittest; Internal – gateway.graph
**Related modules**: gateway.graph

**Classes**
- DummySettings (bases: object) — No docstring. Methods: None.

**Functions**
- `test_graph_cli_migrate_runs_runner(monkeypatch) — No docstring.`
- `test_graph_cli_dry_run_prints_pending(monkeypatch, capsys) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_graph_database_validation.py

**File path**: `tests/test_graph_database_validation.py`
**Purpose**: Pytest coverage for graph database validation.
**Dependencies**: External – __future__, neo4j.exceptions, unittest; Internal – gateway.api
**Related modules**: gateway.api

**Classes**
- None

**Functions**
- `test_verify_graph_database_returns_false_when_database_missing() — No docstring.`
- `test_verify_graph_database_returns_true_on_success() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_graph_migrations.py

**File path**: `tests/test_graph_migrations.py`
**Purpose**: Pytest coverage for graph migrations.
**Dependencies**: External – __future__, collections, types; Internal – gateway.graph.migrations.runner
**Related modules**: gateway.graph.migrations.runner

**Classes**
- FakeResult (bases: object) — No docstring. Methods: __init__(self, record), single(self).
- FakeTransaction (bases: object) — No docstring. Methods: __init__(self, applied_ids, results), run(self, query), commit(self), rollback(self), __enter__(self), __exit__(self, exc_type, exc_val, exc_tb).
- FakeSession (bases: object) — No docstring. Methods: __init__(self, applied_ids, records), run(self, query), begin_transaction(self), close(self), __enter__(self), __exit__(self, exc_type, exc_val, exc_tb).
- FakeDriver (bases: object) — No docstring. Methods: __init__(self), session(self, database), close(self).

**Functions**
- `test_migration_runner_applies_pending_migrations() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_graph_service_startup.py

**File path**: `tests/test_graph_service_startup.py`
**Purpose**: Pytest coverage for graph service startup.
**Dependencies**: External – __future__, fastapi, pytest, starlette.requests, unittest; Internal – gateway.api.app, gateway.config.settings
**Related modules**: gateway.api.app, gateway.config.settings

**Classes**
- None

**Functions**
- `reset_settings_cache() — No docstring.`
- `set_state_path(tmp_path_factory, monkeypatch) — No docstring.`
- `_make_request(app) — No docstring.`
- `test_graph_dependency_returns_503_when_database_missing(monkeypatch) — No docstring.`
- `test_graph_dependency_returns_service_when_available(monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Handles HTTP requests via FastAPI, validates payloads, and returns JSON responses.

**Integration Points**
- FastAPI

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_graph_service_unit.py

**File path**: `tests/test_graph_service_unit.py`
**Purpose**: Pytest coverage for graph service unit.
**Dependencies**: External – __future__, collections, pytest, types, unittest; Internal – gateway.graph, gateway.graph.service
**Related modules**: gateway.graph, gateway.graph.service

**Classes**
- DummyNode (bases: dict[str, object]) — No docstring. Methods: __init__(self, labels, element_id).
- DummyRelationship (bases: dict[str, object]) — No docstring. Methods: __init__(self, start_node, end_node, rel_type).
- DummySession (bases: object) — No docstring. Methods: __init__(self), __enter__(self), __exit__(self, exc_type, exc, tb), execute_read(self, func), run(self, query).
- DummyDriver (bases: object) — No docstring. Methods: __init__(self, session), session(self), execute_query(self, query, parameters, database_).

**Functions**
- `patch_graph_types(monkeypatch) — No docstring.`
- `dummy_driver() — No docstring.`
- `test_get_subsystem_paginates_and_includes_artifacts(monkeypatch, dummy_driver) — No docstring.`
- `test_get_subsystem_missing_raises(monkeypatch, dummy_driver) — No docstring.`
- `test_get_subsystem_graph_returns_nodes_and_edges(monkeypatch, dummy_driver) — No docstring.`
- `test_fetch_subsystem_paths_inlines_depth_literal(monkeypatch) — No docstring.`
- `test_get_node_with_relationships(monkeypatch, dummy_driver) — No docstring.`
- `test_list_orphan_nodes_rejects_unknown_label(dummy_driver) — No docstring.`
- `test_list_orphan_nodes_serializes_results(monkeypatch, dummy_driver) — No docstring.`
- `test_get_node_missing_raises(monkeypatch, dummy_driver) — No docstring.`
- `test_search_serializes_results(monkeypatch, dummy_driver) — No docstring.`
- `test_shortest_path_depth(monkeypatch, dummy_driver) — No docstring.`
- `test_shortest_path_depth_none(monkeypatch, dummy_driver) — No docstring.`
- `test_run_cypher_serializes_records(monkeypatch, dummy_driver) — No docstring.`
- `test_run_cypher_rejects_non_read_queries(dummy_driver) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_graph_validation.py

**File path**: `tests/test_graph_validation.py`
**Purpose**: End-to-end validation of ingestion and graph-backed search.
**Dependencies**: External – __future__, collections, neo4j, os, pathlib, pytest, qdrant_client, typing; Internal – gateway.graph.migrations.runner, gateway.graph.service, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.search
**Related modules**: gateway.graph.migrations.runner, gateway.graph.service, gateway.ingest.embedding, gateway.ingest.neo4j_writer, gateway.ingest.pipeline, gateway.search

**Classes**
- _DummyEmbedder (bases: Embedder) — Minimal embedder returning deterministic vectors for tests. Methods: __init__(self), dimension(self), encode(self, texts).
- _FakePoint (bases: object) — No docstring. Methods: __init__(self, payload, score).
- _DummyQdrantClient (bases: object) — Stub Qdrant client that returns pre-seeded points. Methods: __init__(self, points), search(self).

**Functions**
- `test_ingestion_populates_graph(tmp_path) — Run ingestion and verify graph nodes, edges, and metadata.`
- `test_search_replay_against_real_graph(tmp_path) — Replay saved search results against the populated knowledge graph.`

**Constants and Configuration**
- None

**Data Flow**
- Interacts with Qdrant collections for vector storage and retrieval.

**Integration Points**
- Neo4j driver
- Qdrant client

**Code Quality Notes**
- Classes missing docstrings.

## tests/test_ingest_cli.py

**File path**: `tests/test_ingest_cli.py`
**Purpose**: Pytest coverage for ingest cli.
**Dependencies**: External – __future__, pathlib, pytest, time, unittest; Internal – gateway.config.settings, gateway.ingest, gateway.ingest.audit, gateway.ingest.pipeline
**Related modules**: gateway.config.settings, gateway.ingest, gateway.ingest.audit, gateway.ingest.pipeline

**Classes**
- None

**Functions**
- `reset_settings_cache() — No docstring.`
- `sample_repo(tmp_path) — No docstring.`
- `test_cli_rebuild_dry_run(sample_repo, monkeypatch) — No docstring.`
- `test_cli_rebuild_requires_maintainer_token(sample_repo, monkeypatch) — No docstring.`
- `test_cli_rebuild_with_maintainer_token(sample_repo, monkeypatch) — No docstring.`
- `test_cli_rebuild_full_rebuild_flag(sample_repo, monkeypatch) — No docstring.`
- `test_cli_rebuild_incremental_flag(sample_repo, monkeypatch) — No docstring.`
- `test_cli_audit_history_json(tmp_path, monkeypatch, capsys) — No docstring.`
- `test_cli_audit_history_no_entries(tmp_path, monkeypatch, capsys) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_ingest_pipeline.py

**File path**: `tests/test_ingest_pipeline.py`
**Purpose**: Pytest coverage for ingest pipeline.
**Dependencies**: External – __future__, collections, pathlib, prometheus_client, pytest; Internal – gateway.ingest.pipeline
**Related modules**: gateway.ingest.pipeline

**Classes**
- StubQdrantWriter (bases: object) — No docstring. Methods: __init__(self), ensure_collection(self, vector_size), upsert_chunks(self, chunks), delete_artifact(self, artifact_path).
- StubNeo4jWriter (bases: object) — No docstring. Methods: __init__(self), ensure_constraints(self), sync_artifact(self, artifact), sync_chunks(self, chunk_embeddings), delete_artifact(self, path).

**Functions**
- `_metric_value(name, labels) — No docstring.`
- `sample_repo(tmp_path) — No docstring.`
- `test_pipeline_generates_chunks(sample_repo) — No docstring.`
- `test_pipeline_removes_stale_artifacts(tmp_path) — No docstring.`
- `test_pipeline_skips_unchanged_artifacts(tmp_path) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_km_watch.py

**File path**: `tests/test_km_watch.py`
**Purpose**: Pytest coverage for km watch.
**Dependencies**: External – __future__, os, pathlib, prometheus_client, runpy, sys; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `_metric_value(name, labels) — No docstring.`
- `test_compute_fingerprints(tmp_path) — No docstring.`
- `test_diff_fingerprints_detects_changes() — No docstring.`
- `test_watch_metrics_increment(tmp_path) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_lifecycle_cli.py

**File path**: `tests/test_lifecycle_cli.py`
**Purpose**: Pytest coverage for lifecycle cli.
**Dependencies**: External – __future__, json, pathlib, pytest; Internal – gateway.lifecycle.cli
**Related modules**: gateway.lifecycle.cli

**Classes**
- None

**Functions**
- `test_lifecycle_cli_json(tmp_path, capsys) — No docstring.`
- `test_lifecycle_cli_missing_file(tmp_path, capsys) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_lifecycle_report.py

**File path**: `tests/test_lifecycle_report.py`
**Purpose**: Pytest coverage for lifecycle report.
**Dependencies**: External – __future__, datetime, json, pathlib, prometheus_client, pytest, typing; Internal – gateway.graph, gateway.ingest.lifecycle, gateway.ingest.pipeline
**Related modules**: gateway.graph, gateway.ingest.lifecycle, gateway.ingest.pipeline

**Classes**
- DummyGraphService (bases: object) — Test double that returns pre-seeded orphan graph nodes. Methods: __init__(self, pages), list_orphan_nodes(self).

**Functions**
- `_ingestion_result() — Build a representative ingestion result for lifecycle reporting tests.`
- `test_write_lifecycle_report_without_graph(tmp_path, ingestion_result) — Reports render correctly when graph enrichment is disabled.`
- `test_write_lifecycle_report_with_graph(tmp_path, ingestion_result) — Graph enrichment populates isolated node information in the payload.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## tests/test_mcp_recipes.py

**File path**: `tests/test_mcp_recipes.py`
**Purpose**: Pytest coverage for mcp recipes.
**Dependencies**: External – __future__, json, pathlib, pytest; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `test_snippets_are_valid_json(snippet) — No docstring.`

**Constants and Configuration**
- RECIPES = Path("docs/MCP_RECIPES.md").read_text()

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_mcp_smoke_recipes.py

**File path**: `tests/test_mcp_smoke_recipes.py`
**Purpose**: Pytest coverage for mcp smoke recipes.
**Dependencies**: External – __future__, json, pathlib, pytest; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `_recipe_params() — No docstring.`
- `test_recipe_lines_are_valid_json(line) — No docstring.`

**Constants and Configuration**
- RECIPES = Path("docs/MCP_RECIPES.md").read_text().splitlines()

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_neo4j_writer.py

**File path**: `tests/test_neo4j_writer.py`
**Purpose**: Pytest coverage for neo4j writer.
**Dependencies**: External – __future__, neo4j, pathlib, types, typing; Internal – gateway.ingest.artifacts, gateway.ingest.neo4j_writer
**Related modules**: gateway.ingest.artifacts, gateway.ingest.neo4j_writer

**Classes**
- RecordingSession (bases: object) — Stubbed session that records Cypher queries for assertions. Methods: __init__(self), run(self, query), __enter__(self), __exit__(self, exc_type, exc, tb).
- RecordingDriver (bases: object) — Stubbed driver that yields recording sessions. Methods: __init__(self), session(self).

**Functions**
- `_make_writer() — Create a writer bound to a recording driver for inspection.`
- `test_sync_artifact_creates_domain_relationships() — Artifacts trigger the expected Cypher commands and relationships.`
- `test_sync_artifact_merges_subsystem_edge_once() — Syncing an artifact does not duplicate the subsystem relationship.`
- `test_sync_chunks_links_chunk_to_artifact() — Chunk synchronization creates chunk nodes and linking edges.`

**Constants and Configuration**
- None

**Data Flow**
- Executes Neo4j Cypher statements and serialises graph results.

**Integration Points**
- Neo4j driver

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## tests/test_qdrant_writer.py

**File path**: `tests/test_qdrant_writer.py`
**Purpose**: Pytest coverage for qdrant writer.
**Dependencies**: External – __future__, unittest; Internal – gateway.ingest.artifacts, gateway.ingest.qdrant_writer
**Related modules**: gateway.ingest.artifacts, gateway.ingest.qdrant_writer

**Classes**
- RecordingClient (bases: object) — No docstring. Methods: __init__(self), get_collection(self, name), recreate_collection(self, collection_name, vectors_config, optimizers_config), upsert(self, collection_name, points).

**Functions**
- `build_chunk(path, text, metadata) — No docstring.`
- `test_ensure_collection_creates_when_missing() — No docstring.`
- `test_ensure_collection_noop_when_exists() — No docstring.`
- `test_upsert_chunks_builds_points() — No docstring.`
- `test_upsert_chunks_noop_on_empty() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_recipes_executor.py

**File path**: `tests/test_recipes_executor.py`
**Purpose**: Pytest coverage for recipes executor.
**Dependencies**: External – __future__, pathlib, pytest, types, typing; Internal – gateway.mcp.config, gateway.recipes.executor, gateway.recipes.models
**Related modules**: gateway.mcp.config, gateway.recipes.executor, gateway.recipes.models

**Classes**
- FakeToolExecutor (bases: object) — No docstring. Methods: __init__(self, responses).

**Functions**
- None

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.

## tests/test_release_scripts.py

**File path**: `tests/test_release_scripts.py`
**Purpose**: Pytest coverage for release scripts.
**Dependencies**: External – __future__, os, pathlib, subprocess; Internal – None
**Related modules**: None

**Classes**
- None

**Functions**
- `_env_with_venv() — No docstring.`
- `test_build_wheel_script(tmp_path) — No docstring.`
- `test_checksums_script(tmp_path) — No docstring.`
- `test_generate_changelog(tmp_path) — No docstring.`

**Constants and Configuration**
- REPO_ROOT = Path(__file__).resolve().parents[1]
- SCRIPTS_DIR = REPO_ROOT / "scripts"

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_scheduler.py

**File path**: `tests/test_scheduler.py`
**Purpose**: Unit tests exercising the ingestion scheduler behaviour and metrics.
**Dependencies**: External – __future__, apscheduler.triggers.cron, apscheduler.triggers.interval, collections, filelock, pathlib, prometheus_client, pytest, unittest; Internal – gateway.config.settings, gateway.ingest.pipeline, gateway.scheduler
**Related modules**: gateway.config.settings, gateway.ingest.pipeline, gateway.scheduler

**Classes**
- None

**Functions**
- `reset_cache() — Clear cached settings before and after each test.`
- `scheduler_settings(tmp_path) — Provide scheduler settings pointing at a temporary repo.`
- `make_scheduler(settings) — Instantiate a scheduler with its APScheduler stubbed out.`
- `_metric_value(name, labels) — Fetch a Prometheus sample value with defaults for missing metrics.`
- `make_result(head) — Construct a minimal ingestion result for scheduler tests.`
- `test_scheduler_skips_when_repo_head_unchanged(scheduler_settings) — Scheduler skips when repository head hash matches the cached value.`
- `test_scheduler_runs_when_repo_head_changes(scheduler_settings) — Scheduler triggers ingestion when the repository head changes.`
- `test_scheduler_start_uses_interval_trigger(scheduler_settings) — Schedulers without cron use the configured interval trigger.`
- `test_scheduler_start_uses_cron_trigger(tmp_path) — Cron expressions configure a cron trigger instead of interval.`
- `test_scheduler_skips_when_lock_contended(scheduler_settings) — Lock contention causes the scheduler to skip runs and record metrics.`
- `test_scheduler_requires_maintainer_token(tmp_path) — Schedulers skip setup when auth is enabled without a maintainer token.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## tests/test_search_api.py

**File path**: `tests/test_search_api.py`
**Purpose**: Pytest coverage for search api.
**Dependencies**: External – __future__, datetime, fastapi.testclient, json, pathlib, pytest; Internal – gateway.api.app, gateway.config.settings, gateway.search.service
**Related modules**: gateway.api.app, gateway.config.settings, gateway.search.service

**Classes**
- DummySearchService (bases: object) — No docstring. Methods: __init__(self), search(self).

**Functions**
- `test_search_endpoint_returns_results(monkeypatch, tmp_path) — No docstring.`
- `test_search_reuses_incoming_request_id(monkeypatch, tmp_path) — No docstring.`
- `test_search_requires_reader_token(monkeypatch, tmp_path) — No docstring.`
- `test_search_allows_maintainer_token(monkeypatch, tmp_path) — No docstring.`
- `test_search_feedback_logged(monkeypatch, tmp_path) — No docstring.`
- `test_search_filters_passed_to_service(monkeypatch, tmp_path) — No docstring.`
- `test_search_filters_invalid_type(monkeypatch, tmp_path) — No docstring.`
- `test_search_filters_invalid_namespaces(monkeypatch, tmp_path) — No docstring.`
- `test_search_filters_invalid_updated_after(monkeypatch, tmp_path) — No docstring.`
- `test_search_filters_invalid_max_age(monkeypatch, tmp_path) — No docstring.`
- `test_search_weights_endpoint(monkeypatch, tmp_path) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_search_cli_show_weights.py

**File path**: `tests/test_search_cli_show_weights.py`
**Purpose**: Pytest coverage for search cli show weights.
**Dependencies**: External – __future__, pathlib, pytest; Internal – gateway.config.settings, gateway.search
**Related modules**: gateway.config.settings, gateway.search

**Classes**
- None

**Functions**
- `clear_settings_cache(monkeypatch, tmp_path) — No docstring.`
- `test_show_weights_command(capsys) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_search_evaluation.py

**File path**: `tests/test_search_evaluation.py`
**Purpose**: Pytest coverage for search evaluation.
**Dependencies**: External – __future__, json, math, pathlib, pytest; Internal – gateway.search.cli, gateway.search.dataset, gateway.search.evaluation
**Related modules**: gateway.search.cli, gateway.search.dataset, gateway.search.evaluation

**Classes**
- None

**Functions**
- `test_evaluate_model(tmp_path) — No docstring.`
- `test_evaluate_cli(tmp_path, monkeypatch, capsys) — No docstring.`
- `test_evaluate_model_with_empty_dataset(tmp_path) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_search_exporter.py

**File path**: `tests/test_search_exporter.py`
**Purpose**: Pytest coverage for search exporter.
**Dependencies**: External – __future__, csv, json, pathlib, pytest; Internal – gateway.config.settings, gateway.search.cli, gateway.search.exporter, gateway.search.trainer
**Related modules**: gateway.config.settings, gateway.search.cli, gateway.search.exporter, gateway.search.trainer

**Classes**
- None

**Functions**
- `_write_events(path, events) — No docstring.`
- `_sample_event(request_id, vote) — No docstring.`
- `test_export_training_dataset_csv(tmp_path) — No docstring.`
- `test_export_training_data_cli(tmp_path, monkeypatch) — No docstring.`
- `test_train_model_from_dataset(tmp_path) — No docstring.`
- `test_train_model_cli(tmp_path, monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_search_maintenance.py

**File path**: `tests/test_search_maintenance.py`
**Purpose**: Tests for the search maintenance helpers.
**Dependencies**: External – __future__, datetime, json, os, pathlib, pytest, stat; Internal – gateway.search.maintenance
**Related modules**: gateway.search.maintenance

**Classes**
- None

**Functions**
- `_write_events(path, requests) — Write JSON lines representing feedback events for the supplied requests.`
- `test_prune_feedback_log_parses_various_timestamp_formats(tmp_path) — Ensure prune handles numeric, Z-suffixed, and missing timestamps.`
- `test_prune_feedback_log_by_age(tmp_path) — Retains only entries newer than the configured age threshold.`
- `test_prune_feedback_log_missing_file(tmp_path) — Raises if the feedback log file is absent.`
- `test_prune_feedback_log_requires_limit(tmp_path) — Rejects calls without an age or request limit configured.`
- `test_prune_feedback_log_empty_file(tmp_path) — Returns zeroed stats when the log contains no events.`
- `test_prune_feedback_log_guard_when_pruning_everything(tmp_path, caplog) — Leaves the log intact when filters would drop every request.`
- `test_prune_feedback_log_max_requests_prefers_newest(tmp_path) — Keeps only the newest requests when enforcing a max count.`
- `test_redact_dataset_csv(tmp_path) — Redacts populated CSV fields for queries, contexts, and notes.`
- `test_redact_dataset_csv_handles_missing_and_blank_fields(tmp_path) — Leaves missing or blank CSV fields untouched while redacting non-empty ones.`
- `test_redact_dataset_jsonl(tmp_path) — Redacts JSONL query and context fields when toggled.`
- `test_redact_dataset_jsonl_handles_missing_and_blank_fields(tmp_path) — Leaves absent or empty JSONL fields untouched while redacting populated ones.`
- `test_redact_dataset_missing_file(tmp_path) — Raises if the target dataset file is absent.`
- `test_redact_dataset_unsupported_suffix(tmp_path) — Rejects unsupported dataset extensions.`
- `test_redact_dataset_output_path_copies_metadata(tmp_path) — Preserves metadata when writing to an alternate output path.`
- `test_redact_dataset_jsonl_handles_blank_lines(tmp_path) — Preserves blank lines in JSONL datasets while redacting content.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.

## tests/test_search_profiles.py

**File path**: `tests/test_search_profiles.py`
**Purpose**: Pytest coverage for search profiles.
**Dependencies**: External – __future__, pytest; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

**Classes**
- None

**Functions**
- `clear_weight_env(monkeypatch) — No docstring.`
- `test_resolved_search_weights_default() — No docstring.`
- `test_resolved_search_weights_profile_selection(monkeypatch) — No docstring.`
- `test_resolved_search_weights_overrides(monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_search_service.py

**File path**: `tests/test_search_service.py`
**Purpose**: Pytest coverage for search service.
**Dependencies**: External – __future__, collections, datetime, prometheus_client, pytest, typing; Internal – gateway.graph.service, gateway.search, gateway.search.trainer
**Related modules**: gateway.graph.service, gateway.search, gateway.search.trainer

**Classes**
- FakeEmbedder (bases: object) — No docstring. Methods: encode(self, texts).
- FakePoint (bases: object) — No docstring. Methods: __init__(self, payload, score).
- FakeQdrantClient (bases: object) — No docstring. Methods: __init__(self, points), search(self).
- DummyGraphService (bases: GraphService) — No docstring. Methods: __init__(self, response), get_node(self, node_id), get_subsystem(self), search(self, term), run_cypher(self, query, parameters), shortest_path_depth(self, node_id).
- MapGraphService (bases: GraphService) — No docstring. Methods: __init__(self, data), get_node(self, node_id), get_subsystem(self), search(self, term), run_cypher(self, query, parameters), shortest_path_depth(self, node_id).
- CountingGraphService (bases: GraphService) — No docstring. Methods: __init__(self, response, depth), get_node(self, node_id), shortest_path_depth(self, node_id), get_subsystem(self), search(self, term), run_cypher(self, query, parameters).

**Functions**
- `_metric_value(name, labels) — No docstring.`
- `sample_points() — No docstring.`
- `graph_response() — No docstring.`
- `test_search_service_enriches_with_graph(sample_points, graph_response) — No docstring.`
- `test_search_service_handles_missing_graph(sample_points) — No docstring.`
- `test_search_hnsw_search_params(sample_points) — No docstring.`
- `test_lexical_score_affects_ranking() — No docstring.`
- `test_search_service_orders_by_adjusted_score() — No docstring.`
- `test_search_service_caches_graph_lookups(sample_points, graph_response) — No docstring.`
- `test_search_service_filters_artifact_types() — No docstring.`
- `test_search_service_filters_namespaces() — No docstring.`
- `test_search_service_filters_tags() — No docstring.`
- `test_search_service_filters_recency_updated_after() — No docstring.`
- `test_search_service_filters_recency_max_age_days() — No docstring.`
- `test_search_service_filters_subsystem_via_graph(graph_response) — No docstring.`
- `test_search_service_ml_model_reorders_results() — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Classes missing docstrings.
- Functions missing docstrings.

## tests/test_settings_defaults.py

**File path**: `tests/test_settings_defaults.py`
**Purpose**: Pytest coverage for settings defaults.
**Dependencies**: External – __future__, pytest; Internal – gateway.config.settings
**Related modules**: gateway.config.settings

**Classes**
- None

**Functions**
- `test_neo4j_database_defaults_to_knowledge(monkeypatch) — No docstring.`
- `test_neo4j_auth_enabled_defaults_true(monkeypatch) — No docstring.`
- `test_auth_enabled_defaults_true(monkeypatch) — No docstring.`
- `test_neo4j_password_defaults_empty(monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_tracing.py

**File path**: `tests/test_tracing.py`
**Purpose**: Pytest coverage for tracing.
**Dependencies**: External – __future__, opentelemetry.exporter.otlp.proto.http.trace_exporter, opentelemetry.sdk.trace, opentelemetry.sdk.trace.export, pytest; Internal – gateway.api.app, gateway.config.settings, gateway.observability, gateway.observability.tracing
**Related modules**: gateway.api.app, gateway.config.settings, gateway.observability, gateway.observability.tracing

**Classes**
- None

**Functions**
- `test_tracing_disabled_by_default(monkeypatch) — No docstring.`
- `test_tracing_enabled_instruments_app(monkeypatch) — No docstring.`
- `test_tracing_uses_otlp_exporter(monkeypatch) — No docstring.`
- `test_tracing_console_fallback(monkeypatch) — No docstring.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- Functions missing docstrings.

## tests/test_ui_routes.py

**File path**: `tests/test_ui_routes.py`
**Purpose**: Pytest coverage for ui routes.
**Dependencies**: External – __future__, fastapi.testclient, pathlib, prometheus_client, pytest; Internal – gateway.api.app, gateway.config.settings
**Related modules**: gateway.api.app, gateway.config.settings

**Classes**
- None

**Functions**
- `_reset_settings(tmp_path) — Clear cached settings and ensure the state directory exists for tests.`
- `test_ui_landing_served(tmp_path, monkeypatch) — The landing page renders successfully and increments the landing metric.`
- `test_ui_search_view(tmp_path, monkeypatch) — The search view renders and increments the search metric.`
- `test_ui_subsystems_view(tmp_path, monkeypatch) — The subsystems view renders and increments the subsystem metric.`
- `test_ui_lifecycle_download(tmp_path, monkeypatch) — Lifecycle report downloads are returned and recorded in metrics.`
- `test_ui_events_endpoint(tmp_path, monkeypatch) — Custom UI events are accepted and reflected in Prometheus metrics.`

**Constants and Configuration**
- None

**Data Flow**
- Provides pytest fixtures and assertions to exercise runtime behaviour.

**Integration Points**
- Standard library only

**Code Quality Notes**
- No immediate quality concerns identified during static scan.
