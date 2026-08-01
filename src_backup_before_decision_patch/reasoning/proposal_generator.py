from typing import Optional

from models.commerce_decision import CommerceDecision


class ProposalGenerator:

    @staticmethod
    def generate(
        agent_name,
        reasoner,
        goal: Optional[str] = None
    ):

        action = reasoner.generate_actions()

        selected_goal = goal or "Maximize Business Utility"

        expected_benefit = {}

        if action.agent_id == "PricingAgent":

            if action.operation == "INCREASE":
                expected_benefit = {
                    "profit": 0.10,
                    "inventory_health": 0.05
                }

            elif action.operation == "DECREASE":
                expected_benefit = {
                    "conversion": 0.10,
                    "inventory_health": 0.10
                }

            else:
                expected_benefit = {
                    "profit": 0.02
                }

        elif action.agent_id == "InventoryAgent":

            if action.operation == "PROTECT_STOCK":
                expected_benefit = {
                    "inventory_health": 0.20,
                    "stockout_reduction": 0.15
                }

            elif action.operation == "CLEAR_STOCK":
                expected_benefit = {
                    "inventory_health": 0.20,
                    "holding_cost_reduction": 0.15
                }

            else:
                expected_benefit = {
                    "inventory_health": 0.05
                }

        elif action.agent_id == "MarketingAgent":

            if action.operation == "DECREASE":
                expected_benefit = {
                    "conversion": 0.15,
                    "traffic": 0.10,
                    "profit": -0.05
                }

            elif action.operation == "INCREASE_PROMOTION":
                expected_benefit = {
                    "conversion": 0.08,
                    "traffic": 0.12
                }

            else:
                expected_benefit = {
                    "conversion": 0.03
                }

        return CommerceDecision(
            agent_id=agent_name,
            goal=selected_goal,
            business_action=action,
            confidence=action.confidence,
            risk=action.risk,
            evidence=[
                action.rationale,
                f"Generated using {reasoner.__class__.__name__}"
            ],
            expected_benefit=expected_benefit
        )