from __future__ import annotations

from typing import Callable, Iterable, List, TypeVar

from .cross_experiment_service import (
    CrossExperimentStatisticsService,
)
from .database import ExperimentDatabase
from .leaderboard_models import (
    ExperimentLeaderboardEntry,
    LeaderboardBundle,
    RunLeaderboardEntry,
    VariantLeaderboardEntry,
)
from .models import RunRecord
from .serializers import run_from_row
from .variant_statistics_service import (
    VariantStatisticsService,
)

T = TypeVar("T")


class LeaderboardService:
    """
    Produces ranked run, variant, and experiment views.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()
        self.variant_statistics = (
            VariantStatisticsService(database)
        )
        self.cross_experiment = (
            CrossExperimentStatisticsService(
                database
            )
        )

    def rank_runs(
        self,
        metric_name: str = "reward",
        limit: int | None = 10,
        descending: bool = True,
        successful_only: bool = False,
        experiment_id: str | None = None,
        variant_name: str | None = None,
    ) -> List[RunLeaderboardEntry]:
        runs = self._load_runs(
            experiment_id=experiment_id,
            variant_name=variant_name,
            successful_only=successful_only,
        )

        metric = self._run_metric_getter(
            metric_name
        )

        ranked = self._rank_values(
            runs,
            metric,
            descending=descending,
            limit=limit,
        )

        return [
            RunLeaderboardEntry(
                rank=index,
                run_id=run.run_id,
                experiment_id=run.experiment_id,
                variant_name=run.variant_name,
                metric_name=metric_name,
                metric_value=value,
                successful=run.successful,
                created_at=run.created_at,
            )
            for index, (run, value)
            in enumerate(ranked, start=1)
        ]

    def rank_variants(
        self,
        metric_name: str = "mean_reward",
        limit: int | None = 10,
        descending: bool = True,
        experiment_id: str | None = None,
    ) -> List[VariantLeaderboardEntry]:
        statistics = (
            self.variant_statistics
            .get_all_variant_statistics(
                experiment_id=experiment_id
            )
        )

        scored = [
            (
                item,
                self._variant_metric_value(
                    item,
                    metric_name,
                ),
            )
            for item in statistics.values()
        ]

        ranked = self._rank_values(
            scored,
            lambda item: item[1],
            descending=descending,
            limit=limit,
            values_precomputed=True,
        )

        return [
            VariantLeaderboardEntry(
                rank=index,
                variant_name=item.variant_name,
                metric_name=metric_name,
                metric_value=value,
                total_runs=item.total_runs,
                experiment_count=(
                    item.experiment_count
                ),
                success_rate=item.success_rate,
            )
            for index, (item, value)
            in enumerate(ranked, start=1)
        ]

    def rank_experiments(
        self,
        metric_name: str = "mean_reward",
        limit: int | None = 10,
        descending: bool = True,
    ) -> List[ExperimentLeaderboardEntry]:
        ranking = (
            self.cross_experiment
            .rank_experiments(
                metric_name=metric_name,
                descending=descending,
            )
        )

        if limit is not None:
            ranking = ranking[:limit]

        return [
            ExperimentLeaderboardEntry(
                rank=index,
                experiment_id=(
                    entry.experiment_id
                ),
                metric_name=metric_name,
                metric_value=entry.metric_value,
                total_runs=entry.total_runs,
                success_rate=entry.success_rate,
            )
            for index, entry
            in enumerate(ranking, start=1)
        ]

    def build_bundle(
        self,
        run_metric: str = "reward",
        variant_metric: str = "mean_reward",
        experiment_metric: str = "mean_reward",
        limit: int = 10,
    ) -> LeaderboardBundle:
        return LeaderboardBundle(
            run_leaderboard=self.rank_runs(
                metric_name=run_metric,
                limit=limit,
            ),
            variant_leaderboard=self.rank_variants(
                metric_name=variant_metric,
                limit=limit,
            ),
            experiment_leaderboard=(
                self.rank_experiments(
                    metric_name=(
                        experiment_metric
                    ),
                    limit=limit,
                )
            ),
        )

    def _load_runs(
        self,
        experiment_id: str | None,
        variant_name: str | None,
        successful_only: bool,
    ) -> List[RunRecord]:
        clauses: list[str] = []
        parameters: list[object] = []

        if experiment_id is not None:
            clauses.append(
                "experiment_id = ?"
            )
            parameters.append(experiment_id)

        if variant_name is not None:
            clauses.append(
                "variant_name = ?"
            )
            parameters.append(variant_name)

        if successful_only:
            clauses.append("successful = 1")

        where_sql = (
            ""
            if not clauses
            else " WHERE "
            + " AND ".join(clauses)
        )

        rows = self.database.fetch_all(
            f"""
            SELECT *
            FROM runs
            {where_sql}
            """,
            tuple(parameters),
        )

        return [
            run_from_row(row)
            for row in rows
        ]

    def _run_metric_getter(
        self,
        metric_name: str,
    ) -> Callable[[RunRecord], float | None]:
        mapping = {
            "reward": (
                lambda run: run.reward
            ),
            "duration_seconds": (
                lambda run: run.duration_seconds
            ),
            "successful": (
                lambda run: (
                    1.0 if run.successful else 0.0
                )
            ),
        }

        if metric_name not in mapping:
            raise ValueError(
                "Unsupported run metric: "
                f"{metric_name}"
            )

        return mapping[metric_name]

    def _variant_metric_value(
        self,
        statistics,
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
            "min_reward": (
                statistics.reward_statistics.minimum
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
                "Unsupported variant metric: "
                f"{metric_name}"
            )

        return mapping[metric_name]

    def _rank_values(
        self,
        items: Iterable[T],
        metric_getter: Callable[
            [T],
            float | None,
        ],
        descending: bool,
        limit: int | None,
        values_precomputed: bool = False,
    ) -> list[tuple[T, float | None]]:
        prepared: list[
            tuple[T, float | None]
        ] = []

        for item in items:
            if values_precomputed:
                actual_item = item[0]
                value = item[1]
            else:
                actual_item = item
                value = metric_getter(item)

            prepared.append(
                (actual_item, value)
            )

        prepared.sort(
            key=lambda pair: (
                pair[1] is not None,
                pair[1]
                if pair[1] is not None
                else float("-inf"),
            ),
            reverse=descending,
        )

        if limit is not None:
            prepared = prepared[:limit]

        return prepared
