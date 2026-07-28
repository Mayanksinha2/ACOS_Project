from __future__ import annotations

import random
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, List, Optional

from benchmarking.benchmark_result import (
    StrategyDecision,
)


class BenchmarkStrategy(ABC):
    """
    Base class for all benchmark strategies.
    """

    strategy_name: str = "BaseStrategy"

    @abstractmethod
    def select(
        self,
        proposals: List[Any],
        run_result: Any = None,
        business_state: Any = None,
    ) -> StrategyDecision:
        raise NotImplementedError

    @staticmethod
    def _proposal_to_decision(
        strategy_name: str,
        proposal: Any,
        execution_time: float,
        score: Optional[float] = None,
    ) -> StrategyDecision:
        action = getattr(
            proposal,
            "business_action",
            None,
        )

        operation = getattr(
            action,
            "operation",
            None,
        )

        return StrategyDecision(
            strategy_name=strategy_name,
            selected_agent=str(
                getattr(
                    proposal,
                    "agent_id",
                    "UnknownAgent",
                )
            ),
            selected_operation=(
                str(operation)
                if operation is not None
                else None
            ),
            selected_proposal_id=str(
                getattr(
                    proposal,
                    "proposal_id",
                    "",
                )
            ) or None,
            confidence=float(
                getattr(
                    proposal,
                    "confidence",
                    0.0,
                )
                or 0.0
            ),
            risk=float(
                getattr(
                    proposal,
                    "risk",
                    0.0,
                )
                or 0.0
            ),
            score=(
                float(score)
                if score is not None
                else 0.0
            ),
            execution_time_seconds=(
                execution_time
            ),
        )

    @staticmethod
    def _failure(
        strategy_name: str,
        error: str,
        execution_time: float = 0.0,
    ) -> StrategyDecision:
        return StrategyDecision(
            strategy_name=strategy_name,
            successful=False,
            error=error,
            execution_time_seconds=(
                execution_time
            ),
        )


class ACOSStrategy(BenchmarkStrategy):
    """
    Uses the actual ACOS/MOCRA result.
    """

    strategy_name = "ACOS"

    def select(
        self,
        proposals: List[Any],
        run_result: Any = None,
        business_state: Any = None,
    ) -> StrategyDecision:
        started = perf_counter()

        try:
            if run_result is None:
                raise ValueError(
                    "run_result is required."
                )

            mocra_result = getattr(
                run_result,
                "mocra_result",
                None,
            )

            if mocra_result is None:
                raise ValueError(
                    "MOCRA result is missing."
                )

            winning_decision = getattr(
                mocra_result,
                "winning_decision",
                None,
            )

            if winning_decision is None:
                raise ValueError(
                    "Winning decision is missing."
                )

            winning_score = float(
                getattr(
                    mocra_result,
                    "winning_score",
                    0.0,
                )
                or 0.0
            )

            elapsed = perf_counter() - started

            decision = self._proposal_to_decision(
                self.strategy_name,
                winning_decision,
                elapsed,
                score=winning_score,
            )

            decision.metadata.update(
                {
                    "negotiation_required": bool(
                        getattr(
                            run_result,
                            "negotiation_required",
                            False,
                        )
                    ),
                    "conflict_count": len(
                        list(
                            getattr(
                                run_result,
                                "conflicts",
                                [],
                            )
                            or []
                        )
                    ),
                }
            )

            return decision

        except Exception as error:
            return self._failure(
                self.strategy_name,
                f"{type(error).__name__}: {error}",
                perf_counter() - started,
            )


class HighestConfidenceStrategy(
    BenchmarkStrategy
):
    """
    Selects the proposal with the highest confidence.
    """

    strategy_name = "HighestConfidence"

    def select(
        self,
        proposals: List[Any],
        run_result: Any = None,
        business_state: Any = None,
    ) -> StrategyDecision:
        started = perf_counter()

        try:
            if not proposals:
                raise ValueError(
                    "No proposals available."
                )

            selected = max(
                proposals,
                key=lambda proposal: float(
                    getattr(
                        proposal,
                        "confidence",
                        0.0,
                    )
                    or 0.0
                ),
            )

            return self._proposal_to_decision(
                self.strategy_name,
                selected,
                perf_counter() - started,
                score=float(
                    getattr(
                        selected,
                        "confidence",
                        0.0,
                    )
                    or 0.0
                ),
            )

        except Exception as error:
            return self._failure(
                self.strategy_name,
                f"{type(error).__name__}: {error}",
                perf_counter() - started,
            )


class RandomSelectionStrategy(
    BenchmarkStrategy
):
    """
    Randomly selects one proposal.
    """

    strategy_name = "RandomSelection"

    def __init__(
        self,
        random_seed: Optional[int] = None,
    ) -> None:
        self._random = random.Random(
            random_seed
        )

    def select(
        self,
        proposals: List[Any],
        run_result: Any = None,
        business_state: Any = None,
    ) -> StrategyDecision:
        started = perf_counter()

        try:
            if not proposals:
                raise ValueError(
                    "No proposals available."
                )

            selected = self._random.choice(
                proposals
            )

            return self._proposal_to_decision(
                self.strategy_name,
                selected,
                perf_counter() - started,
            )

        except Exception as error:
            return self._failure(
                self.strategy_name,
                f"{type(error).__name__}: {error}",
                perf_counter() - started,
            )


class RuleBasedStrategy(BenchmarkStrategy):
    """
    Traditional fixed-rule baseline.

    Rules:
    - Very low stock -> protect stock
    - Excess stock -> clear stock
    - High demand -> increase
    - Low demand -> decrease
    - Otherwise -> maintain
    """

    strategy_name = "RuleBased"

    def select(
        self,
        proposals: List[Any],
        run_result: Any = None,
        business_state: Any = None,
    ) -> StrategyDecision:
        started = perf_counter()

        try:
            if not proposals:
                raise ValueError(
                    "No proposals available."
                )

            inventory = self._read_inventory(
                business_state
            )

            demand = self._read_demand(
                business_state
            )

            desired_operation = "MAINTAIN"

            if inventory <= 20:
                desired_operation = (
                    "PROTECT_STOCK"
                )

            elif inventory >= 120:
                desired_operation = (
                    "CLEAR_STOCK"
                )

            elif demand == "HIGH":
                desired_operation = "INCREASE"

            elif demand == "LOW":
                desired_operation = "DECREASE"

            selected = self._find_operation(
                proposals,
                desired_operation,
            )

            if selected is None:
                selected = max(
                    proposals,
                    key=lambda proposal: float(
                        getattr(
                            proposal,
                            "confidence",
                            0.0,
                        )
                        or 0.0
                    ),
                )

            decision = (
                self._proposal_to_decision(
                    self.strategy_name,
                    selected,
                    perf_counter() - started,
                )
            )

            decision.metadata[
                "desired_operation"
            ] = desired_operation

            return decision

        except Exception as error:
            return self._failure(
                self.strategy_name,
                f"{type(error).__name__}: {error}",
                perf_counter() - started,
            )

    @staticmethod
    def _find_operation(
        proposals: List[Any],
        desired_operation: str,
    ) -> Optional[Any]:
        for proposal in proposals:
            action = getattr(
                proposal,
                "business_action",
                None,
            )

            operation = getattr(
                action,
                "operation",
                None,
            )

            if (
                operation is not None
                and str(operation)
                == desired_operation
            ):
                return proposal

        return None

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