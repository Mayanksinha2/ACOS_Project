from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .repository_utils import (
    build_pagination_sql,
    normalize_direction,
)
from .utils import bool_to_int, json_dumps


def append_exact_filter(
    clauses: List[str],
    parameters: List[Any],
    column_name: str,
    value: Any,
) -> None:
    if value is None:
        return

    clauses.append(f"{column_name} = ?")
    parameters.append(value)


def append_like_filter(
    clauses: List[str],
    parameters: List[Any],
    column_name: str,
    value: str | None,
) -> None:
    if value is None:
        return

    normalized = value.strip()

    if not normalized:
        return

    clauses.append(
        f"LOWER({column_name}) LIKE LOWER(?)"
    )
    parameters.append(f"%{normalized}%")


def append_range_filter(
    clauses: List[str],
    parameters: List[Any],
    column_name: str,
    minimum: Any = None,
    maximum: Any = None,
) -> None:
    if minimum is not None:
        clauses.append(f"{column_name} >= ?")
        parameters.append(minimum)

    if maximum is not None:
        clauses.append(f"{column_name} <= ?")
        parameters.append(maximum)


def append_bool_filter(
    clauses: List[str],
    parameters: List[Any],
    column_name: str,
    value: bool | None,
) -> None:
    if value is None:
        return

    clauses.append(f"{column_name} = ?")
    parameters.append(bool_to_int(value))


def append_metadata_filters(
    clauses: List[str],
    parameters: List[Any],
    metadata_contains: Dict[str, Any],
) -> None:
    for key, value in metadata_contains.items():
        clauses.append(
            """
            json_extract(metadata_json, ?) = json_extract(?, '$')
            """.strip()
        )
        parameters.append(f"$.{key}")
        parameters.append(json_dumps(value))


def build_where_clause(
    clauses: List[str],
) -> str:
    if not clauses:
        return ""

    return " WHERE " + " AND ".join(clauses)


def build_order_and_pagination(
    order_column: str,
    direction: str,
    limit: int | None,
    offset: int,
) -> Tuple[str, tuple]:
    normalized_direction = normalize_direction(
        direction
    )

    pagination_sql, pagination_parameters = (
        build_pagination_sql(
            limit,
            offset,
        )
    )

    return (
        f" ORDER BY {order_column} "
        f"{normalized_direction}"
        f"{pagination_sql}",
        pagination_parameters,
    )
