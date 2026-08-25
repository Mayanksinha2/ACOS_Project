from __future__ import annotations

from acos_ui.presentation import (
    actual_conflicts,
    build_final_plan,
    mocra_ranking,
)


def sample_payload() -> dict:
    return {
        "run_id": "RUN-001",
        "status": "COMPLETED",
        "successful": True,
        "scenario": {
            "product_id": "PROD-DEMO-001",
            "current_price": 999.0,
            "inventory": 30,
            "demand": 30.0,
            "visitors": 1200,
            "sales": 45,
            "revenue": 42980.0,
            "profit": 7500.0,
            "season": "SALE",
        },
        "calculated_metrics": {
            "current_price": 999.0,
            "conversion_rate": 0.0375,
            "adjusted_demand": 45.0,
        },
        "proposals": [
            {
                "agent": "PricingAgent",
                "operation": "MAINTAIN",
                "action_type": "PRICE_CHANGE",
                "value": 0,
                "unit": "PERCENT",
                "confidence": 0.65,
                "risk": 0.10,
            },
            {
                "agent": "InventoryAgent",
                "operation": "MAINTAIN_STOCK",
                "action_type": "INVENTORY_POLICY",
                "value": 0,
                "unit": "UNITS",
                "confidence": 0.70,
                "risk": 0.05,
            },
            {
                "agent": "MarketingAgent",
                "operation": "DECREASE",
                "action_type": "PRICE_CHANGE",
                "value": 15,
                "unit": "PERCENT",
                "confidence": 0.82,
                "risk": 0.25,
            },
        ],
        "conflicts": [
            {"conflict_type": "HARD_CONFLICT"},
            {"conflict_type": "SUPPORTING"},
        ],
        "negotiation_result": {
            "target": "PROD-DEMO-001",
            "agreement_reached": True,
            "final_operation": "DECREASE",
            "final_value": 7.91,
            "unit": "PERCENT",
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
                    "score_details": {
                        "final_score": 0.763,
                    },
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
                    "score_details": {
                        "final_score": 0.715,
                    },
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
                "unit": "PERCENT",
                "participant_agents": [
                    "PricingAgent",
                    "MarketingAgent",
                ],
                "rounds_completed": 1,
                "negotiation_id": "NEG-001",
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
    payload = sample_payload()

    plan = build_final_plan(payload)
    assert plan.price_operation == "DECREASE"
    assert round(plan.price_change_percent, 2) == 7.91
    assert round(plan.recommended_price or 0, 2) == 919.98
    assert plan.rounded_price == 920.0
    assert plan.inventory_operation == "MAINTAIN_STOCK"
    assert plan.marketing_operation == "DECREASE"
    assert plan.winning_agent == "MarketingAgent"
    assert plan.winning_score == 0.763
    assert plan.participants == (
        "PricingAgent",
        "MarketingAgent",
    )

    assert len(actual_conflicts(payload["conflicts"])) == 1

    ranking = mocra_ranking(payload)
    assert ranking[0]["agent"] == "MarketingAgent"
    assert ranking[0]["score"] == 0.763
    assert ranking[1]["agent"] == "InventoryAgent"

    print("ACOS UI Phase 2 presentation tests passed.")


if __name__ == "__main__":
    run_tests()
