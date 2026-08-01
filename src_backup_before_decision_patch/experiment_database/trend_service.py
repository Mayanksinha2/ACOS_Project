from __future__ import annotations

from typing import Callable, List

from .database import ExperimentDatabase
from .models import RunRecord
from .serializers import run_from_row
from .trend_models import (
    TrendPoint,
    TrendSummary,
)


class TrendAnalysisService:
    """
    Builds chronological run trends and rolling means.
    """

    def __init__(
        self,
        database: ExperimentDatabase,
    ) -> None:
        self.database = database
        self.database.initialize()

    def analyze_run_trend(
        self,
        metric_name: str = "reward",
        experiment_id: str | None = None,
        variant_name: str | None = None,
        rolling_window: int = 3,
    ) -> TrendSummary:
        if rolling_window <= 0:
            raise ValueError(
                "rolling_window must be greater "
                "than zero."
            )

        runs = self._load_runs(
            experiment_id=experiment_id,
            variant_name=variant_name,
        )

        metric_getter = self._metric_getter(
            metric_name
        )

        values = [
            metric_getter(run)
            for run in runs
        ]

        points = [
            TrendPoint(
                index=index,
                timestamp=run.created_at,
                run_id=run.run_id,
                experiment_id=run.experiment_id,
                variant_name=run.variant_name,
                metric_value=value,
                rolling_mean=self._rolling_mean(
                    values,
                    index - 1,
                    rolling_window,
                ),
            )
            for index, (run, value)
            in enumerate(
                zip(runs, values),
                start=1,
            )
        ]

        non_null_values = [
            value
            for value in values
            if value is not None
        ]

        first_value = (
            non_null_values[0]
            if non_null_values
            else None
        )

        last_value = (
            non_null_values[-1]
            if non_null_values
            else None
        )

        if (
            first_value is None
            or last_value is None
        ):
            absolute_change = None
            percentage_change = None
            direction = "insufficient_data"
        else:
            absolute_change = (
                last_value - first_value
            )

            percentage_change = (
                None
                if first_value == 0
                else (
                    absolute_change
                    / abs(first_value)
                ) * 100.0
            )

            if absolute_change > 0:
                direction = "improving"
            elif absolute_change < 0:
                direction = "declining"
            else:
                direction = "stable"

        return TrendSummary(
            metric_name=metric_name,
            total_points=len(points),
            first_value=first_value,
            last_value=last_value,
            absolute_change=absolute_change,
            percentage_change=(
                percentage_change
            ),
            direction=direction,
            points=points,
        )

    def _load_runs(
        self,
        experiment_id: str | None,
        variant_name: str | None,
    ) -> List[RunRecord]:
        clauses: list[str] = []
        parameters: list[object] = []

        if experiment_id is not None:
            clauses.append(
                "experiment_id = ?"
            )
            parameters.append(experiment_id)

        if variant_name is not None:
            clauses.append(
                "variant_name = ?"
            )
            parameters.append(variant_name)

        where_sql = (
            ""
            if not clauses
            else " WHERE "
            + " AND ".join(clauses)
        )

        rows = self.database.fetch_all(
            f"""
            SELECT *
            FROM runs
            {where_sql}
            ORDER BY created_at ASC, run_id ASC
            """,
            tuple(parameters),
        )

        return [
            run_from_row(row)
            for row in rows
        ]

    def _metric_getter(
        self,
        metric_name: str,
    ) -> Callable[
        [RunRecord],
        float | None,
    ]:
        mapping = {
            "reward": (
                lambda run: run.reward
            ),
            "duration_seconds": (
                lambda run: run.duration_seconds
            ),
            "successful": (
                lambda run: (
                    1.0 if run.successful else 0.0
                )
            ),
            "conflict_detected": (
                lambda run: (
                    1.0
                    if run.conflict_detected
                    else 0.0
                )
            ),
            "negotiation_required": (
                lambda run: (
                    1.0
                    if run.negotiation_required
                    else 0.0
                )
            ),
        }

        if metric_name not in mapping:
            raise ValueError(
                "Unsupported trend metric: "
                f"{metric_name}"
            )

        return mapping[metric_name]

    def _rolling_mean(
        self,
        values: list[float | None],
        end_index: int,
        window: int,
    ) -> float | None:
        start_index = max(
            0,
            end_index - window + 1,
        )

        selected = [
            value
            for value in values[
                start_index:end_index + 1
            ]
            if value is not None
        ]

        if not selected:
            return None

        return sum(selected) / len(selected)
