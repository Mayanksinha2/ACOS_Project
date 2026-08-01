from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class AgentProposalExplanation:
    """
    Human-readable explanation of one agent proposal.
    """

    agent_id: str
    goal: str

    action_type: str
    operation: str
    target: str

    value: float
    unit: str

    rationale: str

    confidence: float
    risk: float
    priority: int

    expected_benefit: Dict[str, Any] = field(
        default_factory=dict
    )

    evidence: List[str] = field(
        default_factory=list
    )

    selected: bool = False
    negotiation_status: str = "PENDING"

    score: Optional[float] = None

    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "goal": self.goal,
            "action_type": self.action_type,
            "operation": self.operation,
            "target": self.target,
            "value": self.value,
            "unit": self.unit,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "risk": self.risk,
            "priority": self.priority,
            "expected_benefit": dict(
                self.expected_benefit
            ),
            "evidence": list(self.evidence),
            "selected": self.selected,
            "negotiation_status": (
                self.negotiation_status
            ),
            "score": self.score,
            "explanation": self.explanation,
        }


@dataclass
class DecisionExplanation:
    """
    Complete explainability output for one ACOS run.
    """

    run_id: str
    status: str

    product_id: Optional[str]

    proposal_explanations: List[
        AgentProposalExplanation
    ] = field(default_factory=list)

    conflict_summary: List[str] = field(
        default_factory=list
    )

    negotiation_summary: List[str] = field(
        default_factory=list
    )

    mocra_summary: List[str] = field(
        default_factory=list
    )

    final_decision_summary: str = ""

    selected_agent: Optional[str] = None
    selected_operation: Optional[str] = None

    negotiation_required: bool = False
    agreement_reached: Optional[bool] = None

    confidence_summary: str = ""
    risk_summary: str = ""

    business_interpretation: str = ""

    errors: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    explanation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def successful(self) -> bool:
        return (
            self.status == "COMPLETED"
            and not self.errors
            and bool(self.final_decision_summary)
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "run_id": self.run_id,
            "status": self.status,
            "successful": self.successful,
            "product_id": self.product_id,
            "proposal_count": len(
                self.proposal_explanations
            ),
            "conflict_count": len(
                self.conflict_summary
            ),
            "negotiation_required": (
                self.negotiation_required
            ),
            "agreement_reached": (
                self.agreement_reached
            ),
            "selected_agent": self.selected_agent,
            "selected_operation": (
                self.selected_operation
            ),
            "final_decision_summary": (
                self.final_decision_summary
            ),
            "created_at": self.created_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "proposal_explanations": [
                proposal.to_dict()
                for proposal
                in self.proposal_explanations
            ],
            "conflict_summary": list(
                self.conflict_summary
            ),
            "negotiation_summary": list(
                self.negotiation_summary
            ),
            "mocra_summary": list(
                self.mocra_summary
            ),
            "confidence_summary": (
                self.confidence_summary
            ),
            "risk_summary": self.risk_summary,
            "business_interpretation": (
                self.business_interpretation
            ),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }