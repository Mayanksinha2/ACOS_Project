from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .database import ExperimentDatabase
from .models import RunRecord
from .serializers import run_from_row
from .statistics_utils import (
    compute_numeric_statistics,
    safe_rate,
)
from .variant_statistics_models import (
    CrossExperimentSummary,
    VariantComparison,
    VariantStatistics,
)


class VariantStatisticsService:
    """
    Computes per-variant and cross-experiment statistics
    from persisted ACOS runs.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()

    def get_variant_statistics(
        self,
        variant_name: str,
        experiment_id: str | None = None,
    ) -> VariantStatistics:
        runs = self._load_runs(
            variant_name=variant_name,
            experiment_id=experiment_id,
        )

        return self._build_variant_statistics(
            variant_name,
            runs,
        )

    def get_all_variant_statistics(
        self,
        experiment_id: str | None = None,
    ) -> Dict[str, VariantStatistics]:
        runs = self._load_runs(
            variant_name=None,
            experiment_id=experiment_id,
        )

        grouped: dict[str, list[RunRecord]] = (
            defaultdict(list)
        )

        for run in runs:
            grouped[run.variant_name].append(run)

        return {
            variant_name: (
                self._build_variant_statistics(
                    variant_name,
                    variant_runs,
                )
            )
            for variant_name, variant_runs
            in sorted(grouped.items())
        }

    def compare_variants(
        self,
        baseline_variant: str,
        candidate_variant: str,
        primary_metric: str = "mean_reward",
        experiment_id: str | None = None,
    ) -> VariantComparison:
        baseline = self.get_variant_statistics(
            baseline_variant,
            experiment_id,
        )

        candidate = self.get_variant_statistics(
            candidate_variant,
            experiment_id,
        )

        baseline_value = self._metric_value(
            baseline,
            primary_metric,
        )

        candidate_value = self._metric_value(
            candidate,
            primary_metric,
        )

        if (
            baseline_value is None
            or candidate_value is None
        ):
            absolute_difference = None
            percentage_difference = None
            better_variant = None
        else:
            absolute_difference = (
                candidate_value
                - baseline_value
            )

            percentage_difference = (
                None
                if baseline_value == 0
                else (
                    absolute_difference
                    / abs(baseline_value)
                ) * 100.0
            )

            if candidate_value > baseline_value:
                better_variant = candidate_variant
            elif candidate_value < baseline_value:
                better_variant = baseline_variant
            else:
                better_variant = None

        return VariantComparison(
            baseline_variant=baseline_variant,
            candidate_variant=candidate_variant,
            primary_metric=primary_metric,
            baseline_value=baseline_value,
            candidate_value=candidate_value,
            absolute_difference=absolute_difference,
            percentage_difference=(
                percentage_difference
            ),
            better_variant=better_variant,
        )

    def get_cross_experiment_summary(
        self,
        ranking_metric: str = "mean_reward",
    ) -> CrossExperimentSummary:
        variants = self.get_all_variant_statistics()

        experiment_ids: set[str] = set()
        total_runs = 0

        for statistics in variants.values():
            total_runs += statistics.total_runs
            experiment_ids.update(
                statistics.experiment_ids
            )

        ranked = [
            (
                variant_name,
                self._metric_value(
                    statistics,
                    ranking_metric,
                ),
            )
            for variant_name, statistics
            in variants.items()
        ]

        ranked = [
            item
            for item in ranked
            if item[1] is not None
        ]

        ranked.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        best_variant = (
            ranked[0][0]
            if ranked
            else None
        )

        worst_variant = (
            ranked[-1][0]
            if ranked
            else None
        )

        return CrossExperimentSummary(
            experiment_count=len(
                experiment_ids
            ),
            run_count=total_runs,
            variant_count=len(variants),
            best_variant=best_variant,
            worst_variant=worst_variant,
            variant_statistics=variants,
        )

    def _load_runs(
        self,
        variant_name: str | None,
        experiment_id: str | None,
    ) -> List[RunRecord]:
        clauses: list[str] = []
        parameters: list[object] = []

        if variant_name is not None:
            clauses.append(
                "variant_name = ?"
            )
            parameters.append(variant_name)

        if experiment_id is not None:
            clauses.append(
                "experiment_id = ?"
            )
            parameters.append(experiment_id)

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
            ORDER BY created_at ASC
            """,
            tuple(parameters),
        )

        return [
            run_from_row(row)
            for row in rows
        ]

    def _build_variant_statistics(
        self,
        variant_name: str,
        runs: Iterable[RunRecord],
    ) -> VariantStatistics:
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

        experiment_ids = sorted({
            run.experiment_id
            for run in run_list
        })

        return VariantStatistics(
            variant_name=variant_name,
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
            negotiation_count=(
                negotiation_count
            ),
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
            experiment_count=len(
                experiment_ids
            ),
            experiment_ids=experiment_ids,
        )

    def _metric_value(
        self,
        statistics: VariantStatistics,
        metric_name: str,
    ) -> float | None:
        metric_map = {
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

        if metric_name not in metric_map:
            raise ValueError(
                "Unsupported metric: "
                f"{metric_name}"
            )

        return metric_map[metric_name]
