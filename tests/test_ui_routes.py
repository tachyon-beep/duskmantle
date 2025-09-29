from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from gateway.api.app import create_app
from gateway.config.settings import get_settings


def _reset_settings(tmp_path: Path | None = None) -> None:
    get_settings.cache_clear()
    if tmp_path is not None:
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)


def test_ui_landing_served(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "landing"}) or 0.0

    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Duskmantle Knowledge Console" in response.text
    assert "Overview" in response.text

    after = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "landing"}) or 0.0
    assert after == before + 1.0

    static = client.get("/ui/static/styles.css")
    assert static.status_code == 200
    assert "dm-nav" in static.text

    _reset_settings()


def test_ui_search_view(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "search"}) or 0.0

    response = client.get("/ui/search")
    assert response.status_code == 200
    assert "Hybrid Search" in response.text
    assert "dm-search-form" in response.text

    after = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "search"}) or 0.0
    assert after == before + 1.0

    script = client.get("/ui/static/app.js")
    assert script.status_code == 200
    assert "performSearch" in script.text

    _reset_settings()
