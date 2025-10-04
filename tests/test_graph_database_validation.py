from __future__ import annotations

from unittest import mock

from neo4j.exceptions import ClientError

from gateway.api import app as gateway_app


def test_verify_graph_database_returns_false_when_database_missing() -> None:
    driver = mock.Mock()
    session_cm = mock.MagicMock()
    session = session_cm.__enter__.return_value
    session.run.side_effect = ClientError(
        "Neo.ClientError.Database.DatabaseNotFound",
        "database does not exist",
    )
    driver.session.return_value = session_cm

    result = gateway_app._verify_graph_database(driver, "knowledge")

    driver.session.assert_called_once_with(database="knowledge")
    assert result is False


def test_verify_graph_database_returns_true_on_success() -> None:
    driver = mock.Mock()
    session_cm = mock.MagicMock()
    session = session_cm.__enter__.return_value
    result_cursor = mock.Mock()
    session.run.return_value = result_cursor
    driver.session.return_value = session_cm

    result = gateway_app._verify_graph_database(driver, "knowledge")

    driver.session.assert_called_once_with(database="knowledge")
    result_cursor.consume.assert_called_once()
    assert result is True
