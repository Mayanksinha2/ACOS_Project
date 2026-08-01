from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from experiment_database import (
    ExperimentDatabase,
    SCHEMA_VERSION,
)


EXPECTED_TABLES = {
    "schema_migrations",
    "experiments",
    "runs",
    "artifacts",
    "reports",
    "publications",
    "aggregated_evaluations",
    "ablation_results",
}


def test_database_initialization() -> None:
    with TemporaryDirectory() as temporary:
        database_path = (
            Path(temporary)
            / "acos_research.db"
        )

        database = ExperimentDatabase(
            database_path
        )

        version = database.initialize()

        assert version == SCHEMA_VERSION
        assert database_path.exists()

        table_names = set(
            database.table_names()
        )

        assert EXPECTED_TABLES.issubset(
            table_names
        )


def test_foreign_keys_and_transactions() -> None:
    with TemporaryDirectory() as temporary:
        database = ExperimentDatabase(
            Path(temporary)
            / "acos_research.db"
        )

        database.initialize()

        with database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO experiments (
                    experiment_id,
                    name,
                    status,
                    description,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "EXP-001",
                    "Core Database Test",
                    "created",
                    "Phase 1 initialization test.",
                    "{}",
                    "2026-07-28T10:00:00+00:00",
                    "2026-07-28T10:00:00+00:00",
                ),
            )

            connection.execute(
                """
                INSERT INTO runs (
                    run_id,
                    experiment_id,
                    variant_name,
                    repetition_index,
                    random_seed,
                    status,
                    successful,
                    reward,
                    duration_seconds,
                    conflict_detected,
                    negotiation_required,
                    metadata_json,
                    warnings_json,
                    errors_json,
                    created_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    "RUN-001",
                    "EXP-001",
                    "baseline",
                    1,
                    100,
                    "success",
                    1,
                    0.82,
                    0.12,
                    1,
                    1,
                    "{}",
                    "[]",
                    "[]",
                    "2026-07-28T10:00:01+00:00",
                ),
            )

        experiment_row = database.fetch_one(
            """
            SELECT *
            FROM experiments
            WHERE experiment_id = ?
            """,
            ("EXP-001",),
        )

        run_row = database.fetch_one(
            """
            SELECT *
            FROM runs
            WHERE run_id = ?
            """,
            ("RUN-001",),
        )

        assert experiment_row is not None
        assert run_row is not None
        assert run_row["experiment_id"] == "EXP-001"
        assert run_row["reward"] == 0.82


def test_transaction_rollback() -> None:
    with TemporaryDirectory() as temporary:
        database = ExperimentDatabase(
            Path(temporary)
            / "acos_research.db"
        )

        database.initialize()

        try:
            with database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO experiments (
                        experiment_id,
                        name,
                        status,
                        description,
                        metadata_json,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "EXP-ROLLBACK",
                        "Rollback Test",
                        "created",
                        "",
                        "{}",
                        "2026-07-28T10:00:00+00:00",
                        "2026-07-28T10:00:00+00:00",
                    ),
                )

                raise RuntimeError(
                    "Force rollback"
                )

        except RuntimeError:
            pass

        row = database.fetch_one(
            """
            SELECT *
            FROM experiments
            WHERE experiment_id = ?
            """,
            ("EXP-ROLLBACK",),
        )

        assert row is None


def print_database_summary() -> None:
    with TemporaryDirectory() as temporary:
        database_path = (
            Path(temporary)
            / "acos_research.db"
        )

        database = ExperimentDatabase(
            database_path
        )

        version = database.initialize()

        print()
        print("EXPERIMENT DATABASE CORE RESULT")
        print("-" * 90)
        print(
            f"database_path           : "
            f"{database_path}"
        )
        print(
            f"schema_version          : "
            f"{version}"
        )
        print(
            f"database_exists         : "
            f"{database_path.exists()}"
        )
        print(
            f"table_count             : "
            f"{len(database.table_names())}"
        )
        print(
            f"tables                  : "
            f"{database.table_names()}"
        )


def run_tests() -> None:
    test_database_initialization()
    test_foreign_keys_and_transactions()
    test_transaction_rollback()
    print_database_summary()

    print()
    print(
        "Experiment Database Core Framework "
        "tests passed."
    )


if __name__ == "__main__":
    run_tests()
