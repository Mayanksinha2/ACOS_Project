from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ExperimentAnalytics:
    """
    Aggregated analytics generated from an ACOS experiment.
    """

    experiment_id: str
    experiment_name: str

    total_scenarios: int = 0
    successful_scenarios: int = 0
    failed_scenarios: int = 0

    success_rate: float = 0.0
    failure_rate: float = 0.0

    total_proposals: int = 0
    total_conflicts: int = 0

    negotiation_count: int = 0
    negotiation_rate: float = 0.0

    agreement_count: int = 0
    agreement_rate: float = 0.0

    average_execution_time: float = 0.0
    minimum_execution_time: float = 0.0
    maximum_execution_time: float = 0.0

    average_confidence: float = 0.0
    average_risk: float = 0.0
    average_mocra_score: float = 0.0

    selected_agent_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    selected_agent_percentage: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    operation_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    operation_percentage: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    proposal_agent_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    conflict_distribution: Dict[
        int,
        int,
    ] = field(default_factory=dict)

    scenario_summaries: List[
        Dict[str, Any]
    ] = field(default_factory=list)

    errors: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    analytics_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    generated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def successful(self) -> bool:
        return not self.errors

    def summary(self) -> Dict[str, Any]:
        return {
            "analytics_id": self.analytics_id,
            "experiment_id": self.experiment_id,
            "experiment_name": self.experiment_name,
            "successful": self.successful,
            "total_scenarios": self.total_scenarios,
            "successful_scenarios": (
                self.successful_scenarios
            ),
            "failed_scenarios": (
                self.failed_scenarios
            ),
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "total_proposals": self.total_proposals,
            "total_conflicts": self.total_conflicts,
            "negotiation_count": (
                self.negotiation_count
            ),
            "negotiation_rate": (
                self.negotiation_rate
            ),
            "agreement_count": self.agreement_count,
            "agreement_rate": self.agreement_rate,
            "average_execution_time": (
                self.average_execution_time
            ),
            "minimum_execution_time": (
                self.minimum_execution_time
            ),
            "maximum_execution_time": (
                self.maximum_execution_time
            ),
            "average_confidence": (
                self.average_confidence
            ),
            "average_risk": self.average_risk,
            "average_mocra_score": (
                self.average_mocra_score
            ),
            "selected_agent_frequency": dict(
                self.selected_agent_frequency
            ),
            "selected_agent_percentage": dict(
                self.selected_agent_percentage
            ),
            "operation_frequency": dict(
                self.operation_frequency
            ),
            "operation_percentage": dict(
                self.operation_percentage
            ),
            "generated_at": self.generated_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "proposal_agent_frequency": dict(
                self.proposal_agent_frequency
            ),
            "conflict_distribution": dict(
                self.conflict_distribution
            ),
            "scenario_summaries": list(
                self.scenario_summaries
            ),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }