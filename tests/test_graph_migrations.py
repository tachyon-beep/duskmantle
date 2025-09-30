from __future__ import annotations

from collections import deque
from types import TracebackType

from gateway.graph.migrations.runner import MIGRATIONS, MigrationRunner


class FakeResult:
    def __init__(self, record: dict[str, object] | None = None) -> None:
        self._record = record

    def single(self) -> dict[str, object] | None:
        return self._record


class FakeTransaction:
    def __init__(self, applied_ids: set[str], results: deque[tuple[str, dict[str, object]]]) -> None:
        self.applied_ids = applied_ids
        self.results = results

    def run(self, query: str, **params: object) -> FakeResult:
        self.results.append((query, params))
        if "MERGE (m:MigrationHistory" in query:
            self.applied_ids.add(params["id"])
        return FakeResult()

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def __enter__(self) -> FakeTransaction:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return False


class FakeSession:
    def __init__(self, applied_ids: set[str], records: deque[tuple[str, dict[str, object]]]) -> None:
        self.applied_ids = applied_ids
        self.records = records

    def run(self, query: str, **params: object) -> FakeResult:
        if "MATCH (m:MigrationHistory" in query:
            migration_id = params["id"]
            if migration_id in self.applied_ids:
                return FakeResult(record={"id": migration_id})
            return FakeResult()
        if "MERGE (m:MigrationHistory" in query:
            self.applied_ids.add(params["id"])
        self.records.append((query, params))
        return FakeResult()

    def begin_transaction(self) -> FakeTransaction:
        return FakeTransaction(self.applied_ids, self.records)

    def close(self) -> None:
        pass

    def __enter__(self) -> FakeSession:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return False


class FakeDriver:
    def __init__(self) -> None:
        self.applied_ids: set[str] = set()
        self.records: deque[tuple[str, dict[str, object]]] = deque()

    def session(self, database: str) -> FakeSession:  # noqa: ARG002 - database unused
        return FakeSession(self.applied_ids, self.records)

    def close(self) -> None:
        pass


def test_migration_runner_applies_pending_migrations() -> None:
    driver = FakeDriver()
    runner = MigrationRunner(driver=driver, database="knowledge")

    pending_before = runner.pending_ids()
    assert pending_before == [migration.id for migration in MIGRATIONS]

    runner.run()

    assert driver.applied_ids == {migration.id for migration in MIGRATIONS}
    assert len(driver.records) >= len(MIGRATIONS[0].statements)

    pending_after = runner.pending_ids()
    assert pending_after == []
