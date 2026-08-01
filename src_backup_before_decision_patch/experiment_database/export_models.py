from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExportManifest:
    export_id: str
    experiment_id: str
    created_at: str
    schema_version: int | None
    format_version: str
    table_counts: dict[str, int] = field(
        default_factory=dict
    )
    files: dict[str, str] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class ExperimentExportPackage:
    manifest: ExportManifest
    experiment: dict[str, Any]
    related_data: dict[
        str,
        list[dict[str, Any]],
    ] = field(default_factory=dict)


@dataclass(slots=True)
class ExportResult:
    experiment_id: str
    json_file: str
    zip_file: str | None
    manifest_file: str
    created_at: str
    total_records: int
