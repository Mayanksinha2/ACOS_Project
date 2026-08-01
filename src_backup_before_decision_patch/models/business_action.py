from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class BusinessAction:
    """
    Represents a structured business action proposed by an ACOS agent.
    """

    action_type: str
    operation: str
    target: str

    value: Optional[float] = None
    unit: Optional[str] = None

    agent_id: str = ""
    rationale: str = ""

    confidence: float = 0.0
    risk: float = 0.0
    priority: int = 5

    metadata: Dict[str, Any] = field(default_factory=dict)

    action_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("risk must be between 0 and 1")

        if not 1 <= self.priority <= 10:
            raise ValueError("priority must be between 1 and 10")