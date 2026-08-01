from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from experiment_manager import (
    ExperimentConfig,
    ExperimentExporter,
    ExperimentManager,
    ExperimentRunner,
    ExperimentStatus,
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


def mock_acos_execution(
    request,
    run_index: int,
    random_seed: int | None,
):
    reward = round(
        0.70 + (run_index * 0.05),
        4,
    )

    return SimpleNamespace(
        successful=True,
        reward=reward,
        final_decision={
            "action": "MAINTAIN",
            "price": 799,
        },
        conflict_detected=(
            run_index % 2 == 0
        ),
        negotiation_required=(
            run_index % 2 == 0
        ),
        warnings=[],
        errors=[],
        output_directory=(
            request.output_directory or ""
        ),
    )


def build_manager() -> ExperimentManager:
    runner = ExperimentRunner(
        execute=mock_acos_execution
    )

    return ExperimentManager(
        runner=runner
    )


def test_submit_and_run() -> None:
    manager = build_manager()

    config = ExperimentConfig(
        experiment_name="Single ACOS Run",
        repetitions=2,
        random_seed=42,
    )

    experiment_id = manager.submit(
        config=config,
        payload={
            "scenario": "festival_market"
        },
    )

    results = manager.run(experiment_id)

    assert len(results) == 2
    assert all(
        result.successful
        for result in results
    )
    assert all(
        result.status
        == ExperimentStatus.SUCCESS
        for result in results
    )
    assert results[0].random_seed == 42
    assert results[1].random_seed == 43


def test_run_all_and_summary() -> None:
    manager = build_manager()

    manager.submit(
        ExperimentConfig(
            experiment_name="Pricing Sweep",
            repetitions=2,
            random_seed=10,
        )
    )

    manager.submit(
        ExperimentConfig(
            experiment_name="Inventory Sweep",
            repetitions=2,
            random_seed=20,
        )
    )

    results = manager.run_all()

    summary = manager.summary()

    print_mapping(
        "EXPERIMENT SUMMARY",
        summary.to_dict(),
    )

    assert len(results) == 4
    assert summary.total_experiments == 4
    assert summary.successful == 4
    assert summary.failed == 0
    assert summary.average_reward is not None
    assert summary.best_reward is not None
    assert summary.worst_reward is not None
    assert summary.success_rate == 100.0
    assert summary.negotiation_count == 2
    assert summary.conflict_count == 2


def test_cancel() -> None:
    manager = build_manager()

    experiment_id = manager.submit(
        ExperimentConfig(
            experiment_name=(
                "Cancelled Experiment"
            )
        )
    )

    assert manager.cancel(experiment_id)
    assert manager.request(
        experiment_id
    ).status == ExperimentStatus.CANCELLED


def test_export() -> None:
    manager = build_manager()

    manager.submit(
        ExperimentConfig(
            experiment_name="Export Test",
            repetitions=3,
        )
    )

    manager.run_all()

    with TemporaryDirectory() as temporary:
        output_directory = (
            Path(temporary)
            / "experiment_exports"
        )

        exporter = ExperimentExporter()

        export_result = exporter.export(
            results=manager.history(),
            summary=manager.summary(),
            output_directory=output_directory,
        )

        print_mapping(
            "EXPERIMENT EXPORT RESULT",
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


def test_failed_execution() -> None:
    def failing_execution(
        request,
        run_index,
        random_seed,
    ):
        raise RuntimeError(
            "Simulated pipeline failure."
        )

    manager = ExperimentManager(
        runner=ExperimentRunner(
            execute=failing_execution
        )
    )

    experiment_id = manager.submit(
        ExperimentConfig(
            experiment_name="Failure Test"
        )
    )

    results = manager.run(experiment_id)

    assert len(results) == 1
    assert not results[0].successful
    assert results[0].errors
    assert (
        results[0].status
        == ExperimentStatus.FAILED
    )


def run_tests() -> None:
    test_submit_and_run()
    test_run_all_and_summary()
    test_cancel()
    test_export()
    test_failed_execution()

    print()
    print(
        "Experiment Manager Framework "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
