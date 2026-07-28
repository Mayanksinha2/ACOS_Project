from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Iterator

from .migrations import apply_migrations


class ExperimentDatabase:
    """
    SQLite database manager for ACOS research data.

    A separate connection is created per operation. This keeps
    the class safe for sequential tests and suitable for future
    worker-based experiment execution.
    """

    def __init__(
        self,
        database_path: str | Path,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.database_path = Path(
            database_path
        ).expanduser().resolve()

        self.timeout_seconds = timeout_seconds
        self._initialization_lock = RLock()
        self._initialized = False

    def initialize(self) -> int:
        with self._initialization_lock:
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with self.connection() as connection:
                version = apply_migrations(
                    connection
                )

            self._initialized = True
            return version

    @contextmanager
    def connection(
        self,
    ) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=self.timeout_seconds,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        connection.execute(
            "PRAGMA synchronous = NORMAL"
        )

        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(
        self,
    ) -> Iterator[sqlite3.Connection]:
        self._ensure_initialized()

        with self.connection() as connection:
            try:
                connection.execute("BEGIN")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def execute(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> int:
        self._ensure_initialized()

        with self.transaction() as connection:
            cursor = connection.execute(
                sql,
                parameters,
            )

            return cursor.rowcount

    def fetch_one(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> sqlite3.Row | None:
        self._ensure_initialized()

        with self.connection() as connection:
            return connection.execute(
                sql,
                parameters,
            ).fetchone()

    def fetch_all(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> list[sqlite3.Row]:
        self._ensure_initialized()

        with self.connection() as connection:
            return list(
                connection.execute(
                    sql,
                    parameters,
                ).fetchall()
            )

    def table_names(self) -> list[str]:
        rows = self.fetch_all(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        return [
            str(row["name"])
            for row in rows
        ]

    def close(self) -> None:
        """
        Included for API symmetry.

        Connections are short-lived and automatically closed,
        so no persistent connection needs to be released.
        """

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()
