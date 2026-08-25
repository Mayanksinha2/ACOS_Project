from typing import Optional

from models.commerce_decision import CommerceDecision


class ProposalGenerator:
    @staticmethod
    def generate(
        agent_name,
        reasoner,
        goal: Optional[str] = None,
    ):
        action = reasoner.generate_actions()
        selected_goal = goal or "Maximize Business Utility"

        expected_benefit = ProposalGenerator._expected_benefit(
            action
        )

        metadata = (
            action.metadata
            if isinstance(action.metadata, dict)
            else {}
        )
        evidence = list(metadata.get("evidence") or [])

        if not evidence:
            evidence = [action.rationale]

        context = {
            "observations": list(
                metadata.get("observations") or []
            ),
            "reasoning": list(
                metadata.get("reasoning") or []
            ),
            "score_inputs": dict(
                metadata.get("score_inputs") or {}
            ),
            "dynamic_scoring": bool(
                metadata.get("dynamic_scoring", False)
            ),
        }

        return CommerceDecision(
            agent_id=agent_name,
            goal=selected_goal,
            business_action=action,
            confidence=action.confidence,
            risk=action.risk,
            evidence=evidence,
            context=context,
            expected_benefit=expected_benefit,
        )

    @staticmethod
    def _expected_benefit(action):
        if action.agent_id == "PricingAgent":
            if action.operation == "INCREASE":
                magnitude = float(action.value or 0.0) / 100.0
                return {
                    "profit": round(magnitude, 4),
                    "inventory_health": round(
                        magnitude * 0.5,
                        4,
                    ),
                }
            if action.operation == "DECREASE":
                magnitude = float(action.value or 0.0) / 100.0
                return {
                    "conversion": round(
                        min(0.25, magnitude * 1.2),
                        4,
                    ),
                    "inventory_health": round(
                        min(0.20, magnitude),
                        4,
                    ),
                    "profit": round(
                        -magnitude * 0.4,
                        4,
                    ),
                }
            return {"profit": 0.02}

        if action.agent_id == "InventoryAgent":
            if action.operation == "PROTECT_STOCK":
                return {
                    "inventory_health": 0.20,
                    "stockout_reduction": 0.15,
                }
            if action.operation == "CLEAR_STOCK":
                magnitude = float(action.value or 0.0) / 100.0
                return {
                    "inventory_health": round(
                        min(0.30, 0.12 + magnitude * 0.5),
                        4,
                    ),
                    "holding_cost_reduction": round(
                        min(0.25, 0.08 + magnitude * 0.4),
                        4,
                    ),
                }
            return {"inventory_health": 0.05}

        if action.agent_id == "MarketingAgent":
            magnitude = float(action.value or 0.0) / 100.0
            if action.operation == "DECREASE":
                return {
                    "conversion": round(
                        min(0.30, magnitude * 1.2),
                        4,
                    ),
                    "traffic": round(
                        min(0.20, magnitude * 0.7),
                        4,
                    ),
                    "profit": round(
                        -magnitude * 0.35,
                        4,
                    ),
                }
            if action.operation == "INCREASE_PROMOTION":
                return {
                    "conversion": round(
                        min(0.20, magnitude * 0.8),
                        4,
                    ),
                    "traffic": round(
                        min(0.30, magnitude * 1.1),
                        4,
                    ),
                }
            return {"conversion": 0.03}

        return {}
