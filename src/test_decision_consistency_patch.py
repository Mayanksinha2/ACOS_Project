from application.acos_application_service import ACOSApplicationService
from application.business_state_builder import BusinessStateBuilder


def test_user_dashboard_scenario():
    state = BusinessStateBuilder.build_from_manual_input(
        product_id="PROD-DEMO-001",
        inventory=30,
        demand=30,
        conversion_rate=45 / 1200,
        advertising_cost=500,
        visitors=1200,
        sales=45,
        revenue=42980,
        profit=7500,
        season="SALE",
        demand_multiplier=1.5,
        competitor_price_factor=1.15,
        additional_metrics={
            "current_price": 999.0,
            "unit_cost": 320.0,
            "marketing_budget": 55000.0,
        },
    )

    result = ACOSApplicationService().run(state)
    operations = {
        proposal.agent_id: proposal.business_action.operation
        for proposal in result.proposals
    }

    assert result.successful
    assert state.market["base_demand"] == 30.0
    assert state.market["adjusted_demand"] == 45.0
    # 45 / 1200 = 3.75%, so MarketingAgent correctly proposes a
    # discount. That creates one price-domain conflict with PricingAgent.
    assert result.conflict_count == 1
    assert result.negotiation_required is True
    assert result.negotiation_result is not None
    assert result.negotiation_result.participant_agents == [
        "PricingAgent",
        "MarketingAgent",
    ]
    assert operations == {
        "PricingAgent": "MAINTAIN",
        "InventoryAgent": "MAINTAIN_STOCK",
        "MarketingAgent": "DECREASE",
    }
    assert result.final_decision["decision_type"] == "NEGOTIATED"
    assert len(result.final_decision["coordinated_actions"]) == 3


def test_negotiation_object_is_reused():
    state = BusinessStateBuilder.build_from_manual_input(
        product_id="PROD-CONFLICT-001",
        inventory=15,
        demand=85,
        conversion_rate=0.03,
        advertising_cost=1200,
        visitors=100,
        sales=3,
        revenue=2397,
        profit=1137,
        season="FESTIVAL",
    )
    result = ACOSApplicationService().run(state)
    assert result.negotiation_required is True
    assert result.negotiation_result is not None
    assert result.final_decision["decision_type"] == "NEGOTIATED"
    assert result.final_decision["result"] is result.negotiation_result
    assert (
        result.final_decision["result"].negotiation_id
        == result.negotiation_result.negotiation_id
    )


if __name__ == "__main__":
    test_user_dashboard_scenario()
    test_negotiation_object_is_reused()
    print("Decision consistency patch tests passed.")
