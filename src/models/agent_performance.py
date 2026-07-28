from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class AgentPerformance:
    """
    Represents the learned performance profile
    of one autonomous ACOS agent.
    """

    agent_name: str

    experience_count: int
    success_count: int
    failure_count: int
    neutral_count: int

    average_reward: float
    success_rate: float
    failure_rate: float

    reward_stability: float
    reliability_score: float
    confidence_modifier: float

    operation_performance: Dict[str, dict] = field(
        default_factory=dict
    )

    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def is_reliable(
        self,
        threshold: float = 0.60
    ) -> bool:
        """
        Return True when the reliability score
        meets the given threshold.
        """

        return self.reliability_score >= threshold

    def to_dict(self) -> dict:
        """
        Convert the performance profile into
        a serializable dictionary.
        """

        return {
            "agent_name": self.agent_name,
            "experience_count": self.experience_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "neutral_count": self.neutral_count,
            "average_reward": self.average_reward,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "reward_stability": self.reward_stability,
            "reliability_score": self.reliability_score,
            "confidence_modifier": self.confidence_modifier,
            "operation_performance": (
                self.operation_performance
            ),
            "calculated_at": (
                self.calculated_at.isoformat()
            )
        }