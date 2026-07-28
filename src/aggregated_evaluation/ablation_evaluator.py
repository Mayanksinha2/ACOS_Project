from __future__ import annotations

from typing import Dict, List, Tuple

from .ablation_config import AblationConfig
from .ablation_result import (
    AblationComparison,
    AblationEvaluationResult,
)
from .aggregated_result import (
    AggregatedEvaluationResult,
    GroupEvaluationResult,
)


class AblationEvaluator:
    def __init__(
        self,
        config: AblationConfig | None = None,
    ) -> None:
        self.config = config or AblationConfig()

    def evaluate(
        self,
        aggregated_result: AggregatedEvaluationResult,
    ) -> AblationEvaluationResult:
        output = AblationEvaluationResult(
            baseline_group=self.config.baseline_group,
            primary_metric=self.config.primary_metric,
            best_group=None,
            worst_group=None,
        )

        groups = aggregated_result.groups

        baseline = groups.get(
            self.config.baseline_group
        )

        if baseline is None:
            output.errors.append(
                f"Baseline group "
                f"'{self.config.baseline_group}' was not found."
            )
            return output

        if (
            baseline.experiment_count
            < self.config.minimum_group_size
        ):
            output.errors.append(
                "Baseline group does not meet the minimum "
                "group size."
            )
            return output

        for group_name, group in groups.items():
            if group_name == self.config.baseline_group:
                continue

            if (
                group.experiment_count
                < self.config.minimum_group_size
            ):
                output.warnings.append(
                    f"Variant group '{group_name}' was skipped "
                    "because it does not meet the minimum "
                    "group size."
                )
                continue

            for metric_name in self.config.comparison_metrics:
                comparison = self._compare_metric(
                    baseline=baseline,
                    variant=group,
                    metric_name=metric_name,
                )

                if comparison is not None:
                    output.comparisons.append(
                        comparison
                    )

        ranking_pairs = self._build_ranking(
            groups
        )

        output.ranking = [
            group_name
            for group_name, _ in ranking_pairs
        ]

        if output.ranking:
            output.best_group = output.ranking[0]
            output.worst_group = output.ranking[-1]
        else:
            output.warnings.append(
                "No groups could be ranked for the "
                "primary metric."
            )

        return output

    def _compare_metric(
        self,
        baseline: GroupEvaluationResult,
        variant: GroupEvaluationResult,
        metric_name: str,
    ) -> AblationComparison | None:
        baseline_metric = baseline.metrics.get(
            metric_name
        )
        variant_metric = variant.metrics.get(
            metric_name
        )

        if (
            baseline_metric is None
            or variant_metric is None
            or baseline_metric.mean is None
            or variant_metric.mean is None
        ):
            return None

        absolute_change = (
            variant_metric.mean
            - baseline_metric.mean
        )

        if baseline_metric.mean == 0:
            percentage_change = None
        else:
            percentage_change = (
                absolute_change
                / abs(baseline_metric.mean)
                * 100.0
            )

        performance_delta = (
            absolute_change
            if self.config.higher_is_better
            else -absolute_change
        )

        if performance_delta > 0:
            interpretation = "variant_improved"
        elif performance_delta < 0:
            interpretation = "variant_degraded"
        else:
            interpretation = "no_change"

        return AblationComparison(
            baseline_group=baseline.group_name,
            variant_group=variant.group_name,
            metric_name=metric_name,
            baseline_mean=baseline_metric.mean,
            variant_mean=variant_metric.mean,
            absolute_change=absolute_change,
            percentage_change=percentage_change,
            performance_delta=performance_delta,
            baseline_count=baseline_metric.count,
            variant_count=variant_metric.count,
            interpretation=interpretation,
        )

    def _build_ranking(
        self,
        groups: Dict[str, GroupEvaluationResult],
    ) -> List[Tuple[str, float]]:
        ranking: List[Tuple[str, float]] = []

        for group_name, group in groups.items():
            metric = group.metrics.get(
                self.config.primary_metric
            )

            if metric is None or metric.mean is None:
                continue

            ranking.append(
                (
                    group_name,
                    metric.mean,
                )
            )

        ranking.sort(
            key=lambda item: item[1],
            reverse=self.config.higher_is_better,
        )

        return ranking
