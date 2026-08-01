from simulator.scenario_generator import (
    ScenarioGenerator,
)


def test_manual_scenario() -> None:
    generator = ScenarioGenerator(
        random_seed=42
    )

    scenario = generator.create_manual_scenario(
        scenario_name="High Demand Frock",
        product_id="PROD-001",
        product_name="Pink Party Frock",
        category="PARTY_WEAR",
        cost_price=420.0,
        selling_price=799.0,
        inventory=35,
        demand_level="HIGH",
        season="FESTIVAL",
        demand_multiplier=1.5,
        competitor_price_factor=1.10,
        advertising_cost=1200.0,
        customer_count=25,
    )

    summary = scenario.summary()

    print("\nManual Scenario")
    print("-" * 50)
    print(summary)

    assert scenario.scenario_name == (
        "High Demand Frock"
    )

    assert len(
        scenario.customers
    ) == 25

    assert scenario.product is not None
    assert scenario.market is not None
    assert scenario.environment is not None


def test_random_scenario() -> None:
    generator = ScenarioGenerator(
        random_seed=100
    )

    scenario = (
        generator.generate_random_scenario()
    )

    summary = scenario.summary()

    print("\nRandom Scenario")
    print("-" * 50)
    print(summary)

    assert scenario.scenario_id
    assert scenario.product is not None
    assert len(
        scenario.customers
    ) > 0


def test_batch_generation() -> None:
    generator = ScenarioGenerator(
        random_seed=200
    )

    scenarios = generator.generate_batch(
        number_of_scenarios=5,
        customer_count=10,
    )

    print("\nGenerated Batch")
    print("-" * 50)

    for scenario in scenarios:
        print(
            scenario.scenario_id,
            scenario.scenario_name,
            scenario.product.demand_level,
        )

    assert len(scenarios) == 5

    for scenario in scenarios:
        assert len(
            scenario.customers
        ) == 10


def run_tests() -> None:
    test_manual_scenario()
    test_random_scenario()
    test_batch_generation()

    print(
        "\nScenario Generator tests passed."
    )


if __name__ == "__main__":
    run_tests()