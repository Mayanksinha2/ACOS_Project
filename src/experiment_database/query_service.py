from __future__ import annotations

from typing import Any, List

from .database import ExperimentDatabase
from .query_models import (
    ExperimentSearchCriteria,
    ExperimentSearchResult,
    RunSearchCriteria,
    RunSearchResult,
)
from .query_utils import (
    append_bool_filter,
    append_exact_filter,
    append_like_filter,
    append_metadata_filters,
    append_range_filter,
    build_order_and_pagination,
    build_where_clause,
)
from .serializers import (
    experiment_from_row,
    run_from_row,
)


class QueryService:
    """
    Read-only search service for ACOS research data.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()

    def search_experiments(
        self,
        criteria: ExperimentSearchCriteria,
    ) -> ExperimentSearchResult:
        clauses: List[str] = []
        parameters: List[Any] = []

        append_exact_filter(
            clauses,
            parameters,
            "experiment_id",
            criteria.experiment_id,
        )

        append_like_filter(
            clauses,
            parameters,
            "name",
            criteria.name_contains,
        )

        append_exact_filter(
            clauses,
            parameters,
            "status",
            criteria.status,
        )

        append_range_filter(
            clauses,
            parameters,
            "created_at",
            criteria.created_from,
            criteria.created_to,
        )

        append_metadata_filters(
            clauses,
            parameters,
            criteria.metadata_contains,
        )

        where_sql = build_where_clause(
            clauses
        )

        count_row = self.database.fetch_one(
            f"""
            SELECT COUNT(*) AS value
            FROM experiments
            {where_sql}
            """,
            tuple(parameters),
        )

        order_sql, pagination_parameters = (
            build_order_and_pagination(
                order_column="created_at",
                direction=criteria.direction,
                limit=criteria.limit,
                offset=criteria.offset,
            )
        )

        rows = self.database.fetch_all(
            f"""
            SELECT *
            FROM experiments
            {where_sql}
            {order_sql}
            """,
            tuple(parameters)
            + pagination_parameters,
        )

        return ExperimentSearchResult(
            items=[
                experiment_from_row(row)
                for row in rows
            ],
            total_count=int(
                count_row["value"]
            ) if count_row else 0,
            limit=criteria.limit,
            offset=criteria.offset,
        )

    def search_runs(
        self,
        criteria: RunSearchCriteria,
    ) -> RunSearchResult:
        clauses: List[str] = []
        parameters: List[Any] = []

        append_exact_filter(
            clauses,
            parameters,
            "run_id",
            criteria.run_id,
        )

        append_exact_filter(
            clauses,
            parameters,
            "experiment_id",
            criteria.experiment_id,
        )

        append_exact_filter(
            clauses,
            parameters,
            "variant_name",
            criteria.variant_name,
        )

        append_exact_filter(
            clauses,
            parameters,
            "status",
            criteria.status,
        )

        append_bool_filter(
            clauses,
            parameters,
            "successful",
            criteria.successful,
        )

        append_bool_filter(
            clauses,
            parameters,
            "conflict_detected",
            criteria.conflict_detected,
        )

        append_bool_filter(
            clauses,
            parameters,
            "negotiation_required",
            criteria.negotiation_required,
        )

        append_range_filter(
            clauses,
            parameters,
            "reward",
            criteria.min_reward,
            criteria.max_reward,
        )

        append_range_filter(
            clauses,
            parameters,
            "created_at",
            criteria.created_from,
            criteria.created_to,
        )

        append_metadata_filters(
            clauses,
            parameters,
            criteria.metadata_contains,
        )

        where_sql = build_where_clause(
            clauses
        )

        count_row = self.database.fetch_one(
            f"""
            SELECT COUNT(*) AS value
            FROM runs
            {where_sql}
            """,
            tuple(parameters),
        )

        order_sql, pagination_parameters = (
            build_order_and_pagination(
                order_column="created_at",
                direction=criteria.direction,
                limit=criteria.limit,
                offset=criteria.offset,
            )
        )

        rows = self.database.fetch_all(
            f"""
            SELECT *
            FROM runs
            {where_sql}
            {order_sql}
            """,
            tuple(parameters)
            + pagination_parameters,
        )

        return RunSearchResult(
            items=[
                run_from_row(row)
                for row in rows
            ],
            total_count=int(
                count_row["value"]
            ) if count_row else 0,
            limit=criteria.limit,
            offset=criteria.offset,
        )

    def get_experiment_with_runs(
        self,
        experiment_id: str,
    ) -> dict[str, Any] | None:
        experiment_result = (
            self.search_experiments(
                ExperimentSearchCriteria(
                    experiment_id=experiment_id,
                    limit=1,
                )
            )
        )

        if not experiment_result.items:
            return None

        run_result = self.search_runs(
            RunSearchCriteria(
                experiment_id=experiment_id,
                direction="ASC",
            )
        )

        return {
            "experiment": (
                experiment_result.items[0]
            ),
            "runs": run_result.items,
            "run_count": (
                run_result.total_count
            ),
        }
