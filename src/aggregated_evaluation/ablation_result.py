from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass(slots=True)
class AblationComparison:
    baseline_group: str
    variant_group: str
    metric_name: str
    baseline_mean: float | None
    variant_mean: float | None
    absolute_change: float | None
    percentage_change: float | None
    performance_delta: float | None
    baseline_count: int
    variant_count: int
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_group": self.baseline_group,
            "variant_group": self.variant_group,
            "metric_name": self.metric_name,
            "baseline_mean": self.baseline_mean,
            "variant_mean": self.variant_mean,
            "absolute_change": self.absolute_change,
            "percentage_change": self.percentage_change,
            "performance_delta": self.performance_delta,
            "baseline_count": self.baseline_count,
            "variant_count": self.variant_count,
            "interpretation": self.interpretation,
        }


@dataclass(slots=True)
class AblationEvaluationResult:
    baseline_group: str
    primary_metric: str
    best_group: str | None
    worst_group: str | None
    comparisons: List[AblationComparison] = field(
        default_factory=list
    )
    ranking: List[str] = field(
        default_factory=list
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    ablation_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def successful(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ablation_id": self.ablation_id,
            "successful": self.successful,
            "baseline_group": self.baseline_group,
            "primary_metric": self.primary_metric,
            "best_group": self.best_group,
            "worst_group": self.worst_group,
            "ranking": list(self.ranking),
            "comparisons": [
                comparison.to_dict()
                for comparison in self.comparisons
            ],
            "warning_count": len(self.warnings),
            "warnings": list(self.warnings),
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }
