"""Pydantic-based configuration for the knowledge gateway."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

SEARCH_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "default": {
        "weight_subsystem": 0.28,
        "weight_relationship": 0.05,
        "weight_support": 0.09,
        "weight_coverage_penalty": 0.15,
        "weight_criticality": 0.12,
    },
    "analysis": {
        "weight_subsystem": 0.38,
        "weight_relationship": 0.10,
        "weight_support": 0.08,
        "weight_coverage_penalty": 0.18,
        "weight_criticality": 0.18,
    },
    "operations": {
        "weight_subsystem": 0.22,
        "weight_relationship": 0.08,
        "weight_support": 0.06,
        "weight_coverage_penalty": 0.28,
        "weight_criticality": 0.10,
    },
    "docs-heavy": {
        "weight_subsystem": 0.26,
        "weight_relationship": 0.04,
        "weight_support": 0.22,
        "weight_coverage_penalty": 0.12,
        "weight_criticality": 0.08,
    },
}


class AppSettings(BaseSettings):
    """Runtime configuration for the knowledge gateway."""

    api_host: str = Field("0.0.0.0", alias="KM_API_HOST")
    api_port: int = Field(8000, alias="KM_API_PORT")
    auth_mode: Literal["secure", "insecure"] = Field("secure", alias="KM_AUTH_MODE")
    auth_enabled: bool = Field(False, alias="KM_AUTH_ENABLED")
    reader_token: str | None = Field(None, alias="KM_READER_TOKEN")
    maintainer_token: str | None = Field(None, alias="KM_ADMIN_TOKEN")
    rate_limit_requests: int = Field(120, alias="KM_RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, alias="KM_RATE_LIMIT_WINDOW")

    repo_root: Path = Field(Path("/workspace/repo"), alias="KM_REPO_PATH")
    state_path: Path = Field(Path("/opt/knowledge/var"), alias="KM_STATE_PATH")
    content_root: Path = Field(Path("/workspace/repo"), alias="KM_CONTENT_ROOT")
    content_docs_subdir: Path = Field(Path("docs"), alias="KM_CONTENT_DOCS_SUBDIR")
    upload_default_overwrite: bool = Field(False, alias="KM_UPLOAD_DEFAULT_OVERWRITE")
    upload_default_ingest: bool = Field(False, alias="KM_UPLOAD_DEFAULT_INGEST")
    qdrant_url: str = Field("http://localhost:6333", alias="KM_QDRANT_URL")
    qdrant_api_key: str | None = Field(None, alias="KM_QDRANT_API_KEY")
    qdrant_collection: str = Field("km_knowledge_v1", alias="KM_QDRANT_COLLECTION")

    neo4j_uri: str = Field("bolt://localhost:7687", alias="KM_NEO4J_URI")
    neo4j_user: str = Field("neo4j", alias="KM_NEO4J_USER")
    neo4j_password: str = Field("neo4jadmin", alias="KM_NEO4J_PASSWORD")
    neo4j_database: str = Field("knowledge", alias="KM_NEO4J_DATABASE")
    neo4j_auth_enabled: bool = Field(True, alias="KM_NEO4J_AUTH_ENABLED")
    neo4j_readonly_uri: str | None = Field(None, alias="KM_NEO4J_READONLY_URI")
    neo4j_readonly_user: str | None = Field(None, alias="KM_NEO4J_READONLY_USER")
    neo4j_readonly_password: str | None = Field(None, alias="KM_NEO4J_READONLY_PASSWORD")

    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", alias="KM_EMBEDDING_MODEL")
    ingest_window: int = Field(1000, alias="KM_INGEST_WINDOW")
    ingest_overlap: int = Field(200, alias="KM_INGEST_OVERLAP")
    ingest_use_dummy_embeddings: bool = Field(False, alias="KM_INGEST_USE_DUMMY")
    ingest_incremental_enabled: bool = Field(True, alias="KM_INGEST_INCREMENTAL")
    ingest_parallel_workers: int = Field(2, alias="KM_INGEST_PARALLEL_WORKERS")
    ingest_max_pending_batches: int = Field(4, alias="KM_INGEST_MAX_PENDING_BATCHES")
    scheduler_enabled: bool = Field(False, alias="KM_SCHEDULER_ENABLED")
    scheduler_interval_minutes: int = Field(30, alias="KM_SCHEDULER_INTERVAL_MINUTES")
    scheduler_cron: str | None = Field(None, alias="KM_SCHEDULER_CRON")
    coverage_enabled: bool = Field(True, alias="KM_COVERAGE_ENABLED")
    coverage_history_limit: int = Field(5, alias="KM_COVERAGE_HISTORY_LIMIT")

    lifecycle_report_enabled: bool = Field(True, alias="KM_LIFECYCLE_REPORT_ENABLED")
    lifecycle_stale_days: int = Field(30, alias="KM_LIFECYCLE_STALE_DAYS")
    lifecycle_history_limit: int = Field(10, alias="KM_LIFECYCLE_HISTORY_LIMIT")

    tracing_enabled: bool = Field(False, alias="KM_TRACING_ENABLED")
    tracing_endpoint: str | None = Field(None, alias="KM_TRACING_ENDPOINT")
    tracing_headers: str | None = Field(None, alias="KM_TRACING_HEADERS")
    tracing_service_name: str = Field("duskmantle-knowledge-gateway", alias="KM_TRACING_SERVICE_NAME")
    tracing_sample_ratio: float = Field(1.0, alias="KM_TRACING_SAMPLE_RATIO")
    tracing_console_export: bool = Field(False, alias="KM_TRACING_CONSOLE_EXPORT")

    graph_auto_migrate: bool = Field(False, alias="KM_GRAPH_AUTO_MIGRATE")
    graph_subsystem_cache_ttl_seconds: int = Field(30, alias="KM_GRAPH_SUBSYSTEM_CACHE_TTL")
    graph_subsystem_cache_max_entries: int = Field(128, alias="KM_GRAPH_SUBSYSTEM_CACHE_MAX")

    search_weight_profile: Literal[
        "default",
        "analysis",
        "operations",
        "docs-heavy",
    ] = Field("default", alias="KM_SEARCH_WEIGHT_PROFILE")
    search_weight_subsystem: float = Field(0.28, alias="KM_SEARCH_W_SUBSYSTEM")
    search_weight_relationship: float = Field(0.05, alias="KM_SEARCH_W_RELATIONSHIP")
    search_weight_support: float = Field(0.09, alias="KM_SEARCH_W_SUPPORT")
    search_weight_coverage_penalty: float = Field(0.15, alias="KM_SEARCH_W_COVERAGE_PENALTY")
    search_weight_criticality: float = Field(0.12, alias="KM_SEARCH_W_CRITICALITY")
    search_sort_by_vector: bool = Field(False, alias="KM_SEARCH_SORT_BY_VECTOR")
    search_scoring_mode: Literal["heuristic", "ml"] = Field("heuristic", alias="KM_SEARCH_SCORING_MODE")
    search_model_path: Path | None = Field(None, alias="KM_SEARCH_MODEL_PATH")
    search_warn_slow_graph_ms: int = Field(250, alias="KM_SEARCH_WARN_GRAPH_MS")
    search_vector_weight: float = Field(1.0, alias="KM_SEARCH_VECTOR_WEIGHT")
    search_lexical_weight: float = Field(0.25, alias="KM_SEARCH_LEXICAL_WEIGHT")
    search_hnsw_ef_search: int | None = Field(128, alias="KM_SEARCH_HNSW_EF_SEARCH")

    dry_run: bool = Field(False, alias="KM_INGEST_DRY_RUN")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    @field_validator("tracing_sample_ratio")
    @classmethod
    def _clamp_tracing_ratio(cls, value: float) -> float:
        """Ensure the tracing sampling ratio stays within [0, 1]."""

        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value

    @field_validator(
        "search_weight_subsystem",
        "search_weight_relationship",
        "search_weight_support",
        "search_weight_coverage_penalty",
        "search_weight_criticality",
        "search_vector_weight",
        "search_lexical_weight",
    )
    @classmethod
    def _clamp_search_weights(cls, value: float) -> float:
        """Clamp search weights to [0, 1] for stability."""

        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value

    @field_validator("search_hnsw_ef_search")
    @classmethod
    def _sanitize_hnsw_ef(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            return None
        return int(value)

    @field_validator("graph_subsystem_cache_ttl_seconds")
    @classmethod
    def _sanitize_graph_cache_ttl(cls, value: int) -> int:
        if value < 0:
            return 0
        return value

    @field_validator("graph_subsystem_cache_max_entries")
    @classmethod
    def _sanitize_graph_cache_max(cls, value: int) -> int:
        if value < 1:
            return 1
        return value

    def resolved_search_weights(self) -> tuple[str, dict[str, float]]:
        """Return the active search weight profile name and resolved weights."""

        profile = self.search_weight_profile
        base = dict(SEARCH_WEIGHT_PROFILES.get(profile, SEARCH_WEIGHT_PROFILES["default"]))

        overrides: dict[str, float] = {}
        fields_set: set[str] = getattr(self, "model_fields_set", set())

        if "search_weight_subsystem" in fields_set:
            overrides["weight_subsystem"] = self.search_weight_subsystem
        if "search_weight_relationship" in fields_set:
            overrides["weight_relationship"] = self.search_weight_relationship
        if "search_weight_support" in fields_set:
            overrides["weight_support"] = self.search_weight_support
        if "search_weight_coverage_penalty" in fields_set:
            overrides["weight_coverage_penalty"] = self.search_weight_coverage_penalty
        if "search_weight_criticality" in fields_set:
            overrides["weight_criticality"] = self.search_weight_criticality

        resolved = base.copy()
        resolved.update(overrides)

        if overrides:
            return f"{profile}+overrides", resolved
        return profile, resolved

    def scheduler_trigger_config(self) -> dict[str, object]:
        """Return trigger configuration for the ingestion scheduler."""

        if self.scheduler_cron and self.scheduler_cron.strip():
            return {"type": "cron", "expression": self.scheduler_cron.strip()}
        return {
            "type": "interval",
            "minutes": max(1, self.scheduler_interval_minutes),
        }

    @field_validator("coverage_history_limit")
    @classmethod
    def _validate_history_limit(cls, value: int) -> int:
        if value < 1:
            return 1
        if value > 100:
            return 100
        return value

    @field_validator("lifecycle_stale_days")
    @classmethod
    def _validate_lifecycle_stale(cls, value: int) -> int:
        if value < 0:
            return 0
        if value > 365:
            return 365
        return value

    @field_validator("ingest_parallel_workers", "ingest_max_pending_batches", mode="before")
    @classmethod
    def _ensure_positive_parallelism(cls, value: int) -> int:
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            return 1
        if numeric < 1:
            return 1
        return numeric


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load settings from environment (cached)."""
    return AppSettings()
