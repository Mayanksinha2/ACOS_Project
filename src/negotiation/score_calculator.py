from typing import Optional

from learning.adaptive_weight_optimizer import (
    AdaptiveWeightOptimizer
)


class ScoreCalculator:
    """
    Calculates MOCRA scores for a CommerceDecision.

    The calculator supports adaptive confidence learning
    while preserving the original score dictionary format.
    """

    def __init__(
        self,
        confidence_weight: float = 0.40,
        risk_weight: float = 0.30,
        priority_weight: float = 0.30,
        adaptive_optimizer: Optional[
            AdaptiveWeightOptimizer
        ] = None
    ):
        self.confidence_weight = confidence_weight
        self.risk_weight = risk_weight
        self.priority_weight = priority_weight
        self.adaptive_optimizer = adaptive_optimizer

        self._validate_weights()

    def calculate(self, decision) -> dict:
        """
        Calculate normalized component scores and
        the final weighted MOCRA score.
        """

        confidence_score = (
            self._get_effective_confidence(
                decision
            )
        )

        risk_value = self._get_risk(
            decision
        )

        # Lower risk produces a higher MOCRA risk score.
        risk_score = 1.0 - risk_value

        priority_score = self._get_priority(
            decision
        )

        final_score = (
            self.confidence_weight
            * confidence_score
            + self.risk_weight
            * risk_score
            + self.priority_weight
            * priority_score
        )

        return {
            "confidence_score": round(
                confidence_score,
                4
            ),
            "risk_score": round(
                risk_score,
                4
            ),
            "priority_score": round(
                priority_score,
                4
            ),
            "final_score": round(
                self._clamp(
                    final_score,
                    0.0,
                    1.0
                ),
                4
            )
        }

    def calculate_score(self, decision) -> dict:
        """
        Compatibility alias for existing MOCRA code.
        """

        return self.calculate(decision)

    def calculate_value(self, decision) -> float:
        """
        Return only the final numeric score.
        """

        return self.calculate(
            decision
        )["final_score"]

    def _get_effective_confidence(
        self,
        decision
    ) -> float:
        """
        Return original confidence or confidence adjusted
        using the Adaptive Weight Optimizer.
        """

        original_confidence = getattr(
            decision,
            "confidence",
            None
        )

        if original_confidence is None:
            business_action = getattr(
                decision,
                "business_action",
                None
            )

            original_confidence = getattr(
                business_action,
                "confidence",
                0.0
            )

        original_confidence = (
            self._normalize_score(
                original_confidence
            )
        )

        if self.adaptive_optimizer is None:
            return original_confidence

        adaptive_score = (
            self.adaptive_optimizer.optimize_proposal(
                decision
            )
        )

        return self._clamp(
            adaptive_score.adjusted_confidence,
            0.0,
            1.0
        )

    def _get_risk(self, decision) -> float:
        """
        Extract risk from CommerceDecision or BusinessAction.
        """

        risk = getattr(
            decision,
            "risk",
            None
        )

        if risk is None:
            business_action = getattr(
                decision,
                "business_action",
                None
            )

            risk = getattr(
                business_action,
                "risk",
                0.0
            )

        return self._normalize_score(
            risk
        )

    def _get_priority(self, decision) -> float:
        """
        Extract priority from the nested BusinessAction.

        In the current ACOS model, priority is stored as:

        decision.business_action.priority
        """

        priority = getattr(
            decision,
            "priority",
            None
        )

        if priority is None:
            business_action = getattr(
                decision,
                "business_action",
                None
            )

            if business_action is not None:
                priority = getattr(
                    business_action,
                    "priority",
                    None
                )

        if priority is None:
            metadata = getattr(
                decision,
                "metadata",
                None
            ) or {}

            if isinstance(metadata, dict):
                priority = metadata.get(
                    "priority",
                    0.0
                )

        return self._normalize_score(
            priority if priority is not None else 0.0
        )

    @staticmethod
    def _normalize_score(value) -> float:
        """
        Normalize a score into the range 0.0–1.0.

        Examples:

        0.85 remains 0.85
        8 becomes 0.8
        10 becomes 1.0
        """

        if hasattr(value, "value"):
            value = value.value

        if not isinstance(
            value,
            (int, float)
        ):
            raise TypeError(
                "Score values must be numeric. "
                f"Received: {value!r}"
            )

        normalized = float(value)

        if normalized > 1.0:
            normalized = normalized / 10.0

        return ScoreCalculator._clamp(
            normalized,
            0.0,
            1.0
        )

    def _validate_weights(self) -> None:
        """
        Validate MOCRA weight configuration.
        """

        weights = {
            "confidence_weight": (
                self.confidence_weight
            ),
            "risk_weight": self.risk_weight,
            "priority_weight": (
                self.priority_weight
            )
        }

        for name, value in weights.items():
            if not isinstance(
                value,
                (int, float)
            ):
                raise TypeError(
                    f"{name} must be numeric."
                )

            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

        total = sum(weights.values())

        if abs(total - 1.0) > 0.0001:
            raise ValueError(
                "MOCRA weights must sum to 1.0. "
                f"Current total: {total}"
            )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float
    ) -> float:
        return max(
            minimum,
            min(value, maximum)
        )