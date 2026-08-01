from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import zipfile
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .csv_export_exceptions import CsvExportValidationError
from .csv_export_models import CsvExportResult, CsvFileResult
from .export_utils import (
    sanitize_name,
    sha256_file,
    timestamp_token,
    utc_now_iso,
    write_json,
)


class CsvExportService:
    """Export ACOS database and analytics data to CSV."""

    def __init__(
        self,
        database: Any,
        output_directory: str | Path,
    ) -> None:
        self.database = database
        self.database_path = self._resolve_database_path(database)
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def export_table(
        self,
        table_name: str,
        experiment_id: str | None = None,
        variant_name: str | None = None,
        filename: str | None = None,
    ) -> CsvFileResult:
        self._initialize_database()

        with closing(self._connect()) as connection:
            self._validate_table_exists(connection, table_name)
            columns = self._table_columns(connection, table_name)

            conditions: list[str] = []
            parameters: list[Any] = []

            if experiment_id is not None and "experiment_id" in columns:
                conditions.append("experiment_id = ?")
                parameters.append(experiment_id)

            if variant_name is not None and "variant_name" in columns:
                conditions.append("variant_name = ?")
                parameters.append(variant_name)

            where_sql = (
                " WHERE " + " AND ".join(conditions)
                if conditions
                else ""
            )

            safe_table = table_name.replace('"', '""')
            sql = f'SELECT * FROM "{safe_table}"{where_sql}'
            rows = connection.execute(
                sql,
                tuple(parameters),
            ).fetchall()
            data = [dict(row) for row in rows]

        output_name = (
            sanitize_name(filename)
            if filename
            else sanitize_name(table_name)
        )
        path = self.output_directory / f"{output_name}.csv"

        return self._write_csv(
            path=path,
            rows=data,
            preferred_headers=columns,
            result_name=table_name,
        )

    def export_all_tables(
        self,
        experiment_id: str | None = None,
        include_empty: bool = True,
        create_zip: bool = True,
        package_name: str | None = None,
    ) -> CsvExportResult:
        self._initialize_database()

        export_id = (
            sanitize_name(package_name)
            if package_name
            else f"csv_export_{timestamp_token()}"
        )
        package_directory = self.output_directory / export_id

        if package_directory.exists():
            shutil.rmtree(package_directory)
        package_directory.mkdir(parents=True, exist_ok=True)

        result = CsvExportResult(
            export_id=export_id,
            created_at=utc_now_iso(),
            output_directory=str(package_directory.resolve()),
        )

        with closing(self._connect()) as connection:
            tables = self._list_tables(connection)

        original_output = self.output_directory
        self.output_directory = package_directory

        try:
            for table_name in tables:
                file_result = self.export_table(
                    table_name=table_name,
                    experiment_id=experiment_id,
                )
                if include_empty or file_result.row_count > 0:
                    result.files[table_name] = file_result
                else:
                    Path(file_result.path).unlink(missing_ok=True)

            manifest_path = package_directory / "manifest.json"
            manifest_payload = {
                "export_id": result.export_id,
                "created_at": result.created_at,
                "experiment_id": experiment_id,
                "total_rows": result.total_rows,
                "files": {
                    name: asdict(item)
                    for name, item in result.files.items()
                },
            }
            write_json(manifest_path, manifest_payload)
            result.manifest_file = str(manifest_path.resolve())

            if create_zip:
                zip_path = original_output / f"{export_id}.zip"
                if zip_path.exists():
                    zip_path.unlink()

                with zipfile.ZipFile(
                    zip_path,
                    "w",
                    zipfile.ZIP_DEFLATED,
                ) as archive:
                    for path in package_directory.rglob("*"):
                        if path.is_file():
                            archive.write(
                                path,
                                path.relative_to(package_directory),
                            )

                result.zip_file = str(zip_path.resolve())

            return result
        finally:
            self.output_directory = original_output

    def export_records(
        self,
        name: str,
        records: Iterable[dict[str, Any]],
        filename: str | None = None,
    ) -> CsvFileResult:
        rows = list(records)
        output_name = (
            sanitize_name(filename)
            if filename
            else sanitize_name(name)
        )
        path = self.output_directory / f"{output_name}.csv"

        return self._write_csv(
            path=path,
            rows=rows,
            preferred_headers=None,
            result_name=name,
        )

    def export_statistics(
        self,
        statistics: Any,
        name: str = "statistics",
    ) -> CsvFileResult:
        payload = self._to_plain_data(statistics)
        rows = self._flatten_mapping(payload)
        return self.export_records(name=name, records=rows)

    def export_leaderboard(
        self,
        entries: Iterable[Any],
        name: str = "leaderboard",
    ) -> CsvFileResult:
        rows = [self._to_plain_data(item) for item in entries]
        return self.export_records(name=name, records=rows)

    def export_trend(
        self,
        trend: Any,
        name: str = "trend",
    ) -> CsvFileResult:
        payload = self._to_plain_data(trend)

        if isinstance(payload, dict):
            if isinstance(payload.get("points"), list):
                rows = payload["points"]
            else:
                rows = self._flatten_mapping(payload)
        elif isinstance(payload, list):
            rows = payload
        else:
            rows = [{"value": payload}]

        return self.export_records(name=name, records=rows)

    def validate_csv(
        self,
        csv_file: str | Path,
        expected_headers: list[str] | None = None,
        expected_rows: int | None = None,
    ) -> bool:
        path = Path(csv_file)
        if not path.exists():
            raise CsvExportValidationError(
                f"CSV file not found: {path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                rows = list(csv.reader(handle))
        except OSError as exc:
            raise CsvExportValidationError(
                "Unable to read CSV file."
            ) from exc

        if not rows:
            raise CsvExportValidationError("CSV file is empty.")

        headers = rows[0]
        data_rows = rows[1:]

        if expected_headers is not None and headers != expected_headers:
            raise CsvExportValidationError("CSV header mismatch.")

        if expected_rows is not None and len(data_rows) != expected_rows:
            raise CsvExportValidationError("CSV row-count mismatch.")

        return True

    def validate_zip(self, zip_file: str | Path) -> bool:
        path = Path(zip_file)
        if not path.exists():
            raise CsvExportValidationError(
                f"CSV ZIP not found: {path}"
            )

        try:
            with zipfile.ZipFile(path, "r") as archive:
                names = set(archive.namelist())

                if "manifest.json" not in names:
                    raise CsvExportValidationError(
                        "CSV ZIP is missing manifest.json."
                    )

                if not any(name.endswith(".csv") for name in names):
                    raise CsvExportValidationError(
                        "CSV ZIP contains no CSV files."
                    )

                bad_file = archive.testzip()
                if bad_file is not None:
                    raise CsvExportValidationError(
                        f"Corrupt ZIP member: {bad_file}"
                    )
        except CsvExportValidationError:
            raise
        except zipfile.BadZipFile as exc:
            raise CsvExportValidationError(
                "Invalid CSV ZIP package."
            ) from exc

        return True

    def _write_csv(
        self,
        path: Path,
        rows: list[dict[str, Any]],
        preferred_headers: list[str] | None,
        result_name: str,
    ) -> CsvFileResult:
        path.parent.mkdir(parents=True, exist_ok=True)
        headers = (
            list(preferred_headers)
            if preferred_headers
            else self._discover_headers(rows)
        )

        with path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=headers,
                extrasaction="ignore",
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        key: self._format_value(row.get(key))
                        for key in headers
                    }
                )

        return CsvFileResult(
            name=result_name,
            path=str(path.resolve()),
            row_count=len(rows),
            column_count=len(headers),
            sha256=sha256_file(path),
        )

    def _discover_headers(
        self,
        rows: list[dict[str, Any]],
    ) -> list[str]:
        headers: list[str] = []
        for row in rows:
            for key in row:
                if key not in headers:
                    headers.append(key)
        return headers or ["value"]

    def _format_value(self, value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple, set)):
            return json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
        if isinstance(value, bool):
            return "true" if value else "false"
        return value

    def _to_plain_data(self, value: Any) -> Any:
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        if isinstance(value, dict):
            return {
                key: self._to_plain_data(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._to_plain_data(item) for item in value]
        if hasattr(value, "to_dict"):
            return value.to_dict()
        return value

    def _flatten_mapping(
        self,
        payload: dict[str, Any],
        prefix: str = "",
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for key, value in payload.items():
            metric = f"{prefix}.{key}" if prefix else str(key)

            if isinstance(value, dict):
                rows.extend(
                    self._flatten_mapping(value, metric)
                )
            else:
                rows.append(
                    {"metric": metric, "value": value}
                )

        return rows

    def _list_tables(
        self,
        connection: sqlite3.Connection,
    ) -> list[str]:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        return [str(row[0]) for row in rows]

    def _table_columns(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[str]:
        safe_table = table_name.replace('"', '""')
        rows = connection.execute(
            f'PRAGMA table_info("{safe_table}")'
        ).fetchall()
        return [str(row[1]) for row in rows]

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
            raise CsvExportValidationError(
                f"Database table not found: {table_name}"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        initialize = getattr(self.database, "initialize", None)
        if callable(initialize):
            initialize()

    def _resolve_database_path(self, database: Any) -> Path:
        if isinstance(database, (str, Path)):
            return Path(database)

        for attribute in (
            "database_path",
            "db_path",
            "path",
            "filename",
        ):
            value = getattr(database, attribute, None)
            if isinstance(value, (str, Path)):
                return Path(value)

        raise TypeError("Unable to resolve database path.")
