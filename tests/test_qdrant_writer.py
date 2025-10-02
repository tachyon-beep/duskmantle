from __future__ import annotations

from unittest import mock

import httpx
import pytest
from qdrant_client.http.exceptions import UnexpectedResponse

from gateway.ingest.qdrant_writer import QdrantWriter


@pytest.fixture(autouse=True)
def stub_qdrant_models(monkeypatch: pytest.MonkeyPatch) -> None:
    vector_params = mock.Mock(name="VectorParams")
    optim_config = mock.Mock(name="OptimizersConfigDiff")
    monkeypatch.setattr("gateway.ingest.qdrant_writer.qmodels.VectorParams", mock.Mock(return_value=vector_params))
    monkeypatch.setattr(
        "gateway.ingest.qdrant_writer.qmodels.OptimizersConfigDiff",
        mock.Mock(return_value=optim_config),
    )


def build_client(**kwargs: object) -> mock.Mock:
    client = mock.Mock(**kwargs)
    # Provide both interfaces used by the writer to keep type-checkers quiet.
    client.collection_exists = kwargs.get("collection_exists", mock.Mock())
    client.get_collection = kwargs.get("get_collection", mock.Mock())
    client.create_collection = kwargs.get("create_collection", mock.Mock())
    client.recreate_collection = kwargs.get("recreate_collection", mock.Mock())
    client.upsert = kwargs.get("upsert", mock.Mock())
    client.delete = kwargs.get("delete", mock.Mock())
    return client


def test_ensure_collection_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client()
    client.collection_exists.return_value = False

    writer = QdrantWriter(client, "km_test")
    writer.ensure_collection(vector_size=384, retries=1)

    client.create_collection.assert_called_once()
    client.recreate_collection.assert_not_called()


def test_ensure_collection_noop_when_collection_exists() -> None:
    client = build_client()
    client.collection_exists.return_value = True

    writer = QdrantWriter(client, "km_test")
    writer.ensure_collection(vector_size=256)

    client.create_collection.assert_not_called()


def test_ensure_collection_retries_on_transient_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client()
    client.collection_exists.return_value = False
    client.create_collection.side_effect = [RuntimeError("temporary"), None]
    sleep_calls: list[float] = []

    monkeypatch.setattr("gateway.ingest.qdrant_writer.time.sleep", sleep_calls.append)

    writer = QdrantWriter(client, "km_test")
    writer.ensure_collection(vector_size=128, retries=2, retry_backoff=0.1)

    assert client.create_collection.call_count == 2
    # Ensure we attempted backoff exactly once with a positive value
    assert sleep_calls and sleep_calls[0] > 0


def test_ensure_collection_handles_conflict() -> None:
    client = build_client()
    client.collection_exists.return_value = False
    conflict = UnexpectedResponse(409, "Conflict", b"conflict", httpx.Headers())
    client.create_collection.side_effect = [conflict]

    writer = QdrantWriter(client, "km_test")
    writer.ensure_collection(vector_size=64, retries=1)

    client.create_collection.assert_called_once()


def test_reset_collection_invokes_recreate() -> None:
    client = build_client()
    writer = QdrantWriter(client, "km_reset")

    writer.reset_collection(vector_size=768)

    client.recreate_collection.assert_called_once()
