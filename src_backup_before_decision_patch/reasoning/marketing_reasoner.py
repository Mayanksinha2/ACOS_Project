from models.business_action import BusinessAction
from reasoning.base_reasoner import BaseReasoner


class MarketingReasoner(BaseReasoner):
    """
    Rule-based reasoning strategy for marketing optimization.
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

        conversion_rate = self.business_state.metrics.get(
            "conversion_rate",
            0.05
        )

        advertising_cost = self.business_state.market.get(
            "advertising_cost",
            100
        )

        product_id = self.business_state.metrics.get(
            "product_id",
            "UNKNOWN_PRODUCT"
        )

        if conversion_rate < 0.04:

            self.action = BusinessAction(
                agent_id="MarketingAgent",
                action_type="PRICE_CHANGE",
                operation="DECREASE",
                target=product_id,
                value=15,
                unit="PERCENT",
                rationale=(
                    "Conversion rate is low; a discount is "
                    "recommended to improve customer purchases"
                ),
                confidence=0.82,
                risk=0.25,
                priority=7,
                metadata={
                    "campaign_type": "CONVERSION_DISCOUNT",
                    "advertising_cost": advertising_cost
                }
            )

        elif conversion_rate > 0.10:

            self.action = BusinessAction(
                agent_id="MarketingAgent",
                action_type="MARKETING_POLICY",
                operation="MAINTAIN_CAMPAIGN",
                target=product_id,
                value=0,
                unit="PERCENT",
                rationale=(
                    "Conversion rate is healthy; current "
                    "campaign strategy should be maintained"
                ),
                confidence=0.75,
                risk=0.10,
                priority=5
            )

        else:

            self.action = BusinessAction(
                agent_id="MarketingAgent",
                action_type="MARKETING_POLICY",
                operation="INCREASE_PROMOTION",
                target=product_id,
                value=10,
                unit="PERCENT",
                rationale=(
                    "Conversion rate is moderate; promotional "
                    "visibility should be increased"
                ),
                confidence=0.72,
                risk=0.15,
                priority=6
            )

        return self.action

    def estimate_confidence(self):
        if self.action is None:
            return 0.0

        return self.action.confidence

    def estimate_risk(self):
        if self.action is None:
            return 0.0

        return self.action.risk