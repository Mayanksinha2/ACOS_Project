"""
Explainability engine for ACOS decisions.

Transforms ACOSRunResult into clear, auditable,
human-readable decision explanations.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from explainability.explanation_result import (
    AgentProposalExplanation,
    DecisionExplanation,
)
from models.acos_run_result import ACOSRunResult


class ExplainabilityEngine:
    """
    Produce structured explanations for ACOS decisions.
    """

    def explain(
        self,
        run_result: ACOSRunResult,
    ) -> DecisionExplanation:
        """
        Generate a complete explanation for one ACOS run.
        """

        if run_result is None:
            raise ValueError(
                "run_result cannot be None."
            )

        product_id = self._extract_product_id(
            run_result
        )

        explanation = DecisionExplanation(
            run_id=str(
                getattr(
                    run_result,
                    "run_id",
                    "UNKNOWN",
                )
            ),
            status=str(
                getattr(
                    run_result,
                    "status",
                    "UNKNOWN",
                )
            ),
            product_id=product_id,
            negotiation_required=bool(
                getattr(
                    run_result,
                    "negotiation_required",
                    False,
                )
            ),
            errors=list(
                getattr(
                    run_result,
                    "errors",
                    [],
                )
                or []
            ),
        )

        try:
            score_map = self._build_score_map(
                getattr(
                    run_result,
                    "mocra_result",
                    None,
                )
            )

            selected_proposal_id = (
                self._extract_selected_proposal_id(
                    getattr(
                        run_result,
                        "mocra_result",
                        None,
                    )
                )
            )

            explanation.proposal_explanations = (
                self._explain_proposals(
                    proposals=getattr(
                        run_result,
                        "proposals",
                        [],
                    ),
                    score_map=score_map,
                    selected_proposal_id=(
                        selected_proposal_id
                    ),
                )
            )

            explanation.conflict_summary = (
                self._explain_conflicts(
                    getattr(
                        run_result,
                        "conflicts",
                        [],
                    )
                )
            )

            (
                explanation.negotiation_summary,
                explanation.agreement_reached,
            ) = self._explain_negotiation(
                getattr(
                    run_result,
                    "negotiation_result",
                    None,
                )
            )

            explanation.mocra_summary = (
                self._explain_mocra(
                    getattr(
                        run_result,
                        "mocra_result",
                        None,
                    )
                )
            )

            (
                explanation.selected_agent,
                explanation.selected_operation,
            ) = self._extract_selected_decision(
                getattr(
                    run_result,
                    "mocra_result",
                    None,
                )
            )

            explanation.final_decision_summary = (
                self._explain_final_decision(
                    getattr(
                        run_result,
                        "final_decision",
                        None,
                    )
                )
            )

            explanation.confidence_summary = (
                self._build_confidence_summary(
                    explanation
                    .proposal_explanations
                )
            )

            explanation.risk_summary = (
                self._build_risk_summary(
                    explanation
                    .proposal_explanations
                )
            )

            explanation.business_interpretation = (
                self._build_business_interpretation(
                    explanation
                )
            )

            explanation.metadata.update(
                {
                    "proposal_count": len(
                        explanation
                        .proposal_explanations
                    ),
                    "conflict_count": len(
                        explanation
                        .conflict_summary
                    ),
                    "mocra_score_count": len(
                        score_map
                    ),
                }
            )

        except Exception as error:
            explanation.status = "FAILED"

            explanation.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return explanation

    def explain_many(
        self,
        run_results: Iterable[
            ACOSRunResult
        ],
    ) -> List[DecisionExplanation]:
        """
        Explain multiple ACOS runs.
        """

        return [
            self.explain(run_result)
            for run_result in run_results
        ]

    def _explain_proposals(
        self,
        *,
        proposals: Iterable[Any],
        score_map: Dict[str, float],
        selected_proposal_id: Optional[str],
    ) -> List[AgentProposalExplanation]:
        explanations: List[
            AgentProposalExplanation
        ] = []

        for proposal in list(
            proposals or []
        ):
            action = getattr(
                proposal,
                "business_action",
                None,
            )

            proposal_id = str(
                getattr(
                    proposal,
                    "proposal_id",
                    "",
                )
            )

            agent_id = str(
                getattr(
                    proposal,
                    "agent_id",
                    "UnknownAgent",
                )
            )

            operation = str(
                getattr(
                    action,
                    "operation",
                    "UNKNOWN",
                )
            )

            action_type = str(
                getattr(
                    action,
                    "action_type",
                    "UNKNOWN",
                )
            )

            target = str(
                getattr(
                    action,
                    "target",
                    "UNKNOWN",
                )
            )

            value = self._safe_float(
                getattr(
                    action,
                    "value",
                    0.0,
                )
            )

            unit = str(
                getattr(
                    action,
                    "unit",
                    "",
                )
            )

            confidence = self._safe_float(
                getattr(
                    proposal,
                    "confidence",
                    getattr(
                        action,
                        "confidence",
                        0.0,
                    ),
                )
            )

            risk = self._safe_float(
                getattr(
                    proposal,
                    "risk",
                    getattr(
                        action,
                        "risk",
                        0.0,
                    ),
                )
            )

            priority = self._safe_int(
                getattr(
                    action,
                    "priority",
                    0,
                )
            )

            selected = (
                bool(selected_proposal_id)
                and proposal_id
                == selected_proposal_id
            )

            score = score_map.get(
                proposal_id
            )

            rationale = str(
                getattr(
                    action,
                    "rationale",
                    "No rationale was supplied.",
                )
            )

            proposal_explanation = (
                AgentProposalExplanation(
                    agent_id=agent_id,
                    goal=str(
                        getattr(
                            proposal,
                            "goal",
                            "",
                        )
                    ),
                    action_type=action_type,
                    operation=operation,
                    target=target,
                    value=value,
                    unit=unit,
                    rationale=rationale,
                    confidence=confidence,
                    risk=risk,
                    priority=priority,
                    expected_benefit=dict(
                        getattr(
                            proposal,
                            "expected_benefit",
                            {},
                        )
                        or {}
                    ),
                    evidence=list(
                        getattr(
                            proposal,
                            "evidence",
                            [],
                        )
                        or []
                    ),
                    selected=selected,
                    negotiation_status=str(
                        getattr(
                            proposal,
                            "negotiation_status",
                            "PENDING",
                        )
                    ),
                    score=score,
                    explanation=(
                        self._build_proposal_sentence(
                            agent_id=agent_id,
                            operation=operation,
                            value=value,
                            unit=unit,
                            target=target,
                            rationale=rationale,
                            confidence=confidence,
                            risk=risk,
                            score=score,
                            selected=selected,
                        )
                    ),
                )
            )

            explanations.append(
                proposal_explanation
            )

        return explanations

    @staticmethod
    def _build_proposal_sentence(
        *,
        agent_id: str,
        operation: str,
        value: float,
        unit: str,
        target: str,
        rationale: str,
        confidence: float,
        risk: float,
        score: Optional[float],
        selected: bool,
    ) -> str:
        action_value = (
            f" by {value:g} {unit}"
            if value != 0
            else ""
        )

        score_text = (
            f" Its MOCRA score was "
            f"{score:.3f}."
            if score is not None
            else ""
        )

        selection_text = (
            " This proposal was selected "
            "by MOCRA."
            if selected
            else ""
        )

        return (
            f"{agent_id} proposed to "
            f"{operation}{action_value} for "
            f"{target}. The stated reason was: "
            f"{rationale}. Confidence was "
            f"{confidence:.2f} and risk was "
            f"{risk:.2f}."
            f"{score_text}"
            f"{selection_text}"
        )

    def _explain_conflicts(
        self,
        conflicts: Iterable[Any],
    ) -> List[str]:
        conflict_list = list(
            conflicts or []
        )

        if not conflict_list:
            return [
                "No decision conflicts were detected."
            ]

        explanations: List[str] = []

        for index, conflict in enumerate(
            conflict_list,
            start=1,
        ):
            conflict_type = str(
                getattr(
                    conflict,
                    "conflict_type",
                    getattr(
                        conflict,
                        "type",
                        "DECISION_CONFLICT",
                    ),
                )
            )

            target = getattr(
                conflict,
                "target",
                None,
            )

            description = getattr(
                conflict,
                "description",
                None,
            )

            involved_agents = getattr(
                conflict,
                "involved_agents",
                getattr(
                    conflict,
                    "agents",
                    [],
                ),
            )

            if description:
                text = str(description)

            elif isinstance(
                conflict,
                dict,
            ):
                text = self._dict_conflict_text(
                    conflict
                )

            else:
                text = (
                    f"Conflict {index} of type "
                    f"{conflict_type}"
                )

                if target:
                    text += (
                        f" affected target "
                        f"{target}"
                    )

                if involved_agents:
                    text += (
                        " and involved "
                        + ", ".join(
                            str(agent)
                            for agent
                            in involved_agents
                        )
                    )

                text += "."

            explanations.append(text)

        return explanations

    @staticmethod
    def _dict_conflict_text(
        conflict: Dict[str, Any],
    ) -> str:
        conflict_type = str(
            conflict.get(
                "conflict_type",
                conflict.get(
                    "type",
                    "DECISION_CONFLICT",
                ),
            )
        )

        target = conflict.get("target")

        agents = conflict.get(
            "involved_agents",
            conflict.get(
                "agents",
                [],
            ),
        )

        text = (
            f"A {conflict_type} conflict "
            "was detected"
        )

        if target:
            text += f" for {target}"

        if agents:
            text += (
                " between "
                + ", ".join(
                    str(agent)
                    for agent in agents
                )
            )

        return text + "."

    def _explain_negotiation(
        self,
        negotiation_result: Any,
    ) -> tuple[List[str], Optional[bool]]:
        if negotiation_result is None:
            return (
                [
                    "Negotiation was not required "
                    "for this decision cycle."
                ],
                None,
            )

        explanation_lines = list(
            getattr(
                negotiation_result,
                "explanation",
                [],
            )
            or []
        )

        agreement_reached = getattr(
            negotiation_result,
            "agreement_reached",
            None,
        )

        final_operation = getattr(
            negotiation_result,
            "final_operation",
            None,
        )

        final_value = getattr(
            negotiation_result,
            "final_value",
            None,
        )

        unit = getattr(
            negotiation_result,
            "unit",
            "",
        )

        rounds = getattr(
            negotiation_result,
            "rounds_completed",
            None,
        )

        if not explanation_lines:
            if agreement_reached:
                explanation_lines.append(
                    "The participating agents "
                    "reached an agreement."
                )
            else:
                explanation_lines.append(
                    "The participating agents "
                    "did not reach an agreement."
                )

        if final_operation is not None:
            explanation_lines.append(
                "Negotiated outcome: "
                f"{final_operation} "
                f"{self._safe_float(final_value):g} "
                f"{unit}."
            )

        if rounds is not None:
            explanation_lines.append(
                f"Negotiation completed in "
                f"{rounds} round(s)."
            )

        return (
            explanation_lines,
            (
                bool(agreement_reached)
                if agreement_reached
                is not None
                else None
            ),
        )

    def _explain_mocra(
        self,
        mocra_result: Any,
    ) -> List[str]:
        if mocra_result is None:
            return [
                "No MOCRA result was available."
            ]

        existing_explanation = list(
            getattr(
                mocra_result,
                "explanation",
                [],
            )
            or []
        )

        if existing_explanation:
            return [
                str(line)
                for line
                in existing_explanation
            ]

        winner = getattr(
            mocra_result,
            "winning_decision",
            None,
        )

        winning_score = getattr(
            mocra_result,
            "winning_score",
            None,
        )

        if winner is None:
            return [
                "MOCRA did not select a "
                "winning proposal."
            ]

        agent_id = getattr(
            winner,
            "agent_id",
            "UnknownAgent",
        )

        operation = getattr(
            getattr(
                winner,
                "business_action",
                None,
            ),
            "operation",
            "UNKNOWN",
        )

        return [
            (
                f"MOCRA selected {agent_id} "
                f"with operation {operation} "
                f"and score "
                f"{self._safe_float(winning_score):.3f}."
            )
        ]

    def _explain_final_decision(
        self,
        final_decision: Any,
    ) -> str:
        if final_decision is None:
            return (
                "No final decision was produced."
            )

        if isinstance(
            final_decision,
            dict,
        ):
            decision_type = str(
                final_decision.get(
                    "decision_type",
                    "UNKNOWN",
                )
            )

            result = final_decision.get(
                "result"
            )

            if result is None:
                return (
                    f"The final decision type was "
                    f"{decision_type}."
                )

            final_operation = getattr(
                result,
                "final_operation",
                None,
            )

            final_value = getattr(
                result,
                "final_value",
                None,
            )

            unit = getattr(
                result,
                "unit",
                "",
            )

            agreement_reached = getattr(
                result,
                "agreement_reached",
                None,
            )

            if final_operation is not None:
                agreement_text = (
                    " after the agents reached "
                    "an agreement"
                    if agreement_reached
                    else ""
                )

                return (
                    f"The final {decision_type.lower()} "
                    f"decision was to "
                    f"{final_operation} "
                    f"{self._safe_float(final_value):g} "
                    f"{unit}{agreement_text}."
                )

            return (
                f"The final decision type was "
                f"{decision_type}: {result}"
            )

        action = getattr(
            final_decision,
            "business_action",
            None,
        )

        if action is not None:
            operation = getattr(
                action,
                "operation",
                "UNKNOWN",
            )

            target = getattr(
                action,
                "target",
                "UNKNOWN",
            )

            value = self._safe_float(
                getattr(
                    action,
                    "value",
                    0.0,
                )
            )

            unit = getattr(
                action,
                "unit",
                "",
            )

            return (
                f"The final decision was to "
                f"{operation} {value:g} {unit} "
                f"for {target}."
            )

        return str(final_decision)

    def _build_score_map(
        self,
        mocra_result: Any,
    ) -> Dict[str, float]:
        score_map: Dict[str, float] = {}

        if mocra_result is None:
            return score_map

        ranking = list(
            getattr(
                mocra_result,
                "ranking",
                [],
            )
            or []
        )

        for ranked_item in ranking:
            if not isinstance(
                ranked_item,
                dict,
            ):
                continue

            decision = ranked_item.get(
                "decision"
            )

            score_details = (
                ranked_item.get(
                    "score_details",
                    {},
                )
                or {}
            )

            proposal_id = str(
                getattr(
                    decision,
                    "proposal_id",
                    "",
                )
            )

            final_score = score_details.get(
                "final_score"
            )

            if (
                proposal_id
                and final_score is not None
            ):
                score_map[proposal_id] = (
                    self._safe_float(
                        final_score
                    )
                )

        return score_map

    @staticmethod
    def _extract_selected_proposal_id(
        mocra_result: Any,
    ) -> Optional[str]:
        if mocra_result is None:
            return None

        winner = getattr(
            mocra_result,
            "winning_decision",
            None,
        )

        if winner is None:
            return None

        proposal_id = getattr(
            winner,
            "proposal_id",
            None,
        )

        return (
            str(proposal_id)
            if proposal_id
            else None
        )

    @staticmethod
    def _extract_selected_decision(
        mocra_result: Any,
    ) -> tuple[
        Optional[str],
        Optional[str],
    ]:
        if mocra_result is None:
            return None, None

        winner = getattr(
            mocra_result,
            "winning_decision",
            None,
        )

        if winner is None:
            return None, None

        action = getattr(
            winner,
            "business_action",
            None,
        )

        return (
            str(
                getattr(
                    winner,
                    "agent_id",
                    "",
                )
            )
            or None,
            str(
                getattr(
                    action,
                    "operation",
                    "",
                )
            )
            or None,
        )

    @staticmethod
    def _extract_product_id(
        run_result: ACOSRunResult,
    ) -> Optional[str]:
        business_state = getattr(
            run_result,
            "business_state",
            None,
        )

        if business_state is None:
            return None

        metrics = getattr(
            business_state,
            "metrics",
            {},
        )

        if not isinstance(
            metrics,
            dict,
        ):
            return None

        product_id = metrics.get(
            "product_id"
        )

        return (
            str(product_id)
            if product_id is not None
            else None
        )

    @staticmethod
    def _build_confidence_summary(
        proposal_explanations: List[
            AgentProposalExplanation
        ],
    ) -> str:
        if not proposal_explanations:
            return (
                "No proposal confidence values "
                "were available."
            )

        highest = max(
            proposal_explanations,
            key=lambda proposal:
            proposal.confidence,
        )

        average = sum(
            proposal.confidence
            for proposal
            in proposal_explanations
        ) / len(proposal_explanations)

        return (
            f"The highest-confidence proposal "
            f"came from {highest.agent_id} "
            f"at {highest.confidence:.2f}. "
            f"Average agent confidence was "
            f"{average:.2f}."
        )

    @staticmethod
    def _build_risk_summary(
        proposal_explanations: List[
            AgentProposalExplanation
        ],
    ) -> str:
        if not proposal_explanations:
            return (
                "No proposal risk values "
                "were available."
            )

        lowest = min(
            proposal_explanations,
            key=lambda proposal:
            proposal.risk,
        )

        highest = max(
            proposal_explanations,
            key=lambda proposal:
            proposal.risk,
        )

        return (
            f"The lowest-risk proposal came "
            f"from {lowest.agent_id} at "
            f"{lowest.risk:.2f}. The highest "
            f"proposal risk was "
            f"{highest.risk:.2f}, submitted "
            f"by {highest.agent_id}."
        )

    @staticmethod
    def _build_business_interpretation(
        explanation: DecisionExplanation,
    ) -> str:
        if explanation.status != "COMPLETED":
            return (
                "The ACOS run did not complete, "
                "so no reliable business "
                "interpretation is available."
            )

        if (
            explanation.negotiation_required
            and explanation.agreement_reached
        ):
            return (
                "The agents identified competing "
                "business objectives and resolved "
                "them through negotiation. The "
                "final action represents a "
                "compromise between pricing, "
                "inventory protection, and "
                "conversion objectives."
            )

        if explanation.selected_agent:
            return (
                f"{explanation.selected_agent} "
                "provided the strongest proposal "
                "under the current confidence, "
                "risk, priority, and knowledge "
                "criteria. Its recommendation "
                "was therefore prioritized."
            )

        return (
            "The system completed its decision "
            "cycle, but no selected agent could "
            "be identified from the available "
            "result."
        )

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)