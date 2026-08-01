from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class StrategyDecision:
    """
    Decision produced by one benchmark strategy.
    """

    strategy_name: str

    selected_agent: Optional[str] = None
    selected_operation: Optional[str] = None
    selected_proposal_id: Optional[str] = None

    confidence: float = 0.0
    risk: float = 0.0
    score: float = 0.0
    reward: float = 0.0

    execution_time_seconds: float = 0.0

    successful: bool = True
    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    decision_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "strategy_name": self.strategy_name,
            "selected_agent": self.selected_agent,
            "selected_operation": (
                self.selected_operation
            ),
            "selected_proposal_id": (
                self.selected_proposal_id
            ),
            "confidence": self.confidence,
            "risk": self.risk,
            "score": self.score,
            "reward": self.reward,
            "execution_time_seconds": (
                self.execution_time_seconds
            ),
            "successful": self.successful,
            "error": self.error,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ScenarioBenchmarkResult:
    """
    Benchmark comparison for one scenario.
    """

    scenario_id: str
    scenario_name: str

    strategy_decisions: Dict[
        str,
        StrategyDecision,
    ] = field(default_factory=dict)

    acos_strategy_name: str = "ACOS"

    agreement_with_acos: Dict[
        str,
        bool,
    ] = field(default_factory=dict)

    best_reward_strategy: Optional[str] = None
    lowest_risk_strategy: Optional[str] = None
    highest_confidence_strategy: Optional[str] = None
    fastest_strategy: Optional[str] = None

    successful: bool = True

    errors: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    benchmark_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def strategy_count(self) -> int:
        return len(self.strategy_decisions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "strategy_count": self.strategy_count,
            "strategy_decisions": {
                name: decision.to_dict()
                for name, decision
                in self.strategy_decisions.items()
            },
            "agreement_with_acos": dict(
                self.agreement_with_acos
            ),
            "best_reward_strategy": (
                self.best_reward_strategy
            ),
            "lowest_risk_strategy": (
                self.lowest_risk_strategy
            ),
            "highest_confidence_strategy": (
                self.highest_confidence_strategy
            ),
            "fastest_strategy": (
                self.fastest_strategy
            ),
            "successful": self.successful,
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class BenchmarkExperimentResult:
    """
    Aggregated benchmark result across scenarios.
    """

    experiment_id: str
    experiment_name: str

    scenario_results: List[
        ScenarioBenchmarkResult
    ] = field(default_factory=list)

    strategy_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    reward_win_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    risk_win_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    confidence_win_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    speed_win_frequency: Dict[
        str,
        int,
    ] = field(default_factory=dict)

    average_reward: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    average_risk: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    average_confidence: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    average_execution_time: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    acos_agreement_rate: Dict[
        str,
        float,
    ] = field(default_factory=dict)

    total_scenarios: int = 0
    successful_scenarios: int = 0
    failed_scenarios: int = 0

    errors: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @property
    def successful(self) -> bool:
        return not self.errors

    def summary(self) -> Dict[str, Any]:
        return {
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
            "reward_win_frequency": dict(
                self.reward_win_frequency
            ),
            "risk_win_frequency": dict(
                self.risk_win_frequency
            ),
            "confidence_win_frequency": dict(
                self.confidence_win_frequency
            ),
            "speed_win_frequency": dict(
                self.speed_win_frequency
            ),
            "average_reward": dict(
                self.average_reward
            ),
            "average_risk": dict(
                self.average_risk
            ),
            "average_confidence": dict(
                self.average_confidence
            ),
            "average_execution_time": dict(
                self.average_execution_time
            ),
            "acos_agreement_rate": dict(
                self.acos_agreement_rate
            ),
            "created_at": self.created_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "strategy_frequency": dict(
                self.strategy_frequency
            ),
            "scenario_results": [
                result.to_dict()
                for result in self.scenario_results
            ],
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }