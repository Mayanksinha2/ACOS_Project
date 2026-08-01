from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class RunLeaderboardEntry:
    rank: int
    run_id: str
    experiment_id: str
    variant_name: str
    metric_name: str
    metric_value: float | None
    successful: bool
    created_at: str | None


@dataclass(slots=True)
class VariantLeaderboardEntry:
    rank: int
    variant_name: str
    metric_name: str
    metric_value: float | None
    total_runs: int
    experiment_count: int
    success_rate: float


@dataclass(slots=True)
class ExperimentLeaderboardEntry:
    rank: int
    experiment_id: str
    metric_name: str
    metric_value: float | None
    total_runs: int
    success_rate: float


@dataclass(slots=True)
class LeaderboardBundle:
    run_leaderboard: List[RunLeaderboardEntry] = field(
        default_factory=list
    )
    variant_leaderboard: List[
        VariantLeaderboardEntry
    ] = field(default_factory=list)
    experiment_leaderboard: List[
        ExperimentLeaderboardEntry
    ] = field(default_factory=list)
