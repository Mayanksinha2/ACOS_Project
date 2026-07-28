from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(slots=True)
class AblationRunRequest:
    """
    Normalized request for one ablation execution.
    """

    variant_name: str
    repetition_index: int
    random_seed: int | None
    base_request: Any
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.variant_name.strip():
            raise ValueError(
                "variant_name cannot be empty."
            )

        if self.repetition_index < 1:
            raise ValueError(
                "repetition_index must be at least 1."
            )
