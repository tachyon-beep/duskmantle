from __future__ import annotations

from unittest import mock

from gateway.graph import cli


class DummySettings:
    neo4j_uri = "bolt://dummy"
    neo4j_user = "neo4j"
    neo4j_password = "password"
    neo4j_database = "knowledge"


def test_graph_cli_migrate_runs_runner(monkeypatch):
    dummy_settings = DummySettings()
    monkeypatch.setattr(cli, "get_settings", lambda: dummy_settings)

    fake_driver = mock.Mock()
    fake_runner = mock.Mock()

    monkeypatch.setattr(cli, "GraphDatabase", mock.Mock(driver=mock.Mock(return_value=fake_driver)))
    monkeypatch.setattr(cli, "MigrationRunner", mock.Mock(return_value=fake_runner))

    cli.main(["migrate"])

    fake_runner.run.assert_called_once()
    fake_driver.close.assert_called_once()


def test_graph_cli_dry_run_prints_pending(monkeypatch, capsys):
    dummy_settings = DummySettings()
    monkeypatch.setattr(cli, "get_settings", lambda: dummy_settings)

    fake_driver = mock.Mock()
    fake_runner = mock.Mock()
    fake_runner.pending_ids.return_value = ["001_constraints"]

    monkeypatch.setattr(cli, "GraphDatabase", mock.Mock(driver=mock.Mock(return_value=fake_driver)))
    monkeypatch.setattr(cli, "MigrationRunner", mock.Mock(return_value=fake_runner))

    cli.main(["migrate", "--dry-run"])

    captured = capsys.readouterr()
    assert "001_constraints" in captured.out
    fake_driver.close.assert_called_once()
