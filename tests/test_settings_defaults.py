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


def test_auth_enabled_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_AUTH_ENABLED", raising=False)
    settings = AppSettings()
    assert settings.auth_enabled is True

def test_symbols_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_SYMBOLS_ENABLED", raising=False)
    settings = AppSettings()
    assert settings.symbols_enabled is False




def test_editor_uri_template_defaults_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_EDITOR_URI_TEMPLATE", raising=False)
    settings = AppSettings()
    assert settings.editor_uri_template is None


def test_symbols_flag_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_SYMBOLS_ENABLED", "true")
    settings = AppSettings()
    assert settings.symbols_enabled is True

def test_editor_uri_template_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_EDITOR_URI_TEMPLATE", "vscode://file/{abs_path}:{line_start}")
    settings = AppSettings()
    assert settings.editor_uri_template == "vscode://file/{abs_path}:{line_start}"
