from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(slots=True)
class TableHealth:
    table_name: str
    row_count: int
    index_count: int
    has_primary_key: bool

@dataclass(slots=True)
class ForeignKeyViolation:
    table_name: str
    row_id: int | None
    parent_table: str
    foreign_key_index: int

@dataclass(slots=True)
class DatabaseHealthReport:
    database_path: str
    generated_at: str
    sqlite_version: str
    journal_mode: str
    page_count: int
    page_size: int
    freelist_count: int
    database_size_bytes: int
    integrity_ok: bool
    quick_check_ok: bool
    foreign_key_ok: bool
    schema_version: str | None
    health_score: int
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    tables: list[TableHealth] = field(default_factory=list)
    foreign_key_violations: list[ForeignKeyViolation] = field(default_factory=list)

@dataclass(slots=True)
class MaintenanceResult:
    started_at: str
    completed_at: str
    analyze_completed: bool
    optimize_completed: bool
    vacuum_completed: bool
    orphan_rows_deleted: int
    health_report: DatabaseHealthReport
