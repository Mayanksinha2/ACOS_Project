from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    ExperimentDatabase,
    ExperimentRecord,
    ExperimentSearchCriteria,
    QueryService,
    RepositoryManager,
    RunRecord,
    RunSearchCriteria,
)


def build_environment(
    directory: str,
) -> tuple[
    RepositoryManager,
    QueryService,
]:
    database = ExperimentDatabase(
        Path(directory) / "acos_research.db"
    )

    repositories = RepositoryManager.create(
        database
    )

    query_service = QueryService(
        database
    )

    return repositories, query_service


def seed_data(
    repositories: RepositoryManager,
) -> None:
    experiments = [
        ExperimentRecord(
            experiment_id="EXP-001",
            name="Baseline Commerce Test",
            status="completed",
            metadata={
                "domain": "pricing",
                "dataset": "synthetic",
            },
            created_at="2026-07-28T10:00:00+00:00",
            updated_at="2026-07-28T10:00:00+00:00",
        ),
        ExperimentRecord(
            experiment_id="EXP-002",
            name="Negotiation Ablation Study",
            status="completed",
            metadata={
                "domain": "pricing",
                "dataset": "realistic",
            },
            created_at="2026-07-29T10:00:00+00:00",
            updated_at="2026-07-29T10:00:00+00:00",
        ),
        ExperimentRecord(
            experiment_id="EXP-003",
            name="Inventory Stress Test",
            status="running",
            metadata={
                "domain": "inventory",
                "dataset": "synthetic",
            },
            created_at="2026-07-30T10:00:00+00:00",
            updated_at="2026-07-30T10:00:00+00:00",
        ),
    ]

    for experiment in experiments:
        repositories.experiments.create(
            experiment
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
            reward=0.88,
            duration_seconds=0.11,
            conflict_detected=True,
            negotiation_required=True,
            metadata={
                "ablation_variant": "baseline",
            },
            created_at="2026-07-28T10:01:00+00:00",
        ),
        RunRecord(
            run_id="RUN-002",
            experiment_id="EXP-002",
            variant_name="without_negotiation",
            repetition_index=1,
            random_seed=100,
            status="success",
            successful=True,
            reward=0.71,
            duration_seconds=0.09,
            conflict_detected=True,
            negotiation_required=False,
            metadata={
                "ablation_variant": (
                    "without_negotiation"
                ),
            },
            created_at="2026-07-29T10:01:00+00:00",
        ),
        RunRecord(
            run_id="RUN-003",
            experiment_id="EXP-002",
            variant_name="baseline",
            repetition_index=2,
            random_seed=101,
            status="failed",
            successful=False,
            reward=0.30,
            duration_seconds=0.20,
            conflict_detected=False,
            negotiation_required=False,
            metadata={
                "ablation_variant": "baseline",
            },
            errors=["Synthetic failure"],
            created_at="2026-07-29T10:02:00+00:00",
        ),
        RunRecord(
            run_id="RUN-004",
            experiment_id="EXP-003",
            variant_name="baseline",
            repetition_index=1,
            random_seed=200,
            status="success",
            successful=True,
            reward=0.91,
            duration_seconds=0.15,
            conflict_detected=False,
            negotiation_required=False,
            metadata={
                "ablation_variant": "baseline",
            },
            created_at="2026-07-30T10:01:00+00:00",
        ),
    ]

    for run in runs:
        repositories.runs.create(run)


def test_experiment_search() -> None:
    with TemporaryDirectory() as temporary:
        repositories, query_service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        result = query_service.search_experiments(
            ExperimentSearchCriteria(
                status="completed",
                metadata_contains={
                    "domain": "pricing",
                },
                direction="ASC",
            )
        )

        assert result.total_count == 2
        assert len(result.items) == 2
        assert result.items[0].experiment_id == (
            "EXP-001"
        )

        name_result = (
            query_service.search_experiments(
                ExperimentSearchCriteria(
                    name_contains="inventory",
                )
            )
        )

        assert name_result.total_count == 1
        assert (
            name_result.items[0].experiment_id
            == "EXP-003"
        )


def test_run_search() -> None:
    with TemporaryDirectory() as temporary:
        repositories, query_service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        result = query_service.search_runs(
            RunSearchCriteria(
                successful=True,
                min_reward=0.80,
                direction="DESC",
            )
        )

        assert result.total_count == 2
        assert len(result.items) == 2

        no_negotiation = (
            query_service.search_runs(
                RunSearchCriteria(
                    negotiation_required=False,
                    metadata_contains={
                        "ablation_variant": (
                            "without_negotiation"
                        ),
                    },
                )
            )
        )

        assert no_negotiation.total_count == 1
        assert (
            no_negotiation.items[0].run_id
            == "RUN-002"
        )


def test_pagination_and_combined_view() -> None:
    with TemporaryDirectory() as temporary:
        repositories, query_service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        paged = query_service.search_runs(
            RunSearchCriteria(
                limit=2,
                offset=1,
                direction="ASC",
            )
        )

        assert paged.total_count == 4
        assert len(paged.items) == 2

        combined = (
            query_service.get_experiment_with_runs(
                "EXP-002"
            )
        )

        assert combined is not None
        assert combined["run_count"] == 2
        assert (
            combined["experiment"].experiment_id
            == "EXP-002"
        )


def print_query_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, query_service = (
            build_environment(temporary)
        )

        seed_data(repositories)

        experiment_result = (
            query_service.search_experiments(
                ExperimentSearchCriteria(
                    status="completed",
                )
            )
        )

        run_result = query_service.search_runs(
            RunSearchCriteria(
                successful=True,
                min_reward=0.70,
            )
        )

        print()
        print("QUERY SERVICE RESULT")
        print("-" * 90)
        print(
            f"completed_experiments   : "
            f"{experiment_result.total_count}"
        )
        print(
            f"successful_runs         : "
            f"{run_result.total_count}"
        )
        print(
            f"top_result_run          : "
            f"{run_result.items[0].run_id}"
        )
        print(
            f"top_result_reward       : "
            f"{run_result.items[0].reward}"
        )


def run_tests() -> None:
    test_experiment_search()
    test_run_search()
    test_pagination_and_combined_view()
    print_query_summary()

    print()
    print(
        "Experiment Database Query Service "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
