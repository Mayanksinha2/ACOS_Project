from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class AblationConfig:
    baseline_group: str = "baseline"
    primary_metric: str = "reward"
    higher_is_better: bool = True
    minimum_group_size: int = 1
    comparison_metrics: List[str] = field(
        default_factory=lambda: [
            "reward",
            "duration_seconds",
            "successful",
            "conflict_detected",
            "negotiation_required",
        ]
    )

    def __post_init__(self) -> None:
        if not self.baseline_group.strip():
            raise ValueError(
                "baseline_group cannot be empty."
            )

        if not self.primary_metric.strip():
            raise ValueError(
                "primary_metric cannot be empty."
            )

        if self.minimum_group_size < 1:
            raise ValueError(
                "minimum_group_size must be at least 1."
            )
