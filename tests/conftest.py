from __future__ import annotations

import os
import shutil
import subprocess
import time
import warnings
from collections.abc import Iterator
from types import SimpleNamespace, TracebackType
from typing import NoReturn
from uuid import uuid4

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
            pytest.fail(
                "Failed to launch Neo4j test container. "
                f"Command: {' '.join(cmd)}\nstdout: {exc.stdout}\nstderr: {exc.stderr}"
            )

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
    for item in items:
        if "neo4j" not in item.keywords:
            continue
        fixturenames = getattr(item, "fixturenames", None)
        if not isinstance(fixturenames, list):
            continue
        if "neo4j_test_environment" not in fixturenames:
            fixturenames.insert(0, "neo4j_test_environment")
