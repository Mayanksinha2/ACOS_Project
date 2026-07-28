from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    AblationResultRecord,
    AggregatedEvaluationRecord,
    ArtifactRecord,
    ExperimentDatabase,
    ExperimentRecord,
    PublicationRecord,
    ReportRecord,
    RepositoryManager,
    RunRecord,
)


def build_repositories(
    directory: str,
) -> RepositoryManager:
    database = ExperimentDatabase(
        Path(directory) / "acos_research.db"
    )

    return RepositoryManager.create(
        database
    )


def seed_experiment(
    repositories: RepositoryManager,
) -> None:
    repositories.experiments.create(
        ExperimentRecord(
            experiment_id="EXP-001",
            name="Repository Integration Test",
            status="running",
            description=(
                "Tests repository persistence."
            ),
            metadata={
                "research_area": "ACOS",
            },
        )
    )


def test_experiment_and_run_repositories() -> None:
    with TemporaryDirectory() as temporary:
        repositories = build_repositories(
            temporary
        )
        seed_experiment(repositories)

        assert repositories.experiments.exists(
            "EXP-001"
        )

        experiment = (
            repositories.experiments.get(
                "EXP-001"
            )
        )

        assert experiment is not None
        assert experiment.name == (
            "Repository Integration Test"
        )

        repositories.runs.create(
            RunRecord(
                run_id="RUN-BASELINE",
                experiment_id="EXP-001",
                variant_name="baseline",
                repetition_index=1,
                random_seed=100,
                status="success",
                successful=True,
                reward=0.82,
                duration_seconds=0.12,
                conflict_detected=True,
                negotiation_required=True,
                metadata={
                    "ablation_variant": "baseline",
                },
            )
        )

        repositories.runs.create(
            RunRecord(
                run_id="RUN-NO-MOCRA",
                experiment_id="EXP-001",
                variant_name="without_mocra",
                repetition_index=1,
                random_seed=100,
                status="success",
                successful=True,
                reward=0.72,
                duration_seconds=0.10,
                conflict_detected=True,
                negotiation_required=True,
                metadata={
                    "ablation_variant": (
                        "without_mocra"
                    ),
                },
            )
        )

        runs = (
            repositories.runs.list_by_experiment(
                "EXP-001"
            )
        )

        assert len(runs) == 2

        strong_runs = (
            repositories.runs.list_by_experiment(
                "EXP-001",
                min_reward=0.8,
            )
        )

        assert len(strong_runs) == 1
        assert strong_runs[0].run_id == (
            "RUN-BASELINE"
        )

        assert (
            repositories.experiments.update_status(
                "EXP-001",
                "completed",
            )
        )

        updated = (
            repositories.experiments.get(
                "EXP-001"
            )
        )

        assert updated is not None
        assert updated.status == "completed"


def test_artifact_research_repositories() -> None:
    with TemporaryDirectory() as temporary:
        repositories = build_repositories(
            temporary
        )
        seed_experiment(repositories)

        repositories.runs.create(
            RunRecord(
                run_id="RUN-001",
                experiment_id="EXP-001",
                variant_name="baseline",
                repetition_index=1,
                random_seed=200,
                status="success",
                successful=True,
                reward=0.85,
            )
        )

        repositories.artifacts.create(
            ArtifactRecord(
                artifact_id="ART-001",
                experiment_id="EXP-001",
                run_id="RUN-001",
                artifact_type="chart",
                path="outputs/reward_chart.png",
            )
        )

        repositories.reports.create(
            ReportRecord(
                report_id="REPORT-001",
                experiment_id="EXP-001",
                run_id="RUN-001",
                markdown_path=(
                    "outputs/report.md"
                ),
                manifest_path=(
                    "outputs/report_manifest.json"
                ),
            )
        )

        repositories.publications.create(
            PublicationRecord(
                publication_id="PUB-001",
                experiment_id="EXP-001",
                markdown_path=(
                    "outputs/paper.md"
                ),
                latex_path=(
                    "outputs/paper.tex"
                ),
            )
        )

        repositories.evaluations.create(
            AggregatedEvaluationRecord(
                evaluation_id="EVAL-001",
                experiment_id="EXP-001",
                metrics={
                    "mean_reward": 0.82,
                    "success_rate": 100.0,
                },
                groups={
                    "baseline": {
                        "mean_reward": 0.82,
                    },
                },
            )
        )

        repositories.ablations.create(
            AblationResultRecord(
                ablation_id="ABL-001",
                experiment_id="EXP-001",
                baseline_group="baseline",
                primary_metric="mean_reward",
                best_group="baseline",
                worst_group="without_mocra",
                ranking=[
                    "baseline",
                    "without_mocra",
                ],
                comparisons=[
                    {
                        "group": "without_mocra",
                        "difference": -0.10,
                    }
                ],
            )
        )

        assert len(
            repositories.artifacts.list_by_experiment(
                "EXP-001"
            )
        ) == 1

        assert len(
            repositories.reports.list_by_experiment(
                "EXP-001"
            )
        ) == 1

        assert len(
            repositories.publications.list_by_experiment(
                "EXP-001"
            )
        ) == 1

        assert len(
            repositories.evaluations.list_by_experiment(
                "EXP-001"
            )
        ) == 1

        assert len(
            repositories.ablations.list_by_experiment(
                "EXP-001"
            )
        ) == 1


def test_cascade_delete() -> None:
    with TemporaryDirectory() as temporary:
        repositories = build_repositories(
            temporary
        )
        seed_experiment(repositories)

        repositories.runs.create(
            RunRecord(
                run_id="RUN-DELETE",
                experiment_id="EXP-001",
                variant_name="baseline",
                repetition_index=1,
                random_seed=None,
                status="success",
                successful=True,
            )
        )

        assert repositories.experiments.delete(
            "EXP-001"
        )

        assert repositories.experiments.get(
            "EXP-001"
        ) is None

        assert repositories.runs.get(
            "RUN-DELETE"
        ) is None


def print_repository_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories = build_repositories(
            temporary
        )
        seed_experiment(repositories)

        repositories.runs.create(
            RunRecord(
                run_id="RUN-001",
                experiment_id="EXP-001",
                variant_name="baseline",
                repetition_index=1,
                random_seed=300,
                status="success",
                successful=True,
                reward=0.88,
                conflict_detected=True,
                negotiation_required=True,
            )
        )

        print()
        print("REPOSITORY LAYER RESULT")
        print("-" * 90)
        print(
            f"experiments             : "
            f"{repositories.experiments.count('experiments')}"
        )
        print(
            f"runs                    : "
            f"{repositories.runs.count('runs')}"
        )
        print(
            f"experiment_exists       : "
            f"{repositories.experiments.exists('EXP-001')}"
        )
        print(
            f"baseline_runs           : "
            f"{len(repositories.runs.list_by_variant('baseline'))}"
        )
        print(
            f"stored_reward           : "
            f"{repositories.runs.get('RUN-001').reward}"
        )


def run_tests() -> None:
    test_experiment_and_run_repositories()
    test_artifact_research_repositories()
    test_cascade_delete()
    print_repository_summary()

    print()
    print(
        "Experiment Database Repository Layer "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
