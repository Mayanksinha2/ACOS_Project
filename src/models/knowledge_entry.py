from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4


@dataclass
class KnowledgeEntry:
    """
    Represents a reusable piece of knowledge learned
    by the ACOS self-optimization system.

    Knowledge can describe:

    - Agent performance
    - Preferred operations
    - Avoided operations
    - Business patterns
    - System-level recommendations
    - System health observations
    """

    knowledge_type: str
    target: str
    statement: str

    confidence: float
    expected_benefit: float

    knowledge_id: str = field(
        default_factory=lambda: (
            f"KNW-{uuid4().hex[:12].upper()}"
        )
    )

    priority: str = "MEDIUM"

    evidence: Dict[str, Any] = field(
        default_factory=dict
    )

    source: str = "SCOE"

    occurrence_count: int = 1

    is_active: bool = True

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

    updated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def __post_init__(self) -> None:
        self.knowledge_type = (
            str(self.knowledge_type)
            .strip()
            .upper()
        )

        self.target = (
            str(self.target)
            .strip()
        )

        self.statement = (
            str(self.statement)
            .strip()
        )

        self.priority = (
            str(self.priority)
            .strip()
            .upper()
        )

        self.source = (
            str(self.source)
            .strip()
            .upper()
        )

        self.confidence = self._clamp(
            float(self.confidence),
            0.0,
            1.0
        )

        self.expected_benefit = self._clamp(
            float(self.expected_benefit),
            -1.0,
            1.0
        )

        self.occurrence_count = max(
            1,
            int(self.occurrence_count)
        )

        valid_priorities = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        }

        if self.priority not in valid_priorities:
            raise ValueError(
                "priority must be one of: "
                "LOW, MEDIUM, HIGH, CRITICAL."
            )

        if not self.knowledge_type:
            raise ValueError(
                "knowledge_type cannot be empty."
            )

        if not self.target:
            raise ValueError(
                "target cannot be empty."
            )

        if not self.statement:
            raise ValueError(
                "statement cannot be empty."
            )

    @property
    def unique_key(self) -> str:
        """
        Stable key used to detect duplicate knowledge.
        """

        return (
            f"{self.knowledge_type}::"
            f"{self.target.strip().upper()}"
        )

    def reinforce(
        self,
        confidence: float,
        expected_benefit: float,
        evidence: Dict[str, Any] | None = None
    ) -> None:
        """
        Reinforce existing knowledge using a running average.

        Repeated observations increase occurrence_count and
        update confidence and expected benefit.
        """

        old_count = self.occurrence_count
        new_count = old_count + 1

        self.confidence = self._clamp(
            (
                self.confidence * old_count
                + float(confidence)
            ) / new_count,
            0.0,
            1.0
        )

        self.expected_benefit = self._clamp(
            (
                self.expected_benefit * old_count
                + float(expected_benefit)
            ) / new_count,
            -1.0,
            1.0
        )

        self.occurrence_count = new_count

        if evidence:
            self.evidence.update(
                evidence
            )

        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Mark this knowledge as inactive.
        """

        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        Reactivate this knowledge.
        """

        self.is_active = True
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """
        Convert the entry into JSON-serializable data.
        """

        data = asdict(self)

        data["created_at"] = (
            self.created_at.isoformat()
        )

        data["updated_at"] = (
            self.updated_at.isoformat()
        )

        return data

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any]
    ) -> "KnowledgeEntry":
        """
        Restore a KnowledgeEntry from serialized data.
        """

        restored_data = dict(data)

        created_at = restored_data.get(
            "created_at"
        )

        updated_at = restored_data.get(
            "updated_at"
        )

        if isinstance(created_at, str):
            restored_data["created_at"] = (
                datetime.fromisoformat(
                    created_at
                )
            )

        if isinstance(updated_at, str):
            restored_data["updated_at"] = (
                datetime.fromisoformat(
                    updated_at
                )
            )

        return cls(
            **restored_data
        )

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