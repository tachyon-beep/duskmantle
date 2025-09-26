from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


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
    qdrant_url: str = Field("http://localhost:6333", alias="KM_QDRANT_URL")
    qdrant_api_key: str | None = Field(None, alias="KM_QDRANT_API_KEY")
    qdrant_collection: str = Field("esper_knowledge_v1", alias="KM_QDRANT_COLLECTION")

    neo4j_uri: str = Field("bolt://localhost:7687", alias="KM_NEO4J_URI")
    neo4j_user: str = Field("neo4j", alias="KM_NEO4J_USER")
    neo4j_password: str = Field("neo4jadmin", alias="KM_NEO4J_PASSWORD")
    neo4j_database: str = Field("knowledge", alias="KM_NEO4J_DATABASE")

    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", alias="KM_EMBEDDING_MODEL")
    ingest_window: int = Field(1000, alias="KM_INGEST_WINDOW")
    ingest_overlap: int = Field(200, alias="KM_INGEST_OVERLAP")
    ingest_use_dummy_embeddings: bool = Field(False, alias="KM_INGEST_USE_DUMMY")
    scheduler_enabled: bool = Field(False, alias="KM_SCHEDULER_ENABLED")
    scheduler_interval_minutes: int = Field(30, alias="KM_SCHEDULER_INTERVAL_MINUTES")
    coverage_enabled: bool = Field(True, alias="KM_COVERAGE_ENABLED")

    dry_run: bool = Field(False, alias="KM_INGEST_DRY_RUN")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load settings from environment (cached)."""
    return AppSettings()
