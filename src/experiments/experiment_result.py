from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from models.acos_run_result import ACOSRunResult


@dataclass
class ScenarioExperimentResult:
    """
    Result of executing one scenario inside an experiment.
    """

    scenario_id: str
    scenario_name: str

    run_result: ACOSRunResult

    successful: bool
    execution_time_seconds: float

    error: str | None = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def summary(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "successful": self.successful,
            "execution_time_seconds": (
                self.execution_time_seconds
            ),
            "proposal_count": (
                self.run_result.proposal_count
            ),
            "conflict_count": (
                self.run_result.conflict_count
            ),
            "negotiation_required": (
                self.run_result.negotiation_required
            ),
            "final_decision": (
                self.run_result.final_decision
            ),
            "error": self.error,
        }


@dataclass
class ExperimentResult:
    """
    Aggregated result of a complete ACOS experiment.
    """

    experiment_name: str

    scenario_results: List[
        ScenarioExperimentResult
    ] = field(default_factory=list)

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    experiment_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    started_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    completed_at: str | None = None

    @property
    def total_scenarios(self) -> int:
        return len(self.scenario_results)

    @property
    def successful_scenarios(self) -> int:
        return sum(
            1
            for result in self.scenario_results
            if result.successful
        )

    @property
    def failed_scenarios(self) -> int:
        return (
            self.total_scenarios
            - self.successful_scenarios
        )

    @property
    def success_rate(self) -> float:
        if self.total_scenarios == 0:
            return 0.0

        return round(
            self.successful_scenarios
            / self.total_scenarios,
            4,
        )

    @property
    def negotiation_count(self) -> int:
        return sum(
            1
            for result in self.scenario_results
            if result.run_result.negotiation_required
        )

    @property
    def total_conflicts(self) -> int:
        return sum(
            result.run_result.conflict_count
            for result in self.scenario_results
        )

    @property
    def average_execution_time(self) -> float:
        if not self.scenario_results:
            return 0.0

        total_time = sum(
            result.execution_time_seconds
            for result in self.scenario_results
        )

        return round(
            total_time / self.total_scenarios,
            6,
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "experiment_name": self.experiment_name,
            "total_scenarios": self.total_scenarios,
            "successful_scenarios": (
                self.successful_scenarios
            ),
            "failed_scenarios": (
                self.failed_scenarios
            ),
            "success_rate": self.success_rate,
            "negotiation_count": (
                self.negotiation_count
            ),
            "total_conflicts": (
                self.total_conflicts
            ),
            "average_execution_time": (
                self.average_execution_time
            ),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }