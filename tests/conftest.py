from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import warnings
from collections.abc import Iterable, Iterator
from types import SimpleNamespace, TracebackType
from typing import NoReturn
from uuid import uuid4

import pytest
from neo4j import GraphDatabase
from urllib.parse import urlparse

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

_INTEGRATION_ENV_VAR = "KM_TEST_RUN_INTEGRATION"


def _integration_enabled(config: pytest.Config) -> bool:
    if config.getoption("run_integration", default=False):
        return True
    value = os.getenv(_INTEGRATION_ENV_VAR, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _check_socket(host: str | None, port: int | None, *, timeout: float = 1.0) -> bool:
    if not host or port is None:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_integration_services() -> dict[str, bool]:
    results: dict[str, bool] = {}

    neo4j_uri = os.getenv("NEO4J_TEST_URI") or os.getenv("KM_NEO4J_URI") or "bolt://127.0.0.1:7687"
    parsed_neo4j = urlparse(neo4j_uri)
    results["neo4j"] = _check_socket(parsed_neo4j.hostname, parsed_neo4j.port or 7687)

    qdrant_url = os.getenv("KM_QDRANT_URL", "http://127.0.0.1:6333")
    parsed_qdrant = urlparse(qdrant_url)
    default_port = 443 if parsed_qdrant.scheme == "https" else 6333
    results["qdrant"] = _check_socket(parsed_qdrant.hostname, parsed_qdrant.port or default_port)

    return results


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        dest="run_integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external services (Neo4j, Qdrant, etc.)",
    )


try:  # pragma: no cover - simple import guard
    import sentence_transformers  # noqa: F401
except Exception:  # pragma: no cover - environment-specific shim

    class _StubSentenceTransformer:
        def __init__(self, model_name: str, *args: object, **kwargs: object) -> None:
            self.model_name = model_name

        def get_sentence_embedding_dimension(self) -> int:
            return 8

        def encode(self, texts: Iterable[str], convert_to_tensor: bool = False) -> list[list[float]]:
            rows = list(texts)
            dimension = self.get_sentence_embedding_dimension()
            return [[float(index + 1) for index in range(dimension)] for _ in rows]

    sys.modules["sentence_transformers"] = SimpleNamespace(
        SentenceTransformer=_StubSentenceTransformer,
    )


class _NullSession:
    def __init__(self) -> None:
        self._result = SimpleNamespace(consume=lambda: None, single=lambda: None)

    def __enter__(self) -> _NullSession:  # pragma: no cover - trivial
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # pragma: no cover - trivial
        return None

    def close(self) -> None:  # pragma: no cover - trivial
        return None

    def execute_read(self, func: object, *args: object, **kwargs: object) -> NoReturn:  # pragma: no cover - defensive
        raise RuntimeError("Graph driver disabled in tests")

    def run(self, *args: object, **kwargs: object) -> SimpleNamespace:  # pragma: no cover - trivial
        return self._result


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

    monkeypatch.setattr(
        "gateway.api.app.GraphDatabase",
        SimpleNamespace(driver=_fake_driver),
        raising=False,
    )
    monkeypatch.setattr(
        "gateway.api.connections.GraphDatabase",
        SimpleNamespace(driver=_fake_driver),
        raising=False,
    )
    monkeypatch.setattr(
        "gateway.api.connections.GRAPH_DRIVER_FACTORY",
        _fake_driver,
        raising=False,
    )
    monkeypatch.setattr(
        "gateway.api.connections.QdrantClient",
        lambda *args, **kwargs: SimpleNamespace(health_check=lambda: None),
        raising=False,
    )
    monkeypatch.setattr(
        "gateway.api.connections.QDRANT_CLIENT_FACTORY",
        lambda *args, **kwargs: SimpleNamespace(health_check=lambda: None),
        raising=False,
    )
    monkeypatch.setattr(
        "gateway.api.app.QdrantClient",
        lambda *args, **kwargs: SimpleNamespace(health_check=lambda: None),
        raising=False,
    )
    if not os.getenv("KM_TEST_USE_REAL_EMBEDDER"):

        class _StubEmbedder:
            def __init__(self, model: str) -> None:
                self.model = model
                self._dimension = 8

            def encode(self, texts: Iterable[str]) -> list[list[float]]:
                return [[float(index % self._dimension)] * self._dimension for index, _ in enumerate(texts)]

        monkeypatch.setattr(
            "gateway.api.dependencies.Embedder",
            _StubEmbedder,
            raising=False,
        )
    warnings.filterwarnings(
        "ignore",
        message="Relying on Driver's destructor to close the session is deprecated",
        category=DeprecationWarning,
    )
    monkeypatch.setattr(
        "gateway.api.app._dependency_heartbeat_loop",
        lambda app, interval: None,
        raising=False,
    )


