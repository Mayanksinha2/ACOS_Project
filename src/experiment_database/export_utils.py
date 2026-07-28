from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_token() -> str:
    return datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )


def sanitize_name(value: str) -> str:
    cleaned = "".join(
        character
        if (
            character.isalnum()
            or character in {"-", "_"}
        )
        else "_"
        for character in value.strip()
    )
    return cleaned.strip("_")[:100]


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def write_json(
    path: str | Path,
    payload: Any,
) -> Path:
    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=json_default,
        ),
        encoding="utf-8",
    )
    return output


def sha256_file(
    path: str | Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    digest = hashlib.sha256()
    source = Path(path)

    with source.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()
