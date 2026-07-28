from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    CsvExportService,
    ExperimentDatabase,
    ExperimentRecord,
    RepositoryManager,
    RunRecord,
)


def build_environment(directory: str):
    database_path = Path(directory) / "acos_research.db"
    output_directory = Path(directory) / "csv_exports"

    database = ExperimentDatabase(database_path)
    repositories = RepositoryManager.create(database)
    exporter = CsvExportService(
        database_path,
        output_directory,
    )
    return repositories, exporter


def seed_data(repositories: RepositoryManager) -> None:
    repositories.experiments.create(
        ExperimentRecord(
            experiment_id="EXP-CSV-001",
            name="CSV Export Experiment",
            status="completed",
            created_at="2026-07-28T13:00:00+00:00",
            updated_at="2026-07-28T13:00:00+00:00",
        )
    )

    repositories.runs.create(
        RunRecord(
            run_id="RUN-CSV-001",
            experiment_id="EXP-CSV-001",
            variant_name="baseline",
            repetition_index=1,
            random_seed=42,
            status="success",
            successful=True,
            reward=0.86,
            duration_seconds=1.8,
            conflict_detected=False,
            negotiation_required=True,
            created_at="2026-07-28T13:10:00+00:00",
        )
    )

    repositories.runs.create(
        RunRecord(
            run_id="RUN-CSV-002",
            experiment_id="EXP-CSV-001",
            variant_name="candidate",
            repetition_index=1,
            random_seed=43,
            status="success",
            successful=True,
            reward=0.91,
            duration_seconds=1.5,
            conflict_detected=True,
            negotiation_required=True,
            created_at="2026-07-28T13:20:00+00:00",
        )
    )


def test_single_table_export() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = build_environment(temporary)
        seed_data(repositories)

        result = exporter.export_table(
            table_name="runs",
            experiment_id="EXP-CSV-001",
        )

        path = Path(result.path)
        assert path.exists()
        assert result.row_count == 2
        assert result.column_count > 0
        assert exporter.validate_csv(path, expected_rows=2)

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            rows = list(csv.DictReader(handle))

        assert rows[0]["run_id"] == "RUN-CSV-001"
        assert rows[1]["run_id"] == "RUN-CSV-002"


def test_records_and_statistics_export() -> None:
    with TemporaryDirectory() as temporary:
        _, exporter = build_environment(temporary)

        leaderboard = exporter.export_leaderboard(
            [
                {
                    "rank": 1,
                    "variant": "candidate",
                    "mean_reward": 0.91,
                },
                {
                    "rank": 2,
                    "variant": "baseline",
                    "mean_reward": 0.86,
                },
            ]
        )

        assert leaderboard.row_count == 2
        assert exporter.validate_csv(
            leaderboard.path,
            expected_rows=2,
        )

        statistics = exporter.export_statistics(
            {
                "run_count": 2,
                "reward": {
                    "mean": 0.885,
                    "maximum": 0.91,
                },
            }
        )

        assert statistics.row_count == 3
        assert exporter.validate_csv(
            statistics.path,
            expected_rows=3,
        )


def test_batch_export_zip() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = build_environment(temporary)
        seed_data(repositories)

        result = exporter.export_all_tables(
            experiment_id="EXP-CSV-001",
            include_empty=True,
            create_zip=True,
            package_name="csv_research_package",
        )

        assert result.total_rows >= 3
        assert result.zip_file is not None
        assert Path(result.zip_file).exists()
        assert Path(result.manifest_file).exists()
        assert exporter.validate_zip(result.zip_file)


def print_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = build_environment(temporary)
        seed_data(repositories)

        result = exporter.export_all_tables(
            experiment_id="EXP-CSV-001",
            create_zip=True,
            package_name="summary_csv_export",
        )

        print()
        print("CSV EXPORT RESULT")
        print("-" * 90)
        print(f"export_id               : {result.export_id}")
        print(f"files_generated         : {len(result.files)}")
        print(f"total_rows              : {result.total_rows}")
        print(f"zip_file                : {result.zip_file}")
        print(f"manifest_file           : {result.manifest_file}")


def run_tests() -> None:
    test_single_table_export()
    test_records_and_statistics_export()
    test_batch_export_zip()
    print_summary()

    print()
    print("CSV Export Framework tests passed.")


if __name__ == "__main__":
    run_tests()
