from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable, Dict

from .schema import (
    CREATE_SCHEMA_SQL,
    SCHEMA_VERSION,
)
from .utils import utc_now_iso


MigrationCallable = Callable[
    [sqlite3.Connection],
    None,
]


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    apply: MigrationCallable


def _migration_1(
    connection: sqlite3.Connection,
) -> None:
    connection.executescript(
        CREATE_SCHEMA_SQL
    )


MIGRATIONS: Dict[int, Migration] = {
    1: Migration(
        version=1,
        apply=_migration_1,
    ),
}


def ensure_migration_table(
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def get_current_schema_version(
    connection: sqlite3.Connection,
) -> int:
    ensure_migration_table(connection)

    row = connection.execute(
        """
        SELECT COALESCE(MAX(version), 0)
        FROM schema_migrations
        """
    ).fetchone()

    return int(row[0])


def apply_migrations(
    connection: sqlite3.Connection,
) -> int:
    ensure_migration_table(connection)

    current_version = (
        get_current_schema_version(connection)
    )

    for version in sorted(MIGRATIONS):
        if version <= current_version:
            continue

        migration = MIGRATIONS[version]

        with connection:
            migration.apply(connection)
            connection.execute(
                """
                INSERT INTO schema_migrations (
                    version,
                    applied_at
                )
                VALUES (?, ?)
                """,
                (
                    migration.version,
                    utc_now_iso(),
                ),
            )

    final_version = (
        get_current_schema_version(connection)
    )

    if final_version != SCHEMA_VERSION:
        raise RuntimeError(
            "Database schema version mismatch: "
            f"expected {SCHEMA_VERSION}, "
            f"received {final_version}."
        )

    return final_version
