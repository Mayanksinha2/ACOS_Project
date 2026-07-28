from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .feature_flags import ACOSFeatureFlags


@dataclass(frozen=True, slots=True)
class AblationVariant:
    """
    One executable ACOS architecture variant.
    """

    name: str
    feature_flags: ACOSFeatureFlags
    description: str = ""
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError(
                "Ablation variant name cannot be empty."
            )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "ablation_variant": self.name,
            "ablation_description": self.description,
            "feature_flags": (
                self.feature_flags.to_dict()
            ),
            **dict(self.metadata),
        }
