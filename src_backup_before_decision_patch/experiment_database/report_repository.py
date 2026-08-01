from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import ReportRecord
from .repository_utils import (
    build_pagination_sql,
    require_non_empty,
)
from .serializers import report_from_row
from .utils import (
    json_dumps,
    utc_now_iso,
)


class ReportRepository(
    BaseRepository[ReportRecord]
):
    def create(
        self,
        record: ReportRecord,
    ) -> ReportRecord:
        if not record.created_at:
            record.created_at = utc_now_iso()

        self.database.execute(
            """
            INSERT INTO reports (
                report_id,
                experiment_id,
                run_id,
                markdown_path,
                html_path,
                manifest_path,
                data_path,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                require_non_empty(
                    record.report_id,
                    "report_id",
                ),
                require_non_empty(
                    record.experiment_id,
                    "experiment_id",
                ),
                record.run_id,
                record.markdown_path,
                record.html_path,
                record.manifest_path,
                record.data_path,
                json_dumps(record.metadata),
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        report_id: str,
    ) -> ReportRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM reports
            WHERE report_id = ?
            """,
            (report_id,),
        )

        return report_from_row(row) if row else None

    def list_by_experiment(
        self,
        experiment_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[ReportRecord]:
        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql = """
            SELECT *
            FROM reports
            WHERE experiment_id = ?
            ORDER BY created_at DESC
        """
        sql += pagination_sql

        parameters = (
            experiment_id,
        ) + pagination_parameters

        return [
            report_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        report_id: str,
    ) -> bool:
        return self.delete_by_id(
            "reports",
            "report_id",
            report_id,
        )
