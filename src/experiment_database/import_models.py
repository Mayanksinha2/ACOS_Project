from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ImportTableResult:
    table_name: str
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0


@dataclass(slots=True)
class ExperimentImportResult:
    experiment_id: str
    mode: str
    source_file: str
    imported_at: str
    successful: bool
    experiment_action: str
    table_results: dict[str, ImportTableResult] = field(
        default_factory=dict
    )

    @property
    def total_inserted(self) -> int:
        return sum(
            result.inserted
            for result in self.table_results.values()
        )

    @property
    def total_updated(self) -> int:
        return sum(
            result.updated
            for result in self.table_results.values()
        )

    @property
    def total_skipped(self) -> int:
        return sum(
            result.skipped
            for result in self.table_results.values()
        )

    @property
    def total_deleted(self) -> int:
        return sum(
            result.deleted
            for result in self.table_results.values()
        )
