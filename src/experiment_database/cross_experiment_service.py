from __future__ import annotations

from typing import List

from .cross_experiment_models import (
    CrossExperimentStatistics,
    ExperimentRankingEntry,
)
from .database import ExperimentDatabase
from .statistics_models import (
    ExperimentStatistics,
)
from .statistics_service import StatisticsService


class CrossExperimentStatisticsService:
    """
    Builds summaries and rankings across experiments.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()
        self.statistics_service = (
            StatisticsService(database)
        )

    def get_all_experiment_statistics(
        self,
    ) -> List[ExperimentStatistics]:
        rows = self.database.fetch_all(
            """
            SELECT experiment_id
            FROM experiments
            ORDER BY created_at ASC
            """
        )

        return [
            self.statistics_service
            .get_experiment_statistics(
                row["experiment_id"]
            )
            for row in rows
        ]

    def rank_experiments(
        self,
        metric_name: str = "mean_reward",
        descending: bool = True,
    ) -> List[ExperimentRankingEntry]:
        statistics = (
            self.get_all_experiment_statistics()
        )

        scored: list[
            tuple[ExperimentStatistics, float | None]
        ] = [
            (
                item,
                self._metric_value(
                    item,
                    metric_name,
                ),
            )
            for item in statistics
        ]

        scored.sort(
            key=lambda item: (
                item[1] is not None,
                item[1]
                if item[1] is not None
                else float("-inf"),
            ),
            reverse=descending,
        )

        return [
            ExperimentRankingEntry(
                rank=index,
                experiment_id=(
                    item.experiment_id
                ),
                metric_name=metric_name,
                metric_value=value,
                total_runs=item.total_runs,
                success_rate=item.success_rate,
            )
            for index, (item, value)
            in enumerate(
                scored,
                start=1,
            )
        ]

    def build_summary(
        self,
        ranking_metric: str = "mean_reward",
    ) -> CrossExperimentStatistics:
        return CrossExperimentStatistics(
            experiment_statistics=(
                self.get_all_experiment_statistics()
            ),
            ranking=self.rank_experiments(
                metric_name=ranking_metric,
            ),
        )

    def _metric_value(
        self,
        statistics: ExperimentStatistics,
        metric_name: str,
    ) -> float | None:
        mapping = {
            "mean_reward": (
                statistics.reward_statistics.mean
            ),
            "median_reward": (
                statistics.reward_statistics.median
            ),
            "max_reward": (
                statistics.reward_statistics.maximum
            ),
            "success_rate": (
                statistics.success_rate
            ),
            "failure_rate": (
                statistics.failure_rate
            ),
            "conflict_rate": (
                statistics.conflict_rate
            ),
            "negotiation_rate": (
                statistics.negotiation_rate
            ),
            "mean_duration": (
                statistics.duration_statistics.mean
            ),
        }

        if metric_name not in mapping:
            raise ValueError(
                "Unsupported experiment metric: "
                f"{metric_name}"
            )

        return mapping[metric_name]
