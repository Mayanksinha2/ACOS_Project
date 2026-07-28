from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass
from typing import Dict, Iterator


@dataclass(frozen=True, slots=True)
class ACOSFeatureFlags:
    """
    Runtime switches used by the ACOS research pipeline.

    The baseline configuration keeps every component enabled.
    Ablation variants disable one or more components while
    preserving the rest of the execution pipeline.
    """

    enable_conflict_detection: bool = True
    enable_negotiation: bool = True
    enable_mocra: bool = True
    enable_adaptive_learning: bool = True
    enable_outcome_evaluation: bool = True

    def to_dict(self) -> Dict[str, bool]:
        return {
            key: bool(value)
            for key, value in asdict(self).items()
        }


_DEFAULT_FLAGS = ACOSFeatureFlags()

_ACTIVE_FEATURE_FLAGS: ContextVar[ACOSFeatureFlags] = (
    ContextVar(
        "acos_active_feature_flags",
        default=_DEFAULT_FLAGS,
    )
)


def get_active_feature_flags() -> ACOSFeatureFlags:
    """
    Return the feature flags for the current experiment run.
    """

    return _ACTIVE_FEATURE_FLAGS.get()


def is_feature_enabled(feature_name: str) -> bool:
    """
    Check one feature by dataclass field name.

    Example:

        is_feature_enabled("enable_negotiation")
    """

    flags = get_active_feature_flags()

    if not hasattr(flags, feature_name):
        raise KeyError(
            f"Unknown ACOS feature flag: {feature_name}"
        )

    return bool(
        getattr(flags, feature_name)
    )


@contextmanager
def use_feature_flags(
    flags: ACOSFeatureFlags,
) -> Iterator[ACOSFeatureFlags]:
    """
    Activate flags only for the current execution context.

    ContextVar keeps parallel and nested experiment runs isolated.
    """

    token: Token[ACOSFeatureFlags] = (
        _ACTIVE_FEATURE_FLAGS.set(flags)
    )

    try:
        yield flags
    finally:
        _ACTIVE_FEATURE_FLAGS.reset(token)
