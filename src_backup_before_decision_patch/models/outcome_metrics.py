from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class OutcomeMetrics:
    """
    Represents the measured business outcome after
    an autonomous commerce decision is executed.
    """

    decision_id: str
    target: str

    revenue_change_percentage: float
    profit_change_percentage: float
    conversion_change_percentage: float
    inventory_health_change: float
    customer_satisfaction_change: float

    overall_reward: float
    outcome_status: str

    metric_scores: Dict[str, float] = field(
        default_factory=dict
    )

    evaluated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def is_successful(self) -> bool:
        """
        Return True when the overall outcome is positive.
        """

        return self.outcome_status == "SUCCESS"

    def is_failure(self) -> bool:
        """
        Return True when the overall outcome is negative.
        """

        return self.outcome_status == "FAILURE"

    def to_dict(self) -> dict:
        """
        Convert the outcome into a serializable dictionary.
        """

        return {
            "decision_id": self.decision_id,
            "target": self.target,
            "revenue_change_percentage": (
                self.revenue_change_percentage
            ),
            "profit_change_percentage": (
                self.profit_change_percentage
            ),
            "conversion_change_percentage": (
                self.conversion_change_percentage
            ),
            "inventory_health_change": (
                self.inventory_health_change
            ),
            "customer_satisfaction_change": (
                self.customer_satisfaction_change
            ),
            "overall_reward": self.overall_reward,
            "outcome_status": self.outcome_status,
            "metric_scores": self.metric_scores,
            "evaluated_at": self.evaluated_at.isoformat()
        }