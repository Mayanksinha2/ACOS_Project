"""
Analytics engine for ACOS experiments.

Transforms ExperimentResult into measurable research
and dashboard metrics.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

from analytics.analytics_result import (
    ExperimentAnalytics,
)
from experiments.experiment_result import (
    ExperimentResult,
)


class AnalyticsEngine:
    """
    Generate aggregated analytics from ACOS experiments.
    """

    def analyze(
        self,
        experiment_result: ExperimentResult,
    ) -> ExperimentAnalytics:
        """
        Analyze one complete ExperimentResult.
        """

        if experiment_result is None:
            raise ValueError(
                "experiment_result cannot be None."
            )

        analytics = ExperimentAnalytics(
            experiment_id=str(
                getattr(
                    experiment_result,
                    "experiment_id",
                    "UNKNOWN",
                )
            ),
            experiment_name=str(
                getattr(
                    experiment_result,
                    "experiment_name",
                    "Unnamed Experiment",
                )
            ),
        )

        try:
            scenario_results = list(
                getattr(
                    experiment_result,
                    "scenario_results",
                    [],
                )
                or []
            )

            analytics.total_scenarios = len(
                scenario_results
            )

            analytics.successful_scenarios = sum(
                1
                for scenario_result
                in scenario_results
                if getattr(
                    scenario_result,
                    "successful",
                    False,
                )
            )

            analytics.failed_scenarios = (
                analytics.total_scenarios
                - analytics.successful_scenarios
            )

            analytics.success_rate = (
                self._safe_rate(
                    analytics.successful_scenarios,
                    analytics.total_scenarios,
                )
            )

            analytics.failure_rate = (
                self._safe_rate(
                    analytics.failed_scenarios,
                    analytics.total_scenarios,
                )
            )

            execution_times = [
                self._safe_float(
                    getattr(
                        scenario_result,
                        "execution_time_seconds",
                        0.0,
                    )
                )
                for scenario_result
                in scenario_results
            ]

            if execution_times:
                analytics.average_execution_time = (
                    round(
                        mean(execution_times),
                        6,
                    )
                )

                analytics.minimum_execution_time = (
                    round(
                        min(execution_times),
                        6,
                    )
                )

                analytics.maximum_execution_time = (
                    round(
                        max(execution_times),
                        6,
                    )
                )

            selected_agent_counter: Counter = (
                Counter()
            )

            operation_counter: Counter = Counter()
            proposal_agent_counter: Counter = (
                Counter()
            )

            conflict_counter: Counter = Counter()

            proposal_confidences: List[float] = []
            proposal_risks: List[float] = []
            mocra_scores: List[float] = []

            for scenario_result in scenario_results:
                run_result = getattr(
                    scenario_result,
                    "run_result",
                    None,
                )

                scenario_summary = (
                    self._analyze_scenario(
                        scenario_result
                    )
                )

                analytics.scenario_summaries.append(
                    scenario_summary
                )

                if run_result is None:
                    continue

                proposals = list(
                    getattr(
                        run_result,
                        "proposals",
                        [],
                    )
                    or []
                )

                analytics.total_proposals += len(
                    proposals
                )

                for proposal in proposals:
                    agent_id = str(
                        getattr(
                            proposal,
                            "agent_id",
                            "UnknownAgent",
                        )
                    )

                    proposal_agent_counter[
                        agent_id
                    ] += 1

                    proposal_confidences.append(
                        self._safe_float(
                            getattr(
                                proposal,
                                "confidence",
                                0.0,
                            )
                        )
                    )

                    proposal_risks.append(
                        self._safe_float(
                            getattr(
                                proposal,
                                "risk",
                                0.0,
                            )
                        )
                    )

                conflict_count = len(
                    list(
                        getattr(
                            run_result,
                            "conflicts",
                            [],
                        )
                        or []
                    )
                )

                analytics.total_conflicts += (
                    conflict_count
                )

                conflict_counter[
                    conflict_count
                ] += 1

                negotiation_required = bool(
                    getattr(
                        run_result,
                        "negotiation_required",
                        False,
                    )
                )

                if negotiation_required:
                    analytics.negotiation_count += 1

                negotiation_result = getattr(
                    run_result,
                    "negotiation_result",
                    None,
                )

                if negotiation_result is not None:
                    agreement_reached = bool(
                        getattr(
                            negotiation_result,
                            "agreement_reached",
                            False,
                        )
                    )

                    if agreement_reached:
                        analytics.agreement_count += 1

                mocra_result = getattr(
                    run_result,
                    "mocra_result",
                    None,
                )

                selected_agent = (
                    self._extract_selected_agent(
                        mocra_result
                    )
                )

                selected_operation = (
                    self._extract_selected_operation(
                        mocra_result
                    )
                )

                if selected_agent:
                    selected_agent_counter[
                        selected_agent
                    ] += 1

                if selected_operation:
                    operation_counter[
                        selected_operation
                    ] += 1

                mocra_scores.extend(
                    self._extract_mocra_scores(
                        mocra_result
                    )
                )

            analytics.negotiation_rate = (
                self._safe_rate(
                    analytics.negotiation_count,
                    analytics.total_scenarios,
                )
            )

            analytics.agreement_rate = (
                self._safe_rate(
                    analytics.agreement_count,
                    analytics.negotiation_count,
                )
            )

            analytics.average_confidence = (
                self._safe_average(
                    proposal_confidences
                )
            )

            analytics.average_risk = (
                self._safe_average(
                    proposal_risks
                )
            )

            analytics.average_mocra_score = (
                self._safe_average(
                    mocra_scores
                )
            )

            analytics.selected_agent_frequency = (
                dict(selected_agent_counter)
            )

            analytics.operation_frequency = dict(
                operation_counter
            )

            analytics.proposal_agent_frequency = (
                dict(proposal_agent_counter)
            )

            analytics.conflict_distribution = (
                dict(conflict_counter)
            )

            analytics.selected_agent_percentage = (
                self._calculate_percentages(
                    selected_agent_counter
                )
            )

            analytics.operation_percentage = (
                self._calculate_percentages(
                    operation_counter
                )
            )

            analytics.metadata.update(
                {
                    "completed_at": getattr(
                        experiment_result,
                        "completed_at",
                        None,
                    ),
                    "source_metadata": dict(
                        getattr(
                            experiment_result,
                            "metadata",
                            {},
                        )
                        or {}
                    ),
                    "scenarios_with_selected_agent": (
                        sum(
                            selected_agent_counter.values()
                        )
                    ),
                    "mocra_score_count": len(
                        mocra_scores
                    ),
                }
            )

        except Exception as error:
            analytics.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return analytics

    def analyze_many(
        self,
        experiment_results: Iterable[
            ExperimentResult
        ],
    ) -> List[ExperimentAnalytics]:
        """
        Analyze multiple experiments.
        """

        return [
            self.analyze(experiment_result)
            for experiment_result
            in experiment_results
        ]

    def compare(
        self,
        experiment_results: Iterable[
            ExperimentResult
        ],
    ) -> Dict[str, Any]:
        """
        Produce a high-level comparison of several experiments.
        """

        analytics_results = self.analyze_many(
            experiment_results
        )

        if not analytics_results:
            return {
                "experiment_count": 0,
                "experiments": [],
                "best_success_rate": None,
                "lowest_average_risk": None,
                "fastest_experiment": None,
            }

        best_success = max(
            analytics_results,
            key=lambda result:
            result.success_rate,
        )

        lowest_risk = min(
            analytics_results,
            key=lambda result:
            result.average_risk,
        )

        fastest = min(
            analytics_results,
            key=lambda result:
            result.average_execution_time,
        )

        return {
            "experiment_count": len(
                analytics_results
            ),
            "experiments": [
                result.summary()
                for result
                in analytics_results
            ],
            "best_success_rate": {
                "experiment_id": (
                    best_success.experiment_id
                ),
                "experiment_name": (
                    best_success.experiment_name
                ),
                "value": (
                    best_success.success_rate
                ),
            },
            "lowest_average_risk": {
                "experiment_id": (
                    lowest_risk.experiment_id
                ),
                "experiment_name": (
                    lowest_risk.experiment_name
                ),
                "value": (
                    lowest_risk.average_risk
                ),
            },
            "fastest_experiment": {
                "experiment_id": (
                    fastest.experiment_id
                ),
                "experiment_name": (
                    fastest.experiment_name
                ),
                "value": (
                    fastest.average_execution_time
                ),
            },
        }

    def _analyze_scenario(
        self,
        scenario_result: Any,
    ) -> Dict[str, Any]:
        run_result = getattr(
            scenario_result,
            "run_result",
            None,
        )

        summary: Dict[str, Any] = {
            "scenario_id": str(
                getattr(
                    scenario_result,
                    "scenario_id",
                    "UNKNOWN",
                )
            ),
            "scenario_name": str(
                getattr(
                    scenario_result,
                    "scenario_name",
                    "Unnamed Scenario",
                )
            ),
            "successful": bool(
                getattr(
                    scenario_result,
                    "successful",
                    False,
                )
            ),
            "execution_time_seconds": (
                self._safe_float(
                    getattr(
                        scenario_result,
                        "execution_time_seconds",
                        0.0,
                    )
                )
            ),
            "error": getattr(
                scenario_result,
                "error",
                None,
            ),
        }

        if run_result is None:
            return summary

        mocra_result = getattr(
            run_result,
            "mocra_result",
            None,
        )

        negotiation_result = getattr(
            run_result,
            "negotiation_result",
            None,
        )

        summary.update(
            {
                "run_id": getattr(
                    run_result,
                    "run_id",
                    None,
                ),
                "proposal_count": len(
                    list(
                        getattr(
                            run_result,
                            "proposals",
                            [],
                        )
                        or []
                    )
                ),
                "conflict_count": len(
                    list(
                        getattr(
                            run_result,
                            "conflicts",
                            [],
                        )
                        or []
                    )
                ),
                "negotiation_required": bool(
                    getattr(
                        run_result,
                        "negotiation_required",
                        False,
                    )
                ),
                "agreement_reached": (
                    bool(
                        getattr(
                            negotiation_result,
                            "agreement_reached",
                            False,
                        )
                    )
                    if negotiation_result
                    is not None
                    else None
                ),
                "selected_agent": (
                    self._extract_selected_agent(
                        mocra_result
                    )
                ),
                "selected_operation": (
                    self._extract_selected_operation(
                        mocra_result
                    )
                ),
                "winning_score": (
                    self._extract_winning_score(
                        mocra_result
                    )
                ),
            }
        )

        return summary

    @staticmethod
    def _extract_selected_agent(
        mocra_result: Any,
    ) -> Optional[str]:
        if mocra_result is None:
            return None

        winning_decision = getattr(
            mocra_result,
            "winning_decision",
            None,
        )

        if winning_decision is None:
            return None

        agent_id = getattr(
            winning_decision,
            "agent_id",
            None,
        )

        return (
            str(agent_id)
            if agent_id is not None
            else None
        )

    @staticmethod
    def _extract_selected_operation(
        mocra_result: Any,
    ) -> Optional[str]:
        if mocra_result is None:
            return None

        winning_decision = getattr(
            mocra_result,
            "winning_decision",
            None,
        )

        if winning_decision is None:
            return None

        action = getattr(
            winning_decision,
            "business_action",
            None,
        )

        if action is None:
            return None

        operation = getattr(
            action,
            "operation",
            None,
        )

        return (
            str(operation)
            if operation is not None
            else None
        )

    def _extract_winning_score(
        self,
        mocra_result: Any,
    ) -> Optional[float]:
        if mocra_result is None:
            return None

        score = getattr(
            mocra_result,
            "winning_score",
            None,
        )

        if score is None:
            return None

        return self._safe_float(score)

    def _extract_mocra_scores(
        self,
        mocra_result: Any,
    ) -> List[float]:
        if mocra_result is None:
            return []

        scores: List[float] = []

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

            score_details = (
                ranked_item.get(
                    "score_details",
                    {},
                )
                or {}
            )

            score = score_details.get(
                "final_score"
            )

            if score is not None:
                scores.append(
                    self._safe_float(score)
                )

        return scores

    @staticmethod
    def _calculate_percentages(
        counter: Counter,
    ) -> Dict[str, float]:
        total = sum(counter.values())

        if total == 0:
            return {}

        return {
            str(key): round(
                value / total,
                4,
            )
            for key, value
            in counter.items()
        }

    @staticmethod
    def _safe_rate(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            numerator / denominator,
            4,
        )

    @staticmethod
    def _safe_average(
        values: List[float],
    ) -> float:
        if not values:
            return 0.0

        return round(
            mean(values),
            6,
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