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

def test_embedding_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("KM_TEXT_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("KM_IMAGE_EMBEDDING_MODEL", raising=False)
    settings = AppSettings()
    assert settings.embedding_model == "BAAI/bge-m3"
    assert settings.text_embedding_model == "BAAI/bge-m3"
    assert settings.image_embedding_model == "sentence-transformers/clip-ViT-L-14"


def test_text_embedding_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_TEXT_EMBEDDING_MODEL", "BAAI/bge-base-en")
    settings = AppSettings()
    assert settings.text_embedding_model == "BAAI/bge-base-en"
    assert settings.embedding_model == "BAAI/bge-m3"


def test_image_embedding_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_IMAGE_EMBEDDING_MODEL", "sentence-transformers/clip-ViT-B-16")
    settings = AppSettings()
    assert settings.image_embedding_model == "sentence-transformers/clip-ViT-B-16"

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


def test_qdrant_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_QDRANT_TIMEOUT_SECONDS", raising=False)
    settings = AppSettings()
    assert settings.qdrant_timeout_seconds == 60.0


def test_qdrant_timeout_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_QDRANT_TIMEOUT_SECONDS", "120")
    settings = AppSettings()
    assert settings.qdrant_timeout_seconds == 120.0
