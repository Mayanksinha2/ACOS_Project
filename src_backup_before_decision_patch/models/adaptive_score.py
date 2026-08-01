from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AdaptiveScore:
    """
    Stores the learned scoring adjustment
    applied to one agent proposal.
    """

    agent_name: str
    original_confidence: float
    confidence_modifier: float
    adjusted_confidence: float
    reliability_score: float
    learning_applied: bool

    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "original_confidence": self.original_confidence,
            "confidence_modifier": self.confidence_modifier,
            "adjusted_confidence": self.adjusted_confidence,
            "reliability_score": self.reliability_score,
            "learning_applied": self.learning_applied,
            "calculated_at": self.calculated_at.isoformat()
        }