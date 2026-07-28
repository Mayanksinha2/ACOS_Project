from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(slots=True)
class CsvFileResult:
    name: str
    path: str
    row_count: int
    column_count: int
    sha256: str

@dataclass(slots=True)
class CsvExportResult:
    export_id: str
    created_at: str
    output_directory: str
    files: dict[str, CsvFileResult] = field(default_factory=dict)
    zip_file: str | None = None
    manifest_file: str | None = None

    @property
    def total_rows(self) -> int:
        return sum(item.row_count for item in self.files.values())
