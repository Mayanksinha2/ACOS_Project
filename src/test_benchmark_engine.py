from benchmarking.benchmark_engine import (
    BenchmarkEngine,
)
from experiments.experiment_runner import (
    ExperimentRunner,
)
from simulator.scenario_generator import (
    ScenarioGenerator,
)


def print_benchmark(result) -> None:
    print("\nACOS BENCHMARK RESULTS")
    print("=" * 80)

    for key, value in (
        result.summary().items()
    ):
        print(f"{key:<32}: {value}")

    print("\nSCENARIO COMPARISONS")
    print("-" * 80)

    for scenario in (
        result.scenario_results[:5]
    ):
        print(
            f"\n{scenario.scenario_name}"
        )

        for strategy_name, decision in (
            scenario.strategy_decisions.items()
        ):
            print(
                f"{strategy_name:<20} "
                f"agent={decision.selected_agent}, "
                f"operation="
                f"{decision.selected_operation}, "
                f"reward={decision.reward}, "
                f"risk={decision.risk}, "
                f"confidence="
                f"{decision.confidence}"
            )

        print(
            "Best reward:",
            scenario.best_reward_strategy,
        )


def test_benchmark_experiment() -> None:
    generator = ScenarioGenerator(
        random_seed=2026
    )

    runner = ExperimentRunner(
        scenario_generator=generator
    )

    experiment = (
        runner.run_random_experiment(
            scenario_count=20,
            customer_count=50,
            experiment_name=(
                "ACOS Baseline Benchmark"
            ),
        )
    )

    benchmark = (
        BenchmarkEngine(
            random_seed=2026
        ).benchmark_experiment(
            experiment
        )
    )

    print_benchmark(
        benchmark
    )

    assert benchmark.successful

    assert benchmark.total_scenarios == 20

    assert (
        benchmark.successful_scenarios
        == 20
    )

    assert benchmark.failed_scenarios == 0

    assert len(
        benchmark.scenario_results
    ) == 20

    expected_strategies = {
        "ACOS",
        "HighestConfidence",
        "RandomSelection",
        "RuleBased",
    }

    assert set(
        benchmark.average_reward.keys()
    ) == expected_strategies

    assert set(
        benchmark.average_risk.keys()
    ) == expected_strategies

    assert set(
        benchmark.average_confidence.keys()
    ) == expected_strategies

    assert set(
        benchmark
        .average_execution_time
        .keys()
    ) == expected_strategies

    assert sum(
        benchmark
        .reward_win_frequency
        .values()
    ) == 20


def test_single_scenario_benchmark() -> None:
    generator = ScenarioGenerator(
        random_seed=99
    )

    scenario = (
        generator.create_manual_scenario(
            scenario_name=(
                "Critical Stock Benchmark"
            ),
            product_id="BENCH-001",
            product_name="Festival Dress",
            category="ETHNIC",
            cost_price=400,
            selling_price=799,
            inventory=10,
            demand_level="HIGH",
            season="FESTIVAL",
            demand_multiplier=1.25,
            competitor_price_factor=1.0,
            advertising_cost=1000,
            customer_count=100,
        )
    )

    experiment = ExperimentRunner(
        scenario_generator=generator
    ).run_scenarios(
        [scenario],
        experiment_name=(
            "Single Scenario Benchmark"
        ),
    )

    scenario_result = (
        experiment.scenario_results[0]
    )

    benchmark = (
        BenchmarkEngine(
            random_seed=99
        ).benchmark_scenario(
            scenario_result
        )
    )

    assert benchmark.successful

    assert benchmark.strategy_count == 4

    assert "ACOS" in (
        benchmark.strategy_decisions
    )

    assert "HighestConfidence" in (
        benchmark.strategy_decisions
    )

    assert "RandomSelection" in (
        benchmark.strategy_decisions
    )

    assert "RuleBased" in (
        benchmark.strategy_decisions
    )

    assert (
        benchmark.best_reward_strategy
        is not None
    )

    assert (
        benchmark.lowest_risk_strategy
        is not None
    )

    assert (
        benchmark
        .highest_confidence_strategy
        is not None
    )

    assert benchmark.fastest_strategy


def test_empty_benchmark() -> None:
    experiment = (
        ExperimentRunner().run_scenarios(
            [],
            experiment_name=(
                "Empty Benchmark"
            ),
        )
    )

    benchmark = (
        BenchmarkEngine()
        .benchmark_experiment(
            experiment
        )
    )

    assert benchmark.total_scenarios == 0
    assert benchmark.successful_scenarios == 0
    assert benchmark.failed_scenarios == 0
    assert benchmark.average_reward == {}
    assert benchmark.average_risk == {}
    assert (
        benchmark.reward_win_frequency
        == {}
    )


def run_tests() -> None:
    test_benchmark_experiment()
    test_single_scenario_benchmark()
    test_empty_benchmark()

    print(
        "\nBenchmark Framework tests passed."
    )


if __name__ == "__main__":
    run_tests()