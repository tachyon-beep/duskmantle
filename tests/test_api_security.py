from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.config.settings import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_audit_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")

    app = create_app()
    client = TestClient(app)

    # Missing credentials
    resp = client.get("/audit/history")
    assert resp.status_code == 401

    # Wrong token
    resp = client.get("/audit/history", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 403

    # Correct maintainer token
    resp = client.get(
        "/audit/history",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("KM_RATE_LIMIT_WINDOW", "60")

    app = create_app()
    client = TestClient(app)

    assert client.get("/metrics").status_code == 200
    assert client.get("/metrics").status_code == 200
    resp = client.get("/metrics")
    assert resp.status_code == 429
    assert resp.json()["detail"] == "Rate limit exceeded"
