from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import PublicationRecord
from .repository_utils import (
    build_pagination_sql,
    require_non_empty,
)
from .serializers import publication_from_row
from .utils import (
    json_dumps,
    utc_now_iso,
)


class PublicationRepository(
    BaseRepository[PublicationRecord]
):
    def create(
        self,
        record: PublicationRecord,
    ) -> PublicationRecord:
        if not record.created_at:
            record.created_at = utc_now_iso()

        self.database.execute(
            """
            INSERT INTO publications (
                publication_id,
                experiment_id,
                run_id,
                markdown_path,
                latex_path,
                manifest_path,
                data_path,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                require_non_empty(
                    record.publication_id,
                    "publication_id",
                ),
                require_non_empty(
                    record.experiment_id,
                    "experiment_id",
                ),
                record.run_id,
                record.markdown_path,
                record.latex_path,
                record.manifest_path,
                record.data_path,
                json_dumps(record.metadata),
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        publication_id: str,
    ) -> PublicationRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM publications
            WHERE publication_id = ?
            """,
            (publication_id,),
        )

        return (
            publication_from_row(row)
            if row
            else None
        )

    def list_by_experiment(
        self,
        experiment_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[PublicationRecord]:
        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql = """
            SELECT *
            FROM publications
            WHERE experiment_id = ?
            ORDER BY created_at DESC
        """
        sql += pagination_sql

        parameters = (
            experiment_id,
        ) + pagination_parameters

        return [
            publication_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        publication_id: str,
    ) -> bool:
        return self.delete_by_id(
            "publications",
            "publication_id",
            publication_id,
        )
