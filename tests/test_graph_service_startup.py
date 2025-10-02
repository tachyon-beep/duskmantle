from __future__ import annotations

from unittest import mock

import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from gateway.api.app import create_app


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def set_state_path(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path_factory.mktemp("state")))


async def _receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


def _make_request(app: FastAPI) -> Request:
    scope = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/graph/subsystems/foo",
        "headers": [],
    }
    return Request(scope, receive=_receive)


def test_graph_dependency_returns_503_when_database_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_driver = mock.Mock()

    graph_database = mock.Mock(driver=mock.Mock(return_value=fake_driver))
    monkeypatch.setattr("gateway.api.app.GraphDatabase", graph_database)
    monkeypatch.setattr("gateway.api.app._verify_graph_database", mock.Mock(return_value=False))
    monkeypatch.setattr("gateway.api.app.QdrantClient", mock.Mock(return_value=mock.Mock()))

    app = create_app()
    dependency = app.state.graph_service_dependency
    request = _make_request(app)

    with pytest.raises(HTTPException) as excinfo:
        dependency(request)

    error = excinfo.value
    assert error.status_code == 503
    assert "unavailable" in error.detail
    fake_driver.close.assert_called_once()


def test_graph_dependency_returns_service_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_driver = mock.Mock()
    graph_database = mock.Mock(driver=mock.Mock(return_value=fake_driver))
    monkeypatch.setattr("gateway.api.app.GraphDatabase", graph_database)
    monkeypatch.setattr("gateway.api.app._verify_graph_database", mock.Mock(return_value=True))
    monkeypatch.setattr("gateway.api.app.QdrantClient", mock.Mock(return_value=mock.Mock()))

    class DummyGraphService:
        def __init__(self, driver: mock.Mock) -> None:
            self.driver = driver

        def get_subsystem(self, name: str, depth: int, limit: int, cursor: str | None, include_artifacts: bool) -> dict[str, object]:
            return {
                "subsystem": {"name": name},
                "related": {"nodes": [], "cursor": None, "total": 0},
                "artifacts": [],
            }

    dummy_service = DummyGraphService(fake_driver)

    monkeypatch.setattr(
        "gateway.api.app.get_graph_service",
        mock.Mock(return_value=dummy_service),
    )

    app = create_app()
    dependency = app.state.graph_service_dependency
    request = _make_request(app)

    service = dependency(request)

    assert service is dummy_service
