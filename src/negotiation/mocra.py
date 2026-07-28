from dataclasses import dataclass
from typing import Any, Dict, List

from models.commerce_decision import CommerceDecision
from negotiation.decision_selector import DecisionSelector
from negotiation.score_calculator import ScoreCalculator


@dataclass
class MOCRAResult:
    """
    Result produced by the MOCRA algorithm.
    """

    winning_decision: CommerceDecision
    winning_score: float
    ranking: List[Dict[str, Any]]
    rejected_decisions: List[CommerceDecision]
    explanation: List[str]


class MOCRA:
    """
    Multi-Objective Conflict Resolution Algorithm.

    MOCRA scores, ranks, and selects the best proposal.
    """

    def __init__(
        self,
        score_calculator: ScoreCalculator = None,
        decision_selector: DecisionSelector = None
    ):
        self.score_calculator = (
            score_calculator or ScoreCalculator()
        )

        self.decision_selector = (
            decision_selector or DecisionSelector()
        )

    def resolve(
        self,
        decisions: List[CommerceDecision]
    ) -> MOCRAResult:

        if not decisions:
            raise ValueError(
                "MOCRA requires at least one proposal."
            )

        scored_proposals = []

        for decision in decisions:
            score_details = (
                self.score_calculator.calculate(decision)
            )

            scored_proposals.append({
                "decision": decision,
                "score_details": score_details
            })

        ranking = self.decision_selector.rank(
            scored_proposals
        )

        winner_entry = ranking[0]

        winning_decision = winner_entry["decision"]

        winning_score = (
            winner_entry["score_details"]["final_score"]
        )

        rejected_decisions = [
            entry["decision"]
            for entry in ranking[1:]
        ]

        explanation = self._build_explanation(
            ranking
        )

        winning_decision.negotiation_status = "SELECTED"

        for decision in rejected_decisions:
            decision.negotiation_status = "REJECTED"

        return MOCRAResult(
            winning_decision=winning_decision,
            winning_score=winning_score,
            ranking=ranking,
            rejected_decisions=rejected_decisions,
            explanation=explanation
        )

    @staticmethod
    def _build_explanation(
        ranking: List[Dict[str, Any]]
    ) -> List[str]:

        winner = ranking[0]

        decision = winner["decision"]
        details = winner["score_details"]
        action = decision.business_action

        explanation = [
            (
                f"{decision.agent_id} was selected with "
                f"a MOCRA score of "
                f"{details['final_score']}."
            ),
            (
                f"Confidence contribution was based on "
                f"a confidence value of "
                f"{details['confidence_score']}."
            ),
            (
                f"Risk-adjusted score was "
                f"{details['risk_score']}."
            ),
            (
                f"Normalized priority score was "
                f"{details['priority_score']}."
            ),
            (
                f"Selected action: "
                f"{action.operation} "
                f"{action.action_type} "
                f"for {action.target}."
            )
        ]

        if len(ranking) > 1:
            runner_up = ranking[1]

            explanation.append(
                (
                    f"The runner-up was "
                    f"{runner_up['decision'].agent_id} "
                    f"with a score of "
                    f"{runner_up['score_details']['final_score']}."
                )
            )

        return explanation