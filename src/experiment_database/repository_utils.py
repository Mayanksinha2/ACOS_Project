from __future__ import annotations

from typing import Iterable


VALID_DIRECTIONS = {
    "ASC",
    "DESC",
}


def normalize_limit(
    limit: int | None,
) -> int | None:
    if limit is None:
        return None

    if limit < 1:
        raise ValueError(
            "limit must be at least 1."
        )

    return int(limit)


def normalize_offset(
    offset: int,
) -> int:
    if offset < 0:
        raise ValueError(
            "offset cannot be negative."
        )

    return int(offset)


def normalize_direction(
    direction: str,
) -> str:
    normalized = direction.strip().upper()

    if normalized not in VALID_DIRECTIONS:
        raise ValueError(
            "direction must be ASC or DESC."
        )

    return normalized


def build_pagination_sql(
    limit: int | None,
    offset: int,
) -> tuple[str, tuple]:
    normalized_limit = normalize_limit(limit)
    normalized_offset = normalize_offset(offset)

    if normalized_limit is None:
        if normalized_offset:
            return (
                " LIMIT -1 OFFSET ?",
                (normalized_offset,),
            )

        return "", ()

    return (
        " LIMIT ? OFFSET ?",
        (
            normalized_limit,
            normalized_offset,
        ),
    )


def require_non_empty(
    value: str,
    field_name: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} cannot be empty."
        )

    return normalized
