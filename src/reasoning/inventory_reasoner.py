from models.business_action import BusinessAction
from reasoning.base_reasoner import BaseReasoner
from reasoning.scenario_analysis import (
    adjusted_demand,
    clamp,
    inventory_level,
    product_id,
    round_step,
    sales_volume,
)


class InventoryReasoner(BaseReasoner):
    """Scenario-sensitive inventory optimization reasoner."""

    def __init__(self):
        self.business_state = None
        self.action = None

    def analyze(self, business_state):
        self.business_state = business_state
        return self.business_state

    def generate_actions(self):
        if self.business_state is None:
            raise RuntimeError(
                "Business state is missing. Call analyze() first."
            )

        inventory = inventory_level(self.business_state)
        demand = adjusted_demand(self.business_state)
        sales = sales_volume(self.business_state)
        target = product_id(self.business_state)

        shortage_threshold = max(20.0, demand * 0.30)
        excess_threshold = max(100.0, demand * 1.80)
        coverage = inventory / max(demand, 1.0)
        sales_coverage = inventory / max(sales, 1.0)

        observations = [
            f"Inventory is {inventory:.0f} units.",
            f"Adjusted demand is {demand:.1f}/100.",
            f"Observed sales are {sales:.0f} units.",
            f"Inventory-to-demand ratio is {coverage:.2f}.",
            f"Inventory-to-sales ratio is {sales_coverage:.2f}.",
        ]

        if inventory < shortage_threshold:
            severity = clamp(
                (shortage_threshold - inventory)
                / max(shortage_threshold, 1.0),
                0.0,
                1.0,
            )
            confidence = clamp(
                0.82 + 0.16 * severity,
                0.75,
                0.98,
            )
            risk = clamp(
                0.06 + 0.12 * (1.0 - severity),
                0.05,
                0.20,
            )
            priority = int(
                round(clamp(8.0 + severity, 8.0, 9.0))
            )
            price_support = round_step(
                clamp(3.0 + 5.0 * severity, 3.0, 8.0),
                1.0,
            )
            operation = "PROTECT_STOCK"
            value = 0.0
            unit = "UNITS"
            rationale = (
                "Inventory is low relative to demand; stock protection "
                "is required to reduce depletion and stock-out risk."
            )
            reasoning = [
                "Inventory is below the demand-sensitive shortage threshold.",
                "The confidence level increases with shortage severity.",
                "A supporting price increase may slow depletion.",
            ]
            metadata = {
                "recommended_price_operation": "INCREASE",
                "recommended_price_value": price_support,
            }

        elif inventory > excess_threshold and demand < 50:
            excess = clamp(
                (inventory - excess_threshold)
                / max(excess_threshold, 1.0),
                0.0,
                1.0,
            )
            weak_demand = clamp(
                (50.0 - demand) / 50.0,
                0.0,
                1.0,
            )
            severity = 0.60 * excess + 0.40 * weak_demand
            confidence = clamp(
                0.74 + 0.22 * severity,
                0.70,
                0.96,
            )
            risk = clamp(
                0.10 + 0.15 * severity,
                0.08,
                0.30,
            )
            priority = int(
                round(clamp(7.0 + 2.0 * severity, 7.0, 9.0))
            )
            value = round_step(
                clamp(10.0 + 20.0 * severity, 10.0, 30.0),
                1.0,
            )
            operation = "CLEAR_STOCK"
            unit = "PERCENT"
            rationale = (
                "Inventory is high relative to demand; controlled stock "
                "clearance is recommended to reduce holding exposure."
            )
            reasoning = [
                "Inventory exceeds the demand-sensitive excess threshold.",
                "Demand is weak enough to increase overstock risk.",
                "Clearance magnitude is scaled by excess-stock severity.",
            ]
            metadata = {
                "recommended_price_operation": "DECREASE",
                "recommended_price_value": round_step(
                    clamp(5.0 + 10.0 * severity, 5.0, 15.0),
                    1.0,
                ),
            }

        else:
            balance = 1.0 - clamp(
                abs(coverage - 1.0),
                0.0,
                1.0,
            )
            confidence = clamp(
                0.58 + 0.25 * balance,
                0.58,
                0.83,
            )
            risk = clamp(
                0.04 + 0.12 * (1.0 - balance),
                0.04,
                0.20,
            )
            priority = int(
                round(clamp(4.0 + 2.0 * balance, 4.0, 6.0))
            )
            operation = "MAINTAIN_STOCK"
            value = 0.0
            unit = "UNITS"
            rationale = (
                "Inventory and demand are sufficiently balanced; no immediate "
                "replenishment or clearance action is required."
            )
            reasoning = [
                "Inventory is above the shortage threshold.",
                "Inventory is below the excess-stock threshold.",
                "Maintaining stock avoids unnecessary holding or shortage cost.",
            ]
            metadata = {
                "recommended_price_operation": "MAINTAIN",
                "recommended_price_value": 0.0,
            }

        evidence = [
            *observations,
            *reasoning,
            f"Calculated confidence: {confidence:.3f}.",
            f"Calculated risk: {risk:.3f}.",
            f"Calculated priority: {priority}/10.",
        ]
        metadata.update(
            {
                "evidence": evidence,
                "observations": observations,
                "reasoning": reasoning,
                "score_inputs": {
                    "adjusted_demand": demand,
                    "inventory": inventory,
                    "sales": sales,
                    "coverage": coverage,
                },
                "dynamic_scoring": True,
            }
        )

        self.action = BusinessAction(
            agent_id="InventoryAgent",
            action_type="INVENTORY_POLICY",
            operation=operation,
            target=target,
            value=value,
            unit=unit,
            rationale=rationale,
            confidence=round(confidence, 4),
            risk=round(risk, 4),
            priority=priority,
            metadata=metadata,
        )
        return self.action

    def estimate_confidence(self):
        return 0.0 if self.action is None else self.action.confidence

    def estimate_risk(self):
        return 0.0 if self.action is None else self.action.risk
