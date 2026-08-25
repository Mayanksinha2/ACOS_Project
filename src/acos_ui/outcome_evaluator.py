from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .outcome_models import (
    MetricChange,
    OutcomeEvaluation,
    OutcomeMetrics,
)
from .presentation import build_final_plan


@dataclass(frozen=True, slots=True)
class RewardWeights:
    revenue: float = 0.20
    profit: float = 0.35
    conversion_rate: float = 0.25
    inventory_health: float = 0.10
    customer_satisfaction: float = 0.10

    def validate(self) -> None:
        values = (
            self.revenue,
            self.profit,
            self.conversion_rate,
            self.inventory_health,
            self.customer_satisfaction,
        )
        if any(value < 0 for value in values):
            raise ValueError("Reward weights cannot be negative.")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("Reward weights must sum to 1.0.")


class UIOutcomeEvaluator:
    """
    Transparent dashboard-level outcome evaluator.

    It does not replace the existing ACOS learning engine. It creates a
    persistent, explainable feedback record that can be bridged into the
    research learning modules in the next integration step.
    """

    def __init__(
        self,
        weights: RewardWeights | None = None,
    ) -> None:
        self.weights = weights or RewardWeights()
        self.weights.validate()

    def evaluate(
        self,
        payload: dict[str, Any],
        before: OutcomeMetrics,
        after: OutcomeMetrics,
        notes: str = "",
    ) -> OutcomeEvaluation:
        before.validate()
        after.validate()

        changes = (
            self._change(
                "Revenue",
                before.revenue,
                after.revenue,
                self.weights.revenue,
            ),
            self._change(
                "Profit",
                before.profit,
                after.profit,
                self.weights.profit,
            ),
            self._change(
                "Conversion",
                before.conversion_rate,
                after.conversion_rate,
                self.weights.conversion_rate,
            ),
            self._change(
                "Inventory health",
                before.inventory_health,
                after.inventory_health,
                self.weights.inventory_health,
            ),
            self._change(
                "Customer satisfaction",
                before.customer_satisfaction,
                after.customer_satisfaction,
                self.weights.customer_satisfaction,
            ),
        )

        reward = round(
            max(
                -1.0,
                min(
                    1.0,
                    sum(item.contribution for item in changes),
                ),
            ),
            6,
        )

        if reward >= 0.05:
            classification = "SUCCESS"
        elif reward <= -0.05:
            classification = "FAILURE"
        else:
            classification = "NEUTRAL"

        plan = build_final_plan(payload)
        scenario = payload.get("scenario") or {}
        summary = payload.get("summary") or {}

        return OutcomeEvaluation(
            evaluation_id=OutcomeEvaluation.new_id(),
            run_id=str(payload.get("run_id") or ""),
            experiment_id=(
                str(summary.get("experiment_id"))
                if summary.get("experiment_id")
                else None
            ),
            product_id=str(
                scenario.get("product_id")
                or plan.product_id
            ),
            winning_agent=plan.winning_agent,
            decision_type=plan.resolution_method,
            primary_operation=plan.price_operation,
            primary_value=plan.price_change_percent,
            primary_unit="PERCENT",
            reward=reward,
            classification=classification,
            successful=classification == "SUCCESS",
            before=before,
            after=after,
            metric_changes=changes,
            notes=notes.strip(),
            evaluated_at=OutcomeEvaluation.timestamp(),
            run_snapshot=payload,
        )

    def _change(
        self,
        name: str,
        before: float,
        after: float,
        weight: float,
    ) -> MetricChange:
        relative = self._relative_change(before, after)
        bounded = max(-1.0, min(1.0, relative))
        contribution = bounded * weight

        return MetricChange(
            metric=name,
            before=before,
            after=after,
            relative_change=relative,
            contribution=contribution,
            weight=weight,
        )

    @staticmethod
    def _relative_change(
        before: float,
        after: float,
    ) -> float:
        if before == 0:
            if after == 0:
                return 0.0
            return 1.0 if after > 0 else -1.0
        return (after - before) / abs(before)
