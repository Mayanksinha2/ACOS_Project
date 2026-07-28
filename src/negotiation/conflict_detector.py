from models.commerce_decision import CommerceDecision
from models.conflict_result import ConflictResult


class ConflictDetector:
    """
    Detects semantic and operational conflicts between
    CommerceDecision proposals.
    """

    OPPOSITE_OPERATIONS = {
        ("INCREASE", "DECREASE"),
        ("DECREASE", "INCREASE"),
        ("PROTECT_STOCK", "CLEAR_STOCK"),
        ("CLEAR_STOCK", "PROTECT_STOCK")
    }

    PRICE_INCREASE_OPERATIONS = {
        "INCREASE",
        "PROTECT_STOCK"
    }

    PRICE_DECREASE_OPERATIONS = {
        "DECREASE",
        "CLEAR_STOCK"
    }

    def compare(
        self,
        first: CommerceDecision,
        second: CommerceDecision
    ) -> ConflictResult:

        first_action = first.business_action
        second_action = second.business_action

        proposal_ids = [
            first.proposal_id,
            second.proposal_id
        ]

        # Different products or entities do not conflict.
        if first_action.target != second_action.target:
            return ConflictResult(
                proposal_ids=proposal_ids,
                conflict_type="NO_CONFLICT",
                target="MULTIPLE_TARGETS",
                reason=(
                    "Proposals apply to different business targets"
                ),
                severity=0.0,
                requires_negotiation=False
            )

        target = first_action.target

        first_effect = self._resolve_price_effect(
            first_action
        )

        second_effect = self._resolve_price_effect(
            second_action
        )

        # Both proposals recommend the same strategic effect.
        if (
            first_effect is not None
            and first_effect == second_effect
        ):
            return ConflictResult(
                proposal_ids=proposal_ids,
                conflict_type="SUPPORTING",
                target=target,
                reason=(
                    "Both proposals support the same "
                    f"strategic effect: {first_effect}"
                ),
                severity=0.0,
                requires_negotiation=False
            )

        # Directly opposite strategic effects.
        if (
            first_effect is not None
            and second_effect is not None
            and first_effect != second_effect
        ):
            return ConflictResult(
                proposal_ids=proposal_ids,
                conflict_type="HARD_CONFLICT",
                target=target,
                reason=(
                    "Proposals recommend opposite strategic "
                    f"effects: {first_effect} versus "
                    f"{second_effect}"
                ),
                severity=1.0,
                requires_negotiation=True
            )

        # Direct operational opposition.
        operation_pair = (
            first_action.operation,
            second_action.operation
        )

        if operation_pair in self.OPPOSITE_OPERATIONS:
            return ConflictResult(
                proposal_ids=proposal_ids,
                conflict_type="HARD_CONFLICT",
                target=target,
                reason=(
                    "Proposals contain directly opposite "
                    "operations"
                ),
                severity=1.0,
                requires_negotiation=True
            )

        # Same target but unrelated actions may still interact.
        if first_action.action_type != second_action.action_type:
            return ConflictResult(
                proposal_ids=proposal_ids,
                conflict_type="SOFT_CONFLICT",
                target=target,
                reason=(
                    "Proposals affect the same target through "
                    "different action types and require impact "
                    "evaluation"
                ),
                severity=0.5,
                requires_negotiation=True
            )

        # Same target, same action type, but different operations.
        if first_action.operation != second_action.operation:
            return ConflictResult(
                proposal_ids=proposal_ids,
                conflict_type="SOFT_CONFLICT",
                target=target,
                reason=(
                    "Proposals use different operations for "
                    "the same action type"
                ),
                severity=0.6,
                requires_negotiation=True
            )

        return ConflictResult(
            proposal_ids=proposal_ids,
            conflict_type="SUPPORTING",
            target=target,
            reason=(
                "Proposals recommend compatible actions"
            ),
            severity=0.0,
            requires_negotiation=False
        )

    @staticmethod
    def _resolve_price_effect(action):

        if action.action_type == "PRICE_CHANGE":
            if action.operation == "INCREASE":
                return "PRICE_INCREASE"

            if action.operation == "DECREASE":
                return "PRICE_DECREASE"

            if action.operation == "MAINTAIN":
                return "PRICE_MAINTAIN"

        recommended_operation = action.metadata.get(
            "recommended_price_operation"
        )

        if recommended_operation == "INCREASE":
            return "PRICE_INCREASE"

        if recommended_operation == "DECREASE":
            return "PRICE_DECREASE"

        if recommended_operation == "MAINTAIN":
            return "PRICE_MAINTAIN"

        return None