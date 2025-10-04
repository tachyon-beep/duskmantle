"""Smoke tests covering the HTML console routes exposed by the gateway API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY
from pytest import MonkeyPatch, approx

from gateway.api.app import create_app
from gateway.config.settings import get_settings


@pytest.fixture(autouse=True)
def stub_dependency_initialisation(monkeypatch: MonkeyPatch) -> None:
    """Avoid external service connections when creating the app under test."""

    monkeypatch.setattr("gateway.api.app._initialise_graph_manager", lambda manager, settings: None)
    monkeypatch.setattr("gateway.api.app._initialise_qdrant_manager", lambda manager: None)


def _reset_settings(tmp_path: Path | None = None) -> None:
    """Clear cached settings and ensure the state directory exists for tests."""
    get_settings.cache_clear()
    if tmp_path is not None:
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)


def test_ui_landing_served(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """The landing page renders successfully and increments the landing metric."""
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "landing"}) or 0.0

    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Duskmantle Knowledge Console" in response.text
    assert "Overview" in response.text
    assert "data-dm-toggle-contrast" in response.text
    assert "data-dm-toggle-motion" in response.text

    after = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "landing"}) or 0.0
    assert after == approx(before + 1.0)

    static = client.get("/ui/static/styles.css")
    assert static.status_code == 200
    assert "dm-nav" in static.text

    _reset_settings()


def test_ui_search_view(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """The search view renders and increments the search metric."""
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "search"}) or 0.0

    response = client.get("/ui/search")
    assert response.status_code == 200
    assert "Hybrid Search" in response.text
    assert "dm-search-form" in response.text
    assert "data-dm-search-actions" in response.text

    after = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "search"}) or 0.0
    assert after == approx(before + 1.0)

    script = client.get("/ui/static/app.js")
    assert script.status_code == 200
    assert "performSearch" in script.text

    _reset_settings()


def test_ui_subsystems_view(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """The subsystems view renders and increments the subsystem metric."""
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "subsystems"}) or 0.0

    response = client.get("/ui/subsystems")
    assert response.status_code == 200
    assert "Subsystem Explorer" in response.text
    assert "dm-subsystem-form" in response.text
    assert "data-dm-subsystem-actions" in response.text

    after = REGISTRY.get_sample_value("km_ui_requests_total", {"view": "subsystems"}) or 0.0
    assert after == approx(before + 1.0)

    _reset_settings()


def test_ui_lifecycle_download(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Lifecycle report downloads are returned and recorded in metrics."""
    state_dir = tmp_path / "state"
    reports_dir = state_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "lifecycle_report.json"
    report_path.write_text('{"stale_docs": [], "isolated_nodes": []}')

    monkeypatch.setenv("KM_STATE_PATH", str(state_dir))
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_events_total", {"event": "lifecycle_download"}) or 0.0

    response = client.get("/ui/lifecycle/report")
    assert response.status_code == 200
    assert response.json() == {"stale_docs": [], "isolated_nodes": []}

    after = REGISTRY.get_sample_value("km_ui_events_total", {"event": "lifecycle_download"}) or 0.0
    assert after == approx(before + 1.0)

    _reset_settings()


def test_ui_events_endpoint(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Custom UI events are accepted and reflected in Prometheus metrics."""
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    _reset_settings()
    app = create_app()
    client = TestClient(app)

    before = REGISTRY.get_sample_value("km_ui_events_total", {"event": "test-event"}) or 0.0
    response = client.post("/ui/events", json={"event": "test-event"})
    assert response.status_code == 200
    after = REGISTRY.get_sample_value("km_ui_events_total", {"event": "test-event"}) or 0.0
    assert after == approx(before + 1.0)

    _reset_settings()


def test_ui_routes_require_auth_when_enabled(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """UI routes become protected when gateway authentication is enabled."""

    state_dir = tmp_path / "state"
    reports_dir = state_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "lifecycle_report.json").write_text('{"status": "ok"}')

    monkeypatch.setenv("KM_STATE_PATH", str(state_dir))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")

    _reset_settings()
    app = create_app()
    client = TestClient(app)

    # HTML landing page requires reader token
    unauth_resp = client.get("/ui/")
    assert unauth_resp.status_code == 401

    reader_headers = {"Authorization": "Bearer reader-token"}
    assert client.get("/ui/", headers=reader_headers).status_code == 200

    # Lifecycle JSON requires reader token
    unauth_lifecycle = client.get("/ui/lifecycle/report")
    assert unauth_lifecycle.status_code == 401
    assert client.get("/ui/lifecycle/report", headers=reader_headers).status_code == 200

    # Events endpoint requires maintainer token
    unauth_event = client.post("/ui/events", json={"event": "smoke"})
    assert unauth_event.status_code == 401
    reader_event = client.post("/ui/events", json={"event": "smoke"}, headers=reader_headers)
    assert reader_event.status_code == 403

    admin_headers = {"Authorization": "Bearer admin-token"}
    assert client.post("/ui/events", json={"event": "smoke"}, headers=admin_headers).status_code == 200

    _reset_settings()
