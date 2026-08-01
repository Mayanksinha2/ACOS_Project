from __future__ import annotations

from collections import Counter
from typing import Iterable, List

from .database import ExperimentDatabase
from .models import RunRecord
from .serializers import run_from_row
from .statistics_models import (
    DatabaseStatistics,
    ExperimentStatistics,
)
from .statistics_utils import (
    compute_numeric_statistics,
    safe_rate,
)


class StatisticsService:
    """
    Computes descriptive statistics from persisted ACOS runs.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()

    def get_experiment_statistics(
        self,
        experiment_id: str,
    ) -> ExperimentStatistics:
        runs = self._load_runs(
            """
            SELECT *
            FROM runs
            WHERE experiment_id = ?
            ORDER BY created_at ASC
            """,
            (experiment_id,),
        )

        return self._build_experiment_statistics(
            experiment_id,
            runs,
        )

    def get_database_statistics(
        self,
    ) -> DatabaseStatistics:
        runs = self._load_runs(
            """
            SELECT *
            FROM runs
            ORDER BY created_at ASC
            """
        )

        total_experiments_row = (
            self.database.fetch_one(
                """
                SELECT COUNT(*) AS value
                FROM experiments
                """
            )
        )

        total_experiments = int(
            total_experiments_row["value"]
        ) if total_experiments_row else 0

        total_runs = len(runs)
        successful_runs = sum(
            1
            for run in runs
            if run.successful
        )
        failed_runs = (
            total_runs - successful_runs
        )

        conflict_count = sum(
            1
            for run in runs
            if run.conflict_detected
        )

        negotiation_count = sum(
            1
            for run in runs
            if run.negotiation_required
        )

        return DatabaseStatistics(
            total_experiments=total_experiments,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            success_rate=safe_rate(
                successful_runs,
                total_runs,
            ),
            conflict_rate=safe_rate(
                conflict_count,
                total_runs,
            ),
            negotiation_rate=safe_rate(
                negotiation_count,
                total_runs,
            ),
            reward_statistics=(
                compute_numeric_statistics(
                    run.reward
                    for run in runs
                )
            ),
            duration_statistics=(
                compute_numeric_statistics(
                    run.duration_seconds
                    for run in runs
                )
            ),
        )

    def _load_runs(
        self,
        sql: str,
        parameters: tuple = (),
    ) -> List[RunRecord]:
        rows = self.database.fetch_all(
            sql,
            parameters,
        )

        return [
            run_from_row(row)
            for row in rows
        ]

    def _build_experiment_statistics(
        self,
        experiment_id: str,
        runs: Iterable[RunRecord],
    ) -> ExperimentStatistics:
        run_list = list(runs)

        total_runs = len(run_list)
        successful_runs = sum(
            1
            for run in run_list
            if run.successful
        )
        failed_runs = (
            total_runs - successful_runs
        )

        conflict_count = sum(
            1
            for run in run_list
            if run.conflict_detected
        )

        negotiation_count = sum(
            1
            for run in run_list
            if run.negotiation_required
        )

        variant_counts = Counter(
            run.variant_name
            for run in run_list
        )

        statuses = Counter(
            run.status
            for run in run_list
        )

        warnings_count = sum(
            len(run.warnings)
            for run in run_list
        )

        errors_count = sum(
            len(run.errors)
            for run in run_list
        )

        return ExperimentStatistics(
            experiment_id=experiment_id,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            success_rate=safe_rate(
                successful_runs,
                total_runs,
            ),
            failure_rate=safe_rate(
                failed_runs,
                total_runs,
            ),
            conflict_count=conflict_count,
            conflict_rate=safe_rate(
                conflict_count,
                total_runs,
            ),
            negotiation_count=negotiation_count,
            negotiation_rate=safe_rate(
                negotiation_count,
                total_runs,
            ),
            reward_statistics=(
                compute_numeric_statistics(
                    run.reward
                    for run in run_list
                )
            ),
            duration_statistics=(
                compute_numeric_statistics(
                    run.duration_seconds
                    for run in run_list
                )
            ),
            variant_counts=dict(
                variant_counts
            ),
            statuses=dict(statuses),
            warnings_count=warnings_count,
            errors_count=errors_count,
        )
