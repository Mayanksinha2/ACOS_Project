from collections import defaultdict
from math import sqrt
from typing import Dict, List, Optional

from learning.experience_memory import ExperienceMemory
from models.agent_performance import AgentPerformance
from models.experience import Experience


class LearningEngine:
    """
    Learns agent performance from stored experiences.

    It calculates:

    - average reward
    - success rate
    - failure rate
    - reward stability
    - reliability score
    - confidence modifier
    - operation-level performance
    """

    DEFAULT_WEIGHTS = {
        "average_reward": 0.40,
        "success_rate": 0.30,
        "stability": 0.20,
        "experience": 0.10
    }

    def __init__(
        self,
        memory: ExperienceMemory,
        weights: Optional[Dict[str, float]] = None,
        minimum_experiences: int = 5
    ):
        if not isinstance(memory, ExperienceMemory):
            raise TypeError(
                "memory must be an ExperienceMemory object."
            )

        if minimum_experiences <= 0:
            raise ValueError(
                "minimum_experiences must be greater than zero."
            )

        self.memory = memory
        self.minimum_experiences = minimum_experiences

        self.weights = (
            weights.copy()
            if weights is not None
            else self.DEFAULT_WEIGHTS.copy()
        )

        self._validate_weights()

    def analyze_agent(
        self,
        agent_name: str
    ) -> AgentPerformance:
        """
        Analyze all experiences belonging to one agent.
        """

        experiences = self.memory.get_by_agent(
            agent_name
        )

        if not experiences:
            return self._empty_performance(
                agent_name
            )

        experience_count = len(experiences)

        success_count = sum(
            1
            for experience in experiences
            if experience.outcome_status == "SUCCESS"
        )

        failure_count = sum(
            1
            for experience in experiences
            if experience.outcome_status == "FAILURE"
        )

        neutral_count = (
            experience_count
            - success_count
            - failure_count
        )

        rewards = [
            experience.reward
            for experience in experiences
        ]

        average_reward = round(
            sum(rewards) / experience_count,
            4
        )

        success_rate = round(
            success_count / experience_count,
            4
        )

        failure_rate = round(
            failure_count / experience_count,
            4
        )

        reward_stability = self._calculate_stability(
            rewards
        )

        experience_factor = min(
            experience_count
            / self.minimum_experiences,
            1.0
        )

        normalized_reward = self._normalize_reward(
            average_reward
        )

        reliability_score = self._calculate_reliability(
            normalized_reward=normalized_reward,
            success_rate=success_rate,
            reward_stability=reward_stability,
            experience_factor=experience_factor
        )

        confidence_modifier = self._calculate_confidence_modifier(
            reliability_score
        )

        operation_performance = (
            self._analyze_operations(
                experiences
            )
        )

        return AgentPerformance(
            agent_name=agent_name,
            experience_count=experience_count,
            success_count=success_count,
            failure_count=failure_count,
            neutral_count=neutral_count,
            average_reward=average_reward,
            success_rate=success_rate,
            failure_rate=failure_rate,
            reward_stability=reward_stability,
            reliability_score=reliability_score,
            confidence_modifier=confidence_modifier,
            operation_performance=operation_performance
        )

    def analyze_all_agents(
        self
    ) -> Dict[str, AgentPerformance]:
        """
        Analyze all agents found in experience memory.
        """

        agent_names = {
            experience.source_agent
            for experience in self.memory.get_all()
        }

        return {
            agent_name: self.analyze_agent(
                agent_name
            )
            for agent_name in sorted(agent_names)
        }

    def rank_agents(
        self
    ) -> List[AgentPerformance]:
        """
        Rank agents from highest to lowest reliability.
        """

        performances = list(
            self.analyze_all_agents().values()
        )

        return sorted(
            performances,
            key=lambda performance: (
                performance.reliability_score,
                performance.average_reward,
                performance.success_rate,
                performance.experience_count
            ),
            reverse=True
        )

    def get_confidence_modifier(
        self,
        agent_name: str
    ) -> float:
        """
        Return the learned confidence modifier
        for one agent.
        """

        performance = self.analyze_agent(
            agent_name
        )

        return performance.confidence_modifier

    def _calculate_reliability(
        self,
        normalized_reward: float,
        success_rate: float,
        reward_stability: float,
        experience_factor: float
    ) -> float:
        """
        Calculate the final reliability score.

        Reliability is between 0.0 and 1.0.
        """

        reliability = (
            normalized_reward
            * self.weights["average_reward"]
            + success_rate
            * self.weights["success_rate"]
            + reward_stability
            * self.weights["stability"]
            + experience_factor
            * self.weights["experience"]
        )

        return round(
            self._clamp(
                reliability,
                0.0,
                1.0
            ),
            4
        )

    @staticmethod
    def _calculate_stability(
        rewards: List[float]
    ) -> float:
        """
        Calculate reward stability.

        Low reward variation gives high stability.
        High reward variation gives low stability.
        """

        if len(rewards) <= 1:
            return 1.0

        mean_reward = (
            sum(rewards)
            / len(rewards)
        )

        variance = sum(
            (
                reward
                - mean_reward
            ) ** 2
            for reward in rewards
        ) / len(rewards)

        standard_deviation = sqrt(
            variance
        )

        stability = 1.0 - min(
            standard_deviation,
            1.0
        )

        return round(
            max(stability, 0.0),
            4
        )

    @staticmethod
    def _normalize_reward(
        reward: float
    ) -> float:
        """
        Convert reward from [-1, 1]
        into [0, 1].
        """

        normalized = (
            reward + 1.0
        ) / 2.0

        return round(
            LearningEngine._clamp(
                normalized,
                0.0,
                1.0
            ),
            4
        )

    @staticmethod
    def _calculate_confidence_modifier(
        reliability_score: float
    ) -> float:
        """
        Convert reliability into a confidence multiplier.

        Reliability 0.50 gives modifier 1.00.
        Higher reliability increases confidence.
        Lower reliability reduces confidence.
        """

        modifier = 0.75 + (
            reliability_score * 0.50
        )

        return round(
            LearningEngine._clamp(
                modifier,
                0.75,
                1.25
            ),
            4
        )

    @staticmethod
    def _analyze_operations(
        experiences: List[Experience]
    ) -> Dict[str, dict]:
        """
        Calculate performance for every operation
        used by the agent.
        """

        grouped = defaultdict(list)

        for experience in experiences:
            grouped[
                experience.operation
            ].append(experience)

        operation_performance = {}

        for operation, operation_experiences in (
            grouped.items()
        ):
            rewards = [
                experience.reward
                for experience
                in operation_experiences
            ]

            success_count = sum(
                1
                for experience
                in operation_experiences
                if experience.outcome_status
                == "SUCCESS"
            )

            count = len(
                operation_experiences
            )

            operation_performance[
                operation
            ] = {
                "experience_count": count,
                "average_reward": round(
                    sum(rewards) / count,
                    4
                ),
                "success_rate": round(
                    success_count / count,
                    4
                )
            }

        return operation_performance

    def _empty_performance(
        self,
        agent_name: str
    ) -> AgentPerformance:
        """
        Return a default performance profile
        for an agent with no experience.
        """

        return AgentPerformance(
            agent_name=agent_name,
            experience_count=0,
            success_count=0,
            failure_count=0,
            neutral_count=0,
            average_reward=0.0,
            success_rate=0.0,
            failure_rate=0.0,
            reward_stability=0.0,
            reliability_score=0.0,
            confidence_modifier=1.0,
            operation_performance={}
        )

    def _validate_weights(self) -> None:
        """
        Validate learning-engine weight configuration.
        """

        required_keys = set(
            self.DEFAULT_WEIGHTS.keys()
        )

        received_keys = set(
            self.weights.keys()
        )

        if received_keys != required_keys:
            raise ValueError(
                "Learning Engine weights must contain: "
                f"{sorted(required_keys)}"
            )

        for name, value in self.weights.items():
            if not isinstance(
                value,
                (int, float)
            ):
                raise TypeError(
                    f"Weight '{name}' must be numeric."
                )

            if value < 0:
                raise ValueError(
                    f"Weight '{name}' cannot be negative."
                )

        total = sum(
            self.weights.values()
        )

        if abs(total - 1.0) > 0.0001:
            raise ValueError(
                "Learning Engine weights must sum to 1.0. "
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