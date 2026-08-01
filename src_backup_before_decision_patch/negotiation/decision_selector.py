from typing import Any, Dict, List


class DecisionSelector:
    """
    Ranks scored proposals and selects the highest-scoring one.
    """

    @staticmethod
    def rank(
        scored_proposals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        if not scored_proposals:
            raise ValueError(
                "At least one scored proposal is required."
            )

        return sorted(
            scored_proposals,
            key=lambda item: (
                item["score_details"]["final_score"],
                item["decision"].confidence,
                -item["decision"].risk,
                item["decision"].business_action.priority
            ),
            reverse=True
        )

    @classmethod
    def select(
        cls,
        scored_proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        ranking = cls.rank(scored_proposals)

        return ranking[0]