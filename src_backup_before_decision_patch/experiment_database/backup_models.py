from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BackupMetadata:
    backup_id: str
    source_database: str
    backup_database: str
    metadata_file: str
    created_at: str
    database_size_bytes: int
    backup_size_bytes: int
    sha256: str
    integrity_status: str
    schema_version: int | None = None


@dataclass(slots=True)
class RestoreResult:
    backup_database: str
    restored_database: str
    restored_at: str
    pre_restore_backup: str | None
    integrity_status: str
    successful: bool
