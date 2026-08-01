from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_token() -> str:
    return datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )


def sha256_file(
    path: str | Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    digest = hashlib.sha256()
    file_path = Path(path)

    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def write_json(
    path: str | Path,
    payload: dict[str, Any],
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    return output_path


def read_json(
    path: str | Path,
) -> dict[str, Any]:
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def sqlite_integrity_check(
    database_path: str | Path,
) -> str:
    path = Path(database_path)

    connection = sqlite3.connect(
        str(path)
    )
    try:
        row = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()
    finally:
        connection.close()

    if not row:
        return "unknown"

    return str(row[0])


def read_schema_version(
    database_path: str | Path,
) -> int | None:
    path = Path(database_path)

    connection = sqlite3.connect(
        str(path)
    )
    try:
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
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(schema_migrations)"
            ).fetchall()
        }

        candidate_columns = [
            "version",
            "schema_version",
        ]

        selected = next(
            (
                column
                for column in candidate_columns
                if column in columns
            ),
            None,
        )

        if selected is None:
            return None

        row = connection.execute(
            f"""
            SELECT MAX({selected})
            FROM schema_migrations
            """
        ).fetchone()

        if (
            row is None
            or row[0] is None
        ):
            return None

        return int(row[0])
    finally:
        connection.close()
