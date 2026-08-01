from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import ExperimentRecord
from .repository_utils import (
    build_pagination_sql,
    normalize_direction,
    require_non_empty,
)
from .serializers import experiment_from_row
from .utils import (
    json_dumps,
    utc_now_iso,
)


class ExperimentRepository(
    BaseRepository[ExperimentRecord]
):
    def create(
        self,
        record: ExperimentRecord,
    ) -> ExperimentRecord:
        record.experiment_id = require_non_empty(
            record.experiment_id,
            "experiment_id",
        )
        record.name = require_non_empty(
            record.name,
            "name",
        )
        record.status = require_non_empty(
            record.status,
            "status",
        )

        now = utc_now_iso()

        if not record.created_at:
            record.created_at = now

        if not record.updated_at:
            record.updated_at = now

        self.database.execute(
            """
            INSERT INTO experiments (
                experiment_id,
                name,
                status,
                description,
                metadata_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.experiment_id,
                record.name,
                record.status,
                record.description,
                json_dumps(record.metadata),
                record.created_at,
                record.updated_at,
            ),
        )

        return record

    def upsert(
        self,
        record: ExperimentRecord,
    ) -> ExperimentRecord:
        now = utc_now_iso()

        if not record.created_at:
            record.created_at = now

        record.updated_at = now

        self.database.execute(
            """
            INSERT INTO experiments (
                experiment_id,
                name,
                status,
                description,
                metadata_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(experiment_id) DO UPDATE SET
                name = excluded.name,
                status = excluded.status,
                description = excluded.description,
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                require_non_empty(
                    record.experiment_id,
                    "experiment_id",
                ),
                require_non_empty(
                    record.name,
                    "name",
                ),
                require_non_empty(
                    record.status,
                    "status",
                ),
                record.description,
                json_dumps(record.metadata),
                record.created_at,
                record.updated_at,
            ),
        )

        return record

    def get(
        self,
        experiment_id: str,
    ) -> ExperimentRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM experiments
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        )

        return (
            experiment_from_row(row)
            if row
            else None
        )

    def exists(
        self,
        experiment_id: str,
    ) -> bool:
        return self.exists_by_id(
            "experiments",
            "experiment_id",
            experiment_id,
        )

    def update_status(
        self,
        experiment_id: str,
        status: str,
    ) -> bool:
        affected = self.database.execute(
            """
            UPDATE experiments
            SET status = ?,
                updated_at = ?
            WHERE experiment_id = ?
            """,
            (
                require_non_empty(
                    status,
                    "status",
                ),
                utc_now_iso(),
                experiment_id,
            ),
        )

        return affected > 0

    def list(
        self,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        direction: str = "DESC",
    ) -> List[ExperimentRecord]:
        normalized_direction = (
            normalize_direction(direction)
        )

        sql = """
            SELECT *
            FROM experiments
        """
        parameters: tuple = ()

        if status is not None:
            sql += " WHERE status = ?"
            parameters += (status,)

        sql += (
            f" ORDER BY created_at "
            f"{normalized_direction}"
        )

        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql += pagination_sql
        parameters += pagination_parameters

        return [
            experiment_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        experiment_id: str,
    ) -> bool:
        return self.delete_by_id(
            "experiments",
            "experiment_id",
            experiment_id,
        )
