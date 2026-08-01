from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import ArtifactRecord
from .repository_utils import (
    build_pagination_sql,
    require_non_empty,
)
from .serializers import artifact_from_row
from .utils import (
    json_dumps,
    utc_now_iso,
)


class ArtifactRepository(
    BaseRepository[ArtifactRecord]
):
    def create(
        self,
        record: ArtifactRecord,
    ) -> ArtifactRecord:
        if not record.created_at:
            record.created_at = utc_now_iso()

        self.database.execute(
            """
            INSERT INTO artifacts (
                artifact_id,
                experiment_id,
                run_id,
                artifact_type,
                path,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                require_non_empty(
                    record.artifact_id,
                    "artifact_id",
                ),
                require_non_empty(
                    record.experiment_id,
                    "experiment_id",
                ),
                record.run_id,
                require_non_empty(
                    record.artifact_type,
                    "artifact_type",
                ),
                require_non_empty(
                    record.path,
                    "path",
                ),
                json_dumps(record.metadata),
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        artifact_id: str,
    ) -> ArtifactRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM artifacts
            WHERE artifact_id = ?
            """,
            (artifact_id,),
        )

        return (
            artifact_from_row(row)
            if row
            else None
        )

    def list_by_experiment(
        self,
        experiment_id: str,
        artifact_type: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[ArtifactRecord]:
        sql = """
            SELECT *
            FROM artifacts
            WHERE experiment_id = ?
        """
        parameters: tuple = (
            experiment_id,
        )

        if artifact_type is not None:
            sql += " AND artifact_type = ?"
            parameters += (
                artifact_type,
            )

        sql += " ORDER BY created_at DESC"

        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql += pagination_sql
        parameters += pagination_parameters

        return [
            artifact_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        artifact_id: str,
    ) -> bool:
        return self.delete_by_id(
            "artifacts",
            "artifact_id",
            artifact_id,
        )
