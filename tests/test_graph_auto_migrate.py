from __future__ import annotations

from unittest import mock

import pytest
from neo4j.exceptions import Neo4jError
from prometheus_client import REGISTRY

from gateway.api.app import create_app
from gateway.api.connections import DependencyStatus
from gateway.observability.metrics import GRAPH_MIGRATION_LAST_STATUS, GRAPH_MIGRATION_LAST_TIMESTAMP


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_migration_metrics() -> None:
    GRAPH_MIGRATION_LAST_STATUS.set(0)
    GRAPH_MIGRATION_LAST_TIMESTAMP.set(0)
    yield
    GRAPH_MIGRATION_LAST_STATUS.set(0)
    GRAPH_MIGRATION_LAST_TIMESTAMP.set(0)


def _metric(name: str) -> float | None:
    value = REGISTRY.get_sample_value(name)
    return float(value) if value is not None else None


def _stub_managers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    driver: mock.Mock | None = None,
    qdrant_client: mock.Mock | None = None,
    write_driver_error: Exception | None = None,
) -> tuple[mock.Mock, mock.Mock]:
    driver = driver or mock.Mock()
    qdrant_client = qdrant_client or mock.Mock(health_check=mock.Mock(return_value=None))

    session = mock.MagicMock()
    session.run.return_value.consume.return_value = None
    session_cm = mock.MagicMock()
    session_cm.__enter__.return_value = session
    session_cm.__exit__.return_value = None
    driver.session.return_value = session_cm

    class _StubNeo4jManager:
        def __init__(self, settings: object, logger: object) -> None:  # noqa: D401 - signature parity for patching
            self.revision = 0
            self._driver = driver
            self._last_success: float | None = None
            self._last_failure: float | None = None
            self._last_error: str | None = None

        def get_write_driver(self) -> mock.Mock:
            if write_driver_error is not None:
                raise write_driver_error
            self.revision += 1
            return self._driver

        def get_readonly_driver(self) -> mock.Mock:
            return self._driver

        def mark_failure(self, exc: Exception | None = None) -> None:
            self.revision += 1
            self._last_failure = 0.0
            self._last_error = str(exc) if exc else None

        def heartbeat(self) -> bool:
            self._last_success = 0.0
            return True

        def describe(self) -> DependencyStatus:
            return DependencyStatus(
                status="ok" if write_driver_error is None else "degraded",
                revision=self.revision,
                last_success=self._last_success,
                last_failure=self._last_failure,
                last_error=self._last_error,
            )

    class _StubQdrantManager:
        def __init__(self, settings: object, logger: object) -> None:  # noqa: D401 - signature parity for patching
            self.revision = 0
            self._client = qdrant_client
            self._last_success: float | None = None
            self._last_failure: float | None = None
            self._last_error: str | None = None

        def get_client(self) -> object:
            self.revision += 1
            return self._client

        def mark_failure(self, exc: Exception | None = None) -> None:
            self.revision += 1
            self._last_failure = 0.0
            self._last_error = str(exc) if exc else None

        def heartbeat(self) -> bool:
            self._last_success = 0.0
            return True

        def describe(self) -> DependencyStatus:
            return DependencyStatus(
                status="ok",
                revision=self.revision,
                last_success=self._last_success,
                last_failure=self._last_failure,
                last_error=self._last_error,
            )

    monkeypatch.setattr("gateway.api.app.Neo4jConnectionManager", _StubNeo4jManager)
    monkeypatch.setattr("gateway.api.app.QdrantConnectionManager", _StubQdrantManager)
    monkeypatch.setattr("gateway.api.connections.GRAPH_DRIVER_FACTORY", lambda *args, **kwargs: driver)
    monkeypatch.setattr("gateway.api.connections.QDRANT_CLIENT_FACTORY", lambda **_: qdrant_client)
    return driver, qdrant_client


@pytest.mark.neo4j
@pytest.mark.integration("neo4j")
def test_auto_migrate_runs_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_GRAPH_AUTO_MIGRATE", "true")

    expected_driver, _ = _stub_managers(monkeypatch)
    runner = mock.Mock()
    runner.pending_ids.return_value = ["001_constraints"]
    runner.run.return_value = None

    def _runner_factory(*, driver: object, database: str) -> mock.Mock:  # noqa: ARG001
        assert driver is expected_driver
        return runner

    monkeypatch.setattr("gateway.api.app.MigrationRunner", _runner_factory)

    create_app()

    runner.pending_ids.assert_called_once()
    runner.run.assert_called_once()
    assert _metric("km_graph_migration_last_status") == 1.0
    assert _metric("km_graph_migration_last_timestamp")


@pytest.mark.neo4j
@pytest.mark.integration("neo4j")
def test_auto_migrate_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_GRAPH_AUTO_MIGRATE", raising=False)

    _stub_managers(monkeypatch)

    def _runner_factory(**kwargs: object) -> mock.Mock:  # pragma: no cover - should not be called
        raise AssertionError("MigrationRunner should not be constructed when auto-migrate disabled")

    monkeypatch.setattr("gateway.api.app.MigrationRunner", _runner_factory)

    create_app()

    assert _metric("km_graph_migration_last_status") == -1.0
    assert _metric("km_graph_migration_last_timestamp") == 0.0


@pytest.mark.neo4j
@pytest.mark.integration("neo4j")
def test_auto_migrate_records_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_GRAPH_AUTO_MIGRATE", "true")

    expected_driver, _ = _stub_managers(monkeypatch)
    runner = mock.Mock()
    runner.pending_ids.return_value = ["001_constraints"]
    runner.run.side_effect = RuntimeError("boom")

    def _runner_factory(*, driver: object, database: str) -> mock.Mock:  # noqa: ARG001
        assert driver is expected_driver
        return runner

    monkeypatch.setattr("gateway.api.app.MigrationRunner", _runner_factory)

    create_app()

    runner.pending_ids.assert_called_once()
    runner.run.assert_called_once()
    assert _metric("km_graph_migration_last_status") == 0.0
    assert _metric("km_graph_migration_last_timestamp")


@pytest.mark.neo4j
@pytest.mark.integration("neo4j")
def test_missing_database_disables_graph_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_GRAPH_AUTO_MIGRATE", raising=False)

    _stub_managers(monkeypatch, write_driver_error=Neo4jError("missing database"))

    app = create_app()

    graph_status = app.state.graph_manager.describe()
    assert graph_status.status == "degraded"
    assert app.state.graph_service_instance is None
    assert _metric("km_graph_migration_last_status") == 0.0
    assert _metric("km_graph_migration_last_timestamp")
