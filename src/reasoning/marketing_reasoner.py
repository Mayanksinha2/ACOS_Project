from models.business_action import BusinessAction
from reasoning.base_reasoner import BaseReasoner
from reasoning.scenario_analysis import (
    advertising_cost,
    clamp,
    conversion_rate,
    product_id,
    round_step,
    sales_volume,
    season,
    visitors_count,
)


class MarketingReasoner(BaseReasoner):
    """Scenario-sensitive conversion and marketing reasoner."""

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

        conversion = conversion_rate(self.business_state)
        ad_cost = advertising_cost(self.business_state)
        visitors = visitors_count(self.business_state)
        sales = sales_volume(self.business_state)
        current_season = season(self.business_state)
        target = product_id(self.business_state)
        cost_per_sale = ad_cost / max(sales, 1.0)

        observations = [
            f"Visitors are {visitors:,.0f}.",
            f"Sales are {sales:,.0f}.",
            f"Conversion is {conversion * 100:.2f}%.",
            f"Advertising cost is ₹{ad_cost:,.2f}.",
            f"Advertising cost per sale is ₹{cost_per_sale:,.2f}.",
            f"Season is {current_season}.",
        ]

        if conversion < 0.04:
            severity = clamp(
                (0.04 - conversion) / 0.04,
                0.0,
                1.0,
            )
            seasonal_boost = (
                0.03
                if current_season in {"SALE", "FESTIVAL"}
                else 0.0
            )
            value = round_step(
                clamp(10.0 + 20.0 * severity, 10.0, 20.0),
                1.0,
            )
            confidence = clamp(
                0.74 + 0.32 * severity + seasonal_boost,
                0.62,
                0.96,
            )
            risk = clamp(
                0.15 + 0.40 * severity,
                0.15,
                0.45,
            )
            priority = int(
                round(clamp(6.0 + 4.0 * severity, 6.0, 9.0))
            )
            operation = "DECREASE"
            action_type = "PRICE_CHANGE"
            rationale = (
                "Conversion is below the acceptable threshold; a scenario-scaled "
                "discount is recommended to reduce purchase hesitation."
            )
            reasoning = [
                "Traffic is being converted into too few purchases.",
                "Discount magnitude increases as conversion weakness becomes more severe.",
                "SALE or FESTIVAL conditions slightly strengthen confidence.",
            ]
            metadata = {
                "campaign_type": "CONVERSION_DISCOUNT",
                "advertising_cost": ad_cost,
            }

        elif conversion > 0.10:
            strength = clamp(
                (conversion - 0.10) / 0.10,
                0.0,
                1.0,
            )
            value = 0.0
            confidence = clamp(
                0.70 + 0.20 * strength,
                0.70,
                0.90,
            )
            risk = clamp(
                0.06 + 0.08 * (1.0 - strength),
                0.05,
                0.15,
            )
            priority = int(
                round(clamp(4.0 + 2.0 * strength, 4.0, 6.0))
            )
            operation = "MAINTAIN_CAMPAIGN"
            action_type = "MARKETING_POLICY"
            rationale = (
                "Conversion is healthy; maintaining the existing campaign "
                "avoids unnecessary spending or discounting."
            )
            reasoning = [
                "Conversion exceeds the healthy-conversion threshold.",
                "No evidence justifies an aggressive promotional change.",
                "The campaign can continue while performance is monitored.",
            ]
            metadata = {}

        else:
            promotion_gap = clamp(
                (0.10 - conversion) / 0.06,
                0.0,
                1.0,
            )
            seasonal_boost = (
                0.10
                if current_season in {"SALE", "FESTIVAL"}
                else 0.0
            )
            value = round_step(
                clamp(
                    5.0 + 15.0 * promotion_gap
                    + 5.0 * seasonal_boost,
                    5.0,
                    20.0,
                ),
                1.0,
            )
            confidence = clamp(
                0.60 + 0.22 * promotion_gap + seasonal_boost,
                0.58,
                0.88,
            )
            risk = clamp(
                0.10
                + 0.14 * promotion_gap
                + (
                    0.05
                    if cost_per_sale > 100.0
                    else 0.0
                ),
                0.08,
                0.32,
            )
            priority = int(
                round(
                    clamp(
                        5.0 + 2.0 * promotion_gap
                        + seasonal_boost * 10.0,
                        5.0,
                        8.0,
                    )
                )
            )
            operation = "INCREASE_PROMOTION"
            action_type = "MARKETING_POLICY"
            rationale = (
                "Conversion is moderate; promotional visibility should be "
                "increased by an amount scaled to the conversion gap."
            )
            reasoning = [
                "Conversion is not critically low but remains below the healthy threshold.",
                "Promotion magnitude is scaled by the gap to healthy conversion.",
                "Advertising efficiency and seasonal context affect risk and priority.",
            ]
            metadata = {}

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
                    "conversion_rate": conversion,
                    "visitors": visitors,
                    "sales": sales,
                    "advertising_cost": ad_cost,
                    "cost_per_sale": cost_per_sale,
                    "season": current_season,
                },
                "dynamic_scoring": True,
            }
        )

        self.action = BusinessAction(
            agent_id="MarketingAgent",
            action_type=action_type,
            operation=operation,
            target=target,
            value=value,
            unit="PERCENT",
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
