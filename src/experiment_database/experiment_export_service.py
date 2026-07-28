from __future__ import annotations

import json
import shutil
import sqlite3
import zipfile
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .export_exceptions import (
    ExperimentNotFoundError,
    ExportValidationError,
)
from .export_models import (
    ExperimentExportPackage,
    ExportManifest,
    ExportResult,
)
from .export_utils import (
    sanitize_name,
    sha256_file,
    timestamp_token,
    utc_now_iso,
    write_json,
)


class ExperimentExportService:
    """
    Exports an experiment and all related records to
    portable JSON and ZIP packages.

    Related tables are discovered automatically when
    they contain an experiment_id column.
    """

    FORMAT_VERSION = "1.0"

    def __init__(
        self,
        database: Any,
        export_directory: str | Path,
    ) -> None:
        self.database = database

        self.database_path = (
            self._resolve_database_path(database)
        )

        self.export_directory = Path(
            export_directory
        )

        self.export_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def build_package(
        self,
        experiment_id: str,
    ) -> ExperimentExportPackage:
        """
        Build an in-memory export package for one
        experiment.
        """

        self._initialize_database()

        # contextlib.closing guarantees that the
        # SQLite connection is closed on Windows.
        with closing(
            self._connect()
        ) as connection:
            experiment = self._fetch_experiment(
                connection=connection,
                experiment_id=experiment_id,
            )

            related_data: dict[
                str,
                list[dict[str, Any]],
            ] = {}

            related_tables = self._related_tables(
                connection
            )

            for table_name in related_tables:
                rows = self._fetch_related_rows(
                    connection=connection,
                    table_name=table_name,
                    experiment_id=experiment_id,
                )

                related_data[table_name] = rows

            table_counts = {
                "experiments": 1,
                **{
                    table_name: len(rows)
                    for table_name, rows
                    in related_data.items()
                },
            }

            manifest = ExportManifest(
                export_id=(
                    "export_"
                    f"{sanitize_name(experiment_id)}_"
                    f"{timestamp_token()}"
                ),
                experiment_id=experiment_id,
                created_at=utc_now_iso(),
                schema_version=(
                    self._read_schema_version(
                        connection
                    )
                ),
                format_version=self.FORMAT_VERSION,
                table_counts=table_counts,
            )

            return ExperimentExportPackage(
                manifest=manifest,
                experiment=experiment,
                related_data=related_data,
            )

    def export_json(
        self,
        experiment_id: str,
        filename: str | None = None,
    ) -> ExportResult:
        """
        Export an experiment to a JSON file and an
        external manifest file.
        """

        package = self.build_package(
            experiment_id
        )

        base_name = (
            sanitize_name(filename)
            if filename
            else package.manifest.export_id
        )

        if not base_name:
            base_name = package.manifest.export_id

        json_path = (
            self.export_directory
            / f"{base_name}.json"
        )

        manifest_path = (
            self.export_directory
            / f"{base_name}.manifest.json"
        )

        payload = self._package_to_dict(
            package
        )

        write_json(
            json_path,
            payload,
        )

        package.manifest.files = {
            json_path.name: sha256_file(
                json_path
            )
        }

        write_json(
            manifest_path,
            asdict(package.manifest),
        )

        total_records = sum(
            package.manifest
            .table_counts
            .values()
        )

        return ExportResult(
            experiment_id=experiment_id,
            json_file=str(
                json_path.resolve()
            ),
            zip_file=None,
            manifest_file=str(
                manifest_path.resolve()
            ),
            created_at=(
                package.manifest.created_at
            ),
            total_records=total_records,
        )

    def export_zip(
        self,
        experiment_id: str,
        filename: str | None = None,
        include_pretty_json: bool = True,
    ) -> ExportResult:
        """
        Export an experiment to a portable ZIP file.

        The ZIP package contains:

        - experiment.json
        - manifest.json
        """

        package = self.build_package(
            experiment_id
        )

        base_name = (
            sanitize_name(filename)
            if filename
            else package.manifest.export_id
        )

        if not base_name:
            base_name = package.manifest.export_id

        working_directory = (
            self.export_directory
            / f".{base_name}_tmp"
        )

        if working_directory.exists():
            shutil.rmtree(
                working_directory,
                ignore_errors=True,
            )

        working_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        zip_path = (
            self.export_directory
            / f"{base_name}.zip"
        )

        external_manifest_path = (
            self.export_directory
            / f"{base_name}.manifest.json"
        )

        try:
            internal_json_path = (
                working_directory
                / "experiment.json"
            )

            internal_manifest_path = (
                working_directory
                / "manifest.json"
            )

            payload = self._package_to_dict(
                package
            )

            if include_pretty_json:
                write_json(
                    internal_json_path,
                    payload,
                )
            else:
                internal_json_path.write_text(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        default=str,
                    ),
                    encoding="utf-8",
                )

            package.manifest.files = {
                internal_json_path.name: (
                    sha256_file(
                        internal_json_path
                    )
                )
            }

            write_json(
                internal_manifest_path,
                asdict(package.manifest),
            )

            if zip_path.exists():
                zip_path.unlink()

            with zipfile.ZipFile(
                zip_path,
                mode="w",
                compression=(
                    zipfile.ZIP_DEFLATED
                ),
            ) as archive:
                archive.write(
                    internal_json_path,
                    arcname="experiment.json",
                )

                archive.write(
                    internal_manifest_path,
                    arcname="manifest.json",
                )

            package.manifest.files[
                zip_path.name
            ] = sha256_file(zip_path)

            write_json(
                external_manifest_path,
                asdict(package.manifest),
            )

            total_records = sum(
                package.manifest
                .table_counts
                .values()
            )

            return ExportResult(
                experiment_id=experiment_id,

                # This identifies the JSON file stored
                # inside the ZIP package.
                json_file=(
                    f"{zip_path.resolve()}"
                    "::experiment.json"
                ),

                zip_file=str(
                    zip_path.resolve()
                ),

                manifest_file=str(
                    external_manifest_path.resolve()
                ),

                created_at=(
                    package.manifest.created_at
                ),

                total_records=total_records,
            )

        finally:
            shutil.rmtree(
                working_directory,
                ignore_errors=True,
            )

    def validate_export_json(
        self,
        json_file: str | Path,
    ) -> bool:
        """
        Validate the structure of an exported JSON
        package.
        """

        path = Path(json_file)

        if not path.exists():
            raise ExportValidationError(
                f"Export file not found: {path}"
            )

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise ExportValidationError(
                "Invalid export JSON."
            ) from exc

        required_sections = {
            "manifest",
            "experiment",
            "related_data",
        }

        if not required_sections.issubset(
            payload.keys()
        ):
            raise ExportValidationError(
                "Export JSON is missing one or "
                "more required sections."
            )

        manifest = payload["manifest"]
        experiment = payload["experiment"]
        related_data = payload["related_data"]

        if not isinstance(
            manifest,
            dict,
        ):
            raise ExportValidationError(
                "The manifest section must be "
                "an object."
            )

        if not isinstance(
            experiment,
            dict,
        ):
            raise ExportValidationError(
                "The experiment section must be "
                "an object."
            )

        if not isinstance(
            related_data,
            dict,
        ):
            raise ExportValidationError(
                "The related_data section must be "
                "an object."
            )

        if (
            manifest.get("format_version")
            != self.FORMAT_VERSION
        ):
            raise ExportValidationError(
                "Unsupported export format version."
            )

        manifest_experiment_id = (
            manifest.get("experiment_id")
        )

        actual_experiment_id = (
            experiment.get("experiment_id")
        )

        if (
            actual_experiment_id
            != manifest_experiment_id
        ):
            raise ExportValidationError(
                "Experiment ID mismatch between "
                "the manifest and experiment data."
            )

        return True

    def validate_export_zip(
        self,
        zip_file: str | Path,
    ) -> bool:
        """
        Validate a portable experiment ZIP package.
        """

        path = Path(zip_file)

        if not path.exists():
            raise ExportValidationError(
                f"Export ZIP not found: {path}"
            )

        try:
            with zipfile.ZipFile(
                path,
                mode="r",
            ) as archive:
                names = set(
                    archive.namelist()
                )

                required_files = {
                    "experiment.json",
                    "manifest.json",
                }

                if not required_files.issubset(
                    names
                ):
                    raise ExportValidationError(
                        "ZIP package is missing one "
                        "or more required files."
                    )

                bad_file = archive.testzip()

                if bad_file is not None:
                    raise ExportValidationError(
                        "ZIP integrity validation "
                        f"failed for: {bad_file}"
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

        except ExportValidationError:
            raise

        except (
            zipfile.BadZipFile,
            json.JSONDecodeError,
            UnicodeDecodeError,
            OSError,
        ) as exc:
            raise ExportValidationError(
                "Invalid export ZIP package."
            ) from exc

        payload_manifest = payload.get(
            "manifest",
            {}
        )

        payload_experiment = payload.get(
            "experiment",
            {}
        )

        if (
            payload_manifest.get(
                "experiment_id"
            )
            != manifest.get(
                "experiment_id"
            )
        ):
            raise ExportValidationError(
                "ZIP manifest experiment ID "
                "mismatch."
            )

        if (
            payload_experiment.get(
                "experiment_id"
            )
            != manifest.get(
                "experiment_id"
            )
        ):
            raise ExportValidationError(
                "ZIP experiment data does not "
                "match the manifest."
            )

        if (
            manifest.get("format_version")
            != self.FORMAT_VERSION
        ):
            raise ExportValidationError(
                "Unsupported ZIP export format "
                "version."
            )

        return True

    def _package_to_dict(
        self,
        package: ExperimentExportPackage,
    ) -> dict[str, Any]:
        """
        Convert an export package dataclass into a
        JSON-serializable dictionary.
        """

        return {
            "manifest": asdict(
                package.manifest
            ),
            "experiment": (
                package.experiment
            ),
            "related_data": (
                package.related_data
            ),
        }

    def _fetch_experiment(
        self,
        connection: sqlite3.Connection,
        experiment_id: str,
    ) -> dict[str, Any]:
        """
        Fetch the experiment record.
        """

        row = connection.execute(
            """
            SELECT *
            FROM experiments
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        ).fetchone()

        if row is None:
            raise ExperimentNotFoundError(
                "Experiment not found: "
                f"{experiment_id}"
            )

        return dict(row)

    def _related_tables(
        self,
        connection: sqlite3.Connection,
    ) -> list[str]:
        """
        Discover tables that contain an experiment_id
        column.
        """

        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
              AND name != 'experiments'
            ORDER BY name
            """
        ).fetchall()

        table_names = [
            str(row[0])
            for row in table_rows
        ]

        related_tables: list[str] = []

        for table_name in table_names:
            safe_table_name = (
                table_name.replace(
                    '"',
                    '""',
                )
            )

            column_rows = connection.execute(
                f"""
                PRAGMA table_info(
                    "{safe_table_name}"
                )
                """
            ).fetchall()

            columns = {
                str(row[1])
                for row in column_rows
            }

            if "experiment_id" in columns:
                related_tables.append(
                    table_name
                )

        return related_tables

    def _fetch_related_rows(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        experiment_id: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch all records for an experiment from one
        related table.
        """

        safe_table_name = table_name.replace(
            '"',
            '""',
        )

        rows = connection.execute(
            f"""
            SELECT *
            FROM "{safe_table_name}"
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def _read_schema_version(
        self,
        connection: sqlite3.Connection,
    ) -> int | None:
        """
        Read the latest database schema version.
        """

        table_row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'schema_migrations'
            """
        ).fetchone()

        if table_row is None:
            return None

        columns = {
            str(row[1])
            for row in connection.execute(
                """
                PRAGMA table_info(
                    schema_migrations
                )
                """
            ).fetchall()
        }

        for candidate_column in (
            "version",
            "schema_version",
        ):
            if candidate_column not in columns:
                continue

            result = connection.execute(
                f"""
                SELECT MAX({candidate_column})
                FROM schema_migrations
                """
            ).fetchone()

            if (
                result is not None
                and result[0] is not None
            ):
                return int(result[0])

        return None

    def _connect(
        self,
    ) -> sqlite3.Connection:
        """
        Create a SQLite connection.

        The caller must close this connection.
        """

        connection = sqlite3.connect(
            str(self.database_path)
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize_database(
        self,
    ) -> None:
        """
        Initialize the database when an
        ExperimentDatabase object was supplied.
        """

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
        """
        Resolve a database path from either a direct
        path or an ExperimentDatabase-like object.
        """

        if isinstance(
            database,
            (str, Path),
        ):
            return Path(database)

        candidate_attributes = (
            "database_path",
            "db_path",
            "path",
            "filename",
        )

        for attribute_name in candidate_attributes:
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
            "Unable to resolve the SQLite database "
            "path. Pass the database path directly, "
            "or provide an object exposing "
            "database_path, db_path, path, or "
            "filename."
        )