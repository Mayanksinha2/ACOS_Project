from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .statistics_models import ExperimentStatistics


@dataclass(slots=True)
class ExperimentRankingEntry:
    rank: int
    experiment_id: str
    metric_name: str
    metric_value: float | None
    total_runs: int
    success_rate: float


@dataclass(slots=True)
class CrossExperimentStatistics:
    experiment_statistics: List[
        ExperimentStatistics
    ] = field(default_factory=list)
    ranking: List[
        ExperimentRankingEntry
    ] = field(default_factory=list)
