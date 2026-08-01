from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    ExperimentDatabase,
    ExperimentRecord,
    RepositoryManager,
    RunRecord,
    StatisticsService,
)


def build_environment(
    directory: str,
) -> tuple[
    RepositoryManager,
    StatisticsService,
]:
    database = ExperimentDatabase(
        Path(directory) / "acos_research.db"
    )

    repositories = RepositoryManager.create(
        database
    )

    statistics_service = StatisticsService(
        database
    )

    return repositories, statistics_service


def seed_data(
    repositories: RepositoryManager,
) -> None:
    repositories.experiments.create(
        ExperimentRecord(
            experiment_id="EXP-001",
            name="Statistics Test",
            status="completed",
        )
    )

    runs = [
        RunRecord(
            run_id="RUN-001",
            experiment_id="EXP-001",
            variant_name="baseline",
            repetition_index=1,
            random_seed=100,
            status="success",
            successful=True,
            reward=0.80,
            duration_seconds=1.0,
            conflict_detected=True,
            negotiation_required=True,
            warnings=["warning-a"],
        ),
        RunRecord(
            run_id="RUN-002",
            experiment_id="EXP-001",
            variant_name="baseline",
            repetition_index=2,
            random_seed=101,
            status="success",
            successful=True,
            reward=0.90,
            duration_seconds=2.0,
            conflict_detected=False,
            negotiation_required=False,
        ),
        RunRecord(
            run_id="RUN-003",
            experiment_id="EXP-001",
            variant_name="without_mocra",
            repetition_index=3,
            random_seed=102,
            status="failed",
            successful=False,
            reward=0.40,
            duration_seconds=3.0,
            conflict_detected=True,
            negotiation_required=False,
            errors=["error-a", "error-b"],
        ),
        RunRecord(
            run_id="RUN-004",
            experiment_id="EXP-001",
            variant_name="without_negotiation",
            repetition_index=4,
            random_seed=103,
            status="success",
            successful=True,
            reward=None,
            duration_seconds=None,
            conflict_detected=False,
            negotiation_required=False,
        ),
    ]

    for run in runs:
        repositories.runs.create(run)


def test_experiment_statistics() -> None:
    with TemporaryDirectory() as temporary:
        repositories, service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        result = (
            service.get_experiment_statistics(
                "EXP-001"
            )
        )

        assert result.total_runs == 4
        assert result.successful_runs == 3
        assert result.failed_runs == 1
        assert result.success_rate == 75.0
        assert result.failure_rate == 25.0
        assert result.conflict_count == 2
        assert result.conflict_rate == 50.0
        assert result.negotiation_count == 1
        assert result.negotiation_rate == 25.0

        reward = result.reward_statistics

        assert reward.count == 3
        assert round(reward.mean, 6) == 0.7
        assert round(reward.median, 6) == 0.8
        assert round(reward.minimum, 6) == 0.4
        assert round(reward.maximum, 6) == 0.9
        assert round(reward.variance, 6) == (
            round(
                (
                    (0.8 - 0.7) ** 2
                    + (0.9 - 0.7) ** 2
                    + (0.4 - 0.7) ** 2
                ) / 3,
                6,
            )
        )

        assert result.variant_counts == {
            "baseline": 2,
            "without_mocra": 1,
            "without_negotiation": 1,
        }

        assert result.statuses == {
            "success": 3,
            "failed": 1,
        }

        assert result.warnings_count == 1
        assert result.errors_count == 2


def test_empty_experiment_statistics() -> None:
    with TemporaryDirectory() as temporary:
        repositories, service = (
            build_environment(temporary)
        )

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-EMPTY",
                name="Empty Experiment",
                status="created",
            )
        )

        result = (
            service.get_experiment_statistics(
                "EXP-EMPTY"
            )
        )

        assert result.total_runs == 0
        assert result.success_rate == 0.0
        assert (
            result.reward_statistics.mean
            is None
        )
        assert (
            result.duration_statistics.count
            == 0
        )


def test_database_statistics() -> None:
    with TemporaryDirectory() as temporary:
        repositories, service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-002",
                name="Second Experiment",
                status="completed",
            )
        )

        repositories.runs.create(
            RunRecord(
                run_id="RUN-005",
                experiment_id="EXP-002",
                variant_name="baseline",
                repetition_index=1,
                random_seed=200,
                status="success",
                successful=True,
                reward=1.0,
                duration_seconds=4.0,
                conflict_detected=False,
                negotiation_required=True,
            )
        )

        result = (
            service.get_database_statistics()
        )

        assert result.total_experiments == 2
        assert result.total_runs == 5
        assert result.successful_runs == 4
        assert result.failed_runs == 1
        assert result.success_rate == 80.0
        assert result.conflict_rate == 40.0
        assert result.negotiation_rate == 40.0
        assert result.reward_statistics.count == 4
        assert round(
            result.reward_statistics.mean,
            6,
        ) == 0.775


def print_statistics_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        result = (
            service.get_experiment_statistics(
                "EXP-001"
            )
        )

        print()
        print("STATISTICS SERVICE RESULT")
        print("-" * 90)
        print(
            f"total_runs              : "
            f"{result.total_runs}"
        )
        print(
            f"success_rate            : "
            f"{result.success_rate:.2f}%"
        )
        print(
            f"failure_rate            : "
            f"{result.failure_rate:.2f}%"
        )
        print(
            f"conflict_rate           : "
            f"{result.conflict_rate:.2f}%"
        )
        print(
            f"negotiation_rate        : "
            f"{result.negotiation_rate:.2f}%"
        )
        print(
            f"mean_reward             : "
            f"{result.reward_statistics.mean:.4f}"
        )
        print(
            f"median_reward           : "
            f"{result.reward_statistics.median:.4f}"
        )
        print(
            f"reward_std_dev          : "
            f"{result.reward_statistics.standard_deviation:.4f}"
        )


def run_tests() -> None:
    test_experiment_statistics()
    test_empty_experiment_statistics()
    test_database_statistics()
    print_statistics_summary()

    print()
    print(
        "Experiment Database Statistics Service "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
