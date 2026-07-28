from __future__ import annotations

from typing import List

from .base_repository import BaseRepository
from .models import RunRecord
from .repository_utils import (
    build_pagination_sql,
    normalize_direction,
    require_non_empty,
)
from .serializers import run_from_row
from .utils import (
    bool_to_int,
    json_dumps,
    utc_now_iso,
)


class RunRepository(
    BaseRepository[RunRecord]
):
    def create(
        self,
        record: RunRecord,
    ) -> RunRecord:
        record.run_id = require_non_empty(
            record.run_id,
            "run_id",
        )
        record.experiment_id = require_non_empty(
            record.experiment_id,
            "experiment_id",
        )
        record.variant_name = require_non_empty(
            record.variant_name,
            "variant_name",
        )
        record.status = require_non_empty(
            record.status,
            "status",
        )

        if record.repetition_index < 1:
            raise ValueError(
                "repetition_index must be at least 1."
            )

        if not record.created_at:
            record.created_at = utc_now_iso()

        self.database.execute(
            """
            INSERT INTO runs (
                run_id,
                experiment_id,
                variant_name,
                repetition_index,
                random_seed,
                status,
                successful,
                reward,
                duration_seconds,
                conflict_detected,
                negotiation_required,
                metadata_json,
                warnings_json,
                errors_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                record.experiment_id,
                record.variant_name,
                record.repetition_index,
                record.random_seed,
                record.status,
                bool_to_int(record.successful),
                record.reward,
                record.duration_seconds,
                bool_to_int(
                    record.conflict_detected
                ),
                bool_to_int(
                    record.negotiation_required
                ),
                json_dumps(record.metadata),
                json_dumps(record.warnings),
                json_dumps(record.errors),
                record.created_at,
            ),
        )

        return record

    def get(
        self,
        run_id: str,
    ) -> RunRecord | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        )

        return run_from_row(row) if row else None

    def exists(
        self,
        run_id: str,
    ) -> bool:
        return self.exists_by_id(
            "runs",
            "run_id",
            run_id,
        )

    def list_by_experiment(
        self,
        experiment_id: str,
        variant_name: str | None = None,
        successful: bool | None = None,
        min_reward: float | None = None,
        limit: int | None = None,
        offset: int = 0,
        direction: str = "ASC",
    ) -> List[RunRecord]:
        normalized_direction = (
            normalize_direction(direction)
        )

        clauses = [
            "experiment_id = ?",
        ]
        parameters: tuple = (
            experiment_id,
        )

        if variant_name is not None:
            clauses.append(
                "variant_name = ?"
            )
            parameters += (variant_name,)

        if successful is not None:
            clauses.append(
                "successful = ?"
            )
            parameters += (
                bool_to_int(successful),
            )

        if min_reward is not None:
            clauses.append(
                "reward >= ?"
            )
            parameters += (min_reward,)

        sql = f"""
            SELECT *
            FROM runs
            WHERE {' AND '.join(clauses)}
            ORDER BY repetition_index {normalized_direction},
                     created_at {normalized_direction}
        """

        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql += pagination_sql
        parameters += pagination_parameters

        return [
            run_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def list_by_variant(
        self,
        variant_name: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[RunRecord]:
        pagination_sql, pagination_parameters = (
            build_pagination_sql(
                limit,
                offset,
            )
        )

        sql = """
            SELECT *
            FROM runs
            WHERE variant_name = ?
            ORDER BY created_at DESC
        """
        sql += pagination_sql

        parameters = (
            variant_name,
        ) + pagination_parameters

        return [
            run_from_row(row)
            for row in self.database.fetch_all(
                sql,
                parameters,
            )
        ]

    def delete(
        self,
        run_id: str,
    ) -> bool:
        return self.delete_by_id(
            "runs",
            "run_id",
            run_id,
        )
