from __future__ import annotations

from typing import Any, Callable, TypeVar

from .feature_flags import (
    is_feature_enabled,
)


T = TypeVar("T")


def run_if_enabled(
    feature_name: str,
    operation: Callable[..., T],
    *args: Any,
    disabled_value: T | None = None,
    **kwargs: Any,
) -> T | None:
    """
    Run an ACOS component only when its feature flag is enabled.
    """

    if not is_feature_enabled(feature_name):
        return disabled_value

    return operation(
        *args,
        **kwargs,
    )


def conflict_detection_enabled() -> bool:
    return is_feature_enabled(
        "enable_conflict_detection"
    )


def negotiation_enabled() -> bool:
    return is_feature_enabled(
        "enable_negotiation"
    )


def mocra_enabled() -> bool:
    return is_feature_enabled(
        "enable_mocra"
    )


def adaptive_learning_enabled() -> bool:
    return is_feature_enabled(
        "enable_adaptive_learning"
    )


def outcome_evaluation_enabled() -> bool:
    return is_feature_enabled(
        "enable_outcome_evaluation"
    )
