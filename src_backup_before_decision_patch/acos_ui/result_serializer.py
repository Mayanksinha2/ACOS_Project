from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any


def to_serializable(value: Any, _seen: set[int] | None = None) -> Any:
    """Convert ACOS result objects into JSON-safe values without coupling to models."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value

    seen = _seen if _seen is not None else set()
    object_id = id(value)
    if object_id in seen:
        return "<circular-reference>"

    if isinstance(value, dict):
        seen.add(object_id)
        try:
            return {str(k): to_serializable(v, seen) for k, v in value.items()}
        finally:
            seen.remove(object_id)

    if isinstance(value, (list, tuple, set, frozenset)):
        seen.add(object_id)
        try:
            return [to_serializable(item, seen) for item in value]
        finally:
            seen.remove(object_id)

    if is_dataclass(value):
        seen.add(object_id)
        try:
            return to_serializable(asdict(value), seen)
        finally:
            seen.remove(object_id)

    if hasattr(value, "summary") and callable(value.summary):
        try:
            summary = value.summary()
            if isinstance(summary, dict):
                return to_serializable(summary, seen)
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        seen.add(object_id)
        try:
            return {
                str(k): to_serializable(v, seen)
                for k, v in vars(value).items()
                if not str(k).startswith("_")
            }
        finally:
            seen.remove(object_id)

    return str(value)
