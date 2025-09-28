from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from neo4j import Driver

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    id: str
    statements: Iterable[str]


MIGRATIONS: list[Migration] = [
    Migration(
        id="001_constraints",
        statements=[
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:SourceFile) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:DesignDoc) REQUIRE d.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
        ],
    ),
    Migration(
        id="002_domain_entities",
        statements=[
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:IntegrationMessage) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (tc:TelemetryChannel) REQUIRE tc.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cfg:ConfigFile) REQUIRE cfg.path IS UNIQUE",
        ],
    ),
]


@dataclass
class MigrationRunner:
    driver: Driver
    database: str = "knowledge"

    def pending_ids(self) -> list[str]:
        pending: list[str] = []
        for migration in MIGRATIONS:
            if not self._is_applied(migration.id):
                pending.append(migration.id)
        return pending

    def run(self) -> None:
        with self.driver.session(database=self.database) as session:
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:MigrationHistory) REQUIRE m.id IS UNIQUE"
            )

        for migration in MIGRATIONS:
            if self._is_applied(migration.id):
                continue
            self._apply(migration)

    def _is_applied(self, migration_id: str) -> bool:
        with self.driver.session(database=self.database) as session:
            record = session.run(
                "MATCH (m:MigrationHistory {id: $id}) RETURN m",
                id=migration_id,
            ).single()
            return record is not None

    def _apply(self, migration: Migration) -> None:
        logger.info("Applying graph migration %s", migration.id)
        with self.driver.session(database=self.database) as session:
            for statement in migration.statements:
                session.run(statement)
            session.run(
                "MERGE (m:MigrationHistory {id: $id}) "
                "SET m.applied_at = datetime()",
                id=migration.id,
            )
