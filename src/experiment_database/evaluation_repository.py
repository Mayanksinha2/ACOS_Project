from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import (
    AggregatedEvaluationRecord,
)
from .repository_utils import (
    build_pagination_sql,
    require_non_empty,
)
from .serializers import evaluation_from_row
from .utils import (
    json_dumps,
    utc_now_iso,
)


class EvaluationRepository(
    BaseRepository[
        AggregatedEvaluationRecord
    ]
):
    def create(
        self,
        record: AggregatedEvaluationRecord,
    ) -> AggregatedEvaluationRecord:
        if not record.created_at:
            record.created_at = utc_now_iso()

        self.database.execute(
            """
            INSERT INTO aggregated_evaluations (
                evaluation_id,
                experiment_id,
                metrics_json,
                groups_json,
                warnings_json,
                errors_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                require_non_empty(
                    record.evaluation_id,
                    "evaluation_id",
                ),
                require_non_empty(
                    record.experiment_id,
                    "experiment_id",
                ),
                json_dumps(record.metrics),
                json_dumps(record.groups),
                json_dumps(record.warnings),
                json_dumps(record.errors),
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        evaluation_id: str,
    ) -> AggregatedEvaluationRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM aggregated_evaluations
            WHERE evaluation_id = ?
            """,
            (evaluation_id,),
        )

        return (
            evaluation_from_row(row)
            if row
            else None
        )

    def list_by_experiment(
        self,
        experiment_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[AggregatedEvaluationRecord]:
        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql = """
            SELECT *
            FROM aggregated_evaluations
            WHERE experiment_id = ?
            ORDER BY created_at DESC
        """
        sql += pagination_sql

        parameters = (
            experiment_id,
        ) + pagination_parameters

        return [
            evaluation_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        evaluation_id: str,
    ) -> bool:
        return self.delete_by_id(
            "aggregated_evaluations",
            "evaluation_id",
            evaluation_id,
        )
