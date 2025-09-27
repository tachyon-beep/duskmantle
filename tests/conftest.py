from __future__ import annotations

import warnings
from types import SimpleNamespace

import pytest


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
    def __enter__(self):  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - trivial
        return None

    def execute_read(self, func, *args, **kwargs):  # pragma: no cover - defensive
        raise RuntimeError("Graph driver disabled in tests")

    def run(self, *args, **kwargs):  # pragma: no cover - defensive
        raise RuntimeError("Graph driver disabled in tests")


class _NullDriver:
    def session(self, **kwargs):  # pragma: no cover - trivial
        return _NullSession()

    def close(self):  # pragma: no cover - trivial
        return None


@pytest.fixture(autouse=True)
def disable_real_graph_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_driver(*args, **kwargs):
        return _NullDriver()

    monkeypatch.setattr("gateway.api.app.GraphDatabase", SimpleNamespace(driver=_fake_driver))
