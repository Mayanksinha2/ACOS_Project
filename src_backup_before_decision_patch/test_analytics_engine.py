from analytics.analytics_engine import (
    AnalyticsEngine,
)
from experiments.experiment_runner import (
    ExperimentRunner,
)
from simulator.scenario_generator import (
    ScenarioGenerator,
)


def print_analytics(analytics) -> None:
    print("\nACOS EXPERIMENT ANALYTICS")
    print("=" * 75)

    summary = analytics.summary()

    for key, value in summary.items():
        print(f"{key:<32}: {value}")

    print("\nCONFLICT DISTRIBUTION")
    print("-" * 75)

    for conflict_count, frequency in (
        analytics.conflict_distribution.items()
    ):
        print(
            f"{conflict_count} conflict(s): "
            f"{frequency} scenario(s)"
        )

    print("\nSCENARIO SUMMARIES")
    print("-" * 75)

    for scenario in (
        analytics.scenario_summaries
    ):
        print(
            scenario["scenario_name"],
            "→",
            scenario.get(
                "selected_agent"
            ),
            "/",
            scenario.get(
                "selected_operation"
            ),
        )


def test_random_experiment_analytics() -> None:
    generator = ScenarioGenerator(
        random_seed=2026
    )

    runner = ExperimentRunner(
        scenario_generator=generator
    )

    experiment = (
        runner.run_random_experiment(
            scenario_count=20,
            customer_count=50,
            experiment_name=(
                "Twenty Scenario Analytics Test"
            ),
        )
    )

    analytics = AnalyticsEngine().analyze(
        experiment
    )

    print_analytics(
        analytics
    )

    assert analytics.successful

    assert analytics.total_scenarios == 20

    assert (
        analytics.successful_scenarios
        + analytics.failed_scenarios
        == 20
    )

    assert 0 <= analytics.success_rate <= 1

    assert 0 <= analytics.failure_rate <= 1

    assert 0 <= analytics.negotiation_rate <= 1

    assert 0 <= analytics.agreement_rate <= 1

    assert analytics.total_proposals >= 0

    assert analytics.total_conflicts >= 0

    assert analytics.average_execution_time >= 0

    assert analytics.average_confidence >= 0

    assert analytics.average_risk >= 0

    assert analytics.average_mocra_score >= 0

    assert len(
        analytics.scenario_summaries
    ) == 20


def test_manual_experiment_analytics() -> None:
    generator = ScenarioGenerator(
        random_seed=42
    )

    scenarios = [
        generator.create_manual_scenario(
            scenario_name=(
                "Critical Inventory"
            ),
            product_id="ANALYTICS-001",
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
                "Excess Inventory"
            ),
            product_id="ANALYTICS-002",
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
        generator.create_manual_scenario(
            scenario_name=(
                "Balanced Conditions"
            ),
            product_id="ANALYTICS-003",
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
    ]

    experiment = ExperimentRunner(
        scenario_generator=generator
    ).run_scenarios(
        scenarios,
        experiment_name=(
            "Manual Analytics Conditions"
        ),
    )

    analytics = AnalyticsEngine().analyze(
        experiment
    )

    print_analytics(
        analytics
    )

    assert analytics.total_scenarios == 3

    assert analytics.total_proposals == 9

    assert len(
        analytics.proposal_agent_frequency
    ) == 3

    assert (
        analytics.proposal_agent_frequency[
            "PricingAgent"
        ]
        == 3
    )

    assert (
        analytics.proposal_agent_frequency[
            "InventoryAgent"
        ]
        == 3
    )

    assert (
        analytics.proposal_agent_frequency[
            "MarketingAgent"
        ]
        == 3
    )

    assert sum(
        analytics
        .selected_agent_frequency
        .values()
    ) == 3

    assert sum(
        analytics
        .operation_frequency
        .values()
    ) == 3


def test_empty_experiment_analytics() -> None:
    experiment = ExperimentRunner().run_scenarios(
        [],
        experiment_name="Empty Analytics Test",
    )

    analytics = AnalyticsEngine().analyze(
        experiment
    )

    assert analytics.total_scenarios == 0
    assert analytics.success_rate == 0.0
    assert analytics.failure_rate == 0.0
    assert analytics.negotiation_rate == 0.0
    assert analytics.agreement_rate == 0.0
    assert analytics.average_confidence == 0.0
    assert analytics.average_risk == 0.0
    assert analytics.average_mocra_score == 0.0


def test_experiment_comparison() -> None:
    generator_one = ScenarioGenerator(
        random_seed=100
    )

    generator_two = ScenarioGenerator(
        random_seed=200
    )

    first_experiment = ExperimentRunner(
        scenario_generator=generator_one
    ).run_random_experiment(
        scenario_count=5,
        customer_count=25,
        experiment_name="Experiment One",
    )

    second_experiment = ExperimentRunner(
        scenario_generator=generator_two
    ).run_random_experiment(
        scenario_count=5,
        customer_count=25,
        experiment_name="Experiment Two",
    )

    comparison = AnalyticsEngine().compare(
        [
            first_experiment,
            second_experiment,
        ]
    )

    print("\nEXPERIMENT COMPARISON")
    print("=" * 75)
    print(comparison)

    assert comparison["experiment_count"] == 2
    assert len(comparison["experiments"]) == 2
    assert comparison["best_success_rate"]
    assert comparison["lowest_average_risk"]
    assert comparison["fastest_experiment"]


def run_tests() -> None:
    test_random_experiment_analytics()
    test_manual_experiment_analytics()
    test_empty_experiment_analytics()
    test_experiment_comparison()

    print(
        "\nAnalytics Engine tests passed."
    )


if __name__ == "__main__":
    run_tests()