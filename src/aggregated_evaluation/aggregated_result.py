from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from .metric_summary import MetricSummary


@dataclass(slots=True)
class GroupEvaluationResult:
    group_name: str
    experiment_count: int
    successful_count: int
    failed_count: int
    cancelled_count: int
    success_rate: float
    failure_rate: float
    conflict_count: int
    negotiation_count: int
    conflict_rate: float
    negotiation_rate: float
    metrics: Dict[str, MetricSummary] = field(
        default_factory=dict
    )
    experiment_ids: List[str] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_name": self.group_name,
            "experiment_count": self.experiment_count,
            "successful_count": self.successful_count,
            "failed_count": self.failed_count,
            "cancelled_count": self.cancelled_count,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "conflict_count": self.conflict_count,
            "negotiation_count": self.negotiation_count,
            "conflict_rate": self.conflict_rate,
            "negotiation_rate": self.negotiation_rate,
            "metrics": {
                name: metric.to_dict()
                for name, metric in self.metrics.items()
            },
            "experiment_ids": list(
                self.experiment_ids
            ),
        }


@dataclass(slots=True)
class AggregatedEvaluationResult:
    total_experiments: int
    successful_count: int
    failed_count: int
    cancelled_count: int
    success_rate: float
    failure_rate: float
    conflict_count: int
    negotiation_count: int
    conflict_rate: float
    negotiation_rate: float
    metrics: Dict[str, MetricSummary] = field(
        default_factory=dict
    )
    groups: Dict[str, GroupEvaluationResult] = field(
        default_factory=dict
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    evaluation_id: str = field(
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
            "evaluation_id": self.evaluation_id,
            "successful": self.successful,
            "total_experiments": self.total_experiments,
            "successful_count": self.successful_count,
            "failed_count": self.failed_count,
            "cancelled_count": self.cancelled_count,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "conflict_count": self.conflict_count,
            "negotiation_count": self.negotiation_count,
            "conflict_rate": self.conflict_rate,
            "negotiation_rate": self.negotiation_rate,
            "metrics": {
                name: metric.to_dict()
                for name, metric in self.metrics.items()
            },
            "groups": {
                name: group.to_dict()
                for name, group in self.groups.items()
            },
            "warning_count": len(self.warnings),
            "warnings": list(self.warnings),
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "created_at": self.created_at,
        }
