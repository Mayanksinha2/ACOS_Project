from pathlib import Path
from tempfile import TemporaryDirectory

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
from visualization_engine.visualization_engine import (
    VisualizationEngine,
)


def build_results(
    scenario_count: int = 50,
):
    generator = ScenarioGenerator(
        random_seed=2026
    )

    experiment_runner = ExperimentRunner(
        scenario_generator=generator
    )

    experiment = (
        experiment_runner.run_random_experiment(
            scenario_count=scenario_count,
            customer_count=100,
            experiment_name=(
                "ACOS Visualization Benchmark"
            ),
        )
    )

    benchmark_result = (
        BenchmarkEngine(
            random_seed=2026
        ).benchmark_experiment(
            experiment
        )
    )

    statistical_result = (
        StatisticalEvaluationEngine()
        .evaluate(
            benchmark_result
        )
    )

    return (
        benchmark_result,
        statistical_result,
    )


def print_visualization_result(
    result,
) -> None:
    print(
        "\nACOS VISUALIZATION RESULTS"
    )

    print("=" * 90)

    for key, value in (
        result.summary().items()
    ):
        print(f"{key:<32}: {value}")

    print(
        "\nGENERATED CHARTS"
    )

    print("-" * 90)

    for chart in result.charts:
        status = (
            "SUCCESS"
            if chart.successful
            else "FAILED"
        )

        print(
            f"{chart.chart_name:<35} "
            f"{status:<10} "
            f"{chart.file_path}"
        )

        if chart.error:
            print(
                f"{'':<35} "
                f"Error: {chart.error}"
            )


def test_visualization_generation() -> None:
    (
        benchmark_result,
        statistical_result,
    ) = build_results(
        scenario_count=50
    )

    with TemporaryDirectory() as directory:
        engine = VisualizationEngine(
            output_root=directory,
            dpi=150,
        )

        result = engine.generate_all(
            benchmark_result=benchmark_result,
            statistical_result=(
                statistical_result
            ),
        )

        print_visualization_result(
            result
        )

        assert result.successful

        assert (
            result.generated_chart_count
            == 8
        )

        assert (
            result.failed_chart_count
            == 0
        )

        assert len(result.charts) == 8

        expected_chart_names = {
            "reward_strategy_comparison",
            "risk_strategy_comparison",
            "confidence_strategy_comparison",
            (
                "execution_time_seconds_"
                "strategy_comparison"
            ),
            "reward_confidence_intervals",
            "reward_win_frequency",
            "risk_win_frequency",
            "reward_effect_sizes",
        }

        actual_chart_names = {
            chart.chart_name
            for chart in result.charts
        }

        assert (
            actual_chart_names
            == expected_chart_names
        )

        for chart in result.charts:
            assert chart.successful
            assert chart.exists()

            file_path = Path(
                chart.file_path
            )

            assert (
                file_path.suffix.lower()
                == ".png"
            )

            assert (
                file_path.stat().st_size
                > 0
            )


def test_persistent_visualization_output() -> None:
    (
        benchmark_result,
        statistical_result,
    ) = build_results(
        scenario_count=20
    )

    output_root = (
        "outputs/test_visualizations"
    )

    engine = VisualizationEngine(
        output_root=output_root,
        dpi=300,
    )

    result = engine.generate_all(
        benchmark_result=benchmark_result,
        statistical_result=statistical_result,
    )

    assert result.successful

    output_directory = Path(
        result.output_directory
    )

    assert output_directory.exists()

    for chart in result.charts:
        assert chart.exists()


def test_empty_visualization() -> None:
    generator = ScenarioGenerator(
        random_seed=1
    )

    empty_experiment = (
        ExperimentRunner(
            scenario_generator=generator
        ).run_scenarios(
            [],
            experiment_name=(
                "Empty Visualization Experiment"
            ),
        )
    )

    benchmark_result = (
        BenchmarkEngine()
        .benchmark_experiment(
            empty_experiment
        )
    )

    statistical_result = (
        StatisticalEvaluationEngine()
        .evaluate(
            benchmark_result
        )
    )

    with TemporaryDirectory() as directory:
        result = (
            VisualizationEngine(
                output_root=directory
            ).generate_all(
                benchmark_result=(
                    benchmark_result
                ),
                statistical_result=(
                    statistical_result
                ),
            )
        )

        assert not result.successful

        assert (
            result.generated_chart_count
            == 0
        )

        assert (
            result.failed_chart_count
            == 8
        )

        assert len(result.errors) == 8


def run_tests() -> None:
    test_visualization_generation()
    test_persistent_visualization_output()
    test_empty_visualization()

    print(
        "\nVisualization Framework "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()