from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import pytest

from gateway.api.connections import Neo4jConnectionManager, QdrantConnectionManager
from gateway.observability import (
    GRAPH_DEPENDENCY_LAST_SUCCESS,
    GRAPH_DEPENDENCY_STATUS,
    QDRANT_DEPENDENCY_LAST_SUCCESS,
    QDRANT_DEPENDENCY_STATUS,
)


def _reset_metric(metric) -> None:
    metric.set(0)


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    _reset_metric(GRAPH_DEPENDENCY_STATUS)
    _reset_metric(GRAPH_DEPENDENCY_LAST_SUCCESS)
    _reset_metric(QDRANT_DEPENDENCY_STATUS)
    _reset_metric(QDRANT_DEPENDENCY_LAST_SUCCESS)
    yield
    _reset_metric(GRAPH_DEPENDENCY_STATUS)
    _reset_metric(GRAPH_DEPENDENCY_LAST_SUCCESS)
    _reset_metric(QDRANT_DEPENDENCY_STATUS)
    _reset_metric(QDRANT_DEPENDENCY_LAST_SUCCESS)


def make_settings(**overrides: object) -> SimpleNamespace:
    defaults = {
        "neo4j_uri": "bolt://unit-test:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "test",
        "neo4j_database": "knowledge",
        "neo4j_readonly_uri": None,
        "neo4j_readonly_user": None,
        "neo4j_readonly_password": None,
        "qdrant_url": "http://localhost:6333",
        "qdrant_api_key": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_dummy_driver() -> mock.Mock:
    session = mock.MagicMock()
    session_context = mock.MagicMock()
    session_context.__enter__.return_value = session
    session_context.__exit__.return_value = None
    session.run.return_value.consume.return_value = None
    driver = mock.MagicMock()
    driver.session.return_value = session_context
    return driver


def test_neo4j_manager_records_success_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = make_settings()
    drivers_created: list[mock.Mock] = []

    def fake_driver(uri: str, auth: tuple[str, str]) -> mock.Mock:
        driver = _make_dummy_driver()
        drivers_created.append(driver)
        return driver

    monkeypatch.setattr("gateway.api.connections.GRAPH_DRIVER_FACTORY", fake_driver)

    manager = Neo4jConnectionManager(settings, log=mock.Mock())

    # First acquisition marks the dependency healthy.
    driver = manager.get_write_driver()
    assert driver is drivers_created[0]
    snapshot = manager.describe()
    assert snapshot.status == "ok"
    assert snapshot.last_success is not None
    assert GRAPH_DEPENDENCY_STATUS._value.get() == 1  # type: ignore[attr-defined]

    # Mark a failure and verify gauges flip.
    manager.mark_failure(Exception("boom"))
    degraded = manager.describe()
    assert degraded.status == "degraded"
    assert degraded.last_error == "boom"
    assert GRAPH_DEPENDENCY_STATUS._value.get() == 0  # type: ignore[attr-defined]

    # Heartbeat should rebuild the driver and set the healthy flag again.
    manager.heartbeat()
    assert manager.describe().status == "ok"
    assert GRAPH_DEPENDENCY_STATUS._value.get() == 1  # type: ignore[attr-defined]
    assert len(drivers_created) >= 2


def test_qdrant_manager_handles_health_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = make_settings()

    class StubClient:
        def __init__(self) -> None:
            self.calls = 0

        def health_check(self) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("offline")

    stub_client = StubClient()
    monkeypatch.setattr("gateway.api.connections.QDRANT_CLIENT_FACTORY", lambda **_: stub_client)

    manager = QdrantConnectionManager(settings, log=mock.Mock())

    # First heartbeat fails and marks dependency unhealthy.
    assert manager.heartbeat() is False
    snapshot = manager.describe()
    assert snapshot.status == "degraded"
    assert QDRANT_DEPENDENCY_STATUS._value.get() == 0  # type: ignore[attr-defined]

    # Subsequent heartbeat succeeds and restores health status.
    assert manager.heartbeat() is True
    healthy = manager.describe()
    assert healthy.status == "ok"
    assert QDRANT_DEPENDENCY_STATUS._value.get() == 1  # type: ignore[attr-defined]
