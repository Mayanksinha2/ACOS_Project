from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from models.commerce_decision import CommerceDecision


@dataclass
class ACNPMessage:
    """
    Standard communication message used inside ACOS.
    """

    sender: str
    decision: CommerceDecision

    receiver: str = "ACOSKernel"
    message_type: str = "PROPOSAL"

    message_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )