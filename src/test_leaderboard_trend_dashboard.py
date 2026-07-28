from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    DashboardSummaryService,
    ExperimentDatabase,
    ExperimentRecord,
    LeaderboardService,
    RepositoryManager,
    RunRecord,
    TrendAnalysisService,
)


def build_environment(directory: str):
    database = ExperimentDatabase(
        Path(directory) / "acos_research.db"
    )
    repositories = RepositoryManager.create(
        database
    )

    return (
        repositories,
        LeaderboardService(database),
        TrendAnalysisService(database),
        DashboardSummaryService(database),
    )


def seed_data(
    repositories: RepositoryManager,
) -> None:
    experiments = [
        ExperimentRecord(
            experiment_id="EXP-001",
            name="Pricing Experiment",
            status="completed",
            created_at="2026-07-28T09:00:00+00:00",
            updated_at="2026-07-28T09:00:00+00:00",
        ),
        ExperimentRecord(
            experiment_id="EXP-002",
            name="Negotiation Experiment",
            status="completed",
            created_at="2026-07-29T09:00:00+00:00",
            updated_at="2026-07-29T09:00:00+00:00",
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
            random_seed=1,
            status="success",
            successful=True,
            reward=0.50,
            duration_seconds=3.0,
            conflict_detected=True,
            negotiation_required=True,
            created_at="2026-07-28T10:00:00+00:00",
        ),
        RunRecord(
            run_id="RUN-002",
            experiment_id="EXP-001",
            variant_name="baseline",
            repetition_index=2,
            random_seed=2,
            status="success",
            successful=True,
            reward=0.70,
            duration_seconds=2.0,
            conflict_detected=False,
            negotiation_required=False,
            created_at="2026-07-28T11:00:00+00:00",
        ),
        RunRecord(
            run_id="RUN-003",
            experiment_id="EXP-002",
            variant_name="without_mocra",
            repetition_index=1,
            random_seed=3,
            status="failed",
            successful=False,
            reward=0.40,
            duration_seconds=1.0,
            conflict_detected=True,
            negotiation_required=False,
            created_at="2026-07-29T10:00:00+00:00",
        ),
        RunRecord(
            run_id="RUN-004",
            experiment_id="EXP-002",
            variant_name="baseline",
            repetition_index=2,
            random_seed=4,
            status="success",
            successful=True,
            reward=0.90,
            duration_seconds=1.5,
            conflict_detected=False,
            negotiation_required=True,
            created_at="2026-07-29T11:00:00+00:00",
        ),
    ]

    for run in runs:
        repositories.runs.create(run)


def test_run_leaderboard() -> None:
    with TemporaryDirectory() as temporary:
        repositories, leaderboards, _, _ = (
            build_environment(temporary)
        )
        seed_data(repositories)

        ranking = leaderboards.rank_runs(
            metric_name="reward",
            limit=3,
        )

        assert len(ranking) == 3
        assert ranking[0].run_id == "RUN-004"
        assert ranking[0].metric_value == 0.90
        assert ranking[1].run_id == "RUN-002"

        fastest = leaderboards.rank_runs(
            metric_name="duration_seconds",
            descending=False,
            limit=1,
        )

        assert fastest[0].run_id == "RUN-003"


def test_variant_and_experiment_leaderboards() -> None:
    with TemporaryDirectory() as temporary:
        repositories, leaderboards, _, _ = (
            build_environment(temporary)
        )
        seed_data(repositories)

        variants = leaderboards.rank_variants(
            metric_name="mean_reward",
        )

        assert variants[0].variant_name == (
            "baseline"
        )
        assert round(
            variants[0].metric_value,
            6,
        ) == 0.7

        experiments = (
            leaderboards.rank_experiments(
                metric_name="mean_reward",
            )
        )

        assert experiments[0].experiment_id == (
        "EXP-002"
        )
        assert experiments[1].experiment_id == (
        "EXP-001"
        )

        assert round(
        experiments[0].metric_value,
        6,
        ) == 0.65

        assert round(
        experiments[1].metric_value,
        6,
        ) == 0.60


def test_trend_analysis() -> None:
    with TemporaryDirectory() as temporary:
        repositories, _, trends, _ = (
            build_environment(temporary)
        )
        seed_data(repositories)

        trend = trends.analyze_run_trend(
            metric_name="reward",
            rolling_window=2,
        )

        assert trend.total_points == 4
        assert trend.first_value == 0.50
        assert trend.last_value == 0.90
        assert round(
            trend.absolute_change,
            6,
        ) == 0.40
        assert trend.direction == "improving"
        assert (
            round(
                trend.points[1].rolling_mean,
                6,
            )
            == 0.60
        )
        assert (
            round(
                trend.points[3].rolling_mean,
                6,
            )
            == 0.65
        )


def test_dashboard_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, _, _, dashboard = (
            build_environment(temporary)
        )
        seed_data(repositories)

        summary = dashboard.build_summary(
            leaderboard_limit=2,
            rolling_window=2,
        )

        assert (
            summary.database_statistics
            .total_experiments
            == 2
        )
        assert (
            summary.database_statistics
            .total_runs
            == 4
        )
        assert (
            summary.variant_summary.best_variant
            == "baseline"
        )
        assert (
            len(
                summary.leaderboards
                .run_leaderboard
            )
            == 2
        )
        assert (
            summary.reward_trend.direction
            == "improving"
        )


def print_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, leaderboards, trends, dashboard = (
            build_environment(temporary)
        )
        seed_data(repositories)

        bundle = leaderboards.build_bundle(
            limit=3
        )

        trend = trends.analyze_run_trend(
            rolling_window=2
        )

        dashboard_result = (
            dashboard.build_summary(
                leaderboard_limit=3,
                rolling_window=2,
            )
        )

        print()
        print("LEADERBOARD AND TREND RESULT")
        print("-" * 90)
        print(
            f"top_run                 : "
            f"{bundle.run_leaderboard[0].run_id}"
        )
        print(
            f"top_run_reward          : "
            f"{bundle.run_leaderboard[0].metric_value}"
        )
        print(
            f"top_variant             : "
            f"{bundle.variant_leaderboard[0].variant_name}"
        )
        print(
            f"trend_direction         : "
            f"{trend.direction}"
        )
        print(
            f"trend_change            : "
            f"{trend.absolute_change}"
        )
        print(
            f"dashboard_total_runs    : "
            f"{dashboard_result.database_statistics.total_runs}"
        )


def run_tests() -> None:
    test_run_leaderboard()
    test_variant_and_experiment_leaderboards()
    test_trend_analysis()
    test_dashboard_summary()
    print_summary()

    print()
    print(
        "Leaderboard, Trend, and Dashboard "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
