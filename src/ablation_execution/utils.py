from __future__ import annotations

from typing import Any


def get_value(
    source: Any,
    name: str,
    default: Any = None,
) -> Any:
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(name, default)

    return getattr(source, name, default)


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            continue

        return value

    return None


def safe_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_bool(
    value: Any,
) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {
            "true",
            "yes",
            "1",
            "success",
        }:
            return True

        if normalized in {
            "false",
            "no",
            "0",
            "failed",
        }:
            return False

    return bool(value)
