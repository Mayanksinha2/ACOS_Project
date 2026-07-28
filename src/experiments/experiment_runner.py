"""
Experiment execution engine for ACOS.

Runs multiple commerce scenarios through the complete
ACOS decision pipeline and aggregates the results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Iterable, List, Optional

from application.acos_application_service import (
    ACOSApplicationService,
)
from application.business_state_builder import (
    BusinessStateBuilder,
)
from experiments.experiment_result import (
    ExperimentResult,
    ScenarioExperimentResult,
)
from models.acos_run_result import ACOSRunResult
from simulator.scenario_generator import (
    ScenarioGenerator,
)


class ExperimentRunner:
    """
    Execute ACOS against one or more generated scenarios.
    """

    def __init__(
        self,
        application_service: Optional[
            ACOSApplicationService
        ] = None,
        scenario_generator: Optional[
            ScenarioGenerator
        ] = None,
    ) -> None:
        self.application_service = (
            application_service
            or ACOSApplicationService()
        )

        self.scenario_generator = (
            scenario_generator
            or ScenarioGenerator()
        )

    def run_scenario(
        self,
        scenario: Any,
    ) -> ScenarioExperimentResult:
        """
        Execute a single CommerceScenario.
        """

        scenario_id = str(
            getattr(
                scenario,
                "scenario_id",
                "UNKNOWN",
            )
        )

        scenario_name = str(
            getattr(
                scenario,
                "scenario_name",
                "Unnamed Scenario",
            )
        )

        started = perf_counter()

        try:
            business_state = (
                BusinessStateBuilder
                .build_from_scenario(
                    scenario
                )
            )

            run_result = (
                self.application_service
                .run_safely(
                    business_state
                )
            )

            execution_time = (
                perf_counter() - started
            )

            return ScenarioExperimentResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                run_result=run_result,
                successful=run_result.successful,
                execution_time_seconds=round(
                    execution_time,
                    6,
                ),
                error=(
                    None
                    if run_result.successful
                    else "; ".join(
                        run_result.errors
                    )
                ),
                metadata={
                    "product_id": (
                        business_state.metrics.get(
                            "product_id"
                        )
                    ),
                    "inventory": (
                        business_state.metrics.get(
                            "inventory"
                        )
                    ),
                    "demand": (
                        business_state.market.get(
                            "demand"
                        )
                    ),
                },
            )

        except Exception as error:
            execution_time = (
                perf_counter() - started
            )

            failed_run = ACOSRunResult(
                business_state=getattr(
                    scenario,
                    "business_state",
                    None,
                ),
                status="FAILED",
                errors=[
                    f"{type(error).__name__}: "
                    f"{error}"
                ],
            )

            return ScenarioExperimentResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                run_result=failed_run,
                successful=False,
                execution_time_seconds=round(
                    execution_time,
                    6,
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    def run_scenarios(
        self,
        scenarios: Iterable[Any],
        *,
        experiment_name: str = (
            "ACOS Scenario Experiment"
        ),
    ) -> ExperimentResult:
        """
        Execute a supplied collection of scenarios.
        """

        experiment = ExperimentResult(
            experiment_name=experiment_name
        )

        scenario_list = list(scenarios)

        experiment.metadata[
            "requested_scenario_count"
        ] = len(scenario_list)

        for scenario in scenario_list:
            scenario_result = (
                self.run_scenario(
                    scenario
                )
            )

            experiment.scenario_results.append(
                scenario_result
            )

        experiment.completed_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return experiment

    def run_random_experiment(
        self,
        *,
        scenario_count: int,
        customer_count: int = 100,
        experiment_name: str = (
            "ACOS Random Experiment"
        ),
    ) -> ExperimentResult:
        """
        Generate and execute random scenarios.
        """

        if scenario_count <= 0:
            raise ValueError(
                "scenario_count must be greater "
                "than zero."
            )

        if customer_count < 0:
            raise ValueError(
                "customer_count cannot be negative."
            )

        scenarios: List[Any] = []

        for _ in range(scenario_count):
            scenario = (
                self.scenario_generator
                .generate_random_scenario(
                    customer_count=customer_count
                )
            )

            scenarios.append(
                scenario
            )

        result = self.run_scenarios(
            scenarios,
            experiment_name=experiment_name,
        )

        result.metadata.update(
            {
                "generation_type": "RANDOM",
                "customer_count_per_scenario": (
                    customer_count
                ),
            }
        )

        return result