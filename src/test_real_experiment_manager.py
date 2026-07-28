from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_manager import (
    ExperimentConfig,
    ExperimentExporter,
    ExperimentManager,
    ExperimentRunner,
    ExperimentStatus,
    execute_acos_experiment,
)


def print_mapping(
    title: str,
    values: dict,
) -> None:
    print()
    print(title)
    print("-" * 90)

    for key, value in values.items():
        print(f"{key:<32}: {value}")


def test_real_acos_execution() -> None:
    """
    Execute one complete real ACOS research run.
    """

    runner = ExperimentRunner(
        execute=execute_acos_experiment
    )

    manager = ExperimentManager(
        runner=runner
    )

    with TemporaryDirectory() as temporary:
        output_directory = (
            Path(temporary)
            / "real_acos_experiments"
        )

        config = ExperimentConfig(
            experiment_name=(
                "Real ACOS End-to-End Experiment"
            ),
            repetitions=1,
            random_seed=42,
            save_bundle=True,
            save_report=True,
            save_publication=True,
            stop_on_error=True,
            tags=[
                "real-pipeline",
                "end-to-end",
                "research",
            ],
        )

        experiment_id = manager.submit(
            config=config,
            payload={
                "scenario_name": (
                    "Default Research Scenario"
                ),
                "description": (
                    "Real ACOS integration test."
                ),
            },
            output_directory=output_directory,
            metadata={
                "framework": "ACOS",
                "test_type": "real_integration",
            },
        )

        results = manager.run(
            experiment_id
        )

        assert len(results) == 1

        result = results[0]

        print_mapping(
            "REAL ACOS EXPERIMENT RESULT",
            result.to_dict(),
        )

        assert result.status == (
            ExperimentStatus.SUCCESS
        )

        assert result.successful
        assert result.experiment_id
        assert result.experiment_name
        assert result.output_directory
        assert result.bundle_path
        assert result.report_path
        assert result.publication_path
        assert not result.errors

        run_directory = Path(
            result.output_directory
        )

        bundle_directory = Path(
            result.bundle_path
        )

        report_path = Path(
            result.report_path
        )

        publication_path = Path(
            result.publication_path
        )

        assert run_directory.exists()
        assert bundle_directory.exists()
        assert report_path.exists()
        assert publication_path.exists()

        summary = manager.summary()

        print_mapping(
            "REAL ACOS EXPERIMENT SUMMARY",
            summary.to_dict(),
        )

        assert summary.total_experiments == 1
        assert summary.successful == 1
        assert summary.failed == 0
        assert summary.cancelled == 0
        assert summary.success_rate == 100.0

        exporter = ExperimentExporter()

        manager_export_directory = (
            output_directory
            / "manager_exports"
        )

        export_result = exporter.export(
            results=manager.history(),
            summary=summary,
            output_directory=(
                manager_export_directory
            ),
        )

        print_mapping(
            "REAL EXPERIMENT MANAGER EXPORT",
            export_result.to_dict(),
        )

        assert export_result.successful
        assert Path(
            export_result.history_path
        ).exists()
        assert Path(
            export_result.summary_path
        ).exists()
        assert not export_result.errors


def test_real_acos_repeated_execution() -> None:
    """
    Verify that repeated real runs use separate folders
    and deterministic seed values.
    """

    runner = ExperimentRunner(
        execute=execute_acos_experiment
    )

    manager = ExperimentManager(
        runner=runner
    )

    with TemporaryDirectory() as temporary:
        output_directory = (
            Path(temporary)
            / "repeated_real_runs"
        )

        experiment_id = manager.submit(
            config=ExperimentConfig(
                experiment_name=(
                    "Repeated Real ACOS Experiment"
                ),
                repetitions=2,
                random_seed=100,
                save_bundle=True,
                save_report=True,
                save_publication=False,
                stop_on_error=True,
            ),
            output_directory=output_directory,
        )

        results = manager.run(
            experiment_id
        )

        assert len(results) == 2

        first_result = results[0]
        second_result = results[1]

        assert first_result.successful
        assert second_result.successful

        assert first_result.random_seed == 100
        assert second_result.random_seed == 101

        assert (
            first_result.output_directory
            != second_result.output_directory
        )

        assert "run_001" in (
            first_result.output_directory
        )

        assert "run_002" in (
            second_result.output_directory
        )

        assert Path(
            first_result.bundle_path
        ).exists()

        assert Path(
            second_result.bundle_path
        ).exists()

        assert Path(
            first_result.report_path
        ).exists()

        assert Path(
            second_result.report_path
        ).exists()

        summary = manager.summary()

        assert summary.total_experiments == 2
        assert summary.successful == 2
        assert summary.failed == 0


def run_tests() -> None:
    test_real_acos_execution()
    test_real_acos_repeated_execution()

    print()
    print(
        "Real ACOS Experiment Manager "
        "integration tests passed."
    )


if __name__ == "__main__":
    run_tests()