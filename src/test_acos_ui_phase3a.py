from __future__ import annotations

from acos_ui.agent_profiles import build_agent_profiles
from acos_ui.presets import get_preset, preset_names
from acos_ui.presentation import build_final_plan


def sample_payload() -> dict:
    return {
        "run_id": "RUN-3A-001",
        "status": "COMPLETED",
        "successful": True,
        "scenario": {
            "product_id": "PROD-DEMO-001",
            "current_price": 999.0,
        },
        "proposals": [
            {
                "agent": "PricingAgent",
                "operation": "MAINTAIN",
                "value": 0,
                "unit": "PERCENT",
                "confidence": 0.65,
                "risk": 0.10,
                "rationale": "Stable pricing condition.",
            },
            {
                "agent": "InventoryAgent",
                "operation": "MAINTAIN_STOCK",
                "value": 0,
                "unit": "UNITS",
                "confidence": 0.70,
                "risk": 0.05,
                "rationale": "Stock and demand are balanced.",
            },
            {
                "agent": "MarketingAgent",
                "operation": "DECREASE",
                "value": 15,
                "unit": "PERCENT",
                "confidence": 0.82,
                "risk": 0.25,
                "rationale": "Conversion is low.",
            },
        ],
        "negotiation_result": {
            "target": "PROD-DEMO-001",
            "agreement_reached": True,
            "final_operation": "DECREASE",
            "final_value": 7.91,
            "participant_agents": [
                "PricingAgent",
                "MarketingAgent",
            ],
            "rounds_completed": 1,
        },
        "mocra_result": {
            "winning_score": 0.763,
            "winning_decision": {
                "agent_id": "MarketingAgent",
            },
            "ranking": [
                {
                    "decision": {
                        "agent_id": "MarketingAgent",
                        "confidence": 0.82,
                        "risk": 0.25,
                        "business_action": {
                            "operation": "DECREASE",
                            "action_type": "PRICE_CHANGE",
                            "priority": 7,
                        },
                    },
                    "score_details": {"final_score": 0.763},
                },
                {
                    "decision": {
                        "agent_id": "InventoryAgent",
                        "confidence": 0.70,
                        "risk": 0.05,
                        "business_action": {
                            "operation": "MAINTAIN_STOCK",
                            "action_type": "INVENTORY_POLICY",
                            "priority": 5,
                        },
                    },
                    "score_details": {"final_score": 0.715},
                },
                {
                    "decision": {
                        "agent_id": "PricingAgent",
                        "confidence": 0.65,
                        "risk": 0.10,
                        "business_action": {
                            "operation": "MAINTAIN",
                            "action_type": "PRICE_CHANGE",
                            "priority": 5,
                        },
                    },
                    "score_details": {"final_score": 0.680},
                },
            ],
        },
        "final_decision": {
            "decision_type": "NEGOTIATED",
            "result": {
                "target": "PROD-DEMO-001",
                "agreement_reached": True,
                "final_operation": "DECREASE",
                "final_value": 7.91,
                "participant_agents": [
                    "PricingAgent",
                    "MarketingAgent",
                ],
                "rounds_completed": 1,
            },
            "coordinated_actions": [
                {
                    "agent_id": "PricingAgent",
                    "business_action": {
                        "action_type": "PRICE_CHANGE",
                        "operation": "MAINTAIN",
                        "value": 0,
                        "unit": "PERCENT",
                    },
                },
                {
                    "agent_id": "InventoryAgent",
                    "business_action": {
                        "action_type": "INVENTORY_POLICY",
                        "operation": "MAINTAIN_STOCK",
                        "value": 0,
                        "unit": "UNITS",
                    },
                },
                {
                    "agent_id": "MarketingAgent",
                    "business_action": {
                        "action_type": "PRICE_CHANGE",
                        "operation": "DECREASE",
                        "value": 15,
                        "unit": "PERCENT",
                    },
                },
            ],
        },
    }


def run_tests() -> None:
    names = preset_names()
    assert "Festival sale" in names
    assert "Low conversion" in names
    assert "Competitor price war" in names
    assert len(names) >= 8

    festival = get_preset("Festival sale")
    assert festival.season == "FESTIVAL"
    assert festival.inventory > 0

    payload = sample_payload()
    profiles = build_agent_profiles(payload)
    assert len(profiles) == 3

    marketing = next(
        item
        for item in profiles
        if item.agent_id == "MarketingAgent"
    )
    assert marketing.mocra_rank == 1
    assert marketing.status == "Primary recommendation"
    assert marketing.confidence == 82.0

    inventory = next(
        item
        for item in profiles
        if item.agent_id == "InventoryAgent"
    )
    assert inventory.latest_operation == "MAINTAIN_STOCK"

    plan = build_final_plan(payload)
    assert plan.rounded_price == 920.0

    print("ACOS UI Phase 3A tests passed.")


if __name__ == "__main__":
    run_tests()
