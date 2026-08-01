from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class TrendPoint:
    index: int
    timestamp: str | None
    run_id: str
    experiment_id: str
    variant_name: str
    metric_value: float | None
    rolling_mean: float | None


@dataclass(slots=True)
class TrendSummary:
    metric_name: str
    total_points: int
    first_value: float | None
    last_value: float | None
    absolute_change: float | None
    percentage_change: float | None
    direction: str
    points: List[TrendPoint] = field(
        default_factory=list
    )
