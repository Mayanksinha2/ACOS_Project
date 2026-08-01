from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    ExperimentDatabase,
    ExperimentExportService,
    ExperimentImportService,
    ExperimentRecord,
    RepositoryManager,
    RunRecord,
)


def create_database(
    path: Path,
):
    database = ExperimentDatabase(path)
    repositories = RepositoryManager.create(
        database
    )
    return database, repositories


def seed_source(
    repositories: RepositoryManager,
) -> None:
    repositories.experiments.create(
        ExperimentRecord(
            experiment_id="EXP-IMPORT-001",
            name="Portable Experiment",
            status="completed",
            created_at="2026-07-28T12:00:00+00:00",
            updated_at="2026-07-28T12:00:00+00:00",
        )
    )

    repositories.runs.create(
        RunRecord(
            run_id="RUN-IMPORT-001",
            experiment_id="EXP-IMPORT-001",
            variant_name="baseline",
            repetition_index=1,
            random_seed=42,
            status="success",
            successful=True,
            reward=0.82,
            duration_seconds=2.1,
            conflict_detected=False,
            negotiation_required=True,
            created_at="2026-07-28T12:10:00+00:00",
        )
    )


def fetch_value(
    database_path: Path,
    sql: str,
    parameters=(),
):
    connection = sqlite3.connect(
        str(database_path)
    )
    try:
        row = connection.execute(
            sql,
            parameters,
        ).fetchone()
        return None if row is None else row[0]
    finally:
        connection.close()


def test_json_import_skip_and_merge() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source_path = root / "source.db"
        target_path = root / "target.db"
        export_dir = root / "exports"

        _, source_repositories = (
            create_database(source_path)
        )
        seed_source(source_repositories)

        exporter = ExperimentExportService(
            source_path,
            export_dir,
        )
        export_result = exporter.export_json(
            "EXP-IMPORT-001",
            filename="portable",
        )

        create_database(target_path)
        importer = ExperimentImportService(
            target_path
        )

        first = importer.import_json(
            export_result.json_file,
            mode="skip",
        )

        assert first.successful
        assert first.total_inserted >= 2

        second = importer.import_json(
            export_result.json_file,
            mode="skip",
        )

        assert second.experiment_action == "skipped"
        assert second.total_skipped == 1

        connection = sqlite3.connect(
            str(target_path)
        )
        try:
            connection.execute(
                """
                UPDATE experiments
                SET name = ?
                WHERE experiment_id = ?
                """,
                (
                    "Changed Locally",
                    "EXP-IMPORT-001",
                ),
            )
            connection.commit()
        finally:
            connection.close()

        merged = importer.import_json(
            export_result.json_file,
            mode="merge",
        )

        assert merged.experiment_action == "updated"

        name = fetch_value(
            target_path,
            """
            SELECT name
            FROM experiments
            WHERE experiment_id = ?
            """,
            ("EXP-IMPORT-001",),
        )

        assert name == "Portable Experiment"


def test_zip_import_replace() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source_path = root / "source.db"
        target_path = root / "target.db"
        export_dir = root / "exports"

        _, source_repositories = (
            create_database(source_path)
        )
        seed_source(source_repositories)

        exporter = ExperimentExportService(
            source_path,
            export_dir,
        )
        export_result = exporter.export_zip(
            "EXP-IMPORT-001",
            filename="portable_zip",
        )

        _, target_repositories = (
            create_database(target_path)
        )

        target_repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-IMPORT-001",
                name="Old Experiment",
                status="failed",
            )
        )

        target_repositories.runs.create(
            RunRecord(
                run_id="RUN-OLD-001",
                experiment_id="EXP-IMPORT-001",
                variant_name="old",
                repetition_index=1,
                random_seed=1,
                status="failed",
                successful=False,
                reward=0.10,
                duration_seconds=9.0,
                conflict_detected=True,
                negotiation_required=False,
            )
        )

        importer = ExperimentImportService(
            target_path
        )

        result = importer.import_zip(
            export_result.zip_file,
            mode="replace",
        )

        assert result.successful
        assert result.experiment_action == "replaced"
        assert result.total_deleted >= 2
        assert result.total_inserted >= 2

        old_count = fetch_value(
            target_path,
            """
            SELECT COUNT(*)
            FROM runs
            WHERE run_id = ?
            """,
            ("RUN-OLD-001",),
        )

        new_count = fetch_value(
            target_path,
            """
            SELECT COUNT(*)
            FROM runs
            WHERE run_id = ?
            """,
            ("RUN-IMPORT-001",),
        )

        assert old_count == 0
        assert new_count == 1


def print_summary() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source_path = root / "source.db"
        target_path = root / "target.db"
        export_dir = root / "exports"

        _, repositories = create_database(
            source_path
        )
        seed_source(repositories)

        exporter = ExperimentExportService(
            source_path,
            export_dir,
        )
        export_result = exporter.export_zip(
            "EXP-IMPORT-001",
            filename="summary_import",
        )

        create_database(target_path)

        importer = ExperimentImportService(
            target_path
        )
        result = importer.import_zip(
            export_result.zip_file,
            mode="merge",
        )

        print()
        print("EXPERIMENT IMPORT RESULT")
        print("-" * 90)
        print(
            f"experiment_id           : "
            f"{result.experiment_id}"
        )
        print(
            f"mode                    : "
            f"{result.mode}"
        )
        print(
            f"experiment_action       : "
            f"{result.experiment_action}"
        )
        print(
            f"total_inserted          : "
            f"{result.total_inserted}"
        )
        print(
            f"total_updated           : "
            f"{result.total_updated}"
        )
        print(
            f"total_skipped           : "
            f"{result.total_skipped}"
        )
        print(
            f"total_deleted           : "
            f"{result.total_deleted}"
        )


def run_tests() -> None:
    test_json_import_skip_and_merge()
    test_zip_import_replace()
    print_summary()

    print()
    print(
        "Experiment Import Framework tests passed."
    )


if __name__ == "__main__":
    run_tests()
