from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import AblationResultRecord
from .repository_utils import (
    build_pagination_sql,
    require_non_empty,
)
from .serializers import ablation_from_row
from .utils import (
    json_dumps,
    utc_now_iso,
)


class AblationRepository(
    BaseRepository[AblationResultRecord]
):
    def create(
        self,
        record: AblationResultRecord,
    ) -> AblationResultRecord:
        if not record.created_at:
            record.created_at = utc_now_iso()

        self.database.execute(
            """
            INSERT INTO ablation_results (
                ablation_id,
                experiment_id,
                baseline_group,
                primary_metric,
                best_group,
                worst_group,
                ranking_json,
                comparisons_json,
                warnings_json,
                errors_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                require_non_empty(
                    record.ablation_id,
                    "ablation_id",
                ),
                require_non_empty(
                    record.experiment_id,
                    "experiment_id",
                ),
                require_non_empty(
                    record.baseline_group,
                    "baseline_group",
                ),
                require_non_empty(
                    record.primary_metric,
                    "primary_metric",
                ),
                record.best_group,
                record.worst_group,
                json_dumps(record.ranking),
                json_dumps(record.comparisons),
                json_dumps(record.warnings),
                json_dumps(record.errors),
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        ablation_id: str,
    ) -> AblationResultRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM ablation_results
            WHERE ablation_id = ?
            """,
            (ablation_id,),
        )

        return (
            ablation_from_row(row)
            if row
            else None
        )

    def list_by_experiment(
        self,
        experiment_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[AblationResultRecord]:
        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql = """
            SELECT *
            FROM ablation_results
            WHERE experiment_id = ?
            ORDER BY created_at DESC
        """
        sql += pagination_sql

        parameters = (
            experiment_id,
        ) + pagination_parameters

        return [
            ablation_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        ablation_id: str,
    ) -> bool:
        return self.delete_by_id(
            "ablation_results",
            "ablation_id",
            ablation_id,
        )
