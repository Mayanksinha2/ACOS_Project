from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    CrossExperimentStatisticsService,
    ExperimentDatabase,
    ExperimentRecord,
    RepositoryManager,
    RunRecord,
    StatisticsExporter,
    VariantStatisticsService,
)


def build_environment(
    directory: str,
):
    database = ExperimentDatabase(
        Path(directory) / "acos_research.db"
    )

    repositories = RepositoryManager.create(
        database
    )

    return (
        repositories,
        VariantStatisticsService(database),
        CrossExperimentStatisticsService(
            database
        ),
    )


def seed_data(
    repositories: RepositoryManager,
) -> None:
    experiments = [
        ExperimentRecord(
            experiment_id="EXP-001",
            name="Pricing Study",
            status="completed",
            created_at="2026-07-28T10:00:00+00:00",
            updated_at="2026-07-28T10:00:00+00:00",
        ),
        ExperimentRecord(
            experiment_id="EXP-002",
            name="Negotiation Study",
            status="completed",
            created_at="2026-07-29T10:00:00+00:00",
            updated_at="2026-07-29T10:00:00+00:00",
        ),
        ExperimentRecord(
            experiment_id="EXP-003",
            name="Inventory Study",
            status="completed",
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
            random_seed=10,
            status="success",
            successful=True,
            reward=0.90,
            duration_seconds=1.0,
            conflict_detected=True,
            negotiation_required=True,
            created_at="2026-07-28T10:01:00+00:00",
        ),
        RunRecord(
            run_id="RUN-002",
            experiment_id="EXP-001",
            variant_name="without_mocra",
            repetition_index=2,
            random_seed=11,
            status="success",
            successful=True,
            reward=0.70,
            duration_seconds=0.8,
            conflict_detected=True,
            negotiation_required=True,
            created_at="2026-07-28T10:02:00+00:00",
        ),
        RunRecord(
            run_id="RUN-003",
            experiment_id="EXP-002",
            variant_name="baseline",
            repetition_index=1,
            random_seed=20,
            status="success",
            successful=True,
            reward=0.80,
            duration_seconds=1.2,
            conflict_detected=False,
            negotiation_required=False,
            created_at="2026-07-29T10:01:00+00:00",
        ),
        RunRecord(
            run_id="RUN-004",
            experiment_id="EXP-002",
            variant_name="without_negotiation",
            repetition_index=2,
            random_seed=21,
            status="failed",
            successful=False,
            reward=0.50,
            duration_seconds=0.7,
            conflict_detected=True,
            negotiation_required=False,
            created_at="2026-07-29T10:02:00+00:00",
        ),
        RunRecord(
            run_id="RUN-005",
            experiment_id="EXP-003",
            variant_name="baseline",
            repetition_index=1,
            random_seed=30,
            status="success",
            successful=True,
            reward=1.00,
            duration_seconds=1.5,
            conflict_detected=False,
            negotiation_required=True,
            created_at="2026-07-30T10:01:00+00:00",
        ),
    ]

    for run in runs:
        repositories.runs.create(run)


def test_variant_statistics() -> None:
    with TemporaryDirectory() as temporary:
        repositories, service, _ = (
            build_environment(temporary)
        )
        seed_data(repositories)

        baseline = (
            service.get_variant_statistics(
                "baseline"
            )
        )

        assert baseline.total_runs == 3
        assert baseline.successful_runs == 3
        assert baseline.success_rate == 100.0
        assert baseline.experiment_count == 3
        assert round(
            baseline.reward_statistics.mean,
            6,
        ) == 0.9

        all_variants = (
            service.get_all_variant_statistics()
        )

        assert set(all_variants) == {
            "baseline",
            "without_mocra",
            "without_negotiation",
        }


def test_variant_comparison_and_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, service, _ = (
            build_environment(temporary)
        )
        seed_data(repositories)

        comparison = service.compare_variants(
            baseline_variant="baseline",
            candidate_variant="without_mocra",
            primary_metric="mean_reward",
        )

        assert comparison.baseline_value == 0.9
        assert comparison.candidate_value == 0.7
        assert round(
            comparison.absolute_difference,
            6,
        ) == -0.2
        assert comparison.better_variant == (
            "baseline"
        )

        summary = (
            service.get_cross_experiment_summary()
        )

        assert summary.experiment_count == 3
        assert summary.run_count == 5
        assert summary.variant_count == 3
        assert summary.best_variant == "baseline"
        assert summary.worst_variant == (
            "without_negotiation"
        )


def test_cross_experiment_ranking() -> None:
    with TemporaryDirectory() as temporary:
        repositories, _, service = (
            build_environment(temporary)
        )
        seed_data(repositories)

        ranking = service.rank_experiments(
            metric_name="mean_reward",
        )

        assert len(ranking) == 3
        assert ranking[0].experiment_id == (
            "EXP-003"
        )
        assert ranking[0].metric_value == 1.0
        assert ranking[-1].experiment_id == (
            "EXP-002"
        )


def test_statistics_export() -> None:
    with TemporaryDirectory() as temporary:
        repositories, variant_service, _ = (
            build_environment(temporary)
        )
        seed_data(repositories)

        summary = (
            variant_service
            .get_cross_experiment_summary()
        )

        exporter = StatisticsExporter()

        output_path = exporter.export_json(
            summary,
            Path(temporary)
            / "variant_summary.json",
        )

        assert output_path.exists()

        payload = json.loads(
            output_path.read_text(
                encoding="utf-8"
            )
        )

        assert payload["variant_count"] == 3
        assert payload["best_variant"] == (
            "baseline"
        )


def print_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, variant_service, cross_service = (
            build_environment(temporary)
        )
        seed_data(repositories)

        summary = (
            variant_service
            .get_cross_experiment_summary()
        )

        ranking = cross_service.rank_experiments(
            "mean_reward"
        )

        print()
        print("VARIANT AND CROSS-EXPERIMENT RESULT")
        print("-" * 90)
        print(
            f"experiment_count        : "
            f"{summary.experiment_count}"
        )
        print(
            f"run_count               : "
            f"{summary.run_count}"
        )
        print(
            f"variant_count           : "
            f"{summary.variant_count}"
        )
        print(
            f"best_variant            : "
            f"{summary.best_variant}"
        )
        print(
            f"worst_variant           : "
            f"{summary.worst_variant}"
        )
        print(
            f"top_experiment          : "
            f"{ranking[0].experiment_id}"
        )
        print(
            f"top_mean_reward         : "
            f"{ranking[0].metric_value}"
        )


def run_tests() -> None:
    test_variant_statistics()
    test_variant_comparison_and_summary()
    test_cross_experiment_ranking()
    test_statistics_export()
    print_summary()

    print()
    print(
        "Variant and Cross-Experiment Statistics "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
