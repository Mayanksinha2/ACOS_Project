from experiments.experiment_runner import (
    ExperimentRunner,
)
from simulator.scenario_generator import (
    ScenarioGenerator,
)


def print_experiment_results(result) -> None:
    print("\nEXPERIMENT SUMMARY")
    print("=" * 70)

    summary = result.summary()

    for key, value in summary.items():
        print(f"{key:<28}: {value}")

    print("\nSCENARIO RESULTS")
    print("=" * 70)

    for index, scenario_result in enumerate(
        result.scenario_results,
        start=1,
    ):
        run_result = (
            scenario_result.run_result
        )

        print(
            f"\nScenario {index}: "
            f"{scenario_result.scenario_name}"
        )

        print(
            "Scenario ID:",
            scenario_result.scenario_id,
        )

        print(
            "Successful:",
            scenario_result.successful,
        )

        print(
            "Execution time:",
            scenario_result
            .execution_time_seconds,
        )

        print(
            "Proposals:",
            run_result.proposal_count,
        )

        print(
            "Conflicts:",
            run_result.conflict_count,
        )

        print(
            "Negotiation required:",
            run_result.negotiation_required,
        )

        print(
            "Final decision:",
            run_result.final_decision,
        )


def test_single_scenario() -> None:
    generator = ScenarioGenerator(
        random_seed=42
    )

    scenario = (
        generator.generate_random_scenario(
            customer_count=50
        )
    )

    runner = ExperimentRunner(
        scenario_generator=generator
    )

    result = runner.run_scenario(
        scenario
    )

    print("\nSingle Scenario Result")
    print("-" * 70)
    print(result.summary())

    assert result.scenario_id
    assert result.execution_time_seconds >= 0

    if result.successful:
        assert result.run_result.successful
        assert (
            result.run_result.proposal_count
            == 3
        )


def test_manual_scenario_batch() -> None:
    generator = ScenarioGenerator(
        random_seed=100
    )

    scenarios = [
        generator.create_manual_scenario(
            scenario_name=(
                "High Demand Low Inventory"
            ),
            product_id="EXP-001",
            product_name="Festival Frock",
            category="ETHNIC",
            cost_price=400,
            selling_price=799,
            inventory=10,
            demand_level="HIGH",
            season="FESTIVAL",
            demand_multiplier=1.2,
            competitor_price_factor=1.0,
            advertising_cost=1200,
            customer_count=100,
        ),
        generator.create_manual_scenario(
            scenario_name=(
                "Medium Demand Normal Inventory"
            ),
            product_id="EXP-002",
            product_name="Cotton Dress",
            category="CASUAL",
            cost_price=300,
            selling_price=599,
            inventory=80,
            demand_level="MEDIUM",
            season="NORMAL",
            demand_multiplier=1.0,
            competitor_price_factor=1.0,
            advertising_cost=600,
            customer_count=100,
        ),
        generator.create_manual_scenario(
            scenario_name=(
                "Low Demand High Inventory"
            ),
            product_id="EXP-003",
            product_name="Winter Jacket",
            category="WINTER",
            cost_price=500,
            selling_price=999,
            inventory=180,
            demand_level="LOW",
            season="OFF_SEASON",
            demand_multiplier=0.7,
            competitor_price_factor=0.95,
            advertising_cost=400,
            customer_count=100,
        ),
    ]

    runner = ExperimentRunner(
        scenario_generator=generator
    )

    result = runner.run_scenarios(
        scenarios,
        experiment_name=(
            "Manual Business Condition Test"
        ),
    )

    print_experiment_results(
        result
    )

    assert result.total_scenarios == 3

    assert (
        result.successful_scenarios
        + result.failed_scenarios
        == 3
    )

    assert 0 <= result.success_rate <= 1

    assert len(
        result.scenario_results
    ) == 3


def test_random_experiment() -> None:
    generator = ScenarioGenerator(
        random_seed=2026
    )

    runner = ExperimentRunner(
        scenario_generator=generator
    )

    result = (
        runner.run_random_experiment(
            scenario_count=10,
            customer_count=50,
            experiment_name=(
                "Ten Scenario ACOS Test"
            ),
        )
    )

    print_experiment_results(
        result
    )

    assert result.total_scenarios == 10

    assert (
        result.successful_scenarios
        + result.failed_scenarios
        == 10
    )

    assert result.average_execution_time >= 0

    assert (
        result.metadata[
            "generation_type"
        ]
        == "RANDOM"
    )


def test_empty_scenario_collection() -> None:
    runner = ExperimentRunner()

    result = runner.run_scenarios(
        [],
        experiment_name="Empty Test",
    )

    assert result.total_scenarios == 0
    assert result.success_rate == 0.0
    assert result.total_conflicts == 0
    assert result.negotiation_count == 0


def run_tests() -> None:
    test_single_scenario()
    test_manual_scenario_batch()
    test_random_experiment()
    test_empty_scenario_collection()

    print(
        "\nExperiment Runner tests passed."
    )


if __name__ == "__main__":
    run_tests()