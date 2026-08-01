from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .statistics_models import NumericStatistics


@dataclass(slots=True)
class VariantStatistics:
    variant_name: str
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
    experiment_count: int
    experiment_ids: List[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class VariantComparison:
    baseline_variant: str
    candidate_variant: str
    primary_metric: str
    baseline_value: float | None
    candidate_value: float | None
    absolute_difference: float | None
    percentage_difference: float | None
    better_variant: str | None


@dataclass(slots=True)
class CrossExperimentSummary:
    experiment_count: int
    run_count: int
    variant_count: int
    best_variant: str | None
    worst_variant: str | None
    variant_statistics: Dict[
        str,
        VariantStatistics,
    ] = field(default_factory=dict)
