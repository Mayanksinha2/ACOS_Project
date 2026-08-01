from __future__ import annotations

from copy import deepcopy
from dataclasses import is_dataclass, replace
from typing import Any, Dict


def clone_request_with_metadata(
    base_request: Any,
    metadata: Dict[str, Any],
) -> Any:
    """
    Clone an ExperimentRequest-like object and merge metadata.

    Supports:
    - dataclass requests
    - mutable objects with a metadata attribute
    - dictionary requests
    """

    if isinstance(base_request, dict):
        cloned = deepcopy(base_request)
        current = dict(
            cloned.get("metadata", {})
        )
        current.update(metadata)
        cloned["metadata"] = current
        return cloned

    if is_dataclass(base_request):
        current = dict(
            getattr(
                base_request,
                "metadata",
                {},
            )
            or {}
        )
        current.update(metadata)

        try:
            return replace(
                base_request,
                metadata=current,
            )
        except TypeError:
            cloned = deepcopy(base_request)

            if hasattr(cloned, "metadata"):
                setattr(
                    cloned,
                    "metadata",
                    current,
                )

            return cloned

    cloned = deepcopy(base_request)

    current = dict(
        getattr(
            cloned,
            "metadata",
            {},
        )
        or {}
    )
    current.update(metadata)

    if hasattr(cloned, "metadata"):
        setattr(
            cloned,
            "metadata",
            current,
        )

    return cloned
