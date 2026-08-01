from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class KnowledgeAdjustment:
    """
    Represents the score adjustment produced from
    previously learned ACOS knowledge.
    """

    agent_name: str
    operation: str

    original_score: float
    adjustment_modifier: float
    adjusted_score: float

    positive_influence: float
    negative_influence: float

    matched_knowledge_ids: List[str] = field(
        default_factory=list
    )

    explanations: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def __post_init__(self) -> None:
        self.agent_name = (
            str(self.agent_name)
            .strip()
        )

        self.operation = (
            str(self.operation)
            .strip()
            .upper()
        )

        self.original_score = self._clamp(
            float(self.original_score),
            0.0,
            1.0
        )

        self.adjustment_modifier = self._clamp(
            float(self.adjustment_modifier),
            0.70,
            1.30
        )

        self.adjusted_score = self._clamp(
            float(self.adjusted_score),
            0.0,
            1.0
        )

        self.positive_influence = max(
            0.0,
            float(self.positive_influence)
        )

        self.negative_influence = max(
            0.0,
            float(self.negative_influence)
        )

    @property
    def net_influence(self) -> float:
        return round(
            self.positive_influence
            - self.negative_influence,
            4
        )

    @property
    def knowledge_applied(self) -> bool:
        return bool(
            self.matched_knowledge_ids
        )

    def to_dict(self) -> dict:
        data = asdict(self)

        data["net_influence"] = (
            self.net_influence
        )

        data["knowledge_applied"] = (
            self.knowledge_applied
        )

        data["calculated_at"] = (
            self.calculated_at.isoformat()
        )

        return data

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float
    ) -> float:
        return max(
            minimum,
            min(value, maximum)
        )