@pytest.fixture(autouse=True)
def default_authentication_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide secure default credentials so create_app() can boot under auth-on defaults."""

    monkeypatch.setenv("KM_ADMIN_TOKEN", os.getenv("KM_ADMIN_TOKEN", "maintainer-token"))
    monkeypatch.setenv("KM_READER_TOKEN", os.getenv("KM_READER_TOKEN", "reader-token"))
    monkeypatch.setenv("KM_NEO4J_PASSWORD", os.getenv("KM_NEO4J_PASSWORD", "super-secure-password"))
    monkeypatch.setenv("KM_STRICT_DEPENDENCY_STARTUP", os.getenv("KM_STRICT_DEPENDENCY_STARTUP", "false"))


@pytest.fixture(scope="session")
def neo4j_test_environment() -> Iterator[dict[str, str | None]]:
    uri = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7687")
    user = os.getenv("NEO4J_TEST_USER")
    password = os.getenv("NEO4J_TEST_PASSWORD")
    database = os.getenv("NEO4J_TEST_DATABASE", "knowledge")

    container_name: str | None = None
    cleanup_container = False

    if os.getenv("NEO4J_TEST_URI") is None:
        docker_path = shutil.which("docker")
        if docker_path is None:
            pytest.fail(
                "Neo4j integration tests require Docker unless NEO4J_TEST_URI is provided. "
                "Install Docker or point NEO4J_TEST_URI at a running instance.",
            )

        container_name = f"neo4j-test-{uuid4().hex[:8]}"
        user = "neo4j"
        # The official Neo4j test image ships with the documented default admin password.
        # We pin it here so fixtures can spin up an isolated throwaway container without
        # relying on host secrets. The container only binds to localhost during tests.
        password = "neo4jadmin"  # NOSONAR - intentional test credential for local Neo4j
        database = "knowledge"
        cleanup_container = True

        cmd = [
            docker_path,
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            "host",
            "-e",
            # The docker image expects the same documented defaults; matches the fixture password.
            "NEO4J_AUTH=neo4j/neo4jadmin",  # NOSONAR - local integration test credential
            "-e",
            "NEO4J_dbms_default__database=knowledge",
            "-e",
            "NEO4J_server_default__listen__address=0.0.0.0",
            "-e",
            "NEO4J_server_default__advertised__address=127.0.0.1",
            "neo4j:5",
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:  # pragma: no cover - environment dependent
            pytest.fail("Failed to launch Neo4j test container. " f"Command: {' '.join(cmd)}\nstdout: {exc.stdout}\nstderr: {exc.stderr}")

        deadline = time.time() + 60
        while True:
            try:
                with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                    driver.verify_connectivity()
                break
            except Exception as exc:  # pragma: no cover - retry loop
                if time.time() > deadline:
                    if cleanup_container:
                        subprocess.run([docker_path, "rm", "-f", container_name], check=False)
                    pytest.fail(f"Timed out waiting for Neo4j test container to start: {exc}")
                time.sleep(1)

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

    os.environ.setdefault("NEO4J_TEST_URI", uri)
    if user:
        os.environ.setdefault("NEO4J_TEST_USER", user)
    if password:
        os.environ.setdefault("NEO4J_TEST_PASSWORD", password)
    os.environ.setdefault("NEO4J_TEST_DATABASE", database)

    try:
        yield {"uri": uri, "user": user, "password": password, "database": database}
    finally:
        if cleanup_container and container_name is not None:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                check=False,
                capture_output=True,
            )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    integration_enabled = _integration_enabled(config)
    service_status: dict[str, bool] = {}
    if integration_enabled:
        service_status = _probe_integration_services()

    for item in items:
        integration_marker = item.get_closest_marker("integration")
        requires_integration = integration_marker is not None or "neo4j" in item.keywords

        if requires_integration:
            if not integration_enabled:
                item.add_marker(
                    pytest.mark.skip(
                        reason="Integration tests require external services; pass --run-integration or set KM_TEST_RUN_INTEGRATION=1",
                    )
                )
                continue

            required_services = set(integration_marker.args if integration_marker else ())
            if "neo4j" in item.keywords:
                required_services.add("neo4j")
            if not required_services:
                required_services = {"neo4j", "qdrant"}

            missing = [name for name in sorted(required_services) if not service_status.get(name, False)]
            if missing:
                item.add_marker(
                    pytest.mark.skip(
                        reason="Integration dependencies unavailable: " + ", ".join(missing),
                    )
                )
                continue

        if "neo4j" in item.keywords:
            fixturenames = getattr(item, "fixturenames", None)
            if not isinstance(fixturenames, list):
                continue
            if "neo4j_test_environment" not in fixturenames:
                fixturenames.insert(0, "neo4j_test_environment")
