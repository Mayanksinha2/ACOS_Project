from typing import List

from knowledge.knowledge_base import (
    KnowledgeBase
)
from models.knowledge_entry import (
    KnowledgeEntry
)
from models.optimization_recommendation import (
    OptimizationRecommendation
)
from models.system_optimization_report import (
    SystemOptimizationReport
)


class KnowledgeIntegrator:
    """
    Converts SCOE reports and recommendations into
    persistent ACOS knowledge.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase
    ):
        if not isinstance(
            knowledge_base,
            KnowledgeBase
        ):
            raise TypeError(
                "knowledge_base must be a KnowledgeBase."
            )

        self.knowledge_base = knowledge_base

    def integrate_report(
        self,
        report: SystemOptimizationReport
    ) -> List[KnowledgeEntry]:
        """
        Store all useful knowledge from an SCOE report.
        """

        if not isinstance(
            report,
            SystemOptimizationReport
        ):
            raise TypeError(
                "report must be a "
                "SystemOptimizationReport."
            )

        entries = []

        entries.extend(
            self._recommendation_entries(
                report.recommendations
            )
        )

        entries.extend(
            self._agent_performance_entries(
                report
            )
        )

        entries.extend(
            self._business_pattern_entries(
                report
            )
        )

        entries.append(
            self._system_health_entry(
                report
            )
        )

        return self.knowledge_base.add_many(
            entries,
            reinforce_duplicates=True
        )

    def integrate_recommendation(
        self,
        recommendation: OptimizationRecommendation
    ) -> KnowledgeEntry:
        """
        Store one SCOE recommendation.
        """

        entry = self._recommendation_to_knowledge(
            recommendation
        )

        return self.knowledge_base.add(
            entry,
            reinforce_duplicates=True
        )

    def _recommendation_entries(
        self,
        recommendations: List[
            OptimizationRecommendation
        ]
    ) -> List[KnowledgeEntry]:
        return [
            self._recommendation_to_knowledge(
                recommendation
            )
            for recommendation in recommendations
        ]

    @staticmethod
    def _recommendation_to_knowledge(
        recommendation: OptimizationRecommendation
    ) -> KnowledgeEntry:
        return KnowledgeEntry(
            knowledge_type=(
                recommendation.recommendation_type
            ),
            target=recommendation.target,
            statement=recommendation.message,
            confidence=recommendation.confidence,
            expected_benefit=(
                recommendation.expected_benefit
            ),
            priority=recommendation.priority,
            evidence=dict(
                recommendation.evidence
            ),
            source="SCOE"
        )

    @staticmethod
    def _agent_performance_entries(
        report: SystemOptimizationReport
    ) -> List[KnowledgeEntry]:
        entries = []

        strong_agents = set(
            report.strong_agents
        )

        weak_agents = set(
            report.weak_agents
        )

        for agent in report.agent_rankings:
            agent_name = agent[
                "agent_name"
            ]

            if agent_name in strong_agents:
                performance_status = (
                    "STRONG"
                )
                priority = "HIGH"

            elif agent_name in weak_agents:
                performance_status = (
                    "WEAK"
                )
                priority = "HIGH"

            else:
                performance_status = (
                    "MODERATE"
                )
                priority = "MEDIUM"

            statement = (
                f"{agent_name} currently has "
                f"{performance_status.lower()} performance "
                f"with reliability "
                f"{agent['reliability_score']:.4f}, "
                f"average reward "
                f"{agent['average_reward']:.4f}, "
                f"and success rate "
                f"{agent['success_rate']:.4f}."
            )

            entries.append(
                KnowledgeEntry(
                    knowledge_type=(
                        "AGENT_PERFORMANCE"
                    ),
                    target=agent_name,
                    statement=statement,
                    confidence=agent[
                        "reliability_score"
                    ],
                    expected_benefit=max(
                        -1.0,
                        min(
                            agent[
                                "average_reward"
                            ],
                            1.0
                        )
                    ),
                    priority=priority,
                    evidence={
                        **agent,
                        "performance_status": (
                            performance_status
                        )
                    },
                    source="LEARNING_ENGINE"
                )
            )

        return entries

    @staticmethod
    def _business_pattern_entries(
        report: SystemOptimizationReport
    ) -> List[KnowledgeEntry]:
        entries = []

        for pattern in report.business_patterns:
            average_reward = pattern[
                "average_reward"
            ]

            if average_reward >= 0.40:
                pattern_status = (
                    "POSITIVE"
                )
                priority = "HIGH"

            elif average_reward <= -0.20:
                pattern_status = (
                    "NEGATIVE"
                )
                priority = "HIGH"

            else:
                pattern_status = (
                    "OBSERVED"
                )
                priority = "MEDIUM"

            statement = (
                f"Business pattern "
                f"{pattern['pattern']} is classified as "
                f"{pattern_status.lower()} with average "
                f"reward {average_reward:.4f} across "
                f"{pattern['experience_count']} "
                f"experiences."
            )

            entries.append(
                KnowledgeEntry(
                    knowledge_type=(
                        "BUSINESS_PATTERN"
                    ),
                    target=pattern[
                        "pattern"
                    ],
                    statement=statement,
                    confidence=max(
                        pattern[
                            "success_rate"
                        ],
                        pattern[
                            "failure_rate"
                        ]
                    ),
                    expected_benefit=max(
                        -1.0,
                        min(
                            average_reward,
                            1.0
                        )
                    ),
                    priority=priority,
                    evidence={
                        **pattern,
                        "pattern_status": (
                            pattern_status
                        )
                    },
                    source="SCOE_PATTERN_ANALYSIS"
                )
            )

        return entries

    @staticmethod
    def _system_health_entry(
        report: SystemOptimizationReport
    ) -> KnowledgeEntry:
        return KnowledgeEntry(
            knowledge_type="SYSTEM_HEALTH",
            target="ACOS",
            statement=(
                f"ACOS system health is "
                f"{report.system_health_status.lower()} "
                f"with a score of "
                f"{report.system_health_score:.4f}."
            ),
            confidence=(
                report.system_health_score
            ),
            expected_benefit=(
                report.system_health_score
                - 0.5
            ),
            priority=(
                "CRITICAL"
                if report.system_health_status
                in {"CRITICAL", "WEAK"}
                else "MEDIUM"
            ),
            evidence={
                "system_health_score": (
                    report.system_health_score
                ),
                "system_health_status": (
                    report.system_health_status
                ),
                "recommendation_count": (
                    report.recommendation_count
                )
            },
            source="SCOE"
        )