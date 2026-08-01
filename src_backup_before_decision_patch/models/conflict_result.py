from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from uuid import uuid4


@dataclass
class ConflictResult:
    """
    Represents the result of comparing two commerce proposals.
    """

    proposal_ids: List[str]

    conflict_type: str

    target: str

    reason: str

    severity: float

    requires_negotiation: bool

    conflict_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        allowed_types = {
            "NO_CONFLICT",
            "SUPPORTING",
            "SOFT_CONFLICT",
            "HARD_CONFLICT"
        }

        if self.conflict_type not in allowed_types:
            raise ValueError(
                f"Invalid conflict type: {self.conflict_type}"
            )

        if not 0.0 <= self.severity <= 1.0:
            raise ValueError(
                "severity must be between 0 and 1"
            )

        if len(self.proposal_ids) != 2:
            raise ValueError(
                "ConflictResult must compare exactly two proposals"
            )