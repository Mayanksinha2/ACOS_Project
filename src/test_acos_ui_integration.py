from acos_ui import ACOSUIAdapter, ScenarioInput


def test_adapter_executes_real_pipeline():
    payload = ACOSUIAdapter().run_payload(
        ScenarioInput(
            product_id="PROD-UI-001",
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
    )
    assert payload["status"] == "COMPLETED", payload.get("errors")
    assert payload["successful"] is True
    assert len(payload["proposals"]) == 3
    assert payload["final_decision"] is not None
    agents = {item["agent"] for item in payload["proposals"]}
    assert agents == {"PricingAgent", "InventoryAgent", "MarketingAgent"}


def test_validation():
    try:
        ScenarioInput(product_id="", inventory=1).validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid product ID to fail")


def run_tests():
    test_adapter_executes_real_pipeline()
    test_validation()
    print("ACOS UI integration tests passed.")


if __name__ == "__main__":
    run_tests()
