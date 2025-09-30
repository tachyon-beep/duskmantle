from __future__ import annotations

from unittest import mock

import pytest
from prometheus_client import REGISTRY

from gateway.api.app import create_app
from gateway.observability.metrics import GRAPH_MIGRATION_LAST_STATUS, GRAPH_MIGRATION_LAST_TIMESTAMP


@pytest.fixture(autouse=True)
def reset_settings_cache():
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_migration_metrics():
    GRAPH_MIGRATION_LAST_STATUS.set(0)
    GRAPH_MIGRATION_LAST_TIMESTAMP.set(0)
    yield
    GRAPH_MIGRATION_LAST_STATUS.set(0)
    GRAPH_MIGRATION_LAST_TIMESTAMP.set(0)


def _metric(name: str) -> float | None:
    value = REGISTRY.get_sample_value(name)
    return float(value) if value is not None else None


def test_auto_migrate_runs_when_enabled(monkeypatch):
    monkeypatch.setenv("KM_GRAPH_AUTO_MIGRATE", "true")

    fake_driver = mock.Mock()
    fake_runner = mock.Mock()
    fake_runner.pending_ids.return_value = ["001_constraints"]

    monkeypatch.setattr("gateway.api.app.GraphDatabase", mock.Mock(driver=mock.Mock(return_value=fake_driver)))
    fake_runner_factory = mock.Mock(return_value=fake_runner)
    monkeypatch.setattr("gateway.api.app.MigrationRunner", fake_runner_factory)
    monkeypatch.setattr("gateway.api.app.QdrantClient", mock.Mock(return_value=mock.Mock()))

    create_app()

    fake_runner_factory.assert_called_once()
    fake_runner.pending_ids.assert_called_once()
    fake_runner.run.assert_called_once()
    assert _metric("km_graph_migration_last_status") == 1.0
    assert _metric("km_graph_migration_last_timestamp")


def test_auto_migrate_skipped_when_disabled(monkeypatch):
    monkeypatch.delenv("KM_GRAPH_AUTO_MIGRATE", raising=False)

    fake_driver = mock.Mock()
    fake_runner = mock.Mock()

    monkeypatch.setattr("gateway.api.app.GraphDatabase", mock.Mock(driver=mock.Mock(return_value=fake_driver)))
    fake_runner_factory = mock.Mock(return_value=fake_runner)
    monkeypatch.setattr("gateway.api.app.MigrationRunner", fake_runner_factory)
    monkeypatch.setattr("gateway.api.app.QdrantClient", mock.Mock(return_value=mock.Mock()))

    create_app()

    fake_runner_factory.assert_not_called()
    fake_runner.pending_ids.assert_not_called()
    fake_runner.run.assert_not_called()
    assert _metric("km_graph_migration_last_status") == -1.0
    assert _metric("km_graph_migration_last_timestamp") == 0.0


def test_auto_migrate_records_failure(monkeypatch):
    monkeypatch.setenv("KM_GRAPH_AUTO_MIGRATE", "true")

    fake_driver = mock.Mock()
    fake_runner = mock.Mock()
    fake_runner.pending_ids.return_value = ["001_constraints"]
    fake_runner.run.side_effect = RuntimeError("boom")

    monkeypatch.setattr("gateway.api.app.GraphDatabase", mock.Mock(driver=mock.Mock(return_value=fake_driver)))
    fake_runner_factory = mock.Mock(return_value=fake_runner)
    monkeypatch.setattr("gateway.api.app.MigrationRunner", fake_runner_factory)
    monkeypatch.setattr("gateway.api.app.QdrantClient", mock.Mock(return_value=mock.Mock()))

    create_app()

    fake_runner_factory.assert_called_once()
    fake_runner.pending_ids.assert_called_once()
    fake_runner.run.assert_called_once()
    assert _metric("km_graph_migration_last_status") == 0.0
    assert _metric("km_graph_migration_last_timestamp")
