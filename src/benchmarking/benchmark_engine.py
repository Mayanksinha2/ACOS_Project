from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Dict, Iterable, List

from benchmarking.benchmark_result import (
    BenchmarkExperimentResult,
    ScenarioBenchmarkResult,
)
from benchmarking.benchmark_reward_evaluator import (
    BenchmarkRewardEvaluator,
)
from benchmarking.benchmark_strategies import (
    ACOSStrategy,
    BenchmarkStrategy,
    HighestConfidenceStrategy,
    RandomSelectionStrategy,
    RuleBasedStrategy,
)


class BenchmarkEngine:
    """
    Compare ACOS against baseline decision strategies.
    """

    def __init__(
        self,
        strategies: Iterable[
            BenchmarkStrategy
        ] | None = None,
        reward_evaluator: (
            BenchmarkRewardEvaluator | None
        ) = None,
        random_seed: int = 2026,
    ) -> None:
        self.strategies = list(
            strategies
            or [
                ACOSStrategy(),
                HighestConfidenceStrategy(),
                RandomSelectionStrategy(
                    random_seed=random_seed
                ),
                RuleBasedStrategy(),
            ]
        )

        self.reward_evaluator = (
            reward_evaluator
            or BenchmarkRewardEvaluator()
        )

    def benchmark_scenario(
        self,
        scenario_result: Any,
    ) -> ScenarioBenchmarkResult:
        scenario_id = str(
            getattr(
                scenario_result,
                "scenario_id",
                "UNKNOWN",
            )
        )

        scenario_name = str(
            getattr(
                scenario_result,
                "scenario_name",
                "Unnamed Scenario",
            )
        )

        result = ScenarioBenchmarkResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
        )

        try:
            run_result = getattr(
                scenario_result,
                "run_result",
                None,
            )

            if run_result is None:
                raise ValueError(
                    "Scenario run result is missing."
                )

            proposals = list(
                getattr(
                    run_result,
                    "proposals",
                    [],
                )
                or []
            )

            business_state = getattr(
                run_result,
                "business_state",
                None,
            )

            if business_state is None:
                business_state = getattr(
                    scenario_result,
                    "business_state",
                    None,
                )

            for strategy in self.strategies:
                decision = strategy.select(
                    proposals=proposals,
                    run_result=run_result,
                    business_state=business_state,
                )

                decision.reward = (
                    self.reward_evaluator.evaluate(
                        decision,
                        business_state,
                    )
                )

                result.strategy_decisions[
                    strategy.strategy_name
                ] = decision

            self._calculate_comparison(
                result
            )

        except Exception as error:
            result.successful = False
            result.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return result

    def benchmark_experiment(
        self,
        experiment_result: Any,
        experiment_name: str | None = None,
    ) -> BenchmarkExperimentResult:
        name = (
            experiment_name
            or str(
                getattr(
                    experiment_result,
                    "experiment_name",
                    "ACOS Benchmark Experiment",
                )
            )
        )

        experiment_id = str(
            getattr(
                experiment_result,
                "experiment_id",
                "",
            )
        ).strip()

        if not experiment_id:
            raise ValueError(
                "experiment_result must contain "
                "a valid experiment_id."
            )

        benchmark = BenchmarkExperimentResult(
            experiment_id=experiment_id,
            experiment_name=name,
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

            benchmark.total_scenarios = len(
                scenario_results
            )

            for scenario_result in scenario_results:
                result = self.benchmark_scenario(
                    scenario_result
                )

                benchmark.scenario_results.append(
                    result
                )

            benchmark.successful_scenarios = sum(
                1
                for result in benchmark.scenario_results
                if result.successful
            )

            benchmark.failed_scenarios = (
                benchmark.total_scenarios
                - benchmark.successful_scenarios
            )

            self._aggregate(
                benchmark
            )

        except Exception as error:
            benchmark.errors.append(
                f"{type(error).__name__}: "
                f"{error}"
            )

        return benchmark

    def benchmark_many(
        self,
        experiment_results: Iterable[Any],
    ) -> List[BenchmarkExperimentResult]:
        return [
            self.benchmark_experiment(
                experiment_result
            )
            for experiment_result
            in experiment_results
        ]

    def _calculate_comparison(
        self,
        result: ScenarioBenchmarkResult,
    ) -> None:
        decisions = {
            name: decision
            for name, decision
            in result.strategy_decisions.items()
            if decision.successful
        }

        if not decisions:
            result.successful = False
            result.errors.append(
                "No strategy produced a valid decision."
            )
            return

        acos = decisions.get("ACOS")

        if acos is not None:
            for name, decision in (
                decisions.items()
            ):
                if name == "ACOS":
                    continue

                result.agreement_with_acos[
                    name
                ] = (
                    decision.selected_agent
                    == acos.selected_agent
                    and
                    decision.selected_operation
                    == acos.selected_operation
                )

        result.best_reward_strategy = max(
            decisions,
            key=lambda name: (
                decisions[name].reward
            ),
        )

        result.lowest_risk_strategy = min(
            decisions,
            key=lambda name: (
                decisions[name].risk
            ),
        )

        result.highest_confidence_strategy = max(
            decisions,
            key=lambda name: (
                decisions[name].confidence
            ),
        )

        result.fastest_strategy = min(
            decisions,
            key=lambda name: (
                decisions[
                    name
                ].execution_time_seconds
            ),
        )

    def _aggregate(
        self,
        benchmark: BenchmarkExperimentResult,
    ) -> None:
        strategy_frequency: Counter = Counter()
        reward_wins: Counter = Counter()
        risk_wins: Counter = Counter()
        confidence_wins: Counter = Counter()
        speed_wins: Counter = Counter()

        rewards: Dict[
            str,
            List[float],
        ] = defaultdict(list)

        risks: Dict[
            str,
            List[float],
        ] = defaultdict(list)

        confidences: Dict[
            str,
            List[float],
        ] = defaultdict(list)

        execution_times: Dict[
            str,
            List[float],
        ] = defaultdict(list)

        agreement_counts: Counter = Counter()
        agreement_totals: Counter = Counter()

        for scenario_result in (
            benchmark.scenario_results
        ):
            if (
                scenario_result
                .best_reward_strategy
            ):
                reward_wins[
                    scenario_result
                    .best_reward_strategy
                ] += 1

            if (
                scenario_result
                .lowest_risk_strategy
            ):
                risk_wins[
                    scenario_result
                    .lowest_risk_strategy
                ] += 1

            if (
                scenario_result
                .highest_confidence_strategy
            ):
                confidence_wins[
                    scenario_result
                    .highest_confidence_strategy
                ] += 1

            if scenario_result.fastest_strategy:
                speed_wins[
                    scenario_result.fastest_strategy
                ] += 1

            for strategy_name, decision in (
                scenario_result
                .strategy_decisions
                .items()
            ):
                strategy_frequency[
                    strategy_name
                ] += 1

                if not decision.successful:
                    continue

                rewards[
                    strategy_name
                ].append(
                    decision.reward
                )

                risks[
                    strategy_name
                ].append(
                    decision.risk
                )

                confidences[
                    strategy_name
                ].append(
                    decision.confidence
                )

                execution_times[
                    strategy_name
                ].append(
                    decision
                    .execution_time_seconds
                )

            for strategy_name, agreed in (
                scenario_result
                .agreement_with_acos
                .items()
            ):
                agreement_totals[
                    strategy_name
                ] += 1

                if agreed:
                    agreement_counts[
                        strategy_name
                    ] += 1

        benchmark.strategy_frequency = dict(
            strategy_frequency
        )

        benchmark.reward_win_frequency = dict(
            reward_wins
        )

        benchmark.risk_win_frequency = dict(
            risk_wins
        )

        benchmark.confidence_win_frequency = (
            dict(confidence_wins)
        )

        benchmark.speed_win_frequency = dict(
            speed_wins
        )

        benchmark.average_reward = {
            name: round(
                mean(values),
                6,
            )
            for name, values
            in rewards.items()
            if values
        }

        benchmark.average_risk = {
            name: round(
                mean(values),
                6,
            )
            for name, values
            in risks.items()
            if values
        }

        benchmark.average_confidence = {
            name: round(
                mean(values),
                6,
            )
            for name, values
            in confidences.items()
            if values
        }

        benchmark.average_execution_time = {
            name: round(
                mean(values),
                9,
            )
            for name, values
            in execution_times.items()
            if values
        }

        benchmark.acos_agreement_rate = {
            name: round(
                agreement_counts[name]
                / agreement_totals[name],
                4,
            )
            for name in agreement_totals
            if agreement_totals[name] > 0
        }