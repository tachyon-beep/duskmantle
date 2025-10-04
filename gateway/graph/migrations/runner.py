"""Helpers for applying and tracking Neo4j schema migrations."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from neo4j import Driver

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Describe a single migration and the Cypher statements it executes."""

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
        id="003_symbols",
        statements=[
            "CREATE CONSTRAINT IF NOT EXISTS FOR (sym:Symbol) REQUIRE sym.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (sym:Symbol) ON (sym.name)",
            "CREATE INDEX IF NOT EXISTS FOR (sym:Symbol) ON (sym.language)",
        ],
    ),
]


@dataclass
class MigrationRunner:
    """Apply ordered graph migrations using a shared Neo4j driver."""

    driver: Driver
    database: str = "knowledge"

    def pending_ids(self) -> list[str]:
        """Return the identifiers of migrations that have not yet been applied."""
        pending: list[str] = []
        for migration in MIGRATIONS:
            if not self._is_applied(migration.id):
                pending.append(migration.id)
        return pending

    def run(self) -> None:
        """Apply all pending migrations to the configured Neo4j database."""
        with self.driver.session(database=self.database) as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:MigrationHistory) REQUIRE m.id IS UNIQUE")

        for migration in MIGRATIONS:
            if self._is_applied(migration.id):
                continue
            self._apply(migration)

    def _is_applied(self, migration_id: str) -> bool:
        """Return whether the given migration has already been recorded."""
        with self.driver.session(database=self.database) as session:
            record = session.run(
                "MATCH (m:MigrationHistory {id: $id}) RETURN m",
                id=migration_id,
            ).single()
            return record is not None

    def _apply(self, migration: Migration) -> None:
        """Execute migration statements and record completion."""
        logger.info("Applying graph migration %s", migration.id)
        with self.driver.session(database=self.database) as session:
            for statement in migration.statements:
                session.run(statement)
            session.run(
                "MERGE (m:MigrationHistory {id: $id}) SET m.applied_at = datetime()",
                id=migration.id,
            )
