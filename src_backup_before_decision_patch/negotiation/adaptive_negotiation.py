from typing import Dict, List, Optional

from models.commerce_decision import CommerceDecision
from models.negotiation_result import NegotiationResult


class AdaptiveNegotiationEngine:
    """
    Produces a compromise between conflicting price-related
    CommerceDecision proposals.
    """

    def __init__(
        self,
        confidence_weight: float = 0.5,
        risk_weight: float = 0.3,
        priority_weight: float = 0.2,
        maximum_adjustment: float = 20.0
    ):

        self.confidence_weight = confidence_weight
        self.risk_weight = risk_weight
        self.priority_weight = priority_weight
        self.maximum_adjustment = maximum_adjustment

        self._validate_weights()

    def _validate_weights(self) -> None:

        total = (
            self.confidence_weight
            + self.risk_weight
            + self.priority_weight
        )

        if abs(total - 1.0) > 0.000001:
            raise ValueError(
                "Negotiation weights must total 1.0"
            )

    def negotiate(
        self,
        decisions: List[CommerceDecision]
    ) -> NegotiationResult:

        if len(decisions) < 2:
            raise ValueError(
                "Negotiation requires at least two proposals."
            )

        targets = {
            decision.business_action.target
            for decision in decisions
        }

        if len(targets) != 1:
            raise ValueError(
                "All negotiated proposals must target "
                "the same business entity."
            )

        target = next(iter(targets))

        weighted_adjustment_total = 0.0
        influence_total = 0.0

        participant_agents = []
        influence_scores: Dict[str, float] = {}
        explanation = []

        valid_proposal_count = 0

        for decision in decisions:

            signed_adjustment = (
                self._extract_signed_adjustment(
                    decision
                )
            )

            if signed_adjustment is None:
                explanation.append(
                    (
                        f"{decision.agent_id} was excluded "
                        "because it did not provide a "
                        "price-related recommendation."
                    )
                )

                continue

            influence = self._calculate_influence(
                decision
            )

            participant_agents.append(
                decision.agent_id
            )

            influence_scores[
                decision.agent_id
            ] = round(influence, 6)

            weighted_adjustment_total += (
                signed_adjustment * influence
            )

            influence_total += influence
            valid_proposal_count += 1

            explanation.append(
                (
                    f"{decision.agent_id} proposed "
                    f"{signed_adjustment:+.2f}% with an "
                    f"influence score of {influence:.3f}."
                )
            )

        if valid_proposal_count < 2:
            raise ValueError(
                "At least two price-related proposals "
                "are required."
            )

        if influence_total == 0:
            raise ValueError(
                "Total negotiation influence cannot be zero."
            )

        negotiated_adjustment = (
            weighted_adjustment_total
            / influence_total
        )

        negotiated_adjustment = max(
            -self.maximum_adjustment,
            min(
                self.maximum_adjustment,
                negotiated_adjustment
            )
        )

        final_operation, final_value = (
            self._resolve_final_action(
                negotiated_adjustment
            )
        )

        explanation.append(
            (
                f"The weighted negotiated adjustment was "
                f"{negotiated_adjustment:+.2f}%."
            )
        )

        explanation.append(
            (
                f"Final agreement: {final_operation} "
                f"price by {final_value:.2f}%."
            )
        )

        return NegotiationResult(
            target=target,
            agreement_reached=True,
            final_operation=final_operation,
            final_value=round(final_value, 2),
            unit="PERCENT",
            participant_agents=participant_agents,
            influence_scores=influence_scores,
            rounds_completed=1,
            explanation=explanation
        )

    def _calculate_influence(
        self,
        decision: CommerceDecision
    ) -> float:

        confidence = decision.confidence
        risk_adjusted = 1.0 - decision.risk

        priority = (
            decision.business_action.priority / 10
        )

        return (
            self.confidence_weight * confidence
            + self.risk_weight * risk_adjusted
            + self.priority_weight * priority
        )

    @staticmethod
    def _extract_signed_adjustment(
        decision: CommerceDecision
    ) -> Optional[float]:

        action = decision.business_action

        operation = action.operation
        value = action.value or 0.0

        if action.action_type == "PRICE_CHANGE":

            if operation == "INCREASE":
                return float(value)

            if operation == "DECREASE":
                return -float(value)

            if operation == "MAINTAIN":
                return 0.0

        recommended_operation = action.metadata.get(
            "recommended_price_operation"
        )

        recommended_value = action.metadata.get(
            "recommended_price_value",
            0.0
        )

        if recommended_operation == "INCREASE":
            return float(recommended_value)

        if recommended_operation == "DECREASE":
            return -float(recommended_value)

        if recommended_operation == "MAINTAIN":
            return 0.0

        return None

    @staticmethod
    def _resolve_final_action(
        signed_adjustment: float
    ):

        tolerance = 0.5

        if signed_adjustment > tolerance:
            return "INCREASE", abs(signed_adjustment)

        if signed_adjustment < -tolerance:
            return "DECREASE", abs(signed_adjustment)

        return "MAINTAIN", 0.0