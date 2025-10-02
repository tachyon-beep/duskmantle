"""Connection managers for external services (Neo4j and Qdrant)."""

from __future__ import annotations

import contextlib
import logging
import threading
import time
from dataclasses import dataclass

from neo4j import READ_ACCESS, Driver, GraphDatabase, RoutingControl
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from qdrant_client import QdrantClient

from gateway.config.settings import AppSettings
from gateway.observability import (
    GRAPH_DEPENDENCY_LAST_SUCCESS,
    GRAPH_DEPENDENCY_STATUS,
    QDRANT_DEPENDENCY_LAST_SUCCESS,
    QDRANT_DEPENDENCY_STATUS,
)

logger = logging.getLogger(__name__)

GRAPH_DRIVER_FACTORY = GraphDatabase.driver
QDRANT_CLIENT_FACTORY = QdrantClient


@dataclass(slots=True)
class DependencyStatus:
    """Serializable snapshot of an external dependency."""

    status: str
    revision: int
    last_success: float | None
    last_failure: float | None
    last_error: str | None


class Neo4jConnectionManager:
    """Lazy initialisation and health tracking for Neo4j drivers."""

    def __init__(self, settings: AppSettings, log: logging.Logger | None = None) -> None:
        self._settings = settings
        self._log = log or logger
        self._lock = threading.Lock()
        self._driver: Driver | None = None
        self._readonly_driver: Driver | None = None
        self._revision = 0
        self._healthy = False
        self._last_success: float | None = None
        self._last_failure: float | None = None
        self._last_error: str | None = None

    @property
    def revision(self) -> int:
        return self._revision

    def describe(self) -> DependencyStatus:
        status = "ok" if self._healthy else "degraded"
        return DependencyStatus(
            status=status,
            revision=self._revision,
            last_success=self._last_success,
            last_failure=self._last_failure,
            last_error=self._last_error,
        )

    def get_write_driver(self) -> Driver:
        driver = self._driver
        if driver is None:
            with self._lock:
                if self._driver is None:
                    self._driver = self._create_driver(
                        uri=self._settings.neo4j_uri,
                        user=self._settings.neo4j_user,
                        password=self._settings.neo4j_password,
                    )
                    self._revision += 1
            driver = self._driver
        return driver

    def get_readonly_driver(self) -> Driver:
        readonly_uri = self._settings.neo4j_readonly_uri or self._settings.neo4j_uri
        readonly_user = self._settings.neo4j_readonly_user or self._settings.neo4j_user
        readonly_password = self._settings.neo4j_readonly_password or self._settings.neo4j_password

        if (
            readonly_uri == self._settings.neo4j_uri
            and readonly_user == self._settings.neo4j_user
            and readonly_password == self._settings.neo4j_password
        ):
            return self.get_write_driver()

        driver = self._readonly_driver
        if driver is None:
            with self._lock:
                if self._readonly_driver is None:
                    self._readonly_driver = self._create_driver(
                        uri=readonly_uri,
                        user=readonly_user,
                        password=readonly_password,
                    )
                    self._revision += 1
            driver = self._readonly_driver
        return driver

    def mark_failure(self, exc: Exception | None = None) -> None:
        with self._lock:
            for candidate in (self._driver, self._readonly_driver):
                if candidate is not None:
                    with contextlib.suppress(Neo4jError, OSError):
                        candidate.close()
            self._driver = None
            self._readonly_driver = None
            self._revision += 1
            self._healthy = False
            self._last_success = None
            self._last_failure = time.time()
            self._last_error = str(exc) if exc else None
        GRAPH_DEPENDENCY_STATUS.set(0)

    def heartbeat(self) -> bool:
        try:
            driver = self.get_readonly_driver()
            with driver.session(
                database=self._settings.neo4j_database,
                default_access_mode=READ_ACCESS,
                routing_=RoutingControl.READ,
            ) as session:
                session.run("RETURN 1 AS ok").consume()
        except Exception as exc:  # pragma: no cover - exercised in unit tests
            self._log.warning("Neo4j heartbeat failed: %s", exc)
            self.mark_failure(exc)
            return False

        self._record_success()
        return True

    def _create_driver(self, *, uri: str, user: str, password: str) -> Driver:
        try:
            driver = GRAPH_DRIVER_FACTORY(uri, auth=(user, password))
            session_obj = driver.session(database=self._settings.neo4j_database)
            if hasattr(session_obj, "__enter__") and callable(getattr(session_obj, "__exit__", None)):
                with session_obj as session:
                    session.run("RETURN 1 AS ok").consume()
            else:
                try:
                    session_obj.run("RETURN 1 AS ok").consume()
                finally:
                    close_session = getattr(session_obj, "close", None)
                    if callable(close_session):
                        with contextlib.suppress(Exception):
                            close_session()
        except (Neo4jError, ServiceUnavailable, OSError) as exc:
            self._log.warning("Neo4j driver initialization failed: %s", exc)
            self.mark_failure(exc)
            raise

        self._record_success()
        self._log.info("Connected to Neo4j database '%s'", self._settings.neo4j_database)
        return driver

    def _record_success(self) -> None:
        now = time.time()
        self._healthy = True
        self._last_success = now
        GRAPH_DEPENDENCY_STATUS.set(1)
        GRAPH_DEPENDENCY_LAST_SUCCESS.set(now)


class QdrantConnectionManager:
    """Lazy initialisation and health tracking for Qdrant clients."""

    def __init__(self, settings: AppSettings, log: logging.Logger | None = None) -> None:
        self._settings = settings
        self._log = log or logger
        self._lock = threading.Lock()
        self._client: QdrantClient | None = None
        self._revision = 0
        self._healthy = False
        self._last_success: float | None = None
        self._last_failure: float | None = None
        self._last_error: str | None = None

    @property
    def revision(self) -> int:
        return self._revision

    def describe(self) -> DependencyStatus:
        status = "ok" if self._healthy else "degraded"
        return DependencyStatus(
            status=status,
            revision=self._revision,
            last_success=self._last_success,
            last_failure=self._last_failure,
            last_error=self._last_error,
        )

    def get_client(self) -> QdrantClient:
        client = self._client
        if client is None:
            with self._lock:
                if self._client is None:
                    self._client = self._create_client()
                    self._revision += 1
            client = self._client
        return client

    def mark_failure(self, exc: Exception | None = None) -> None:
        with self._lock:
            self._client = None
            self._revision += 1
            self._healthy = False
            self._last_success = None
            self._last_failure = time.time()
            self._last_error = str(exc) if exc else None
        QDRANT_DEPENDENCY_STATUS.set(0)

    def heartbeat(self) -> bool:
        try:
            client = self.get_client()
            client.health_check()
        except Exception as exc:  # pragma: no cover - exercised in unit tests
            self._log.warning("Qdrant heartbeat failed: %s", exc)
            self.mark_failure(exc)
            return False
        self._record_success()
        return True

    def _create_client(self) -> QdrantClient:
        try:
            client = QDRANT_CLIENT_FACTORY(
                url=self._settings.qdrant_url,
                api_key=self._settings.qdrant_api_key,
            )
        except (ValueError, ConnectionError, RuntimeError) as exc:
            self._log.warning("Qdrant client initialization failed: %s", exc)
            self.mark_failure(exc)
            raise

        self._record_success()
        self._log.info("Connected to Qdrant at %s", self._settings.qdrant_url)
        return client

    def _record_success(self) -> None:
        now = time.time()
        self._healthy = True
        self._last_success = now
        QDRANT_DEPENDENCY_STATUS.set(1)
        QDRANT_DEPENDENCY_LAST_SUCCESS.set(now)
