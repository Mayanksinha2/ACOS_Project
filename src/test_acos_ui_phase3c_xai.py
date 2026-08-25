from __future__ import annotations

from acos_ui.xai_explanations import DynamicExplanationEngine


def payload() -> dict:
    return {
        "scenario": {
            "product_id": "PROD-XAI-001",
            "current_price": 999.0,
            "competitor_price_factor": 0.90,
            "inventory": 95,
            "demand": 58.0,
            "visitors": 4200,
            "sales": 134,
            "revenue": 120466.0,
            "profit": 17600.0,
            "advertising_cost": 500.0,
            "marketing_budget": 55000.0,
            "season": "SALE",
        },
        "calculated_metrics": {
            "adjusted_demand": 66.7,
            "conversion_rate": 134 / 4200,
        },
        "proposals": [
            {
                "agent": "PricingAgent",
                "operation": "MAINTAIN",
                "value": 0,
            },
            {
                "agent": "InventoryAgent",
                "operation": "MAINTAIN_STOCK",
                "value": 0,
            },
            {
                "agent": "MarketingAgent",
                "operation": "DECREASE",
                "value": 15,
            },
        ],
    }


def run_tests() -> None:
    explanations = DynamicExplanationEngine().explain_all(payload())

    pricing = explanations["PricingAgent"]
    inventory = explanations["InventoryAgent"]
    marketing = explanations["MarketingAgent"]

    assert any("₹999.00" in item for item in pricing.observations)
    assert any("3.19%" in item for item in pricing.observations)
    assert any("95 units" in item for item in inventory.observations)
    assert any("4,200" in item for item in marketing.observations)
    assert any("134" in item for item in marketing.observations)
    assert "15.00%" in marketing.conclusion

    print("ACOS UI Phase 3C XAI tests passed.")


if __name__ == "__main__":
    run_tests()
