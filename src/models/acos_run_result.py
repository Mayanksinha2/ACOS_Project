from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from models.business_state import BusinessState
from models.commerce_decision import CommerceDecision


@dataclass
class ACOSRunResult:
    """Complete result produced by one ACOS decision cycle."""

    business_state: Optional[BusinessState]
    proposals: List[CommerceDecision] = field(default_factory=list)
    conflicts: List[Any] = field(default_factory=list)
    negotiation_result: Optional[Any] = None
    mocra_result: Optional[Any] = None
    final_decision: Optional[Any] = None
    status: str = "COMPLETED"
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def successful(self) -> bool:
        return self.status == "COMPLETED" and not self.errors and self.final_decision is not None

    @property
    def proposal_count(self) -> int:
        return len(self.proposals)

    @property
    def conflict_count(self) -> int:
        # Pairwise comparison results include NO_CONFLICT and SUPPORTING.
        # Only actual soft/hard conflicts should appear in the summary count.
        return sum(
            1
            for conflict in self.conflicts
            if getattr(conflict, "conflict_type", "") in {"SOFT_CONFLICT", "HARD_CONFLICT"}
        )

    @property
    def negotiation_required(self) -> bool:
        return bool(self.metadata.get("negotiation_required", False))

    def summary(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "successful": self.successful,
            "proposal_count": self.proposal_count,
            "conflict_count": self.conflict_count,
            "negotiation_required": self.negotiation_required,
            "final_decision_available": self.final_decision is not None,
            "errors": list(self.errors),
            "timestamp": self.timestamp,
        }
