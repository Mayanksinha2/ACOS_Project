from __future__ import annotations

from typing import Generic, Iterable, Optional, TypeVar

from .database import ExperimentDatabase


T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()

    def count(
        self,
        table_name: str,
        where_sql: str = "",
        parameters: tuple = (),
    ) -> int:
        sql = f"SELECT COUNT(*) AS value FROM {table_name}"

        if where_sql:
            sql += f" WHERE {where_sql}"

        row = self.database.fetch_one(
            sql,
            parameters,
        )

        return int(row["value"]) if row else 0

    def exists_by_id(
        self,
        table_name: str,
        id_column: str,
        identifier: str,
    ) -> bool:
        row = self.database.fetch_one(
            f"""
            SELECT 1 AS value
            FROM {table_name}
            WHERE {id_column} = ?
            LIMIT 1
            """,
            (identifier,),
        )

        return row is not None

    def delete_by_id(
        self,
        table_name: str,
        id_column: str,
        identifier: str,
    ) -> bool:
        affected = self.database.execute(
            f"""
            DELETE FROM {table_name}
            WHERE {id_column} = ?
            """,
            (identifier,),
        )

        return affected > 0
