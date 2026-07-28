from __future__ import annotations

import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    ExperimentDatabase,
    ExperimentExportService,
    ExperimentRecord,
    RepositoryManager,
    RunRecord,
)


def build_environment(
    directory: str,
):
    database_path = (
        Path(directory) / "acos_research.db"
    )
    export_directory = (
        Path(directory) / "exports"
    )

    database = ExperimentDatabase(
        database_path
    )
    repositories = RepositoryManager.create(
        database
    )

    exporter = ExperimentExportService(
        database_path,
        export_directory,
    )

    return repositories, exporter


def seed_data(
    repositories: RepositoryManager,
) -> None:
    repositories.experiments.create(
        ExperimentRecord(
            experiment_id="EXP-EXPORT-001",
            name="Export Experiment",
            status="completed",
            created_at="2026-07-28T10:00:00+00:00",
            updated_at="2026-07-28T10:00:00+00:00",
        )
    )

    repositories.runs.create(
        RunRecord(
            run_id="RUN-EXPORT-001",
            experiment_id="EXP-EXPORT-001",
            variant_name="baseline",
            repetition_index=1,
            random_seed=42,
            status="success",
            successful=True,
            reward=0.81,
            duration_seconds=2.4,
            conflict_detected=False,
            negotiation_required=True,
            created_at="2026-07-28T10:30:00+00:00",
        )
    )


def test_build_package() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = (
            build_environment(temporary)
        )
        seed_data(repositories)

        package = exporter.build_package(
            "EXP-EXPORT-001"
        )

        assert (
            package.experiment[
                "experiment_id"
            ]
            == "EXP-EXPORT-001"
        )
        assert "runs" in package.related_data
        assert (
            len(
                package.related_data["runs"]
            )
            == 1
        )
        assert (
            package.manifest
            .table_counts["experiments"]
            == 1
        )


def test_json_export() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = (
            build_environment(temporary)
        )
        seed_data(repositories)

        result = exporter.export_json(
            "EXP-EXPORT-001",
            filename="experiment_export",
        )

        json_path = Path(
            result.json_file
        )
        manifest_path = Path(
            result.manifest_file
        )

        assert json_path.exists()
        assert manifest_path.exists()
        assert result.total_records >= 2
        assert exporter.validate_export_json(
            json_path
        )

        payload = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            payload["experiment"][
                "experiment_id"
            ]
            == "EXP-EXPORT-001"
        )


def test_zip_export() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = (
            build_environment(temporary)
        )
        seed_data(repositories)

        result = exporter.export_zip(
            "EXP-EXPORT-001",
            filename="portable_package",
        )

        zip_path = Path(
            result.zip_file
        )

        assert zip_path.exists()
        assert exporter.validate_export_zip(
            zip_path
        )

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as archive:
            names = set(
                archive.namelist()
            )

        assert "experiment.json" in names
        assert "manifest.json" in names


def print_summary() -> None:
    with TemporaryDirectory() as temporary:
        repositories, exporter = (
            build_environment(temporary)
        )
        seed_data(repositories)

        result = exporter.export_zip(
            "EXP-EXPORT-001",
            filename="summary_package",
        )

        print()
        print("EXPERIMENT EXPORT RESULT")
        print("-" * 90)
        print(
            f"experiment_id           : "
            f"{result.experiment_id}"
        )
        print(
            f"zip_file                : "
            f"{result.zip_file}"
        )
        print(
            f"manifest_file           : "
            f"{result.manifest_file}"
        )
        print(
            f"total_records           : "
            f"{result.total_records}"
        )
        print(
            f"created_at              : "
            f"{result.created_at}"
        )


def run_tests() -> None:
    test_build_package()
    test_json_export()
    test_zip_export()
    print_summary()

    print()
    print(
        "Experiment Export Framework tests passed."
    )


if __name__ == "__main__":
    run_tests()
