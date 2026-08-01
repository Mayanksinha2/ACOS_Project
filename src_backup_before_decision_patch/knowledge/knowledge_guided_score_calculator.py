from typing import Any, Dict, Optional

from knowledge.knowledge_advisor import (
    KnowledgeAdvisor
)


class KnowledgeGuidedScoreCalculator:
    """
    Backward-compatible wrapper around the existing
    MOCRA ScoreCalculator.

    The original calculator still produces:

    {
        "confidence_score": ...,
        "risk_score": ...,
        "priority_score": ...,
        "final_score": ...
    }

    This wrapper keeps those fields and replaces only
    final_score with the knowledge-adjusted result.
    """

    def __init__(
        self,
        base_score_calculator: Any,
        knowledge_advisor: KnowledgeAdvisor
    ):
        if not hasattr(
            base_score_calculator,
            "calculate"
        ):
            raise TypeError(
                "base_score_calculator must provide "
                "a calculate() method."
            )

        if not isinstance(
            knowledge_advisor,
            KnowledgeAdvisor
        ):
            raise TypeError(
                "knowledge_advisor must be a "
                "KnowledgeAdvisor."
            )

        self.base_score_calculator = (
            base_score_calculator
        )

        self.knowledge_advisor = (
            knowledge_advisor
        )

    def calculate(
        self,
        decision: Any
    ) -> Dict[str, Any]:
        """
        Calculate the original MOCRA score and then
        apply relevant stored knowledge.
        """

        base_result = (
            self.base_score_calculator.calculate(
                decision
            )
        )

        if not isinstance(
            base_result,
            dict
        ):
            raise TypeError(
                "The base ScoreCalculator.calculate() "
                "method must return a dictionary."
            )

        if "final_score" not in base_result:
            raise KeyError(
                "The base score result must contain "
                "'final_score'."
            )

        result = dict(
            base_result
        )

        original_final_score = float(
            result["final_score"]
        )

        agent_name = self._extract_agent_name(
            decision
        )

        operation = self._extract_operation(
            decision
        )

        context = self._extract_context(
            decision
        )

        adjustment = (
            self.knowledge_advisor.advise(
                original_score=(
                    original_final_score
                ),
                agent_name=agent_name,
                operation=operation,
                context=context
            )
        )

        result["base_final_score"] = round(
            original_final_score,
            4
        )

        result["final_score"] = (
            adjustment.adjusted_score
        )

        result["knowledge_modifier"] = (
            adjustment.adjustment_modifier
        )

        result["knowledge_applied"] = (
            adjustment.knowledge_applied
        )

        result["knowledge_adjustment"] = (
            adjustment.to_dict()
        )

        return result

    def calculate_value(
        self,
        decision: Any
    ) -> float:
        """
        Return only the final knowledge-guided score.
        """

        return float(
            self.calculate(
                decision
            )["final_score"]
        )

    @staticmethod
    def _extract_agent_name(
        decision: Any
    ) -> str:
        fields = [
            "source_agent",
            "agent_name",
            "agent_id",
            "proposed_by",
            "sender"
        ]

        for field_name in fields:
            value = getattr(
                decision,
                field_name,
                None
            )

            if value:
                return str(
                    value
                )

        metadata = getattr(
            decision,
            "metadata",
            None
        ) or {}

        if isinstance(
            metadata,
            dict
        ):
            for field_name in fields:
                value = metadata.get(
                    field_name
                )

                if value:
                    return str(
                        value
                    )

        return "UNKNOWN"

    @staticmethod
    def _extract_operation(
        decision: Any
    ) -> str:
        direct_operation = getattr(
            decision,
            "operation",
            None
        )

        if direct_operation:
            return str(
                direct_operation
            ).upper()

        action_fields = [
            "business_action",
            "action",
            "proposed_action"
        ]

        for action_field in action_fields:
            action = getattr(
                decision,
                action_field,
                None
            )

            if action is None:
                continue

            operation = getattr(
                action,
                "operation",
                None
            )

            if operation:
                return str(
                    operation
                ).upper()

            action_type = getattr(
                action,
                "action_type",
                None
            )

            if action_type:
                return str(
                    action_type
                ).upper()

        metadata = getattr(
            decision,
            "metadata",
            None
        ) or {}

        if isinstance(
            metadata,
            dict
        ):
            operation = metadata.get(
                "operation"
            )

            if operation:
                return str(
                    operation
                ).upper()

        return "UNKNOWN"

    @staticmethod
    def _extract_context(
        decision: Any
    ) -> Dict[str, Any]:
        context = getattr(
            decision,
            "context",
            None
        )

        if isinstance(
            context,
            dict
        ):
            return dict(
                context
            )

        metadata = getattr(
            decision,
            "metadata",
            None
        ) or {}

        if not isinstance(
            metadata,
            dict
        ):
            return {}

        metadata_context = metadata.get(
            "context"
        )

        if isinstance(
            metadata_context,
            dict
        ):
            return dict(
                metadata_context
            )

        supported_keys = {
            "season",
            "demand_level",
            "inventory_level",
            "campaign",
            "customer_segment",
            "market_condition"
        }

        return {
            key: value
            for key, value in metadata.items()
            if key in supported_keys
        }