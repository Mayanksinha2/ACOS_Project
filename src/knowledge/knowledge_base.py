import json
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional

from models.knowledge_entry import KnowledgeEntry


class KnowledgeBase:
    """
    Persistent knowledge repository for ACOS.

    The knowledge base stores learned information and
    retrieves it during future commerce decisions.
    """

    def __init__(
        self,
        storage_path: str = "data/knowledge_base.json",
        auto_load: bool = True,
        auto_save: bool = True
    ):
        self.storage_path = Path(
            storage_path
        )

        self.auto_save = auto_save

        self._entries: Dict[
            str,
            KnowledgeEntry
        ] = {}

        if auto_load:
            self.load()

    def add(
        self,
        entry: KnowledgeEntry,
        reinforce_duplicates: bool = True
    ) -> KnowledgeEntry:
        """
        Add knowledge to the repository.

        When the same knowledge type and target already
        exist, it is reinforced instead of duplicated.
        """

        if not isinstance(
            entry,
            KnowledgeEntry
        ):
            raise TypeError(
                "entry must be a KnowledgeEntry."
            )

        existing = self.get_by_unique_key(
            entry.unique_key
        )

        if (
            existing is not None
            and reinforce_duplicates
        ):
            existing.reinforce(
                confidence=entry.confidence,
                expected_benefit=(
                    entry.expected_benefit
                ),
                evidence=entry.evidence
            )

            existing.statement = entry.statement
            existing.priority = self._higher_priority(
                existing.priority,
                entry.priority
            )

            existing.is_active = True

            if self.auto_save:
                self.save()

            return existing

        if entry.knowledge_id in self._entries:
            raise ValueError(
                "A knowledge entry with ID "
                f"{entry.knowledge_id} already exists."
            )

        self._entries[
            entry.knowledge_id
        ] = entry

        if self.auto_save:
            self.save()

        return entry

    def add_many(
        self,
        entries: Iterable[KnowledgeEntry],
        reinforce_duplicates: bool = True
    ) -> List[KnowledgeEntry]:
        """
        Add multiple knowledge entries.
        """

        added_entries = []

        original_auto_save = self.auto_save
        self.auto_save = False

        try:
            for entry in entries:
                added_entries.append(
                    self.add(
                        entry=entry,
                        reinforce_duplicates=(
                            reinforce_duplicates
                        )
                    )
                )
        finally:
            self.auto_save = original_auto_save

        if self.auto_save:
            self.save()

        return added_entries

    def get_all(
        self,
        active_only: bool = False
    ) -> List[KnowledgeEntry]:
        """
        Return all stored knowledge.
        """

        entries = list(
            self._entries.values()
        )

        if active_only:
            entries = [
                entry
                for entry in entries
                if entry.is_active
            ]

        return sorted(
            entries,
            key=lambda entry: (
                entry.updated_at,
                entry.confidence
            ),
            reverse=True
        )

    def get_by_id(
        self,
        knowledge_id: str
    ) -> Optional[KnowledgeEntry]:
        """
        Retrieve knowledge by its ID.
        """

        return self._entries.get(
            knowledge_id
        )

    def get_by_unique_key(
        self,
        unique_key: str
    ) -> Optional[KnowledgeEntry]:
        """
        Retrieve knowledge using its stable semantic key.
        """

        normalized_key = (
            str(unique_key)
            .strip()
            .upper()
        )

        for entry in self._entries.values():
            if (
                entry.unique_key.upper()
                == normalized_key
            ):
                return entry

        return None

    def get_by_type(
        self,
        knowledge_type: str,
        active_only: bool = True
    ) -> List[KnowledgeEntry]:
        """
        Retrieve knowledge by category.
        """

        normalized_type = (
            str(knowledge_type)
            .strip()
            .upper()
        )

        return [
            entry
            for entry in self.get_all(
                active_only=active_only
            )
            if entry.knowledge_type
            == normalized_type
        ]

    def get_by_target(
        self,
        target: str,
        active_only: bool = True
    ) -> List[KnowledgeEntry]:
        """
        Retrieve knowledge associated with a target.
        """

        normalized_target = (
            str(target)
            .strip()
            .upper()
        )

        return [
            entry
            for entry in self.get_all(
                active_only=active_only
            )
            if entry.target.upper()
            == normalized_target
        ]

    def search(
        self,
        query: str,
        active_only: bool = True
    ) -> List[KnowledgeEntry]:
        """
        Search knowledge using text matching.
        """

        normalized_query = (
            str(query)
            .strip()
            .lower()
        )

        if not normalized_query:
            return self.get_all(
                active_only=active_only
            )

        matches = []

        for entry in self.get_all(
            active_only=active_only
        ):
            searchable_text = " ".join([
                entry.knowledge_type,
                entry.target,
                entry.statement,
                entry.priority,
                entry.source,
                json.dumps(
                    entry.evidence,
                    default=str
                )
            ]).lower()

            if normalized_query in searchable_text:
                matches.append(
                    entry
                )

        return matches

    def get_relevant_knowledge(
        self,
        agent_name: Optional[str] = None,
        operation: Optional[str] = None,
        context: Optional[dict] = None,
        minimum_confidence: float = 0.0
    ) -> List[KnowledgeEntry]:
        """
        Retrieve knowledge relevant to a future decision.

        Relevance is determined using:

        - Agent name
        - Operation
        - Business context
        - Confidence threshold
        """

        minimum_confidence = max(
            0.0,
            min(
                float(minimum_confidence),
                1.0
            )
        )

        context = context or {}

        search_terms = set()

        if agent_name:
            search_terms.add(
                str(agent_name)
                .strip()
                .upper()
            )

        if operation:
            search_terms.add(
                str(operation)
                .strip()
                .upper()
            )

        for key, value in context.items():
            search_terms.add(
                str(key)
                .strip()
                .upper()
            )

            search_terms.add(
                str(value)
                .strip()
                .upper()
            )

            search_terms.add(
                (
                    f"{str(key).strip().upper()}="
                    f"{str(value).strip().upper()}"
                )
            )

        relevant = []

        for entry in self.get_all(
            active_only=True
        ):
            if (
                entry.confidence
                < minimum_confidence
            ):
                continue

            searchable_values = {
                entry.target.upper(),
                entry.knowledge_type.upper()
            }

            searchable_text = " ".join([
                entry.target,
                entry.statement,
                entry.knowledge_type,
                json.dumps(
                    entry.evidence,
                    default=str
                )
            ]).upper()

            exact_target_match = any(
                term in searchable_values
                for term in search_terms
            )

            text_match = any(
                term
                and term in searchable_text
                for term in search_terms
            )

            if exact_target_match or text_match:
                relevant.append(
                    entry
                )

        return sorted(
            relevant,
            key=lambda entry: (
                self._priority_value(
                    entry.priority
                ),
                entry.confidence,
                entry.occurrence_count
            ),
            reverse=True
        )

    def get_preferred_operations(
        self
    ) -> List[KnowledgeEntry]:
        """
        Return learned preferred operations.
        """

        return self.get_by_type(
            "OPERATION_PREFERENCE"
        )

    def get_avoided_operations(
        self
    ) -> List[KnowledgeEntry]:
        """
        Return learned operations that should be avoided.
        """

        return self.get_by_type(
            "OPERATION_AVOIDANCE"
        )

    def get_agent_knowledge(
        self,
        agent_name: str
    ) -> List[KnowledgeEntry]:
        """
        Return learned knowledge about an agent.
        """

        valid_types = {
            "AGENT_WEIGHT_INCREASE",
            "AGENT_WEIGHT_REDUCTION"
        }

        return [
            entry
            for entry in self.get_by_target(
                agent_name
            )
            if entry.knowledge_type
            in valid_types
        ]

    def average_confidence(
        self,
        active_only: bool = True
    ) -> float:
        """
        Calculate average knowledge confidence.
        """

        entries = self.get_all(
            active_only=active_only
        )

        if not entries:
            return 0.0

        return round(
            mean(
                entry.confidence
                for entry in entries
            ),
            4
        )

    def deactivate(
        self,
        knowledge_id: str
    ) -> bool:
        """
        Deactivate a knowledge entry.
        """

        entry = self.get_by_id(
            knowledge_id
        )

        if entry is None:
            return False

        entry.deactivate()

        if self.auto_save:
            self.save()

        return True

    def activate(
        self,
        knowledge_id: str
    ) -> bool:
        """
        Reactivate a knowledge entry.
        """

        entry = self.get_by_id(
            knowledge_id
        )

        if entry is None:
            return False

        entry.activate()

        if self.auto_save:
            self.save()

        return True

    def remove(
        self,
        knowledge_id: str
    ) -> bool:
        """
        Permanently remove knowledge.
        """

        if knowledge_id not in self._entries:
            return False

        del self._entries[
            knowledge_id
        ]

        if self.auto_save:
            self.save()

        return True

    def clear(
        self,
        delete_storage_file: bool = False
    ) -> None:
        """
        Remove all in-memory knowledge.
        """

        self._entries.clear()

        if delete_storage_file:
            if self.storage_path.exists():
                self.storage_path.unlink()
        elif self.auto_save:
            self.save()

    def save(self) -> None:
        """
        Persist knowledge to JSON.
        """

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        payload = {
            "version": "1.0",
            "entry_count": len(
                self._entries
            ),
            "entries": [
                entry.to_dict()
                for entry in self._entries.values()
            ]
        }

        temporary_path = self.storage_path.with_suffix(
            self.storage_path.suffix + ".tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                payload,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        temporary_path.replace(
            self.storage_path
        )

    def load(self) -> int:
        """
        Load knowledge from persistent storage.

        Returns the number of loaded entries.
        """

        if not self.storage_path.exists():
            return 0

        try:
            with self.storage_path.open(
                "r",
                encoding="utf-8"
            ) as file:
                payload = json.load(
                    file
                )
        except (
            json.JSONDecodeError,
            OSError
        ) as error:
            raise RuntimeError(
                "Unable to load knowledge base from "
                f"{self.storage_path}: {error}"
            ) from error

        entries_data = payload.get(
            "entries",
            []
        )

        loaded_entries: Dict[
            str,
            KnowledgeEntry
        ] = {}

        for entry_data in entries_data:
            entry = KnowledgeEntry.from_dict(
                entry_data
            )

            loaded_entries[
                entry.knowledge_id
            ] = entry

        self._entries = loaded_entries

        return len(
            self._entries
        )

    def summary(self) -> dict:
        """
        Return knowledge-base statistics.
        """

        all_entries = self.get_all()
        active_entries = self.get_all(
            active_only=True
        )

        type_counts: Dict[str, int] = {}

        for entry in all_entries:
            type_counts[
                entry.knowledge_type
            ] = (
                type_counts.get(
                    entry.knowledge_type,
                    0
                )
                + 1
            )

        return {
            "total_entries": len(
                all_entries
            ),
            "active_entries": len(
                active_entries
            ),
            "inactive_entries": (
                len(all_entries)
                - len(active_entries)
            ),
            "average_confidence": (
                self.average_confidence()
            ),
            "type_counts": type_counts,
            "storage_path": str(
                self.storage_path
            )
        }

    def __len__(self) -> int:
        return len(
            self._entries
        )

    @staticmethod
    def _priority_value(
        priority: str
    ) -> int:
        return {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }.get(
            str(priority).upper(),
            0
        )

    @classmethod
    def _higher_priority(
        cls,
        first: str,
        second: str
    ) -> str:
        if (
            cls._priority_value(second)
            > cls._priority_value(first)
        ):
            return second

        return first