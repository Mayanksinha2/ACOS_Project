from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4


@dataclass
class NegotiationResult:
    """
    Represents the final outcome of an adaptive negotiation session.
    """

    target: str
    agreement_reached: bool
    final_operation: str
    final_value: float
    unit: str

    participant_agents: List[str]
    influence_scores: Dict[str, float]

    rounds_completed: int
    explanation: List[str]

    negotiation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:

        allowed_operations = {
            "INCREASE",
            "DECREASE",
            "MAINTAIN"
        }

        if self.final_operation not in allowed_operations:
            raise ValueError(
                f"Invalid final operation: "
                f"{self.final_operation}"
            )

        if self.final_value < 0:
            raise ValueError(
                "final_value cannot be negative"
            )