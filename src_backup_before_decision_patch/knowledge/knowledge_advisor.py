from typing import Any, Dict, List, Optional

from knowledge.knowledge_base import (
    KnowledgeBase
)
from models.knowledge_adjustment import (
    KnowledgeAdjustment
)
from models.knowledge_entry import (
    KnowledgeEntry
)


class KnowledgeAdvisor:
    """
    Uses the persistent Knowledge Base to advise
    future autonomous decisions.

    It converts learned knowledge into a bounded
    decision-score modifier.
    """

    POSITIVE_TYPES = {
        "AGENT_WEIGHT_INCREASE",
        "OPERATION_PREFERENCE",
        "STRATEGY_REINFORCEMENT"
    }

    NEGATIVE_TYPES = {
        "AGENT_WEIGHT_REDUCTION",
        "OPERATION_AVOIDANCE",
        "STRATEGY_CORRECTION",
        "SYSTEM_STABILIZATION"
    }

    PRIORITY_WEIGHTS = {
        "LOW": 0.50,
        "MEDIUM": 0.75,
        "HIGH": 1.00,
        "CRITICAL": 1.20
    }

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        minimum_confidence: float = 0.40,
        maximum_adjustment: float = 0.30
    ):
        if not isinstance(
            knowledge_base,
            KnowledgeBase
        ):
            raise TypeError(
                "knowledge_base must be a KnowledgeBase."
            )

        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be "
                "between 0 and 1."
            )

        if not 0.0 <= maximum_adjustment <= 0.50:
            raise ValueError(
                "maximum_adjustment must be "
                "between 0 and 0.50."
            )

        self.knowledge_base = knowledge_base
        self.minimum_confidence = (
            minimum_confidence
        )
        self.maximum_adjustment = (
            maximum_adjustment
        )

    def advise(
        self,
        original_score: float,
        agent_name: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> KnowledgeAdjustment:
        """
        Apply relevant stored knowledge to a score.
        """

        original_score = self._clamp(
            float(original_score),
            0.0,
            1.0
        )

        agent_name = (
            str(agent_name or "UNKNOWN")
            .strip()
        )

        operation = (
            str(operation or "UNKNOWN")
            .strip()
            .upper()
        )

        context = context or {}

        relevant_entries = (
            self.knowledge_base
            .get_relevant_knowledge(
                agent_name=agent_name,
                operation=operation,
                context=context,
                minimum_confidence=(
                    self.minimum_confidence
                )
            )
        )

        applicable_entries = [
            entry
            for entry in relevant_entries
            if self._is_applicable(
                entry=entry,
                agent_name=agent_name,
                operation=operation,
                context=context
            )
        ]

        positive_influence = 0.0
        negative_influence = 0.0

        matched_ids: List[str] = []
        explanations: List[str] = []

        for entry in applicable_entries:
            influence = self._calculate_influence(
                entry
            )

            direction = self._get_direction(
                entry
            )

            if direction > 0:
                positive_influence += influence

                explanations.append(
                    f"Positive knowledge: "
                    f"{entry.knowledge_type} "
                    f"for {entry.target} "
                    f"added influence "
                    f"{influence:.4f}."
                )

            elif direction < 0:
                negative_influence += influence

                explanations.append(
                    f"Negative knowledge: "
                    f"{entry.knowledge_type} "
                    f"for {entry.target} "
                    f"added penalty "
                    f"{influence:.4f}."
                )

            else:
                continue

            matched_ids.append(
                entry.knowledge_id
            )

        raw_net_influence = (
            positive_influence
            - negative_influence
        )

        bounded_net_influence = self._clamp(
            raw_net_influence,
            -self.maximum_adjustment,
            self.maximum_adjustment
        )

        modifier = self._clamp(
            1.0 + bounded_net_influence,
            1.0 - self.maximum_adjustment,
            1.0 + self.maximum_adjustment
        )

        adjusted_score = self._clamp(
            original_score * modifier,
            0.0,
            1.0
        )

        return KnowledgeAdjustment(
            agent_name=agent_name,
            operation=operation,
            original_score=round(
                original_score,
                4
            ),
            adjustment_modifier=round(
                modifier,
                4
            ),
            adjusted_score=round(
                adjusted_score,
                4
            ),
            positive_influence=round(
                positive_influence,
                4
            ),
            negative_influence=round(
                negative_influence,
                4
            ),
            matched_knowledge_ids=matched_ids,
            explanations=explanations,
            metadata={
                "relevant_entry_count": len(
                    relevant_entries
                ),
                "applicable_entry_count": len(
                    applicable_entries
                ),
                "raw_net_influence": round(
                    raw_net_influence,
                    4
                ),
                "bounded_net_influence": round(
                    bounded_net_influence,
                    4
                ),
                "minimum_confidence": (
                    self.minimum_confidence
                ),
                "maximum_adjustment": (
                    self.maximum_adjustment
                )
            }
        )

    def _is_applicable(
        self,
        entry: KnowledgeEntry,
        agent_name: str,
        operation: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Prevent unrelated knowledge from affecting
        a decision merely because of broad text matching.
        """

        target = entry.target.upper()
        agent = agent_name.upper()
        operation = operation.upper()

        if entry.knowledge_type in {
            "AGENT_WEIGHT_INCREASE",
            "AGENT_WEIGHT_REDUCTION",
            "AGENT_PERFORMANCE"
        }:
            return target == agent

        if entry.knowledge_type in {
            "OPERATION_PREFERENCE",
            "OPERATION_AVOIDANCE"
        }:
            return target == operation

        if entry.knowledge_type == "BUSINESS_PATTERN":
            return self._context_matches_target(
                target=target,
                context=context
            )

        if entry.knowledge_type in {
            "STRATEGY_REINFORCEMENT",
            "STRATEGY_CORRECTION"
        }:
            return self._context_matches_target(
                target=target,
                context=context
            )

        if entry.knowledge_type == "BUSINESS_RULE":
            return self._business_rule_matches(
                entry=entry,
                operation=operation,
                context=context
            )

        if entry.knowledge_type in {
            "SYSTEM_STABILIZATION",
            "AUTONOMY_EXPANSION"
        }:
            return target == "ACOS"

        return False

    def _calculate_influence(
        self,
        entry: KnowledgeEntry
    ) -> float:
        """
        Influence formula:

        confidence
        × evidence strength
        × priority weight
        × base influence scale
        """

        confidence = self._clamp(
            entry.confidence,
            0.0,
            1.0
        )

        benefit_strength = self._clamp(
            abs(entry.expected_benefit),
            0.05,
            1.0
        )

        priority_weight = (
            self.PRIORITY_WEIGHTS.get(
                entry.priority,
                0.75
            )
        )

        occurrence_factor = min(
            1.25,
            1.0
            + max(
                0,
                entry.occurrence_count - 1
            ) * 0.05
        )

        influence = (
            confidence
            * benefit_strength
            * priority_weight
            * occurrence_factor
            * 0.25
        )

        return self._clamp(
            influence,
            0.0,
            self.maximum_adjustment
        )

    def _get_direction(
        self,
        entry: KnowledgeEntry
    ) -> int:
        if entry.knowledge_type in self.POSITIVE_TYPES:
            return 1

        if entry.knowledge_type in self.NEGATIVE_TYPES:
            return -1

        if entry.knowledge_type == "AGENT_PERFORMANCE":
            status = (
                str(
                    entry.evidence.get(
                        "performance_status",
                        ""
                    )
                )
                .strip()
                .upper()
            )

            if status == "STRONG":
                return 1

            if status == "WEAK":
                return -1

        if entry.knowledge_type == "BUSINESS_PATTERN":
            status = (
                str(
                    entry.evidence.get(
                        "pattern_status",
                        ""
                    )
                )
                .strip()
                .upper()
            )

            if status == "POSITIVE":
                return 1

            if status == "NEGATIVE":
                return -1

        if entry.knowledge_type == "BUSINESS_RULE":
            recommendation = (
                str(
                    entry.evidence.get(
                        "recommendation",
                        entry.evidence.get(
                            "recommended_action",
                            ""
                        )
                    )
                )
                .strip()
                .upper()
            )

            if recommendation.startswith(
                "AVOID"
            ):
                return -1

            if recommendation:
                return 1

        return 0

    @staticmethod
    def _context_matches_target(
        target: str,
        context: Dict[str, Any]
    ) -> bool:
        if "=" not in target:
            return False

        key, expected_value = target.split(
            "=",
            1
        )

        normalized_context = {
            str(context_key).strip().upper():
            str(context_value).strip().upper()
            for context_key, context_value
            in context.items()
        }

        actual_value = normalized_context.get(
            key.strip().upper()
        )

        return (
            actual_value
            == expected_value.strip().upper()
        )

    @staticmethod
    def _business_rule_matches(
        entry: KnowledgeEntry,
        operation: str,
        context: Dict[str, Any]
    ) -> bool:
        target = entry.target.upper()

        normalized_context = {
            str(key).strip().upper():
            str(value).strip().upper()
            for key, value in context.items()
        }

        context_values = set(
            normalized_context.values()
        )

        context_patterns = {
            f"{key}={value}"
            for key, value
            in normalized_context.items()
        }

        if (
            target in context_values
            or target in context_patterns
        ):
            return True

        evidence_operation = (
            str(
                entry.evidence.get(
                    "operation",
                    ""
                )
            )
            .strip()
            .upper()
        )

        return bool(
            evidence_operation
            and evidence_operation == operation
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