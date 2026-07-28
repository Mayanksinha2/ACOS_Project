from __future__ import annotations

import csv
import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .maintenance_exceptions import DatabaseIntegrityError, MaintenanceValidationError
from .maintenance_models import (
    DatabaseHealthReport,
    ForeignKeyViolation,
    MaintenanceResult,
    TableHealth,
)


class DatabaseMaintenanceService:
    def __init__(self, database: Any) -> None:
        self.database = database
        self.database_path = self._resolve_database_path(database)

    def health_report(self) -> DatabaseHealthReport:
        self._initialize_database()
        with closing(self._connect()) as connection:
            integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
            quick_rows = connection.execute("PRAGMA quick_check").fetchall()
            foreign_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
            integrity_ok = self._pragma_ok(integrity_rows)
            quick_ok = self._pragma_ok(quick_rows)
            foreign_ok = len(foreign_rows) == 0
            journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
            page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
            page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
            freelist_count = int(connection.execute("PRAGMA freelist_count").fetchone()[0])
            sqlite_version = str(connection.execute("SELECT sqlite_version()").fetchone()[0])
            tables = self._table_health(connection)
            schema_version = self._read_schema_version(connection)
            violations = [
                ForeignKeyViolation(
                    table_name=str(row[0]),
                    row_id=int(row[1]) if row[1] is not None else None,
                    parent_table=str(row[2]),
                    foreign_key_index=int(row[3]),
                )
                for row in foreign_rows
            ]

        warnings = []
        recommendations = []
        score = 100

        if not integrity_ok:
            warnings.append("Database integrity check failed.")
            recommendations.append("Restore from a verified backup.")
            score -= 50
        if not quick_ok:
            warnings.append("Database quick check failed.")
            score -= 20
        if not foreign_ok:
            warnings.append(f"Detected {len(violations)} foreign-key violation(s).")
            recommendations.append("Review or clean orphaned child records.")
            score -= min(30, len(violations) * 5)
        if page_count > 0 and freelist_count / page_count >= 0.20:
            warnings.append("High free-page ratio detected.")
            recommendations.append("Run VACUUM to reclaim unused space.")
            score -= 10
        if not tables:
            warnings.append("No application tables were detected.")
            score -= 10

        return DatabaseHealthReport(
            database_path=str(self.database_path.resolve()),
            generated_at=self._utc_now(),
            sqlite_version=sqlite_version,
            journal_mode=journal_mode,
            page_count=page_count,
            page_size=page_size,
            freelist_count=freelist_count,
            database_size_bytes=page_count * page_size,
            integrity_ok=integrity_ok,
            quick_check_ok=quick_ok,
            foreign_key_ok=foreign_ok,
            schema_version=schema_version,
            health_score=max(0, min(100, score)),
            warnings=warnings,
            recommendations=recommendations,
            tables=tables,
            foreign_key_violations=violations,
        )

    def integrity_check(self, quick: bool = False) -> bool:
        pragma = "PRAGMA quick_check" if quick else "PRAGMA integrity_check"
        with closing(self._connect()) as connection:
            rows = connection.execute(pragma).fetchall()
        if not self._pragma_ok(rows):
            raise DatabaseIntegrityError("SQLite integrity validation failed.")
        return True

    def foreign_key_check(self) -> list[ForeignKeyViolation]:
        with closing(self._connect()) as connection:
            rows = connection.execute("PRAGMA foreign_key_check").fetchall()
        return [
            ForeignKeyViolation(
                table_name=str(row[0]),
                row_id=int(row[1]) if row[1] is not None else None,
                parent_table=str(row[2]),
                foreign_key_index=int(row[3]),
            )
            for row in rows
        ]

    def analyze(self) -> bool:
        with closing(self._connect()) as connection:
            connection.execute("ANALYZE")
            connection.commit()
        return True

    def optimize(self) -> bool:
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA optimize")
            connection.commit()
        return True

    def vacuum(self) -> bool:
        with closing(self._connect()) as connection:
            connection.execute("VACUUM")
        return True

    def detect_orphans(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            result = {}
            for rel in self._relationships(connection):
                key = f"{rel['child_table']}.{rel['child_column']} -> {rel['parent_table']}.{rel['parent_column']}"
                sql = (
                    f"SELECT COUNT(*) FROM {self._q(rel['child_table'])} "
                    f"WHERE {self._q(rel['child_column'])} IS NOT NULL "
                    f"AND NOT EXISTS (SELECT 1 FROM {self._q(rel['parent_table'])} "
                    f"WHERE {self._q(rel['parent_table'])}.{self._q(rel['parent_column'])} = "
                    f"{self._q(rel['child_table'])}.{self._q(rel['child_column'])})"
                )
                result[key] = int(connection.execute(sql).fetchone()[0])
            return result

    def cleanup_orphans(self) -> int:
        deleted = 0
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            try:
                connection.execute("BEGIN")
                for rel in self._relationships(connection):
                    sql = (
                        f"DELETE FROM {self._q(rel['child_table'])} "
                        f"WHERE {self._q(rel['child_column'])} IS NOT NULL "
                        f"AND NOT EXISTS (SELECT 1 FROM {self._q(rel['parent_table'])} "
                        f"WHERE {self._q(rel['parent_table'])}.{self._q(rel['parent_column'])} = "
                        f"{self._q(rel['child_table'])}.{self._q(rel['child_column'])})"
                    )
                    cursor = connection.execute(sql)
                    if cursor.rowcount and cursor.rowcount > 0:
                        deleted += cursor.rowcount
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.execute("PRAGMA foreign_keys = ON")
        return deleted

    def run_maintenance(
        self,
        cleanup_orphans: bool = False,
        run_vacuum: bool = False,
    ) -> MaintenanceResult:
        started = self._utc_now()
        self.integrity_check(quick=True)
        analyzed = self.analyze()
        optimized = self.optimize()
        deleted = self.cleanup_orphans() if cleanup_orphans else 0
        vacuumed = self.vacuum() if run_vacuum else False
        report = self.health_report()
        return MaintenanceResult(
            started_at=started,
            completed_at=self._utc_now(),
            analyze_completed=analyzed,
            optimize_completed=optimized,
            vacuum_completed=vacuumed,
            orphan_rows_deleted=deleted,
            health_report=report,
        )

    def export_health_json(self, output_file, report=None) -> str:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(report or self.health_report()), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(path.resolve())

    def export_health_csv(self, output_file, report=None) -> str:
        current = report or self.health_report()
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            ("database_path", current.database_path),
            ("generated_at", current.generated_at),
            ("sqlite_version", current.sqlite_version),
            ("journal_mode", current.journal_mode),
            ("database_size_bytes", current.database_size_bytes),
            ("integrity_ok", current.integrity_ok),
            ("quick_check_ok", current.quick_check_ok),
            ("foreign_key_ok", current.foreign_key_ok),
            ("health_score", current.health_score),
            ("warnings", " | ".join(current.warnings)),
            ("recommendations", " | ".join(current.recommendations)),
        ]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["metric", "value"])
            writer.writerows(rows)
        return str(path.resolve())

    def export_health_text(self, output_file, report=None) -> str:
        current = report or self.health_report()
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "ACOS DATABASE HEALTH REPORT",
            "=" * 80,
            f"Database: {current.database_path}",
            f"Generated: {current.generated_at}",
            f"Health score: {current.health_score}/100",
            f"Integrity OK: {current.integrity_ok}",
            f"Quick check OK: {current.quick_check_ok}",
            f"Foreign keys OK: {current.foreign_key_ok}",
            "",
            "Warnings:",
        ]
        lines.extend([f"- {x}" for x in current.warnings] or ["- None"])
        lines.extend(["", "Recommendations:"])
        lines.extend([f"- {x}" for x in current.recommendations] or ["- None"])
        lines.extend(["", "Tables:"])
        for table in current.tables:
            lines.append(
                f"- {table.table_name}: rows={table.row_count}, "
                f"indexes={table.index_count}, primary_key={table.has_primary_key}"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path.resolve())

    def _relationships(self, connection):
        result = []
        for table in self._list_tables(connection):
            for row in connection.execute(
                f"PRAGMA foreign_key_list({self._q(table)})"
            ).fetchall():
                result.append({
                    "child_table": table,
                    "child_column": str(row[3]),
                    "parent_table": str(row[2]),
                    "parent_column": str(row[4]),
                })
        return result

    def _table_health(self, connection):
        result = []
        for table in self._list_tables(connection):
            count = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM {self._q(table)}"
                ).fetchone()[0]
            )
            indexes = len(
                connection.execute(
                    f"PRAGMA index_list({self._q(table)})"
                ).fetchall()
            )
            info = connection.execute(
                f"PRAGMA table_info({self._q(table)})"
            ).fetchall()
            result.append(
                TableHealth(
                    table_name=table,
                    row_count=count,
                    index_count=indexes,
                    has_primary_key=any(int(row[5]) > 0 for row in info),
                )
            )
        return result

    def _read_schema_version(self, connection):
        tables = set(self._list_tables(connection))
        for table in ("schema_metadata", "database_metadata", "metadata"):
            if table not in tables:
                continue
            columns = {
                str(row[1])
                for row in connection.execute(
                    f"PRAGMA table_info({self._q(table)})"
                ).fetchall()
            }
            if {"key", "value"}.issubset(columns):
                row = connection.execute(
                    f"SELECT value FROM {self._q(table)} "
                    "WHERE key IN ('schema_version', 'version') LIMIT 1"
                ).fetchone()
                if row is not None:
                    return str(row[0])
            if "schema_version" in columns:
                row = connection.execute(
                    f"SELECT schema_version FROM {self._q(table)} LIMIT 1"
                ).fetchone()
                if row is not None:
                    return str(row[0])
        return None

    def _list_tables(self, connection):
        rows = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [str(row[0]) for row in rows]

    def _pragma_ok(self, rows) -> bool:
        return len(rows) == 1 and str(rows[0][0]).lower() == "ok"

    def _connect(self):
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self):
        initialize = getattr(self.database, "initialize", None)
        if callable(initialize):
            initialize()

    def _resolve_database_path(self, database):
        if isinstance(database, (str, Path)):
            return Path(database)
        for name in ("database_path", "db_path", "path", "filename"):
            value = getattr(database, name, None)
            if isinstance(value, (str, Path)):
                return Path(value)
        raise MaintenanceValidationError("Unable to resolve SQLite database path.")

    def _q(self, identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
