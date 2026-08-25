from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    DatabaseMaintenanceService,
    ExperimentDatabase,
    ExperimentRecord,
    RepositoryManager,
    RunRecord,
)


def build_environment(directory: str):
    db_path = Path(directory) / "acos_research.db"
    report_dir = Path(directory) / "reports"
    database = ExperimentDatabase(db_path)
    repositories = RepositoryManager.create(database)
    service = DatabaseMaintenanceService(db_path)
    return db_path, report_dir, repositories, service


def seed_data(repositories):
    repositories.experiments.create(
        ExperimentRecord(
            experiment_id="EXP-HEALTH-001",
            name="Database Health Experiment",
            status="completed",
            created_at="2026-07-28T14:00:00+00:00",
            updated_at="2026-07-28T14:00:00+00:00",
        )
    )
    repositories.runs.create(
        RunRecord(
            run_id="RUN-HEALTH-001",
            experiment_id="EXP-HEALTH-001",
            variant_name="baseline",
            repetition_index=1,
            random_seed=101,
            status="success",
            successful=True,
            reward=0.88,
            duration_seconds=1.7,
            conflict_detected=False,
            negotiation_required=True,
            created_at="2026-07-28T14:05:00+00:00",
        )
    )


def test_health_report():
    with TemporaryDirectory() as temporary:
        _, _, repositories, service = build_environment(temporary)
        seed_data(repositories)
        report = service.health_report()
        assert report.integrity_ok
        assert report.quick_check_ok
        assert report.foreign_key_ok
        assert report.health_score >= 90
        assert report.tables
        assert report.database_size_bytes > 0


def test_optimization_and_exports():
    with TemporaryDirectory() as temporary:
        _, report_dir, repositories, service = build_environment(temporary)
        seed_data(repositories)
        assert service.integrity_check()
        assert service.integrity_check(quick=True)
        assert service.analyze()
        assert service.optimize()
        assert service.vacuum()

        report = service.health_report()
        assert Path(service.export_health_json(report_dir / "health.json", report)).exists()
        assert Path(service.export_health_csv(report_dir / "health.csv", report)).exists()
        assert Path(service.export_health_text(report_dir / "health.txt", report)).exists()


def test_orphan_detection_and_cleanup():
    with TemporaryDirectory() as temporary:
        db_path, _, repositories, service = build_environment(temporary)
        seed_data(repositories)
        assert sum(service.detect_orphans().values()) == 0

        connection = sqlite3.connect(str(db_path))
        try:
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.execute(
                "UPDATE runs SET experiment_id=? WHERE run_id=?",
                ("MISSING-EXPERIMENT", "RUN-HEALTH-001"),
            )
            connection.commit()
        finally:
            connection.close()

        assert sum(service.detect_orphans().values()) >= 1
        assert service.cleanup_orphans() >= 1
        assert sum(service.detect_orphans().values()) == 0


def print_summary():
    with TemporaryDirectory() as temporary:
        _, _, repositories, service = build_environment(temporary)
        seed_data(repositories)
        result = service.run_maintenance(run_vacuum=True)
        report = result.health_report

        print()
        print("DATABASE MAINTENANCE RESULT")
        print("-" * 90)
        print(f"health_score            : {report.health_score}")
        print(f"integrity_ok            : {report.integrity_ok}")
        print(f"quick_check_ok          : {report.quick_check_ok}")
        print(f"foreign_key_ok          : {report.foreign_key_ok}")
        print(f"tables_checked          : {len(report.tables)}")
        print(f"analyze_completed       : {result.analyze_completed}")
        print(f"optimize_completed      : {result.optimize_completed}")
        print(f"vacuum_completed        : {result.vacuum_completed}")
        print(f"orphan_rows_deleted     : {result.orphan_rows_deleted}")


def run_tests():
    test_health_report()
    test_optimization_and_exports()
    test_orphan_detection_and_cleanup()
    print_summary()
    print()
    print("Database Maintenance Framework tests passed.")


if __name__ == "__main__":
    run_tests()
