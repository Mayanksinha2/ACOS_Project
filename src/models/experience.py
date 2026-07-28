from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from models.execution_result import ExecutionResult
from models.outcome_metrics import OutcomeMetrics


@dataclass
class Experience:
    """
    Represents one complete ACOS learning experience.

    An experience links:

    decision
    execution
    outcome
    reward
    responsible agent
    """

    experience_id: str
    decision_id: str
    target: str
    source_agent: str

    decision_type: str
    action_type: str
    operation: str

    execution_result: ExecutionResult
    outcome_metrics: OutcomeMetrics

    context: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

    @property
    def reward(self) -> float:
        """
        Return the final outcome reward.
        """

        return self.outcome_metrics.overall_reward

    @property
    def outcome_status(self) -> str:
        """
        Return SUCCESS, FAILURE, or NEUTRAL.
        """

        return self.outcome_metrics.outcome_status

    def is_positive(self) -> bool:
        """
        Return True when this experience produced
        a successful business outcome.
        """

        return self.outcome_status == "SUCCESS"

    def is_negative(self) -> bool:
        """
        Return True when this experience produced
        a failed business outcome.
        """

        return self.outcome_status == "FAILURE"

    def to_dict(self) -> dict:
        """
        Convert the experience into a serializable dictionary.
        """

        return {
            "experience_id": self.experience_id,
            "decision_id": self.decision_id,
            "target": self.target,
            "source_agent": self.source_agent,
            "decision_type": self.decision_type,
            "action_type": self.action_type,
            "operation": self.operation,
            "reward": self.reward,
            "outcome_status": self.outcome_status,
            "execution_result": {
                "success": self.execution_result.success,
                "source": self.execution_result.source,
                "message": self.execution_result.message,
                "previous_state": (
                    self.execution_result.previous_state
                ),
                "updated_state": (
                    self.execution_result.updated_state
                )
            },
            "outcome_metrics": (
                self.outcome_metrics.to_dict()
            ),
            "context": self.context,
            "created_at": self.created_at.isoformat()
        }