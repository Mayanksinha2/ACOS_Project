from __future__ import annotations

import json
import os
import shutil
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .backup_exceptions import (
    BackupIntegrityError,
    BackupNotFoundError,
    RestoreError,
)
from .backup_models import (
    BackupMetadata,
    RestoreResult,
)
from .backup_utils import (
    read_schema_version,
    sha256_file,
    sqlite_integrity_check,
    timestamp_token,
    utc_now_iso,
    write_json,
)


class DatabaseBackupManager:
    """
    Creates verified SQLite backups and restores them
    safely.

    The manager accepts either an ExperimentDatabase
    instance or a direct database path.
    """

    def __init__(
        self,
        database: Any,
        backup_directory: str | Path,
        retention_count: int | None = None,
    ) -> None:
        self.database = database
        self.database_path = (
            self._resolve_database_path(database)
        )
        self.backup_directory = Path(
            backup_directory
        )
        self.retention_count = retention_count

        if (
            retention_count is not None
            and retention_count <= 0
        ):
            raise ValueError(
                "retention_count must be greater "
                "than zero."
            )

        self.backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def create_backup(
        self,
        label: str | None = None,
        verify_integrity: bool = True,
        apply_retention: bool = True,
    ) -> BackupMetadata:
        self._initialize_database()

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: "
                f"{self.database_path}"
            )

        source_integrity = sqlite_integrity_check(
            self.database_path
        )

        if (
            verify_integrity
            and source_integrity.lower() != "ok"
        ):
            raise BackupIntegrityError(
                "Source database integrity check "
                f"failed: {source_integrity}"
            )

        token = timestamp_token()
        safe_label = self._sanitize_label(label)
        backup_id = (
            f"backup_{token}"
            if not safe_label
            else f"backup_{safe_label}_{token}"
        )

        backup_path = (
            self.backup_directory
            / f"{backup_id}.sqlite3"
        )
        metadata_path = (
            self.backup_directory
            / f"{backup_id}.json"
        )

        temporary_path = backup_path.with_suffix(
            ".sqlite3.tmp"
        )

        self._sqlite_backup(
            self.database_path,
            temporary_path,
        )

        backup_integrity = sqlite_integrity_check(
            temporary_path
        )

        if (
            verify_integrity
            and backup_integrity.lower() != "ok"
        ):
            temporary_path.unlink(
                missing_ok=True
            )
            raise BackupIntegrityError(
                "Backup database integrity check "
                f"failed: {backup_integrity}"
            )

        os.replace(
            temporary_path,
            backup_path,
        )

        metadata = BackupMetadata(
            backup_id=backup_id,
            source_database=str(
                self.database_path.resolve()
            ),
            backup_database=str(
                backup_path.resolve()
            ),
            metadata_file=str(
                metadata_path.resolve()
            ),
            created_at=utc_now_iso(),
            database_size_bytes=(
                self.database_path.stat().st_size
            ),
            backup_size_bytes=(
                backup_path.stat().st_size
            ),
            sha256=sha256_file(backup_path),
            integrity_status=backup_integrity,
            schema_version=read_schema_version(
                backup_path
            ),
        )

        write_json(
            metadata_path,
            asdict(metadata),
        )

        if apply_retention:
            self.rotate_backups()

        return metadata

    def restore_backup(
        self,
        backup_path: str | Path,
        create_pre_restore_backup: bool = True,
        verify_integrity: bool = True,
    ) -> RestoreResult:
        source_backup = Path(backup_path)

        if not source_backup.exists():
            raise BackupNotFoundError(
                f"Backup not found: "
                f"{source_backup}"
            )

        expected_hash = self._expected_hash(
            source_backup
        )

        if expected_hash is not None:
            actual_hash = sha256_file(
                source_backup
            )
            if actual_hash != expected_hash:
                raise BackupIntegrityError(
                    "Backup checksum validation "
                    "failed."
                )

        backup_integrity = sqlite_integrity_check(
            source_backup
        )

        if (
            verify_integrity
            and backup_integrity.lower() != "ok"
        ):
            raise BackupIntegrityError(
                "Backup integrity check failed: "
                f"{backup_integrity}"
            )

        pre_restore_backup: str | None = None

        if (
            create_pre_restore_backup
            and self.database_path.exists()
        ):
            pre_restore = self.create_backup(
                label="pre_restore",
                verify_integrity=verify_integrity,
                apply_retention=False,
            )
            pre_restore_backup = (
                pre_restore.backup_database
            )

        restore_temp = (
            self.database_path.parent
            / (
                self.database_path.name
                + ".restore.tmp"
            )
        )

        restore_temp.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            self._sqlite_backup(
                source_backup,
                restore_temp,
            )

            restored_integrity = (
                sqlite_integrity_check(
                    restore_temp
                )
            )

            if (
                verify_integrity
                and restored_integrity.lower()
                != "ok"
            ):
                raise BackupIntegrityError(
                    "Restored database integrity "
                    "check failed: "
                    f"{restored_integrity}"
                )

            os.replace(
                restore_temp,
                self.database_path,
            )

            self._remove_wal_sidecars(
                self.database_path
            )

            return RestoreResult(
                backup_database=str(
                    source_backup.resolve()
                ),
                restored_database=str(
                    self.database_path.resolve()
                ),
                restored_at=utc_now_iso(),
                pre_restore_backup=(
                    pre_restore_backup
                ),
                integrity_status=(
                    restored_integrity
                ),
                successful=True,
            )

        except Exception as exc:
            restore_temp.unlink(
                missing_ok=True
            )

            if isinstance(
                exc,
                BackupIntegrityError,
            ):
                raise

            raise RestoreError(
                "Database restore failed."
            ) from exc

    def verify_backup(
        self,
        backup_path: str | Path,
        validate_checksum: bool = True,
    ) -> bool:
        path = Path(backup_path)

        if not path.exists():
            raise BackupNotFoundError(
                f"Backup not found: {path}"
            )

        if (
            sqlite_integrity_check(path).lower()
            != "ok"
        ):
            return False

        if validate_checksum:
            expected = self._expected_hash(path)
            if expected is not None:
                return (
                    sha256_file(path)
                    == expected
                )

        return True

    def list_backups(
        self,
    ) -> list[BackupMetadata]:
        backups: list[BackupMetadata] = []

        for metadata_path in sorted(
            self.backup_directory.glob(
                "backup_*.json"
            ),
            reverse=True,
        ):
            try:
                payload = json.loads(
                    metadata_path.read_text(
                        encoding="utf-8"
                    )
                )
                backups.append(
                    BackupMetadata(**payload)
                )
            except (
                OSError,
                ValueError,
                TypeError,
            ):
                continue

        return backups

    def rotate_backups(
        self,
        retention_count: int | None = None,
    ) -> list[str]:
        keep = (
            retention_count
            if retention_count is not None
            else self.retention_count
        )

        if keep is None:
            return []

        if keep <= 0:
            raise ValueError(
                "retention_count must be greater "
                "than zero."
            )

        backups = self.list_backups()
        removed: list[str] = []

        for metadata in backups[keep:]:
            database_path = Path(
                metadata.backup_database
            )
            metadata_path = Path(
                metadata.metadata_file
            )

            database_path.unlink(
                missing_ok=True
            )
            metadata_path.unlink(
                missing_ok=True
            )

            removed.append(
                metadata.backup_id
            )

        return removed

    def _initialize_database(self) -> None:
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

        candidate_attributes = [
            "database_path",
            "db_path",
            "path",
            "filename",
        ]

        for name in candidate_attributes:
            value = getattr(
                database,
                name,
                None,
            )
            if isinstance(
                value,
                (str, Path),
            ):
                return Path(value)

        connection = getattr(
            database,
            "connection",
            None,
        )

        if isinstance(
            connection,
            sqlite3.Connection,
        ):
            row = connection.execute(
                "PRAGMA database_list"
            ).fetchone()

            if row and row[2]:
                return Path(row[2])

        raise TypeError(
            "Unable to resolve the SQLite database "
            "path. Pass a database path directly or "
            "expose database_path, db_path, or path "
            "on ExperimentDatabase."
        )

    def _sqlite_backup(
        self,
        source_path: Path,
        destination_path: Path,
    ) -> None:
        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        destination_path.unlink(
            missing_ok=True
        )

        source = sqlite3.connect(
            str(source_path)
        )
        destination = sqlite3.connect(
            str(destination_path)
        )

        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

    def _expected_hash(
        self,
        backup_path: Path,
    ) -> str | None:
        metadata_path = (
            backup_path.with_suffix(".json")
        )

        if not metadata_path.exists():
            return None

        try:
            payload = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            ValueError,
        ):
            return None

        value = payload.get("sha256")

        return (
            str(value)
            if value
            else None
        )

    def _remove_wal_sidecars(
        self,
        database_path: Path,
    ) -> None:
        for suffix in ("-wal", "-shm"):
            Path(
                str(database_path) + suffix
            ).unlink(
                missing_ok=True
            )

    def _sanitize_label(
        self,
        label: str | None,
    ) -> str:
        if not label:
            return ""

        cleaned = "".join(
            character
            if (
                character.isalnum()
                or character in {"-", "_"}
            )
            else "_"
            for character in label.strip()
        )

        return cleaned.strip("_")[:60]
