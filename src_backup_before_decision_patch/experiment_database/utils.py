from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def to_serializable(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value):
        return {
            key: to_serializable(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): to_serializable(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            to_serializable(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)):
        return value

    to_dict = getattr(value, "to_dict", None)

    if callable(to_dict):
        return to_serializable(to_dict())

    return str(value)


def json_dumps(value: Any) -> str:
    return json.dumps(
        to_serializable(value),
        ensure_ascii=False,
        sort_keys=True,
    )


def json_loads(
    value: str | None,
    default: Any,
) -> Any:
    if value is None or value == "":
        return default

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def bool_to_int(value: bool) -> int:
    return 1 if bool(value) else 0


def int_to_bool(value: int | bool | None) -> bool:
    return bool(value)
