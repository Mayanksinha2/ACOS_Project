from __future__ import annotations

from typing import Any

from benchmarking.benchmark_result import (
    StrategyDecision,
)


class BenchmarkRewardEvaluator:
    """
    Common reward function used to compare strategies.

    Higher reward is better.
    """

    def evaluate(
        self,
        decision: StrategyDecision,
        business_state: Any = None,
    ) -> float:
        if not decision.successful:
            return -1.0

        confidence = self._clamp(
            decision.confidence
        )

        risk = self._clamp(
            decision.risk
        )

        score = self._clamp(
            decision.score
        )

        context_bonus = (
            self._context_alignment_bonus(
                decision,
                business_state,
            )
        )

        reward = (
            (0.40 * confidence)
            + (0.25 * (1.0 - risk))
            + (0.20 * score)
            + (0.15 * context_bonus)
        )

        return round(
            self._clamp(reward),
            6,
        )

    def _context_alignment_bonus(
        self,
        decision: StrategyDecision,
        business_state: Any,
    ) -> float:
        operation = (
            decision.selected_operation
            or ""
        ).upper()

        inventory = self._read_inventory(
            business_state
        )

        demand = self._read_demand(
            business_state
        )

        if (
            inventory <= 20
            and operation
            == "PROTECT_STOCK"
        ):
            return 1.0

        if (
            inventory >= 120
            and operation
            == "CLEAR_STOCK"
        ):
            return 1.0

        if (
            demand == "HIGH"
            and operation == "INCREASE"
        ):
            return 1.0

        if (
            demand == "LOW"
            and operation == "DECREASE"
        ):
            return 1.0

        if operation == "MAINTAIN":
            return 0.6

        return 0.3

    @staticmethod
    def _read_inventory(
        business_state: Any,
    ) -> float:
        if business_state is None:
            return 0.0

        for field_name in (
            "inventory",
            "inventory_level",
            "stock",
            "stock_level",
        ):
            value = getattr(
                business_state,
                field_name,
                None,
            )

            if value is not None:
                return float(value)

        product = getattr(
            business_state,
            "product",
            None,
        )

        if product is not None:
            for field_name in (
                "inventory",
                "inventory_level",
                "stock",
            ):
                value = getattr(
                    product,
                    field_name,
                    None,
                )

                if value is not None:
                    return float(value)

        return 0.0

    @staticmethod
    def _read_demand(
        business_state: Any,
    ) -> str:
        if business_state is None:
            return "MEDIUM"

        for field_name in (
            "demand_level",
            "demand",
        ):
            value = getattr(
                business_state,
                field_name,
                None,
            )

            if value is not None:
                return str(value).upper()

        market = getattr(
            business_state,
            "market",
            None,
        )

        if market is not None:
            value = getattr(
                market,
                "demand_level",
                None,
            )

            if value is not None:
                return str(value).upper()

        return "MEDIUM"

    @staticmethod
    def _clamp(value: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0

        return max(
            0.0,
            min(1.0, numeric),
        )