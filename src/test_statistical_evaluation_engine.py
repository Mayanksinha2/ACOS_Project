from benchmarking.benchmark_engine import (
    BenchmarkEngine,
)
from experiments.experiment_runner import (
    ExperimentRunner,
)
from simulator.scenario_generator import (
    ScenarioGenerator,
)
from statistics_engine.statistical_evaluation_engine import (
    StatisticalEvaluationEngine,
)


def print_statistical_result(
    result,
) -> None:
    print(
        "\nACOS STATISTICAL EVALUATION"
    )
    print("=" * 90)

    for key, value in (
        result.summary().items()
    ):
        print(f"{key:<32}: {value}")

    print(
        "\nDESCRIPTIVE STATISTICS"
    )
    print("-" * 90)

    for metric_name, strategy_results in (
        result.descriptive_statistics.items()
    ):
        print(f"\nMetric: {metric_name}")

        for strategy_name, statistics in (
            strategy_results.items()
        ):
            print(
                f"{strategy_name:<20} "
                f"n={statistics.sample_size:<4} "
                f"mean={statistics.mean:<10} "
                f"median={statistics.median:<10} "
                f"std={statistics.standard_deviation:<10} "
                f"CI95=["
                f"{statistics.confidence_interval_lower}, "
                f"{statistics.confidence_interval_upper}]"
            )

    print(
        "\nPAIRWISE COMPARISONS WITH ACOS"
    )
    print("-" * 90)

    for metric_name, comparisons in (
        result.pairwise_comparisons.items()
    ):
        print(f"\nMetric: {metric_name}")

        for strategy_name, comparison in (
            comparisons.items()
        ):
            print(
                f"ACOS vs {strategy_name:<20} "
                f"diff={comparison.mean_difference:<10} "
                f"d={comparison.effect_size:<10} "
                f"effect="
                f"{comparison.effect_size_interpretation:<10} "
                f"t={comparison.t_statistic:<10} "
                f"p={comparison.p_value:<10} "
                f"significant="
                f"{comparison.statistically_significant} "
                f"better="
                f"{comparison.better_strategy}"
            )


def build_benchmark(
    scenario_count: int = 50,
):
    generator = ScenarioGenerator(
        random_seed=2026
    )

    runner = ExperimentRunner(
        scenario_generator=generator
    )

    experiment = (
        runner.run_random_experiment(
            scenario_count=scenario_count,
            customer_count=100,
            experiment_name=(
                "ACOS Statistical Benchmark"
            ),
        )
    )

    return BenchmarkEngine(
        random_seed=2026
    ).benchmark_experiment(
        experiment
    )


def test_statistical_evaluation() -> None:
    benchmark = build_benchmark(
        scenario_count=50
    )

    result = (
        StatisticalEvaluationEngine()
        .evaluate(
            benchmark
        )
    )

    print_statistical_result(
        result
    )

    assert result.successful

    assert result.total_scenarios == 50

    assert result.evaluated_scenarios == 50

    expected_metrics = {
        "reward",
        "risk",
        "confidence",
        "execution_time_seconds",
    }

    assert set(
        result
        .descriptive_statistics
        .keys()
    ) == expected_metrics

    assert set(
        result
        .pairwise_comparisons
        .keys()
    ) == expected_metrics

    expected_strategies = {
        "ACOS",
        "HighestConfidence",
        "RandomSelection",
        "RuleBased",
    }

    for metric_name in expected_metrics:
        assert set(
            result
            .descriptive_statistics[
                metric_name
            ]
            .keys()
        ) == expected_strategies

        assert (
            len(
                result.strategy_rankings[
                    metric_name
                ]
            )
            == 4
        )

    reward_comparisons = (
        result.pairwise_comparisons[
            "reward"
        ]
    )

    assert set(
        reward_comparisons.keys()
    ) == {
        "HighestConfidence",
        "RandomSelection",
        "RuleBased",
    }

    for comparison in (
        reward_comparisons.values()
    ):
        assert comparison.sample_size == 50

        assert (
            comparison.reference_win_count
            + comparison.comparison_win_count
            + comparison.tie_count
            == 50
        )

        assert (
            0.0
            <= comparison.p_value
            <= 1.0
        )


def test_empty_statistical_evaluation() -> None:
    generator = ScenarioGenerator(
        random_seed=1
    )

    empty_experiment = (
        ExperimentRunner(
            scenario_generator=generator
        ).run_scenarios(
            [],
            experiment_name=(
                "Empty Statistical Experiment"
            ),
        )
    )

    benchmark = (
        BenchmarkEngine()
        .benchmark_experiment(
            empty_experiment
        )
    )

    result = (
        StatisticalEvaluationEngine()
        .evaluate(
            benchmark
        )
    )

    assert result.successful
    assert result.total_scenarios == 0
    assert result.evaluated_scenarios == 0

    assert result.strategy_rankings == {}

    for metric_results in (
        result.pairwise_comparisons.values()
    ):
        assert metric_results == {}


def test_statistical_utilities() -> None:
    from statistics_engine.statistical_utils import (
        StatisticalUtils,
    )

    values = [
        0.60,
        0.70,
        0.80,
        0.90,
        1.00,
    ]

    result = StatisticalUtils.descriptive(
        values
    )

    assert result["sample_size"] == 5
    assert result["mean"] == 0.8
    assert result["median"] == 0.8
    assert result["minimum"] == 0.6
    assert result["maximum"] == 1.0

    effect_size = (
        StatisticalUtils.paired_cohens_d(
            [0.8, 0.9, 0.85, 0.95],
            [0.6, 0.7, 0.65, 0.75],
        )
    )

    assert effect_size >= 0.0

    t_statistic, p_value = (
        StatisticalUtils.paired_t_test(
            [0.8, 0.9, 0.85, 0.95],
            [0.6, 0.7, 0.65, 0.75],
        )
    )

    assert t_statistic >= 0.0
    assert 0.0 <= p_value <= 1.0


def run_tests() -> None:
    test_statistical_utilities()
    test_statistical_evaluation()
    test_empty_statistical_evaluation()

    print(
        "\nStatistical Evaluation "
        "Framework tests passed."
    )


if __name__ == "__main__":
    run_tests()