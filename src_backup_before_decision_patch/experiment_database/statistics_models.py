from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class NumericStatistics:
    count: int
    mean: float | None
    median: float | None
    minimum: float | None
    maximum: float | None
    variance: float | None
    standard_deviation: float | None


@dataclass(slots=True)
class RateStatistics:
    total_count: int
    positive_count: int
    negative_count: int
    positive_rate: float
    negative_rate: float


@dataclass(slots=True)
class ExperimentStatistics:
    experiment_id: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    failure_rate: float
    conflict_count: int
    conflict_rate: float
    negotiation_count: int
    negotiation_rate: float
    reward_statistics: NumericStatistics
    duration_statistics: NumericStatistics
    variant_counts: Dict[str, int] = field(
        default_factory=dict
    )
    statuses: Dict[str, int] = field(
        default_factory=dict
    )
    warnings_count: int = 0
    errors_count: int = 0


@dataclass(slots=True)
class DatabaseStatistics:
    total_experiments: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    conflict_rate: float
    negotiation_rate: float
    reward_statistics: NumericStatistics
    duration_statistics: NumericStatistics
