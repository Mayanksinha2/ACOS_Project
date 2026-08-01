from __future__ import annotations

from dataclasses import dataclass

from .leaderboard_models import LeaderboardBundle
from .statistics_models import DatabaseStatistics
from .trend_models import TrendSummary
from .variant_statistics_models import (
    CrossExperimentSummary,
)


@dataclass(slots=True)
class DashboardSummary:
    database_statistics: DatabaseStatistics
    variant_summary: CrossExperimentSummary
    leaderboards: LeaderboardBundle
    reward_trend: TrendSummary
