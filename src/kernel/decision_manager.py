from typing import Dict, List, Optional

from knowledge.knowledge_advisor import KnowledgeAdvisor
from knowledge.knowledge_base import KnowledgeBase
from knowledge.knowledge_guided_score_calculator import (
    KnowledgeGuidedScoreCalculator,
)
from models.commerce_decision import CommerceDecision
from models.conflict_result import ConflictResult
from models.negotiation_result import NegotiationResult
from negotiation.adaptive_negotiation import AdaptiveNegotiationEngine
from negotiation.conflict_detector import ConflictDetector
from negotiation.mocra import MOCRA, MOCRAResult
from negotiation.score_calculator import ScoreCalculator


class DecisionManager:
    """
    Collects, compares, negotiates, and resolves CommerceDecision
    proposals submitted to the ACOS Kernel.
    """

    def __init__(self):
        self._pending_decisions: Dict[str, CommerceDecision] = {}
        self._decision_history: List[CommerceDecision] = []

        self._conflict_detector = ConflictDetector()
        self._conflict_results: List[ConflictResult] = []

        knowledge_base = KnowledgeBase(
            storage_path="data/knowledge_base.json",
            auto_load=True,
            auto_save=True,
        )

        knowledge_advisor = KnowledgeAdvisor(
            knowledge_base=knowledge_base,
            minimum_confidence=0.40,
            maximum_adjustment=0.30,
        )

        base_score_calculator = ScoreCalculator()

        knowledge_guided_calculator = (
            KnowledgeGuidedScoreCalculator(
                base_score_calculator=base_score_calculator,
                knowledge_advisor=knowledge_advisor,
            )
        )

        self._mocra = MOCRA(
            score_calculator=knowledge_guided_calculator
        )

        self._latest_mocra_result: Optional[MOCRAResult] = None

        self._negotiation_engine = AdaptiveNegotiationEngine()
        self._latest_negotiation_result: Optional[
            NegotiationResult
        ] = None

    def add_proposal(
        self,
        decision: CommerceDecision,
    ) -> CommerceDecision:
        """
        Add a new proposal to the pending proposal collection.
        """

        if decision.proposal_id in self._pending_decisions:
            raise ValueError(
                f"Duplicate proposal ID: {decision.proposal_id}"
            )

        decision.negotiation_status = "QUEUED"

        self._pending_decisions[
            decision.proposal_id
        ] = decision

        return decision

    def get_proposal(
        self,
        proposal_id: str,
    ) -> Optional[CommerceDecision]:
        """
        Retrieve one pending proposal by its ID.
        """

        return self._pending_decisions.get(
            proposal_id
        )

    def get_pending_proposals(
        self,
    ) -> List[CommerceDecision]:
        """
        Return all pending proposals.
        """

        return list(
            self._pending_decisions.values()
        )

    def pending_count(
        self,
    ) -> int:
        """
        Return the number of pending proposals.
        """

        return len(
            self._pending_decisions
        )

    def remove_proposal(
        self,
        proposal_id: str,
    ) -> Optional[CommerceDecision]:
        """
        Remove one proposal from the pending collection.
        """

        return self._pending_decisions.pop(
            proposal_id,
            None,
        )

    def mark_completed(
        self,
        proposal_id: str,
        final_status: str = "COMPLETED",
    ) -> CommerceDecision:
        """
        Move a pending proposal into decision history.
        """

        decision = self.remove_proposal(
            proposal_id
        )

        if decision is None:
            raise KeyError(
                f"Proposal not found: {proposal_id}"
            )

        decision.negotiation_status = final_status

        self._decision_history.append(
            decision
        )

        return decision

    def get_history(
        self,
    ) -> List[CommerceDecision]:
        """
        Return completed decision history.
        """

        return list(
            self._decision_history
        )

    def detect_conflicts(
        self,
    ) -> List[ConflictResult]:
        """
        Compare every pending proposal pair exactly once.
        """

        self._conflict_results = []

        proposals = self.get_pending_proposals()

        for first_index in range(
            len(proposals)
        ):
            for second_index in range(
                first_index + 1,
                len(proposals),
            ):
                result = (
                    self._conflict_detector.compare(
                        proposals[first_index],
                        proposals[second_index],
                    )
                )

                self._conflict_results.append(
                    result
                )

        return list(
            self._conflict_results
        )

    def get_conflict_results(
        self,
    ) -> List[ConflictResult]:
        """
        Return the latest conflict-detection results.
        """

        return list(
            self._conflict_results
        )

    def has_negotiation_required(
        self,
    ) -> bool:
        """
        Return True when at least one detected conflict
        requires negotiation.
        """

        for result in self._conflict_results:
            if result.requires_negotiation:
                return True

        return False

    def negotiate_pending_proposals(
        self,
    ) -> Optional[NegotiationResult]:
        """
        Run adaptive negotiation over the pending proposals.
        """

        proposals = self.get_pending_proposals()

        if len(proposals) < 2:
            return None

        self._latest_negotiation_result = (
            self._negotiation_engine.negotiate(
                proposals
            )
        )

        return self._latest_negotiation_result

    def get_latest_negotiation_result(
        self,
    ) -> Optional[NegotiationResult]:
        """
        Return the most recent negotiation result.
        """

        return self._latest_negotiation_result

    def resolve_pending_proposals(
        self,
    ) -> MOCRAResult:
        """
        Resolve pending proposals using MOCRA.
        """

        proposals = self.get_pending_proposals()

        if not proposals:
            raise ValueError(
                "No pending proposals are available."
            )

        self._latest_mocra_result = (
            self._mocra.resolve(
                proposals
            )
        )

        return self._latest_mocra_result

    def get_latest_mocra_result(
        self,
    ) -> Optional[MOCRAResult]:
        """
        Return the most recent MOCRA result.
        """

        return self._latest_mocra_result

    def make_final_decision(
        self,
    ):
        """
        Main decision-orchestration method.

        Process:
        1. Detect proposal conflicts.
        2. Attempt negotiation when required.
        3. Return the negotiated agreement when successful.
        4. Otherwise resolve proposals using MOCRA.
        """

        self.detect_conflicts()

        if self.has_negotiation_required():
            negotiation_result = (
                self.negotiate_pending_proposals()
            )

            if (
                negotiation_result is not None
                and negotiation_result.agreement_reached
            ):
                return {
                    "decision_type": "NEGOTIATED",
                    "result": negotiation_result,
                }

        mocra_result = (
            self.resolve_pending_proposals()
        )

        return {
            "decision_type": "MOCRA",
            "result": mocra_result,
        }