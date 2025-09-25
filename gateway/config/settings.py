from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Runtime configuration for the knowledge gateway."""

    api_host: str = Field("0.0.0.0", alias="KM_API_HOST")
    api_port: int = Field(8000, alias="KM_API_PORT")
    auth_mode: str = Field("secure", alias="KM_AUTH_MODE")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load settings from environment (cached)."""
    return AppSettings()
