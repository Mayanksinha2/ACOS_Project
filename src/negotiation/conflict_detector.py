from models.commerce_decision import CommerceDecision
from models.conflict_result import ConflictResult


class ConflictDetector:
    """Detect semantic conflicts without treating all cross-domain actions as conflicts."""

    OPPOSITE_OPERATIONS = {
        ("INCREASE", "DECREASE"),
        ("DECREASE", "INCREASE"),
        ("PROTECT_STOCK", "CLEAR_STOCK"),
        ("CLEAR_STOCK", "PROTECT_STOCK"),
    }

    def compare(
        self,
        first: CommerceDecision,
        second: CommerceDecision,
    ) -> ConflictResult:
        first_action = first.business_action
        second_action = second.business_action
        proposal_ids = [first.proposal_id, second.proposal_id]

        if first_action.target != second_action.target:
            return self._result(
                proposal_ids,
                "NO_CONFLICT",
                "MULTIPLE_TARGETS",
                "Proposals apply to different business targets.",
                0.0,
                False,
            )

        target = first_action.target
        first_effect = self._resolve_price_effect(first_action)
        second_effect = self._resolve_price_effect(second_action)

        # Price-domain advice is compared only when both proposals explicitly
        # provide a price effect. A stock or marketing action with no price
        # recommendation must not be converted into a price proposal.
        if first_effect is not None and second_effect is not None:
            if first_effect == second_effect:
                return self._result(
                    proposal_ids,
                    "SUPPORTING",
                    target,
                    f"Both proposals support the same price effect: {first_effect}.",
                    0.0,
                    False,
                )

            if "PRICE_MAINTAIN" in {first_effect, second_effect}:
                return self._result(
                    proposal_ids,
                    "SOFT_CONFLICT",
                    target,
                    f"One proposal recommends maintaining price while the other recommends {first_effect if second_effect == 'PRICE_MAINTAIN' else second_effect}.",
                    0.45,
                    True,
                )

            return self._result(
                proposal_ids,
                "HARD_CONFLICT",
                target,
                f"Proposals recommend opposite price effects: {first_effect} versus {second_effect}.",
                1.0,
                True,
            )

        operation_pair = (first_action.operation, second_action.operation)
        if (
            first_action.action_type == second_action.action_type
            and operation_pair in self.OPPOSITE_OPERATIONS
        ):
            return self._result(
                proposal_ids,
                "HARD_CONFLICT",
                target,
                "Proposals contain directly opposite operations in the same action domain.",
                1.0,
                True,
            )

        # Different action domains can normally coexist in a coordinated plan.
        if first_action.action_type != second_action.action_type:
            return self._result(
                proposal_ids,
                "NO_CONFLICT",
                target,
                "Proposals affect different action domains and can be coordinated.",
                0.0,
                False,
            )

        if first_action.operation != second_action.operation:
            return self._result(
                proposal_ids,
                "SOFT_CONFLICT",
                target,
                "Proposals use different operations within the same action domain.",
                0.6,
                True,
            )

        return self._result(
            proposal_ids,
            "SUPPORTING",
            target,
            "Proposals recommend compatible actions.",
            0.0,
            False,
        )

    @staticmethod
    def _result(proposal_ids, conflict_type, target, reason, severity, requires_negotiation):
        return ConflictResult(
            proposal_ids=proposal_ids,
            conflict_type=conflict_type,
            target=target,
            reason=reason,
            severity=severity,
            requires_negotiation=requires_negotiation,
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

        metadata = action.metadata or {}
        recommended_operation = metadata.get("recommended_price_operation")
        if recommended_operation == "INCREASE":
            return "PRICE_INCREASE"
        if recommended_operation == "DECREASE":
            return "PRICE_DECREASE"
        if recommended_operation == "MAINTAIN":
            return "PRICE_MAINTAIN"
        return None
