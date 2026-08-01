from typing import Any

from learning.learning_engine import LearningEngine
from models.adaptive_score import AdaptiveScore


class AdaptiveWeightOptimizer:
    """
    Applies learned agent reliability to proposal confidence.

    It does not permanently modify the original proposal.
    Instead, it calculates an adjusted confidence value
    for MOCRA scoring.
    """

    def __init__(
        self,
        learning_engine: LearningEngine,
        minimum_experiences: int = 3
    ):
        if not isinstance(
            learning_engine,
            LearningEngine
        ):
            raise TypeError(
                "learning_engine must be a LearningEngine object."
            )

        if minimum_experiences <= 0:
            raise ValueError(
                "minimum_experiences must be greater than zero."
            )

        self.learning_engine = learning_engine
        self.minimum_experiences = minimum_experiences

    def optimize_proposal(
        self,
        proposal: Any
    ) -> AdaptiveScore:
        """
        Calculate an adjusted confidence score
        for one proposal.
        """

        agent_name = self._extract_agent_name(
            proposal
        )

        original_confidence = self._extract_confidence(
            proposal
        )

        performance = (
            self.learning_engine.analyze_agent(
                agent_name
            )
        )

        learning_applied = (
            performance.experience_count
            >= self.minimum_experiences
        )

        if learning_applied:
            confidence_modifier = (
                performance.confidence_modifier
            )
        else:
            confidence_modifier = 1.0

        adjusted_confidence = self._clamp(
            original_confidence
            * confidence_modifier,
            0.0,
            1.0
        )

        return AdaptiveScore(
            agent_name=agent_name,
            original_confidence=round(
                original_confidence,
                4
            ),
            confidence_modifier=round(
                confidence_modifier,
                4
            ),
            adjusted_confidence=round(
                adjusted_confidence,
                4
            ),
            reliability_score=round(
                performance.reliability_score,
                4
            ),
            learning_applied=learning_applied
        )

    def apply_to_proposal(
        self,
        proposal: Any
    ) -> Any:
        """
        Attach learning metadata to the proposal.

        The original confidence remains unchanged.
        """

        adaptive_score = self.optimize_proposal(
            proposal
        )

        metadata = getattr(
            proposal,
            "metadata",
            None
        ) or {}

        if not isinstance(metadata, dict):
            raise TypeError(
                "Proposal metadata must be a dictionary."
            )

        metadata = metadata.copy()

        metadata["adaptive_learning"] = (
            adaptive_score.to_dict()
        )

        proposal.metadata = metadata

        return proposal

    @staticmethod
    def _extract_agent_name(
        proposal: Any
    ) -> str:
        """
        Extract the responsible agent name
        from different proposal structures.
        """

        possible_attributes = [
           "source_agent",
           "agent_name",
           "agent_id",
           "proposed_by",
           "sender"
       ]

        for attribute in possible_attributes:
            value = getattr(
                proposal,
                attribute,
                None
            )

            if isinstance(value, str) and value:
                return value

        raise ValueError(
            "Unable to determine proposal agent name."
        )

    @staticmethod
    def _extract_confidence(
        proposal: Any
    ) -> float:
        """
        Extract proposal confidence safely.
        """

        confidence = getattr(
            proposal,
            "confidence",
            None
        )

        if confidence is None:
            raise ValueError(
                "Proposal does not contain confidence."
            )

        if not isinstance(
            confidence,
            (int, float)
        ):
            raise TypeError(
                "Proposal confidence must be numeric."
            )

        return AdaptiveWeightOptimizer._clamp(
            float(confidence),
            0.0,
            1.0
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