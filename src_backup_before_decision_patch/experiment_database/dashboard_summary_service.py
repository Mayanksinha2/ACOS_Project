from __future__ import annotations

from .dashboard_models import DashboardSummary
from .database import ExperimentDatabase
from .leaderboard_service import (
    LeaderboardService,
)
from .statistics_service import StatisticsService
from .trend_service import TrendAnalysisService
from .variant_statistics_service import (
    VariantStatisticsService,
)


class DashboardSummaryService:
    """
    Creates a dashboard-ready research summary.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.statistics = StatisticsService(
            database
        )
        self.variants = VariantStatisticsService(
            database
        )
        self.leaderboards = LeaderboardService(
            database
        )
        self.trends = TrendAnalysisService(
            database
        )

    def build_summary(
        self,
        leaderboard_limit: int = 10,
        rolling_window: int = 3,
    ) -> DashboardSummary:
        return DashboardSummary(
            database_statistics=(
                self.statistics
                .get_database_statistics()
            ),
            variant_summary=(
                self.variants
                .get_cross_experiment_summary()
            ),
            leaderboards=(
                self.leaderboards.build_bundle(
                    limit=leaderboard_limit
                )
            ),
            reward_trend=(
                self.trends.analyze_run_trend(
                    metric_name="reward",
                    rolling_window=rolling_window,
                )
            ),
        )
