from models.business_action import BusinessAction
from reasoning.base_reasoner import BaseReasoner
from reasoning.scenario_analysis import (
    adjusted_demand,
    clamp,
    competitor_factor,
    conversion_rate,
    current_price,
    inventory_level,
    product_id,
    profit_margin,
    round_step,
)


class RuleReasoner(BaseReasoner):
    """
    Scenario-sensitive pricing reasoner.

    Operation, magnitude, confidence, risk, priority and evidence are
    calculated from the actual business state instead of fixed branch values.
    """

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
        conversion = conversion_rate(self.business_state)
        factor = competitor_factor(self.business_state)
        price = current_price(self.business_state)
        margin = profit_margin(self.business_state)
        target = product_id(self.business_state)

        shortage_threshold = max(20.0, demand * 0.30)
        excess_threshold = max(100.0, demand * 1.80)

        observations = [
            f"Current price is ₹{price:,.2f}.",
            f"Adjusted demand is {demand:.1f}/100.",
            f"Inventory is {inventory:.0f} units.",
            f"Conversion is {conversion * 100:.2f}%.",
            f"Competitor price factor is {factor:.2f}.",
            f"Observed profit margin is {margin * 100:.1f}%.",
        ]

        if inventory < shortage_threshold and demand > 70:
            shortage_severity = clamp(
                (shortage_threshold - inventory)
                / max(shortage_threshold, 1.0),
                0.0,
                1.0,
            )
            demand_severity = clamp(
                (demand - 70.0) / 30.0,
                0.0,
                1.0,
            )
            severity = (
                0.55 * shortage_severity
                + 0.45 * demand_severity
            )

            value = round_step(
                clamp(5.0 + 10.0 * severity, 5.0, 15.0),
                1.0,
            )
            confidence = clamp(
                0.76 + 0.14 * severity
                + (0.03 if factor >= 1.0 else -0.03),
                0.60,
                0.95,
            )
            risk = clamp(
                0.12
                + 0.16 * (1.0 - severity)
                + (0.08 if conversion < 0.03 else 0.0),
                0.08,
                0.40,
            )
            priority = int(
                round(clamp(7.0 + 2.0 * severity, 7.0, 9.0))
            )
            operation = "INCREASE"
            rationale = (
                "High demand and constrained inventory support a controlled "
                "price increase to protect availability and margin."
            )
            reasoning = [
                "Demand exceeds the high-demand threshold.",
                "Inventory is below the demand-sensitive shortage threshold.",
                "The increase magnitude is scaled by shortage and demand severity.",
            ]

        elif inventory > excess_threshold and demand < 50:
            excess_severity = clamp(
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
            competitor_pressure = clamp(
                (1.0 - factor) / 0.30,
                0.0,
                1.0,
            )
            severity = (
                0.45 * excess_severity
                + 0.35 * weak_demand
                + 0.20 * competitor_pressure
            )

            value = round_step(
                clamp(5.0 + 15.0 * severity, 5.0, 20.0),
                1.0,
            )
            confidence = clamp(
                0.68 + 0.24 * severity,
                0.60,
                0.94,
            )
            risk = clamp(
                0.16
                + 0.14 * severity
                + (0.08 if margin < 0.10 else 0.0),
                0.10,
                0.45,
            )
            priority = int(
                round(clamp(6.0 + 3.0 * severity, 6.0, 9.0))
            )
            operation = "DECREASE"
            rationale = (
                "Excess inventory and weak demand support a calibrated "
                "price reduction to improve sell-through."
            )
            reasoning = [
                "Inventory exceeds the demand-sensitive excess threshold.",
                "Demand is below the neutral-demand threshold.",
                "The discount is scaled by overstock, demand weakness and competitor pressure.",
            ]

        else:
            demand_stability = 1.0 - clamp(
                abs(demand - 55.0) / 55.0,
                0.0,
                1.0,
            )
            competitor_stability = 1.0 - clamp(
                abs(factor - 1.0) / 0.30,
                0.0,
                1.0,
            )
            inventory_balance = 1.0 - clamp(
                abs(inventory - max(demand, 1.0))
                / max(inventory, demand, 1.0),
                0.0,
                1.0,
            )
            stability = (
                0.35 * demand_stability
                + 0.35 * competitor_stability
                + 0.30 * inventory_balance
            )

            value = 0.0
            confidence = clamp(
                0.52 + 0.30 * stability,
                0.52,
                0.82,
            )
            risk = clamp(
                0.07
                + 0.15 * (1.0 - stability)
                + (0.05 if conversion < 0.025 else 0.0),
                0.05,
                0.30,
            )
            priority = int(
                round(clamp(4.0 + 2.0 * stability, 4.0, 6.0))
            )
            operation = "MAINTAIN"
            rationale = (
                "The combined demand, inventory, competitor and margin signals "
                "do not justify an independent price change."
            )
            reasoning = [
                "No severe shortage or overstock condition was detected.",
                "Competitor pricing is not strong enough to force a direct move.",
                "Maintaining price avoids unnecessary margin or conversion risk.",
            ]

        evidence = [
            *observations,
            *reasoning,
            f"Calculated confidence: {confidence:.3f}.",
            f"Calculated risk: {risk:.3f}.",
            f"Calculated priority: {priority}/10.",
        ]

        self.action = BusinessAction(
            agent_id="PricingAgent",
            action_type="PRICE_CHANGE",
            operation=operation,
            target=target,
            value=value,
            unit="PERCENT",
            rationale=rationale,
            confidence=round(confidence, 4),
            risk=round(risk, 4),
            priority=priority,
            metadata={
                "evidence": evidence,
                "observations": observations,
                "reasoning": reasoning,
                "score_inputs": {
                    "adjusted_demand": demand,
                    "inventory": inventory,
                    "conversion_rate": conversion,
                    "competitor_price_factor": factor,
                    "profit_margin": margin,
                },
                "dynamic_scoring": True,
            },
        )
        return self.action

    def estimate_confidence(self):
        return 0.0 if self.action is None else self.action.confidence

    def estimate_risk(self):
        return 0.0 if self.action is None else self.action.risk
