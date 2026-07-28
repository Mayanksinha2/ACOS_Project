from agents.inventory_agent import InventoryAgent
from agents.marketing_agent import MarketingAgent
from agents.pricing_agent import PricingAgent
from application.business_state_builder import (
    BusinessStateBuilder,
)
from reasoning.inventory_reasoner import (
    InventoryReasoner,
)
from reasoning.marketing_reasoner import (
    MarketingReasoner,
)
from reasoning.rule_reasoner import RuleReasoner
from simulator.scenario_generator import (
    ScenarioGenerator,
)


def test_manual_business_state() -> None:
    state = (
        BusinessStateBuilder.build_from_manual_input(
            product_id="PROD-MANUAL-001",
            inventory=15,
            demand=85,
            conversion_rate=0.03,
            advertising_cost=1200,
            sales=3,
            revenue=2397,
            profit=1137,
            visitors=100,
            season="FESTIVAL",
            demand_multiplier=1.5,
            competitor_price_factor=1.1,
        )
    )

    print("\nManual BusinessState")
    print("-" * 60)
    print("Market:", state.market)
    print("Metrics:", state.metrics)

    assert (
        state.metrics["product_id"]
        == "PROD-MANUAL-001"
    )
    assert state.metrics["inventory"] == 15
    assert state.market["demand"] == 85.0
    assert (
        state.metrics["conversion_rate"]
        == 0.03
    )


def test_scenario_conversion() -> None:
    generator = ScenarioGenerator(
        random_seed=42
    )

    scenario = generator.create_manual_scenario(
        scenario_name="Festival Frock Test",
        product_id="PROD-SCENARIO-001",
        product_name="Pink Festival Frock",
        category="PARTY_WEAR",
        cost_price=420,
        selling_price=799,
        inventory=15,
        demand_level="HIGH",
        season="FESTIVAL",
        demand_multiplier=1.0,
        competitor_price_factor=1.1,
        advertising_cost=1200,
        customer_count=100,
    )

    state = BusinessStateBuilder.build_from_scenario(
        scenario,
        visitors=100,
        sales=3,
        revenue=2397,
    )

    print("\nScenario BusinessState")
    print("-" * 60)
    print("Market:", state.market)
    print("Metrics:", state.metrics)

    assert (
        state.metrics["product_id"]
        == "PROD-SCENARIO-001"
    )
    assert state.metrics["inventory"] == 15
    assert state.market["demand"] == 85.0
    assert (
        state.metrics["conversion_rate"]
        == 0.03
    )
    assert len(state.products) == 1
    assert len(state.customers) == 100


def test_environment_conversion() -> None:
    generator = ScenarioGenerator(
        random_seed=100
    )

    scenario = (
        generator.generate_random_scenario(
            customer_count=20
        )
    )

    state = (
        BusinessStateBuilder.build_from_environment(
            scenario.environment
        )
    )

    print("\nEnvironment BusinessState")
    print("-" * 60)
    print("Market:", state.market)
    print("Metrics:", state.metrics)

    assert state.metrics["product_id"]
    assert state.metrics["inventory"] >= 0
    assert 0 <= state.market["demand"] <= 100
    assert len(state.customers) == 20


def test_agents_use_built_state() -> None:
    state = (
        BusinessStateBuilder.build_from_manual_input(
            product_id="PROD-AGENT-001",
            inventory=15,
            demand=85,
            conversion_rate=0.03,
            advertising_cost=1200,
            visitors=100,
            sales=3,
            revenue=2397,
            profit=1137,
        )
    )

    agents = [
        PricingAgent(
            RuleReasoner()
        ),
        InventoryAgent(
            InventoryReasoner()
        ),
        MarketingAgent(
            MarketingReasoner()
        ),
    ]

    decisions = []

    for agent in agents:
        agent.observe(state)
        agent.analyze()

        decision = agent.generate_decision()
        decisions.append(decision)

        print(
            "\n",
            decision.agent_id,
            "→",
            decision.business_action.operation,
        )

    pricing_action = (
        decisions[0].business_action
    )

    inventory_action = (
        decisions[1].business_action
    )

    marketing_action = (
        decisions[2].business_action
    )

    assert pricing_action.operation == "INCREASE"
    assert (
        inventory_action.operation
        == "PROTECT_STOCK"
    )
    assert marketing_action.operation == "DECREASE"

    for decision in decisions:
        assert (
            decision.business_action.target
            == "PROD-AGENT-001"
        )


def test_metrics_dictionary_conversion() -> None:
    state = BusinessStateBuilder.build_from_metrics(
        metrics={
            "product_id": "PROD-DICT-001",
            "inventory": 150,
            "conversion_rate": 0.08,
            "sales": 8,
            "revenue": 6392,
            "profit": 3032,
            "visitors": 100,
            "custom_metric": "preserved",
        },
        market={
            "demand": 30,
            "advertising_cost": 800,
            "season": "NORMAL",
            "demand_multiplier": 0.8,
            "competitor_price_factor": 0.95,
            "custom_market_value": "preserved",
        },
    )

    assert (
        state.metrics["custom_metric"]
        == "preserved"
    )

    assert (
        state.market["custom_market_value"]
        == "preserved"
    )


def test_invalid_input() -> None:
    try:
        BusinessStateBuilder.build_from_manual_input(
            product_id="PROD-INVALID",
            inventory=-1,
            demand=50,
            conversion_rate=0.05,
            advertising_cost=100,
        )

        raise AssertionError(
            "Negative inventory should fail"
        )

    except ValueError as error:
        print(
            "\nExpected validation error:",
            error,
        )


def run_tests() -> None:
    test_manual_business_state()
    test_scenario_conversion()
    test_environment_conversion()
    test_agents_use_built_state()
    test_metrics_dictionary_conversion()
    test_invalid_input()

    print(
        "\nBusinessStateBuilder tests passed."
    )


if __name__ == "__main__":
    run_tests()