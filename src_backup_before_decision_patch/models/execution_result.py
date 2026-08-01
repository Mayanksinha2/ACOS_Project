from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


@dataclass
class ExecutionResult:
    """
    Records the outcome of executing a final ACOS decision.
    """

    target: str
    action_type: str
    operation: str

    success: bool

    previous_state: Dict[str, Any]
    updated_state: Dict[str, Any]

    message: str
    source: str

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )