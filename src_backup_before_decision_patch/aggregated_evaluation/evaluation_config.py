from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class AggregatedEvaluationConfig:
    confidence_level: float = 0.95
    include_failed_rewards: bool = False
    reward_failure_value: float = 0.0
    group_by_metadata_key: str = "ablation_variant"
    minimum_group_size: int = 1
    metric_names: List[str] = field(
        default_factory=lambda: [
            "reward",
            "duration_seconds",
            "conflict_detected",
            "negotiation_required",
            "successful",
        ]
    )

    def __post_init__(self) -> None:
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError(
                "confidence_level must be between 0 and 1."
            )

        if self.minimum_group_size < 1:
            raise ValueError(
                "minimum_group_size must be at least 1."
            )
