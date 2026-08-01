from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Dict, Iterable, List

from benchmarking.benchmark_result import (
    BenchmarkExperimentResult,
)
from statistics_engine.statistical_result import (
    DescriptiveStatistics,
    PairwiseStatisticalComparison,
    StatisticalEvaluationResult,
)
from statistics_engine.statistical_utils import (
    StatisticalUtils,
)


class StatisticalEvaluationEngine:
    """
    Produces descriptive and inferential
    statistics from benchmark results.
    """

    SUPPORTED_METRICS = (
        "reward",
        "risk",
        "confidence",
        "execution_time_seconds",
    )

    HIGHER_IS_BETTER = {
        "reward": True,
        "risk": False,
        "confidence": True,
        "execution_time_seconds": False,
    }

    def __init__(
        self,
        reference_strategy: str = "ACOS",
        confidence_level: float = 0.95,
        significance_level: float = 0.05,
    ) -> None:
        self.reference_strategy = (
            reference_strategy
        )

        self.confidence_level = (
            confidence_level
        )

        self.significance_level = (
            significance_level
        )

    def evaluate(
        self,
        benchmark_result: (
            BenchmarkExperimentResult
        ),
    ) -> StatisticalEvaluationResult:
        result = StatisticalEvaluationResult(
            experiment_id=str(
                benchmark_result.experiment_id
            ),
            experiment_name=str(
                benchmark_result.experiment_name
            ),
            reference_strategy=(
                self.reference_strategy
            ),
            total_scenarios=(
                benchmark_result.total_scenarios
            ),
        )

        try:
            metric_values = (
                self._extract_metric_values(
                    benchmark_result
                )
            )

            result.evaluated_scenarios = sum(
                1
                for scenario
                in benchmark_result.scenario_results
                if scenario.successful
            )

            self._calculate_descriptive_statistics(
                metric_values,
                result,
            )

            self._calculate_pairwise_comparisons(
                metric_values,
                result,
            )

            self._calculate_rankings(
                result
            )

        except Exception as error:
            result.successful = False
            result.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return result

    def evaluate_many(
        self,
        benchmark_results: Iterable[
            BenchmarkExperimentResult
        ],
    ) -> List[StatisticalEvaluationResult]:
        return [
            self.evaluate(benchmark_result)
            for benchmark_result
            in benchmark_results
        ]

    def _extract_metric_values(
        self,
        benchmark_result: (
            BenchmarkExperimentResult
        ),
    ) -> Dict[
        str,
        Dict[str, List[float]],
    ]:
        values: Dict[
            str,
            Dict[str, List[float]],
        ] = {
            metric: defaultdict(list)
            for metric in self.SUPPORTED_METRICS
        }

        for scenario_result in (
            benchmark_result.scenario_results
        ):
            if not scenario_result.successful:
                continue

            for strategy_name, decision in (
                scenario_result
                .strategy_decisions
                .items()
            ):
                if not decision.successful:
                    continue

                values["reward"][
                    strategy_name
                ].append(
                    float(decision.reward)
                )

                values["risk"][
                    strategy_name
                ].append(
                    float(decision.risk)
                )

                values["confidence"][
                    strategy_name
                ].append(
                    float(decision.confidence)
                )

                values[
                    "execution_time_seconds"
                ][strategy_name].append(
                    float(
                        decision
                        .execution_time_seconds
                    )
                )

        return values

    def _calculate_descriptive_statistics(
        self,
        metric_values: Dict[
            str,
            Dict[str, List[float]],
        ],
        result: StatisticalEvaluationResult,
    ) -> None:
        for metric_name, strategy_values in (
            metric_values.items()
        ):
            result.descriptive_statistics[
                metric_name
            ] = {}

            for strategy_name, values in (
                strategy_values.items()
            ):
                calculated = (
                    StatisticalUtils.descriptive(
                        values,
                        confidence_level=(
                            self.confidence_level
                        ),
                    )
                )

                statistics = (
                    DescriptiveStatistics(
                        strategy_name=(
                            strategy_name
                        ),
                        metric_name=metric_name,
                        confidence_level=(
                            self.confidence_level
                        ),
                        **calculated,
                    )
                )

                result.descriptive_statistics[
                    metric_name
                ][strategy_name] = statistics

    def _calculate_pairwise_comparisons(
        self,
        metric_values: Dict[
            str,
            Dict[str, List[float]],
        ],
        result: StatisticalEvaluationResult,
    ) -> None:
        for metric_name, strategy_values in (
            metric_values.items()
        ):
            result.pairwise_comparisons[
                metric_name
            ] = {}

            reference_values = (
                strategy_values.get(
                    self.reference_strategy,
                    [],
                )
            )

            for strategy_name, values in (
                strategy_values.items()
            ):
                if (
                    strategy_name
                    == self.reference_strategy
                ):
                    continue

                comparison = (
                    self._compare_pair(
                        reference_strategy=(
                            self.reference_strategy
                        ),
                        comparison_strategy=(
                            strategy_name
                        ),
                        metric_name=metric_name,
                        reference_values=(
                            reference_values
                        ),
                        comparison_values=values,
                    )
                )

                result.pairwise_comparisons[
                    metric_name
                ][strategy_name] = comparison

                if (
                    comparison
                    .statistically_significant
                ):
                    result.significant_comparisons.append(
                        (
                            f"{metric_name}: "
                            f"{self.reference_strategy} "
                            f"vs {strategy_name}"
                        )
                    )

    def _compare_pair(
        self,
        reference_strategy: str,
        comparison_strategy: str,
        metric_name: str,
        reference_values: List[float],
        comparison_values: List[float],
    ) -> PairwiseStatisticalComparison:
        sample_size = min(
            len(reference_values),
            len(comparison_values),
        )

        comparison = (
            PairwiseStatisticalComparison(
                reference_strategy=(
                    reference_strategy
                ),
                comparison_strategy=(
                    comparison_strategy
                ),
                metric_name=metric_name,
                sample_size=sample_size,
                significance_level=(
                    self.significance_level
                ),
            )
        )

        if sample_size == 0:
            comparison.successful = False
            comparison.error = (
                "No paired observations available."
            )
            return comparison

        reference = reference_values[
            :sample_size
        ]

        baseline = comparison_values[
            :sample_size
        ]

        comparison.reference_mean = round(
            mean(reference),
            6,
        )

        comparison.comparison_mean = round(
            mean(baseline),
            6,
        )

        comparison.mean_difference = round(
            comparison.reference_mean
            - comparison.comparison_mean,
            6,
        )

        higher_is_better = (
            self.HIGHER_IS_BETTER[
                metric_name
            ]
        )

        reference_wins = 0
        baseline_wins = 0
        ties = 0

        tolerance = 1e-12

        for reference_value, baseline_value in zip(
            reference,
            baseline,
        ):
            difference = (
                reference_value
                - baseline_value
            )

            if abs(difference) <= tolerance:
                ties += 1
                continue

            if higher_is_better:
                if reference_value > baseline_value:
                    reference_wins += 1
                else:
                    baseline_wins += 1
            else:
                if reference_value < baseline_value:
                    reference_wins += 1
                else:
                    baseline_wins += 1

        comparison.reference_win_count = (
            reference_wins
        )

        comparison.comparison_win_count = (
            baseline_wins
        )

        comparison.tie_count = ties

        comparison.reference_win_rate = round(
            reference_wins / sample_size,
            4,
        )

        comparison.comparison_win_rate = round(
            baseline_wins / sample_size,
            4,
        )

        comparison.tie_rate = round(
            ties / sample_size,
            4,
        )

        comparison.effect_size = (
            StatisticalUtils.paired_cohens_d(
                reference,
                baseline,
            )
        )

        comparison.effect_size_interpretation = (
            StatisticalUtils
            .interpret_effect_size(
                comparison.effect_size
            )
        )

        (
            comparison.t_statistic,
            comparison.p_value,
        ) = StatisticalUtils.paired_t_test(
            reference,
            baseline,
        )

        comparison.statistically_significant = (
            comparison.p_value
            < self.significance_level
        )

        comparison.better_strategy = (
            self._determine_better_strategy(
                reference_strategy=(
                    reference_strategy
                ),
                comparison_strategy=(
                    comparison_strategy
                ),
                reference_mean=(
                    comparison.reference_mean
                ),
                comparison_mean=(
                    comparison.comparison_mean
                ),
                higher_is_better=(
                    higher_is_better
                ),
            )
        )

        return comparison

    @staticmethod
    def _determine_better_strategy(
        reference_strategy: str,
        comparison_strategy: str,
        reference_mean: float,
        comparison_mean: float,
        higher_is_better: bool,
    ) -> str:
        if reference_mean == comparison_mean:
            return "TIE"

        if higher_is_better:
            if reference_mean > comparison_mean:
                return reference_strategy

            return comparison_strategy

        if reference_mean < comparison_mean:
            return reference_strategy

        return comparison_strategy

    def _calculate_rankings(
    self,
    result: StatisticalEvaluationResult,
) -> None:
     for metric_name, statistics_by_strategy in (
        result.descriptive_statistics.items()
     ):
        # Skip metrics with no strategy data.
        if not statistics_by_strategy:
            continue

        higher_is_better = (
            self.HIGHER_IS_BETTER[
                metric_name
            ]
        )

        ranked = sorted(
            statistics_by_strategy.keys(),
            key=lambda strategy_name: (
                statistics_by_strategy[
                    strategy_name
                ].mean
            ),
            reverse=higher_is_better,
        )

        result.strategy_rankings[
            metric_name
        ] = ranked