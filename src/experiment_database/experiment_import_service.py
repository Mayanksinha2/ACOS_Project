from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path
from typing import Any

from .import_exceptions import (
    DuplicateExperimentError,
    ImportPackageValidationError,
    SchemaCompatibilityError,
)
from .import_models import (
    ExperimentImportResult,
    ImportTableResult,
)
from .import_utils import (
    quote_identifier,
    read_json,
    utc_now_iso,
)


class ExperimentImportService:
    """
    Imports experiment JSON or ZIP packages produced
    by ExperimentExportService.

    Supported modes:

    - skip: leave an existing experiment untouched
    - merge: insert new records and update duplicates
    - replace: delete the existing experiment and all
      related records, then import the package
    """

    FORMAT_VERSION = "1.0"
    VALID_MODES = {
        "skip",
        "merge",
        "replace",
    }

    def __init__(
        self,
        database: Any,
    ) -> None:
        self.database = database
        self.database_path = (
            self._resolve_database_path(database)
        )

    def import_json(
        self,
        json_file: str | Path,
        mode: str = "skip",
    ) -> ExperimentImportResult:
        path = Path(json_file)

        if not path.exists():
            raise ImportPackageValidationError(
                f"Import file not found: {path}"
            )

        try:
            payload = read_json(path)
        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise ImportPackageValidationError(
                "Invalid import JSON."
            ) from exc

        return self._import_payload(
            payload=payload,
            source_file=path,
            mode=mode,
        )

    def import_zip(
        self,
        zip_file: str | Path,
        mode: str = "skip",
    ) -> ExperimentImportResult:
        path = Path(zip_file)

        if not path.exists():
            raise ImportPackageValidationError(
                f"Import ZIP not found: {path}"
            )

        try:
            with zipfile.ZipFile(
                path,
                mode="r",
            ) as archive:
                required = {
                    "experiment.json",
                    "manifest.json",
                }

                names = set(
                    archive.namelist()
                )

                if not required.issubset(names):
                    raise ImportPackageValidationError(
                        "Import ZIP is missing required files."
                    )

                bad_file = archive.testzip()
                if bad_file is not None:
                    raise ImportPackageValidationError(
                        f"Corrupt ZIP member: {bad_file}"
                    )

                payload = json.loads(
                    archive.read(
                        "experiment.json"
                    ).decode("utf-8")
                )

                manifest = json.loads(
                    archive.read(
                        "manifest.json"
                    ).decode("utf-8")
                )

        except ImportPackageValidationError:
            raise

        except (
            zipfile.BadZipFile,
            json.JSONDecodeError,
            UnicodeDecodeError,
            OSError,
        ) as exc:
            raise ImportPackageValidationError(
                "Invalid import ZIP."
            ) from exc

        payload_manifest = payload.get(
            "manifest",
            {}
        )

        if (
            payload_manifest.get("experiment_id")
            != manifest.get("experiment_id")
        ):
            raise ImportPackageValidationError(
                "ZIP manifest experiment ID mismatch."
            )

        return self._import_payload(
            payload=payload,
            source_file=path,
            mode=mode,
        )

    def validate_package(
        self,
        payload: dict[str, Any],
    ) -> bool:
        required = {
            "manifest",
            "experiment",
            "related_data",
        }

        if not isinstance(payload, dict):
            raise ImportPackageValidationError(
                "Import package must be an object."
            )

        if not required.issubset(payload):
            raise ImportPackageValidationError(
                "Import package is missing required sections."
            )

        manifest = payload["manifest"]
        experiment = payload["experiment"]
        related_data = payload["related_data"]

        if not isinstance(manifest, dict):
            raise ImportPackageValidationError(
                "manifest must be an object."
            )

        if not isinstance(experiment, dict):
            raise ImportPackageValidationError(
                "experiment must be an object."
            )

        if not isinstance(related_data, dict):
            raise ImportPackageValidationError(
                "related_data must be an object."
            )

        if (
            manifest.get("format_version")
            != self.FORMAT_VERSION
        ):
            raise ImportPackageValidationError(
                "Unsupported import format version."
            )

        experiment_id = experiment.get(
            "experiment_id"
        )

        if not experiment_id:
            raise ImportPackageValidationError(
                "Experiment ID is missing."
            )

        if (
            manifest.get("experiment_id")
            != experiment_id
        ):
            raise ImportPackageValidationError(
                "Experiment ID mismatch."
            )

        for table_name, rows in related_data.items():
            if not isinstance(table_name, str):
                raise ImportPackageValidationError(
                    "Related table names must be strings."
                )
            if not isinstance(rows, list):
                raise ImportPackageValidationError(
                    f"Rows for {table_name} must be a list."
                )
            if not all(
                isinstance(row, dict)
                for row in rows
            ):
                raise ImportPackageValidationError(
                    f"Rows for {table_name} must be objects."
                )

        return True

    def _import_payload(
        self,
        payload: dict[str, Any],
        source_file: Path,
        mode: str,
    ) -> ExperimentImportResult:
        self._validate_mode(mode)
        self.validate_package(payload)
        self._initialize_database()

        experiment = payload["experiment"]
        related_data = payload["related_data"]
        experiment_id = str(
            experiment["experiment_id"]
        )

        with closing(
            self._connect()
        ) as connection:
            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            try:
                connection.execute("BEGIN")

                exists = self._experiment_exists(
                    connection,
                    experiment_id,
                )

                if exists and mode == "skip":
                    connection.rollback()
                    return ExperimentImportResult(
                        experiment_id=experiment_id,
                        mode=mode,
                        source_file=str(
                            source_file.resolve()
                        ),
                        imported_at=utc_now_iso(),
                        successful=True,
                        experiment_action="skipped",
                        table_results={
                            "experiments": ImportTableResult(
                                table_name="experiments",
                                skipped=1,
                            )
                        },
                    )

                table_results: dict[
                    str,
                    ImportTableResult,
                ] = {}

                if exists and mode == "replace":
                    deleted = self._delete_experiment_tree(
                        connection,
                        experiment_id,
                    )
                    table_results.update(deleted)

                experiment_result = (
                    table_results.setdefault(
                        "experiments",
                        ImportTableResult(
                            table_name="experiments"
                        ),
                    )
                )

                experiment_action = self._upsert_row(
                    connection=connection,
                    table_name="experiments",
                    row=experiment,
                    mode=(
                        "merge"
                        if mode == "merge"
                        else "insert"
                    ),
                )

                if experiment_action == "inserted":
                    experiment_result.inserted += 1
                elif experiment_action == "updated":
                    experiment_result.updated += 1
                else:
                    experiment_result.skipped += 1

                ordered_tables = self._order_related_tables(
                    connection,
                    related_data.keys(),
                )

                for table_name in ordered_tables:
                    rows = related_data.get(
                        table_name,
                        [],
                    )

                    result = table_results.setdefault(
                        table_name,
                        ImportTableResult(
                            table_name=table_name
                        ),
                    )

                    self._validate_table_exists(
                        connection,
                        table_name,
                    )

                    for row in rows:
                        action = self._upsert_row(
                            connection=connection,
                            table_name=table_name,
                            row=row,
                            mode=(
                                "merge"
                                if mode == "merge"
                                else "insert"
                            ),
                        )

                        if action == "inserted":
                            result.inserted += 1
                        elif action == "updated":
                            result.updated += 1
                        else:
                            result.skipped += 1

                connection.commit()

                return ExperimentImportResult(
                    experiment_id=experiment_id,
                    mode=mode,
                    source_file=str(
                        source_file.resolve()
                    ),
                    imported_at=utc_now_iso(),
                    successful=True,
                    experiment_action=(
                        "replaced"
                        if exists and mode == "replace"
                        else experiment_action
                    ),
                    table_results=table_results,
                )

            except Exception:
                connection.rollback()
                raise

    def _upsert_row(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        row: dict[str, Any],
        mode: str,
    ) -> str:
        table_columns = self._table_columns(
            connection,
            table_name,
        )

        unknown = set(row) - set(table_columns)
        if unknown:
            raise SchemaCompatibilityError(
                f"Unknown columns for {table_name}: "
                f"{sorted(unknown)}"
            )

        usable = {
            key: value
            for key, value in row.items()
            if key in table_columns
        }

        if not usable:
            raise SchemaCompatibilityError(
                f"No compatible columns for {table_name}."
            )

        primary_keys = self._primary_key_columns(
            connection,
            table_name,
        )

        if not primary_keys:
            return self._insert_row(
                connection,
                table_name,
                usable,
            )

        if not all(
            key in usable
            for key in primary_keys
        ):
            raise SchemaCompatibilityError(
                f"Primary key missing for {table_name}: "
                f"{primary_keys}"
            )

        exists = self._row_exists(
            connection,
            table_name,
            usable,
            primary_keys,
        )

        if not exists:
            return self._insert_row(
                connection,
                table_name,
                usable,
            )

        if mode != "merge":
            return "skipped"

        update_columns = [
            column
            for column in usable
            if column not in primary_keys
        ]

        if not update_columns:
            return "skipped"

        assignments = ", ".join(
            f"{quote_identifier(column)} = ?"
            for column in update_columns
        )

        where = " AND ".join(
            f"{quote_identifier(column)} = ?"
            for column in primary_keys
        )

        parameters = [
            usable[column]
            for column in update_columns
        ] + [
            usable[column]
            for column in primary_keys
        ]

        connection.execute(
            f"""
            UPDATE {quote_identifier(table_name)}
            SET {assignments}
            WHERE {where}
            """,
            tuple(parameters),
        )

        return "updated"

    def _insert_row(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        row: dict[str, Any],
    ) -> str:
        columns = list(row)
        placeholders = ", ".join(
            "?"
            for _ in columns
        )
        column_sql = ", ".join(
            quote_identifier(column)
            for column in columns
        )

        connection.execute(
            f"""
            INSERT INTO {quote_identifier(table_name)}
            ({column_sql})
            VALUES ({placeholders})
            """,
            tuple(
                row[column]
                for column in columns
            ),
        )

        return "inserted"

    def _delete_experiment_tree(
        self,
        connection: sqlite3.Connection,
        experiment_id: str,
    ) -> dict[str, ImportTableResult]:
        results: dict[
            str,
            ImportTableResult,
        ] = {}

        related_tables = self._tables_with_experiment_id(
            connection
        )

        for table_name in reversed(
            self._order_related_tables(
                connection,
                related_tables,
            )
        ):
            cursor = connection.execute(
                f"""
                DELETE FROM {quote_identifier(table_name)}
                WHERE experiment_id = ?
                """,
                (experiment_id,),
            )

            results[table_name] = ImportTableResult(
                table_name=table_name,
                deleted=max(
                    cursor.rowcount,
                    0,
                ),
            )

        cursor = connection.execute(
            """
            DELETE FROM experiments
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        )

        results["experiments"] = ImportTableResult(
            table_name="experiments",
            deleted=max(
                cursor.rowcount,
                0,
            ),
        )

        return results

    def _order_related_tables(
        self,
        connection: sqlite3.Connection,
        tables,
    ) -> list[str]:
        remaining = list(dict.fromkeys(tables))
        ordered: list[str] = []

        while remaining:
            progress = False

            for table_name in list(remaining):
                parents = self._foreign_key_parents(
                    connection,
                    table_name,
                )

                relevant_parents = {
                    parent
                    for parent in parents
                    if parent in remaining
                }

                if not relevant_parents:
                    ordered.append(table_name)
                    remaining.remove(table_name)
                    progress = True

            if not progress:
                ordered.extend(sorted(remaining))
                break

        return ordered

    def _foreign_key_parents(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> set[str]:
        rows = connection.execute(
            f"""
            PRAGMA foreign_key_list(
                {quote_identifier(table_name)}
            )
            """
        ).fetchall()

        return {
            str(row[2])
            for row in rows
        }

    def _experiment_exists(
        self,
        connection: sqlite3.Connection,
        experiment_id: str,
    ) -> bool:
        row = connection.execute(
            """
            SELECT 1
            FROM experiments
            WHERE experiment_id = ?
            LIMIT 1
            """,
            (experiment_id,),
        ).fetchone()

        return row is not None

    def _row_exists(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        row: dict[str, Any],
        primary_keys: list[str],
    ) -> bool:
        where = " AND ".join(
            f"{quote_identifier(column)} = ?"
            for column in primary_keys
        )

        result = connection.execute(
            f"""
            SELECT 1
            FROM {quote_identifier(table_name)}
            WHERE {where}
            LIMIT 1
            """,
            tuple(
                row[column]
                for column in primary_keys
            ),
        ).fetchone()

        return result is not None

    def _tables_with_experiment_id(
        self,
        connection: sqlite3.Connection,
    ) -> list[str]:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
              AND name != 'experiments'
            ORDER BY name
            """
        ).fetchall()

        result: list[str] = []

        for row in rows:
            table_name = str(row[0])
            if (
                "experiment_id"
                in self._table_columns(
                    connection,
                    table_name,
                )
            ):
                result.append(table_name)

        return result

    def _table_columns(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[str]:
        self._validate_table_exists(
            connection,
            table_name,
        )

        rows = connection.execute(
            f"""
            PRAGMA table_info(
                {quote_identifier(table_name)}
            )
            """
        ).fetchall()

        return [
            str(row[1])
            for row in rows
        ]

    def _primary_key_columns(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[str]:
        rows = connection.execute(
            f"""
            PRAGMA table_info(
                {quote_identifier(table_name)}
            )
            """
        ).fetchall()

        primary = [
            (
                int(row[5]),
                str(row[1]),
            )
            for row in rows
            if int(row[5]) > 0
        ]

        primary.sort(
            key=lambda item: item[0]
        )

        return [
            name
            for _, name in primary
        ]

    def _validate_table_exists(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> None:
        row = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        if row is None:
            raise SchemaCompatibilityError(
                f"Target table does not exist: "
                f"{table_name}"
            )

    def _validate_mode(
        self,
        mode: str,
    ) -> None:
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Unsupported import mode: {mode}. "
                f"Expected one of "
                f"{sorted(self.VALID_MODES)}"
            )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path)
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(
        self,
    ) -> None:
        initialize = getattr(
            self.database,
            "initialize",
            None,
        )
        if callable(initialize):
            initialize()

    def _resolve_database_path(
        self,
        database: Any,
    ) -> Path:
        if isinstance(
            database,
            (str, Path),
        ):
            return Path(database)

        for attribute_name in (
            "database_path",
            "db_path",
            "path",
            "filename",
        ):
            value = getattr(
                database,
                attribute_name,
                None,
            )

            if isinstance(
                value,
                (str, Path),
            ):
                return Path(value)

        raise TypeError(
            "Unable to resolve the SQLite database path."
        )
