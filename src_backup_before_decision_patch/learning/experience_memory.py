from collections import defaultdict
from typing import Dict, List, Optional

from models.experience import Experience


class ExperienceMemory:
    """
    Stores and retrieves ACOS decision experiences.

    This first version uses in-memory storage.
    Later it can be replaced by a database or
    persistent knowledge store.
    """

    def __init__(self):
        self._experiences: List[Experience] = []
        self._experience_ids = set()

    def add(
        self,
        experience: Experience
    ) -> None:
        """
        Add one new experience.

        Duplicate experience IDs are rejected.
        """

        if not isinstance(experience, Experience):
            raise TypeError(
                "ExperienceMemory accepts only Experience objects."
            )

        if experience.experience_id in self._experience_ids:
            raise ValueError(
                "Duplicate experience ID: "
                f"{experience.experience_id}"
            )

        self._experiences.append(experience)
        self._experience_ids.add(
            experience.experience_id
        )

    def add_many(
        self,
        experiences: List[Experience]
    ) -> None:
        """
        Add multiple experiences.
        """

        if not isinstance(experiences, list):
            raise TypeError(
                "experiences must be a list."
            )

        for experience in experiences:
            self.add(experience)

    def get_all(self) -> List[Experience]:
        """
        Return all stored experiences.
        """

        return list(self._experiences)

    def get_by_id(
        self,
        experience_id: str
    ) -> Optional[Experience]:
        """
        Find an experience by its unique ID.
        """

        for experience in self._experiences:
            if experience.experience_id == experience_id:
                return experience

        return None

    def get_by_agent(
        self,
        source_agent: str
    ) -> List[Experience]:
        """
        Return experiences produced by one agent.
        """

        return [
            experience
            for experience in self._experiences
            if experience.source_agent == source_agent
        ]

    def get_by_target(
        self,
        target: str
    ) -> List[Experience]:
        """
        Return experiences associated with one target.
        """

        return [
            experience
            for experience in self._experiences
            if experience.target == target
        ]

    def get_by_status(
        self,
        outcome_status: str
    ) -> List[Experience]:
        """
        Return experiences with a specific outcome status.
        """

        valid_statuses = {
            "SUCCESS",
            "FAILURE",
            "NEUTRAL"
        }

        if outcome_status not in valid_statuses:
            raise ValueError(
                "Invalid outcome status: "
                f"{outcome_status}"
            )

        return [
            experience
            for experience in self._experiences
            if experience.outcome_status == outcome_status
        ]

    def get_recent(
        self,
        limit: int = 10
    ) -> List[Experience]:
        """
        Return the most recently added experiences.
        """

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        return self._experiences[-limit:]

    def average_reward(
        self,
        source_agent: Optional[str] = None
    ) -> float:
        """
        Calculate average reward across all experiences
        or for one specific agent.
        """

        experiences = (
            self.get_by_agent(source_agent)
            if source_agent is not None
            else self._experiences
        )

        if not experiences:
            return 0.0

        total_reward = sum(
            experience.reward
            for experience in experiences
        )

        return round(
            total_reward / len(experiences),
            4
        )

    def success_rate(
        self,
        source_agent: Optional[str] = None
    ) -> float:
        """
        Calculate the success rate as a value
        between 0.0 and 1.0.
        """

        experiences = (
            self.get_by_agent(source_agent)
            if source_agent is not None
            else self._experiences
        )

        if not experiences:
            return 0.0

        successful_count = sum(
            1
            for experience in experiences
            if experience.is_positive()
        )

        return round(
            successful_count / len(experiences),
            4
        )

    def failure_rate(
        self,
        source_agent: Optional[str] = None
    ) -> float:
        """
        Calculate the failure rate as a value
        between 0.0 and 1.0.
        """

        experiences = (
            self.get_by_agent(source_agent)
            if source_agent is not None
            else self._experiences
        )

        if not experiences:
            return 0.0

        failed_count = sum(
            1
            for experience in experiences
            if experience.is_negative()
        )

        return round(
            failed_count / len(experiences),
            4
        )

    def agent_summary(self) -> Dict[str, dict]:
        """
        Produce a basic performance summary
        for every agent in memory.
        """

        grouped_experiences = defaultdict(list)

        for experience in self._experiences:
            grouped_experiences[
                experience.source_agent
            ].append(experience)

        summary = {}

        for agent_name, experiences in (
            grouped_experiences.items()
        ):
            rewards = [
                experience.reward
                for experience in experiences
            ]

            success_count = sum(
                1
                for experience in experiences
                if experience.is_positive()
            )

            failure_count = sum(
                1
                for experience in experiences
                if experience.is_negative()
            )

            summary[agent_name] = {
                "experience_count": len(experiences),
                "average_reward": round(
                    sum(rewards) / len(rewards),
                    4
                ),
                "success_count": success_count,
                "failure_count": failure_count,
                "neutral_count": (
                    len(experiences)
                    - success_count
                    - failure_count
                ),
                "success_rate": round(
                    success_count / len(experiences),
                    4
                )
            }

        return summary

    def clear(self) -> None:
        """
        Remove all stored experiences.
        """

        self._experiences.clear()
        self._experience_ids.clear()

    def __len__(self) -> int:
        """
        Return the number of stored experiences.
        """

        return len(self._experiences)