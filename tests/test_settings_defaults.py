from __future__ import annotations

import pytest

from gateway.config.settings import AppSettings


def test_neo4j_database_defaults_to_neo4j(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_NEO4J_DATABASE", raising=False)
    settings = AppSettings()
    assert settings.neo4j_database == "neo4j"


def test_neo4j_auth_enabled_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_NEO4J_AUTH_ENABLED", raising=False)
    settings = AppSettings()
    assert settings.neo4j_auth_enabled is True
