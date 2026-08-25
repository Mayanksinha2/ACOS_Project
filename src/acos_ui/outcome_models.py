from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class OutcomeMetrics:
    revenue: float
    profit: float
    conversion_rate: float
    inventory_health: float
    customer_satisfaction: float

    def validate(self) -> None:
        if self.revenue < 0:
            raise ValueError("Revenue cannot be negative.")
        if not 0 <= self.conversion_rate <= 1:
            raise ValueError("Conversion rate must be between 0 and 1.")
        if not 0 <= self.inventory_health <= 1:
            raise ValueError("Inventory health must be between 0 and 1.")
        if not 0 <= self.customer_satisfaction <= 1:
            raise ValueError(
                "Customer satisfaction must be between 0 and 1."
            )


@dataclass(frozen=True, slots=True)
class MetricChange:
    metric: str
    before: float
    after: float
    relative_change: float
    contribution: float
    weight: float


@dataclass(frozen=True, slots=True)
class OutcomeEvaluation:
    evaluation_id: str
    run_id: str
    experiment_id: str | None
    product_id: str
    winning_agent: str
    decision_type: str
    primary_operation: str
    primary_value: float
    primary_unit: str
    reward: float
    classification: str
    successful: bool
    before: OutcomeMetrics
    after: OutcomeMetrics
    metric_changes: tuple[MetricChange, ...]
    notes: str
    evaluated_at: str
    run_snapshot: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new_id() -> str:
        return str(uuid4())

    @staticmethod
    def timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
