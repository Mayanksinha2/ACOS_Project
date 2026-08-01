from __future__ import annotations

from dataclasses import asdict, dataclass

from .experiment_result import ExperimentResult
from .experiment_status import ExperimentStatus


@dataclass(slots=True)
class ExperimentSummary:
    total_experiments: int = 0
    successful: int = 0
    failed: int = 0
    cancelled: int = 0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    average_reward: float | None = None
    best_reward: float | None = None
    worst_reward: float | None = None
    average_duration_seconds: float = 0.0
    conflict_count: int = 0
    negotiation_count: int = 0
    conflict_rate: float = 0.0
    negotiation_rate: float = 0.0

    @classmethod
    def from_results(
        cls,
        results: list[ExperimentResult],
    ) -> "ExperimentSummary":
        total = len(results)

        successful = sum(
            result.status
            == ExperimentStatus.SUCCESS
            for result in results
        )

        failed = sum(
            result.status
            == ExperimentStatus.FAILED
            for result in results
        )

        cancelled = sum(
            result.status
            == ExperimentStatus.CANCELLED
            for result in results
        )

        rewards = [
            result.reward
            for result in results
            if result.reward is not None
        ]

        conflict_count = sum(
            result.conflict_detected
            for result in results
        )

        negotiation_count = sum(
            result.negotiation_required
            for result in results
        )

        average_duration = (
            sum(
                result.duration_seconds
                for result in results
            )
            / total
            if total
            else 0.0
        )

        return cls(
            total_experiments=total,
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            success_rate=_percentage(
                successful,
                total,
            ),
            failure_rate=_percentage(
                failed,
                total,
            ),
            average_reward=(
                round(
                    sum(rewards) / len(rewards),
                    6,
                )
                if rewards
                else None
            ),
            best_reward=(
                max(rewards)
                if rewards
                else None
            ),
            worst_reward=(
                min(rewards)
                if rewards
                else None
            ),
            average_duration_seconds=round(
                average_duration,
                6,
            ),
            conflict_count=conflict_count,
            negotiation_count=negotiation_count,
            conflict_rate=_percentage(
                conflict_count,
                total,
            ),
            negotiation_rate=_percentage(
                negotiation_count,
                total,
            ),
        )

    def to_dict(self) -> dict:
        return asdict(self)


def _percentage(
    value: int,
    total: int,
) -> float:
    if not total:
        return 0.0

    return round(
        value / total * 100.0,
        2,
    )
