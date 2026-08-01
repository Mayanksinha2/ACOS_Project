from collections import defaultdict
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

from learning.experience_memory import (
    ExperienceMemory
)
from learning.learning_engine import (
    LearningEngine
)
from models.optimization_recommendation import (
    OptimizationRecommendation
)
from models.system_optimization_report import (
    SystemOptimizationReport
)


class SelfOptimizationEngine:
    """
    Self-Commerce Optimization Engine (SCOE).

    SCOE analyzes historical experiences and learned
    agent performance to generate autonomous system-level
    optimization recommendations.
    """

    def __init__(
        self,
        experience_memory: ExperienceMemory,
        learning_engine: LearningEngine,
        strong_agent_threshold: float = 0.70,
        weak_agent_threshold: float = 0.45,
        strong_operation_threshold: float = 0.40,
        weak_operation_threshold: float = -0.20,
        minimum_operation_experiences: int = 2
    ):
        self.experience_memory = experience_memory
        self.learning_engine = learning_engine

        self.strong_agent_threshold = (
            strong_agent_threshold
        )

        self.weak_agent_threshold = (
            weak_agent_threshold
        )

        self.strong_operation_threshold = (
            strong_operation_threshold
        )

        self.weak_operation_threshold = (
            weak_operation_threshold
        )

        self.minimum_operation_experiences = (
            minimum_operation_experiences
        )

        self._validate_configuration()

    def analyze_system(
        self
    ) -> SystemOptimizationReport:
        """
        Perform complete SCOE analysis.
        """

        agent_rankings = self._build_agent_rankings()

        strong_agents = [
            item["agent_name"]
            for item in agent_rankings
            if item["reliability_score"]
            >= self.strong_agent_threshold
        ]

        weak_agents = [
            item["agent_name"]
            for item in agent_rankings
            if item["reliability_score"]
            <= self.weak_agent_threshold
        ]

        operation_analysis = (
            self._analyze_operations()
        )

        best_operations = [
            item
            for item in operation_analysis
            if (
                item["experience_count"]
                >= self.minimum_operation_experiences
                and item["average_reward"]
                >= self.strong_operation_threshold
            )
        ]

        weak_operations = [
            item
            for item in operation_analysis
            if (
                item["experience_count"]
                >= self.minimum_operation_experiences
                and item["average_reward"]
                <= self.weak_operation_threshold
            )
        ]

        business_patterns = (
            self._analyze_business_patterns()
        )

        health_score = (
            self._calculate_system_health(
                agent_rankings=agent_rankings,
                operation_analysis=operation_analysis
            )
        )

        health_status = (
            self._classify_system_health(
                health_score
            )
        )

        recommendations = (
            self.generate_recommendations(
                agent_rankings=agent_rankings,
                best_operations=best_operations,
                weak_operations=weak_operations,
                business_patterns=business_patterns,
                system_health_score=health_score
            )
        )

        return SystemOptimizationReport(
            system_health_score=round(
                health_score,
                4
            ),
            system_health_status=health_status,
            agent_rankings=agent_rankings,
            strong_agents=strong_agents,
            weak_agents=weak_agents,
            best_operations=best_operations,
            weak_operations=weak_operations,
            business_patterns=business_patterns,
            recommendations=recommendations
        )

    def recommend_agent_updates(
        self,
        agent_rankings: Optional[
            List[Dict[str, Any]]
        ] = None
    ) -> List[OptimizationRecommendation]:
        """
        Generate recommendations from agent reliability.
        """

        if agent_rankings is None:
            agent_rankings = (
                self._build_agent_rankings()
            )

        recommendations = []

        for agent in agent_rankings:
            agent_name = agent["agent_name"]
            reliability = agent[
                "reliability_score"
            ]
            average_reward = agent[
                "average_reward"
            ]
            failure_rate = agent[
                "failure_rate"
            ]
            experience_count = agent[
                "experience_count"
            ]

            if experience_count == 0:
                continue

            if (
                reliability
                >= self.strong_agent_threshold
            ):
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_type=(
                            "AGENT_WEIGHT_INCREASE"
                        ),
                        target=agent_name,
                        message=(
                            f"Increase the decision influence "
                            f"of {agent_name} because its "
                            f"historical reliability is "
                            f"{reliability:.2f}."
                        ),
                        expected_benefit=round(
                            min(
                                0.30,
                                reliability - 0.50
                            ),
                            4
                        ),
                        confidence=reliability,
                        priority="HIGH",
                        evidence={
                            "reliability_score": reliability,
                            "average_reward": average_reward,
                            "experience_count": experience_count
                        }
                    )
                )

            elif (
                reliability
                <= self.weak_agent_threshold
            ):
                priority = (
                    "CRITICAL"
                    if failure_rate >= 0.60
                    else "HIGH"
                )

                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_type=(
                            "AGENT_WEIGHT_REDUCTION"
                        ),
                        target=agent_name,
                        message=(
                            f"Reduce the decision influence "
                            f"of {agent_name} and increase "
                            f"monitoring because its "
                            f"historical reliability is "
                            f"{reliability:.2f}."
                        ),
                        expected_benefit=round(
                            min(
                                0.35,
                                0.50 - reliability
                            ),
                            4
                        ),
                        confidence=round(
                            1.0 - reliability,
                            4
                        ),
                        priority=priority,
                        evidence={
                            "reliability_score": reliability,
                            "average_reward": average_reward,
                            "failure_rate": failure_rate,
                            "experience_count": experience_count
                        }
                    )
                )

        return recommendations

    def recommend_operation_updates(
        self,
        best_operations: Optional[
            List[Dict[str, Any]]
        ] = None,
        weak_operations: Optional[
            List[Dict[str, Any]]
        ] = None
    ) -> List[OptimizationRecommendation]:
        """
        Generate recommendations for commerce operations.
        """

        if (
            best_operations is None
            or weak_operations is None
        ):
            operation_analysis = (
                self._analyze_operations()
            )

            best_operations = [
                item
                for item in operation_analysis
                if (
                    item["experience_count"]
                    >= self.minimum_operation_experiences
                    and item["average_reward"]
                    >= self.strong_operation_threshold
                )
            ]

            weak_operations = [
                item
                for item in operation_analysis
                if (
                    item["experience_count"]
                    >= self.minimum_operation_experiences
                    and item["average_reward"]
                    <= self.weak_operation_threshold
                )
            ]

        recommendations = []

        for operation in best_operations:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_type=(
                        "OPERATION_PREFERENCE"
                    ),
                    target=operation["operation"],
                    message=(
                        f"Prefer operation "
                        f"{operation['operation']} in "
                        f"similar contexts because it has "
                        f"an average reward of "
                        f"{operation['average_reward']:.2f}."
                    ),
                    expected_benefit=round(
                        min(
                            0.40,
                            operation["average_reward"]
                        ),
                        4
                    ),
                    confidence=operation[
                        "success_rate"
                    ],
                    priority="HIGH",
                    evidence=operation
                )
            )

        for operation in weak_operations:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_type=(
                        "OPERATION_AVOIDANCE"
                    ),
                    target=operation["operation"],
                    message=(
                        f"Avoid or constrain operation "
                        f"{operation['operation']} in "
                        f"similar contexts because it has "
                        f"an average reward of "
                        f"{operation['average_reward']:.2f}."
                    ),
                    expected_benefit=round(
                        min(
                            0.40,
                            abs(
                                operation[
                                    "average_reward"
                                ]
                            )
                        ),
                        4
                    ),
                    confidence=operation[
                        "failure_rate"
                    ],
                    priority=(
                        "CRITICAL"
                        if operation[
                            "failure_rate"
                        ] >= 0.70
                        else "HIGH"
                    ),
                    evidence=operation
                )
            )

        return recommendations

    def recommend_business_strategies(
        self,
        business_patterns: Optional[
            List[Dict[str, Any]]
        ] = None
    ) -> List[OptimizationRecommendation]:
        """
        Generate recommendations from recurring context
        and business patterns.
        """

        if business_patterns is None:
            business_patterns = (
                self._analyze_business_patterns()
            )

        recommendations = []

        for pattern in business_patterns:
            if pattern["experience_count"] < 2:
                continue

            average_reward = pattern[
                "average_reward"
            ]

            if average_reward >= 0.40:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_type=(
                            "STRATEGY_REINFORCEMENT"
                        ),
                        target=pattern["pattern"],
                        message=(
                            f"Reinforce strategy pattern "
                            f"{pattern['pattern']} because "
                            f"it produced an average reward "
                            f"of {average_reward:.2f}."
                        ),
                        expected_benefit=round(
                            min(
                                0.40,
                                average_reward
                            ),
                            4
                        ),
                        confidence=pattern[
                            "success_rate"
                        ],
                        priority="MEDIUM",
                        evidence=pattern
                    )
                )

            elif average_reward <= -0.20:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_type=(
                            "STRATEGY_CORRECTION"
                        ),
                        target=pattern["pattern"],
                        message=(
                            f"Review or replace strategy "
                            f"pattern {pattern['pattern']} "
                            f"because it produced an "
                            f"average reward of "
                            f"{average_reward:.2f}."
                        ),
                        expected_benefit=round(
                            min(
                                0.40,
                                abs(average_reward)
                            ),
                            4
                        ),
                        confidence=pattern[
                            "failure_rate"
                        ],
                        priority="HIGH",
                        evidence=pattern
                    )
                )

        return recommendations

    def generate_recommendations(
        self,
        agent_rankings: Optional[
            List[Dict[str, Any]]
        ] = None,
        best_operations: Optional[
            List[Dict[str, Any]]
        ] = None,
        weak_operations: Optional[
            List[Dict[str, Any]]
        ] = None,
        business_patterns: Optional[
            List[Dict[str, Any]]
        ] = None,
        system_health_score: Optional[
            float
        ] = None
    ) -> List[OptimizationRecommendation]:
        """
        Generate all SCOE recommendations.
        """

        recommendations = []

        recommendations.extend(
            self.recommend_agent_updates(
                agent_rankings
            )
        )

        recommendations.extend(
            self.recommend_operation_updates(
                best_operations,
                weak_operations
            )
        )

        recommendations.extend(
            self.recommend_business_strategies(
                business_patterns
            )
        )

        if system_health_score is not None:
            if system_health_score < 0.40:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_type=(
                            "SYSTEM_STABILIZATION"
                        ),
                        target="ACOS",
                        message=(
                            "System health is low. "
                            "Temporarily reduce autonomous "
                            "decision aggressiveness and "
                            "increase human review."
                        ),
                        expected_benefit=round(
                            0.40 - system_health_score,
                            4
                        ),
                        confidence=round(
                            1.0 - system_health_score,
                            4
                        ),
                        priority="CRITICAL",
                        evidence={
                            "system_health_score": (
                                system_health_score
                            )
                        }
                    )
                )

            elif system_health_score >= 0.75:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_type=(
                            "AUTONOMY_EXPANSION"
                        ),
                        target="ACOS",
                        message=(
                            "System health is strong. "
                            "Gradually increase autonomous "
                            "decision authority while "
                            "continuing outcome monitoring."
                        ),
                        expected_benefit=round(
                            system_health_score - 0.50,
                            4
                        ),
                        confidence=system_health_score,
                        priority="MEDIUM",
                        evidence={
                            "system_health_score": (
                                system_health_score
                            )
                        }
                    )
                )

        return self._deduplicate_recommendations(
            recommendations
        )

    def _build_agent_rankings(
        self
    ) -> List[Dict[str, Any]]:
        """
        Convert LearningEngine rankings into a stable
        serializable report format.
        """

        performances = (
            self.learning_engine.rank_agents()
        )

        rankings = []

        for position, performance in enumerate(
            performances,
            start=1
        ):
            rankings.append({
                "rank": position,
                "agent_name": (
                    performance.agent_name
                ),
                "experience_count": (
                    performance.experience_count
                ),
                "average_reward": round(
                    performance.average_reward,
                    4
                ),
                "success_rate": round(
                    performance.success_rate,
                    4
                ),
                "failure_rate": round(
                    performance.failure_rate,
                    4
                ),
                "reward_stability": round(
                    performance.reward_stability,
                    4
                ),
                "reliability_score": round(
                    performance.reliability_score,
                    4
                ),
                "confidence_modifier": round(
                    performance.confidence_modifier,
                    4
                )
            })

        return rankings

    def _analyze_operations(
        self
    ) -> List[Dict[str, Any]]:
        """
        Aggregate rewards and outcomes by operation.
        """

        grouped = defaultdict(list)

        for experience in (
            self.experience_memory.get_all()
        ):
            operation = getattr(
                experience,
                "operation",
                None
            )

            operation = (
                str(operation).strip().upper()
                if operation
                else "UNKNOWN"
            )

            grouped[operation].append(
                experience
            )

        results = []

        for operation, experiences in grouped.items():
            rewards = [
                float(experience.reward)
                for experience in experiences
            ]

            success_count = sum(
                1
                for experience in experiences
                if experience.outcome_status
                == "SUCCESS"
            )

            failure_count = sum(
                1
                for experience in experiences
                if experience.outcome_status
                == "FAILURE"
            )

            count = len(
                experiences
            )

            results.append({
                "operation": operation,
                "experience_count": count,
                "average_reward": round(
                    mean(rewards),
                    4
                ),
                "success_rate": round(
                    success_count / count,
                    4
                ),
                "failure_rate": round(
                    failure_count / count,
                    4
                )
            })

        return sorted(
            results,
            key=lambda item: (
                item["average_reward"],
                item["experience_count"]
            ),
            reverse=True
        )

    def _analyze_business_patterns(
        self
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring context patterns.

        Supported context keys include:

        season
        demand_level
        inventory_level
        campaign
        customer_segment
        market_condition
        """

        supported_keys = [
            "season",
            "demand_level",
            "inventory_level",
            "campaign",
            "customer_segment",
            "market_condition"
        ]

        grouped = defaultdict(list)

        for experience in (
            self.experience_memory.get_all()
        ):
            context = getattr(
                experience,
                "context",
                None
            ) or {}

            if not isinstance(context, dict):
                continue

            for key in supported_keys:
                value = context.get(
                    key
                )

                if value is None:
                    continue

                pattern = (
                    f"{key.upper()}="
                    f"{str(value).strip().upper()}"
                )

                grouped[pattern].append(
                    experience
                )

        results = []

        for pattern, experiences in grouped.items():
            rewards = [
                float(experience.reward)
                for experience in experiences
            ]

            success_count = sum(
                1
                for experience in experiences
                if experience.outcome_status
                == "SUCCESS"
            )

            failure_count = sum(
                1
                for experience in experiences
                if experience.outcome_status
                == "FAILURE"
            )

            count = len(
                experiences
            )

            results.append({
                "pattern": pattern,
                "experience_count": count,
                "average_reward": round(
                    mean(rewards),
                    4
                ),
                "success_rate": round(
                    success_count / count,
                    4
                ),
                "failure_rate": round(
                    failure_count / count,
                    4
                )
            })

        return sorted(
            results,
            key=lambda item: (
                item["average_reward"],
                item["experience_count"]
            ),
            reverse=True
        )

    def _calculate_system_health(
        self,
        agent_rankings: List[Dict[str, Any]],
        operation_analysis: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall system health.

        Formula:

        Agent reliability    45%
        Agent reward         25%
        Operation reward     20%
        Experience coverage  10%
        """

        if not agent_rankings:
            return 0.0

        average_reliability = mean(
            item["reliability_score"]
            for item in agent_rankings
        )

        average_agent_reward = mean(
            item["average_reward"]
            for item in agent_rankings
        )

        normalized_agent_reward = (
            self._normalize_reward(
                average_agent_reward
            )
        )

        if operation_analysis:
            average_operation_reward = mean(
                item["average_reward"]
                for item in operation_analysis
            )
        else:
            average_operation_reward = 0.0

        normalized_operation_reward = (
            self._normalize_reward(
                average_operation_reward
            )
        )

        total_experiences = sum(
            item["experience_count"]
            for item in agent_rankings
        )

        expected_experiences = max(
            1,
            len(agent_rankings) * 5
        )

        experience_coverage = min(
            1.0,
            total_experiences
            / expected_experiences
        )

        health = (
            0.45 * average_reliability
            + 0.25 * normalized_agent_reward
            + 0.20 * normalized_operation_reward
            + 0.10 * experience_coverage
        )

        return self._clamp(
            health,
            0.0,
            1.0
        )

    @staticmethod
    def _classify_system_health(
        health_score: float
    ) -> str:
        if health_score >= 0.80:
            return "EXCELLENT"

        if health_score >= 0.65:
            return "GOOD"

        if health_score >= 0.50:
            return "STABLE"

        if health_score >= 0.35:
            return "WEAK"

        return "CRITICAL"

    @staticmethod
    def _normalize_reward(
        reward: float
    ) -> float:
        """
        Convert reward from [-1, 1] to [0, 1].
        """

        normalized = (
            float(reward) + 1.0
        ) / 2.0

        return SelfOptimizationEngine._clamp(
            normalized,
            0.0,
            1.0
        )

    @staticmethod
    def _deduplicate_recommendations(
        recommendations: Iterable[
            OptimizationRecommendation
        ]
    ) -> List[OptimizationRecommendation]:
        unique = []
        seen = set()

        for recommendation in recommendations:
            key = (
                recommendation.recommendation_type,
                recommendation.target
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                recommendation
            )

        priority_order = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }

        return sorted(
            unique,
            key=lambda recommendation: (
                priority_order.get(
                    recommendation.priority,
                    0
                ),
                recommendation.confidence,
                recommendation.expected_benefit
            ),
            reverse=True
        )

    def _validate_configuration(
        self
    ) -> None:
        threshold_values = {
            "strong_agent_threshold": (
                self.strong_agent_threshold
            ),
            "weak_agent_threshold": (
                self.weak_agent_threshold
            ),
            "strong_operation_threshold": (
                self.strong_operation_threshold
            ),
            "weak_operation_threshold": (
                self.weak_operation_threshold
            )
        }

        for name, value in threshold_values.items():
            if not isinstance(
                value,
                (int, float)
            ):
                raise TypeError(
                    f"{name} must be numeric."
                )

        if not 0.0 <= self.strong_agent_threshold <= 1.0:
            raise ValueError(
                "strong_agent_threshold must be "
                "between 0 and 1."
            )

        if not 0.0 <= self.weak_agent_threshold <= 1.0:
            raise ValueError(
                "weak_agent_threshold must be "
                "between 0 and 1."
            )

        if (
            self.weak_agent_threshold
            >= self.strong_agent_threshold
        ):
            raise ValueError(
                "weak_agent_threshold must be lower "
                "than strong_agent_threshold."
            )

        if self.minimum_operation_experiences < 1:
            raise ValueError(
                "minimum_operation_experiences "
                "must be at least 1."
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