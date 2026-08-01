from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class DescriptiveStatistics:
    """
    Descriptive statistics for one strategy and metric.
    """

    strategy_name: str
    metric_name: str

    sample_size: int = 0

    mean: float = 0.0
    median: float = 0.0
    standard_deviation: float = 0.0
    variance: float = 0.0

    minimum: float = 0.0
    maximum: float = 0.0

    confidence_interval_lower: float = 0.0
    confidence_interval_upper: float = 0.0
    confidence_level: float = 0.95

    successful: bool = True
    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "metric_name": self.metric_name,
            "sample_size": self.sample_size,
            "mean": self.mean,
            "median": self.median,
            "standard_deviation": (
                self.standard_deviation
            ),
            "variance": self.variance,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "confidence_interval_lower": (
                self.confidence_interval_lower
            ),
            "confidence_interval_upper": (
                self.confidence_interval_upper
            ),
            "confidence_level": (
                self.confidence_level
            ),
            "successful": self.successful,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass
class PairwiseStatisticalComparison:
    """
    Statistical comparison between ACOS and one baseline.
    """

    reference_strategy: str
    comparison_strategy: str
    metric_name: str

    sample_size: int = 0

    reference_mean: float = 0.0
    comparison_mean: float = 0.0
    mean_difference: float = 0.0

    reference_win_count: int = 0
    comparison_win_count: int = 0
    tie_count: int = 0

    reference_win_rate: float = 0.0
    comparison_win_rate: float = 0.0
    tie_rate: float = 0.0

    effect_size: float = 0.0
    effect_size_interpretation: str = (
        "negligible"
    )

    t_statistic: float = 0.0
    p_value: float = 1.0
    statistically_significant: bool = False
    significance_level: float = 0.05

    better_strategy: Optional[str] = None

    successful: bool = True
    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    comparison_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "reference_strategy": (
                self.reference_strategy
            ),
            "comparison_strategy": (
                self.comparison_strategy
            ),
            "metric_name": self.metric_name,
            "sample_size": self.sample_size,
            "reference_mean": (
                self.reference_mean
            ),
            "comparison_mean": (
                self.comparison_mean
            ),
            "mean_difference": (
                self.mean_difference
            ),
            "reference_win_count": (
                self.reference_win_count
            ),
            "comparison_win_count": (
                self.comparison_win_count
            ),
            "tie_count": self.tie_count,
            "reference_win_rate": (
                self.reference_win_rate
            ),
            "comparison_win_rate": (
                self.comparison_win_rate
            ),
            "tie_rate": self.tie_rate,
            "effect_size": self.effect_size,
            "effect_size_interpretation": (
                self.effect_size_interpretation
            ),
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "statistically_significant": (
                self.statistically_significant
            ),
            "significance_level": (
                self.significance_level
            ),
            "better_strategy": (
                self.better_strategy
            ),
            "successful": self.successful,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass
class StatisticalEvaluationResult:
    """
    Complete statistical evaluation of one benchmark.
    """

    experiment_id: str
    experiment_name: str

    reference_strategy: str = "ACOS"

    descriptive_statistics: Dict[
        str,
        Dict[str, DescriptiveStatistics],
    ] = field(default_factory=dict)

    pairwise_comparisons: Dict[
        str,
        Dict[
            str,
            PairwiseStatisticalComparison,
        ],
    ] = field(default_factory=dict)

    strategy_rankings: Dict[
        str,
        List[str],
    ] = field(default_factory=dict)

    significant_comparisons: List[
        str
    ] = field(default_factory=list)

    total_scenarios: int = 0
    evaluated_scenarios: int = 0

    successful: bool = True

    errors: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    evaluation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def summary(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "experiment_id": self.experiment_id,
            "experiment_name": (
                self.experiment_name
            ),
            "reference_strategy": (
                self.reference_strategy
            ),
            "successful": self.successful,
            "total_scenarios": (
                self.total_scenarios
            ),
            "evaluated_scenarios": (
                self.evaluated_scenarios
            ),
            "strategy_rankings": dict(
                self.strategy_rankings
            ),
            "significant_comparisons": list(
                self.significant_comparisons
            ),
            "created_at": self.created_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "descriptive_statistics": {
                metric: {
                    strategy: statistics.to_dict()
                    for strategy, statistics
                    in strategy_statistics.items()
                }
                for metric, strategy_statistics
                in self.descriptive_statistics.items()
            },
            "pairwise_comparisons": {
                metric: {
                    strategy: comparison.to_dict()
                    for strategy, comparison
                    in metric_comparisons.items()
                }
                for metric, metric_comparisons
                in self.pairwise_comparisons.items()
            },
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }