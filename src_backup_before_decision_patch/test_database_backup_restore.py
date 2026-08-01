from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    DatabaseBackupManager,
    ExperimentDatabase,
    ExperimentRecord,
    RepositoryManager,
)


def build_environment(
    directory: str,
):
    database_path = (
        Path(directory) / "acos_research.db"
    )
    backup_directory = (
        Path(directory) / "backups"
    )

    database = ExperimentDatabase(
        database_path
    )
    repositories = RepositoryManager.create(
        database
    )

    manager = DatabaseBackupManager(
        database_path,
        backup_directory,
        retention_count=2,
    )

    return (
        database_path,
        repositories,
        manager,
    )


def experiment_count(
    database_path: Path,
) -> int:
    connection = sqlite3.connect(
        str(database_path)
    )
    try:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM experiments
            """
        ).fetchone()
        return int(row[0])
    finally:
        connection.close()


def test_create_and_verify_backup() -> None:
    with TemporaryDirectory() as temporary:
        database_path, repositories, manager = (
            build_environment(temporary)
        )

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-001",
                name="Backup Test",
                status="completed",
            )
        )

        metadata = manager.create_backup(
            label="initial"
        )

        backup_path = Path(
            metadata.backup_database
        )
        metadata_path = Path(
            metadata.metadata_file
        )

        assert database_path.exists()
        assert backup_path.exists()
        assert metadata_path.exists()
        assert metadata.integrity_status == "ok"
        assert len(metadata.sha256) == 64
        assert manager.verify_backup(
            backup_path
        )


def test_restore_backup() -> None:
    with TemporaryDirectory() as temporary:
        database_path, repositories, manager = (
            build_environment(temporary)
        )

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-001",
                name="Original Experiment",
                status="completed",
            )
        )

        backup = manager.create_backup(
            label="before_change"
        )

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-002",
                name="Later Experiment",
                status="completed",
            )
        )

        assert experiment_count(
            database_path
        ) == 2

        result = manager.restore_backup(
            backup.backup_database,
            create_pre_restore_backup=True,
        )

        assert result.successful
        assert result.integrity_status == "ok"
        assert result.pre_restore_backup is not None
        assert experiment_count(
            database_path
        ) == 1


def test_backup_rotation() -> None:
    with TemporaryDirectory() as temporary:
        _, repositories, manager = (
            build_environment(temporary)
        )

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-001",
                name="Rotation Test",
                status="completed",
            )
        )

        manager.create_backup(
            label="one"
        )
        manager.create_backup(
            label="two"
        )
        manager.create_backup(
            label="three"
        )

        backups = manager.list_backups()

        assert len(backups) == 2

        labels = [
            item.backup_id
            for item in backups
        ]

        assert any(
            "three" in value
            for value in labels
        )
        assert any(
            "two" in value
            for value in labels
        )


def print_summary() -> None:
    with TemporaryDirectory() as temporary:
        database_path, repositories, manager = (
            build_environment(temporary)
        )

        repositories.experiments.create(
            ExperimentRecord(
                experiment_id="EXP-001",
                name="Backup Summary",
                status="completed",
            )
        )

        metadata = manager.create_backup(
            label="summary"
        )

        print()
        print("DATABASE BACKUP RESULT")
        print("-" * 90)
        print(
            f"backup_id               : "
            f"{metadata.backup_id}"
        )
        print(
            f"source_database         : "
            f"{metadata.source_database}"
        )
        print(
            f"backup_database         : "
            f"{metadata.backup_database}"
        )
        print(
            f"integrity_status        : "
            f"{metadata.integrity_status}"
        )
        print(
            f"sha256                  : "
            f"{metadata.sha256}"
        )
        print(
            f"backup_size_bytes       : "
            f"{metadata.backup_size_bytes}"
        )


def run_tests() -> None:
    test_create_and_verify_backup()
    test_restore_backup()
    test_backup_rotation()
    print_summary()

    print()
    print(
        "Database Backup and Restore tests passed."
    )


if __name__ == "__main__":
    run_tests()
