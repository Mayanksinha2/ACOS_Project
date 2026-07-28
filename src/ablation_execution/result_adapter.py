from __future__ import annotations

from typing import Any, List

from .utils import (
    first_non_empty,
    get_value,
    safe_bool,
    safe_float,
)


def normalize_messages(
    value: Any,
) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value] if value.strip() else []

    try:
        return [
            str(item)
            for item in value
            if str(item).strip()
        ]
    except TypeError:
        return [str(value)]


def extract_experiment_id(
    result: Any,
) -> str:
    return str(
        first_non_empty(
            get_value(
                result,
                "experiment_id",
                None,
            ),
            get_value(
                result,
                "run_id",
                None,
            ),
            "",
        )
    )


def extract_successful(
    result: Any,
) -> bool:
    explicit = get_value(
        result,
        "successful",
        None,
    )

    if explicit is not None:
        return safe_bool(explicit)

    status = get_value(
        result,
        "status",
        "",
    )

    status_value = get_value(
        status,
        "value",
        status,
    )

    return (
        str(status_value).strip().lower()
        == "success"
    )


def extract_reward(
    result: Any,
) -> float | None:
    return safe_float(
        first_non_empty(
            get_value(
                result,
                "reward",
                None,
            ),
            get_value(
                result,
                "average_reward",
                None,
            ),
            get_value(
                result,
                "final_reward",
                None,
            ),
        )
    )


def extract_duration(
    result: Any,
) -> float | None:
    return safe_float(
        first_non_empty(
            get_value(
                result,
                "duration_seconds",
                None,
            ),
            get_value(
                result,
                "execution_time_seconds",
                None,
            ),
        )
    )


def extract_conflict_detected(
    result: Any,
) -> bool:
    return safe_bool(
        first_non_empty(
            get_value(
                result,
                "conflict_detected",
                None,
            ),
            get_value(
                result,
                "has_conflict",
                None,
            ),
            False,
        )
    )


def extract_negotiation_required(
    result: Any,
) -> bool:
    return safe_bool(
        first_non_empty(
            get_value(
                result,
                "negotiation_required",
                None,
            ),
            get_value(
                result,
                "negotiated",
                None,
            ),
            False,
        )
    )
