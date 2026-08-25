from __future__ import annotations

from typing import Any

from knowledge.knowledge_base import KnowledgeBase
from models.knowledge_entry import KnowledgeEntry

from .learning_store import PersistentLearningStore


class LearningKnowledgeSynchronizer:
    """
    Converts sufficiently supported persistent outcome history into the
    knowledge types already consumed by KnowledgeAdvisor and MOCRA.

    This closes the loop:
        outcome -> persistent store -> knowledge base -> future MOCRA score
    """

    MINIMUM_EXPERIENCES = 3
    MINIMUM_ABSOLUTE_REWARD = 0.05

    def __init__(
        self,
        store: PersistentLearningStore,
        knowledge_base: KnowledgeBase | None = None,
    ) -> None:
        self.store = store
        self.knowledge_base = knowledge_base or KnowledgeBase(
            storage_path="data/knowledge_base.json",
            auto_load=True,
            auto_save=True,
        )

    def synchronize(self) -> list[KnowledgeEntry]:
        entries: list[KnowledgeEntry] = []

        for stats in self.store.agent_statistics():
            if not self._supported(stats):
                continue

            reward = float(stats["average_reward"])
            positive = reward > 0
            entries.append(
                KnowledgeEntry(
                    knowledge_type=(
                        "AGENT_WEIGHT_INCREASE"
                        if positive
                        else "AGENT_WEIGHT_REDUCTION"
                    ),
                    target=str(stats["agent"]),
                    statement=(
                        f"{stats['agent']} has an average observed reward "
                        f"of {reward:.4f} across "
                        f"{stats['decision_count']} evaluated outcomes."
                    ),
                    confidence=self._confidence(
                        int(stats["decision_count"]),
                        abs(reward),
                    ),
                    expected_benefit=reward,
                    priority=self._priority(
                        int(stats["decision_count"]),
                        abs(reward),
                    ),
                    evidence=dict(stats),
                    source="PHASE_3B_OUTCOME_FEEDBACK",
                )
            )

        for stats in self.store.operation_statistics():
            if not self._supported(stats):
                continue

            reward = float(stats["average_reward"])
            positive = reward > 0
            entries.append(
                KnowledgeEntry(
                    knowledge_type=(
                        "OPERATION_PREFERENCE"
                        if positive
                        else "OPERATION_AVOIDANCE"
                    ),
                    target=str(stats["operation"]).upper(),
                    statement=(
                        f"Operation {stats['operation']} has an average "
                        f"observed reward of {reward:.4f} across "
                        f"{stats['decision_count']} evaluated outcomes."
                    ),
                    confidence=self._confidence(
                        int(stats["decision_count"]),
                        abs(reward),
                    ),
                    expected_benefit=reward,
                    priority=self._priority(
                        int(stats["decision_count"]),
                        abs(reward),
                    ),
                    evidence=dict(stats),
                    source="PHASE_3B_OUTCOME_FEEDBACK",
                )
            )

        if not entries:
            return []

        return self.knowledge_base.add_many(
            entries,
            reinforce_duplicates=True,
        )

    def status(self) -> dict[str, Any]:
        return {
            "minimum_experiences": self.MINIMUM_EXPERIENCES,
            "minimum_absolute_reward": self.MINIMUM_ABSOLUTE_REWARD,
            "agent_candidates": len(
                self.store.agent_statistics()
            ),
            "operation_candidates": len(
                self.store.operation_statistics()
            ),
        }

    def _supported(self, stats: dict[str, Any]) -> bool:
        return (
            int(stats["decision_count"])
            >= self.MINIMUM_EXPERIENCES
            and abs(float(stats["average_reward"]))
            >= self.MINIMUM_ABSOLUTE_REWARD
        )

    @staticmethod
    def _confidence(
        count: int,
        absolute_reward: float,
    ) -> float:
        return round(
            min(
                0.95,
                0.40
                + min(count, 10) * 0.04
                + min(absolute_reward, 1.0) * 0.20,
            ),
            4,
        )

    @staticmethod
    def _priority(
        count: int,
        absolute_reward: float,
    ) -> str:
        if count >= 8 and absolute_reward >= 0.25:
            return "CRITICAL"
        if count >= 5 or absolute_reward >= 0.15:
            return "HIGH"
        return "MEDIUM"
