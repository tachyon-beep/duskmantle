from __future__ import annotations

import os
import warnings
from collections.abc import Iterator
from types import SimpleNamespace, TracebackType
from typing import NoReturn

import pytest
from neo4j import GraphDatabase

warnings.filterwarnings(
    "ignore",
    message=r"Relying on Driver's destructor to close the session is deprecated",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r"neo4j\._sync\.driver",
)


class _NullSession:
    def __enter__(self) -> _NullSession:  # pragma: no cover - trivial
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # pragma: no cover - trivial
        return None

    def execute_read(self, func: object, *args: object, **kwargs: object) -> NoReturn:  # pragma: no cover - defensive
        raise RuntimeError("Graph driver disabled in tests")

    def run(self, *args: object, **kwargs: object) -> NoReturn:  # pragma: no cover - defensive
        raise RuntimeError("Graph driver disabled in tests")


class _NullDriver:
    def session(self, **kwargs: object) -> _NullSession:  # pragma: no cover - trivial
        return _NullSession()

    def close(self) -> None:  # pragma: no cover - trivial
        return None


@pytest.fixture(autouse=True)
def disable_real_graph_driver(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("neo4j"):
        return

    def _fake_driver(*args: object, **kwargs: object) -> _NullDriver:
        return _NullDriver()

    try:
        monkeypatch.setattr(
            "gateway.api.app.GraphDatabase",
            SimpleNamespace(driver=_fake_driver),
        )
    except ImportError:
        # Optional dependencies (e.g., sentence-transformers) may be missing in minimal envs.
        pass


@pytest.fixture(scope="session")
def neo4j_test_environment() -> Iterator[dict[str, str | None]]:
    uri = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7687")
    user = os.getenv("NEO4J_TEST_USER")
    password = os.getenv("NEO4J_TEST_PASSWORD")
    database = os.getenv("NEO4J_TEST_DATABASE", "knowledge")

    if user is None:
        auth = None
    else:
        if password is None:
            pytest.fail("NEO4J_TEST_PASSWORD must be set when NEO4J_TEST_USER is provided.")
        auth = (user, password)

    try:
        with GraphDatabase.driver(uri, auth=auth) as driver:
            driver.verify_connectivity()
    except Exception as exc:  # pragma: no cover - connection failures must surface
        pytest.fail(
            "Neo4j integration tests expect the packaged database to be running. " f"Failed to connect to {uri}: {exc}",
        )

    yield {"uri": uri, "user": user, "password": password, "database": database}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        if "neo4j" not in item.keywords:
            continue
        fixturenames = getattr(item, "fixturenames", None)
        if not isinstance(fixturenames, list):
            continue
        if "neo4j_test_environment" not in fixturenames:
            fixturenames.insert(0, "neo4j_test_environment")
