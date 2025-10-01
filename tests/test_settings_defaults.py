from __future__ import annotations

import pytest

from gateway.config.settings import AppSettings


def test_neo4j_database_defaults_to_knowledge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_NEO4J_DATABASE", raising=False)
    settings = AppSettings()
    assert settings.neo4j_database == "knowledge"
