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

    repo_root: Path = Field(Path("/workspace/repo"), alias="KM_REPO_PATH")
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

    dry_run: bool = Field(False, alias="KM_INGEST_DRY_RUN")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load settings from environment (cached)."""
    return AppSettings()
