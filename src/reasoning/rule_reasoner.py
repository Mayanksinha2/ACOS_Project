from models.business_action import BusinessAction
from reasoning.base_reasoner import BaseReasoner


class RuleReasoner(BaseReasoner):

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

        inventory = self.business_state.metrics.get(
            "inventory",
            100
        )

        demand = self.business_state.market.get(
            "adjusted_demand",
            self.business_state.market.get("demand", 50),
        )

        product_id = self.business_state.metrics.get(
            "product_id",
            "UNKNOWN_PRODUCT"
        )

        if inventory < 20 and demand > 70:

            self.action = BusinessAction(
                agent_id="PricingAgent",
                action_type="PRICE_CHANGE",
                operation="INCREASE",
                target=product_id,
                value=10,
                unit="PERCENT",
                rationale="High demand and low inventory",
                confidence=0.85,
                risk=0.20,
                priority=8
            )

        elif inventory > 100 and demand < 40:

            self.action = BusinessAction(
                agent_id="PricingAgent",
                action_type="PRICE_CHANGE",
                operation="DECREASE",
                target=product_id,
                value=10,
                unit="PERCENT",
                rationale="Low demand and high inventory",
                confidence=0.80,
                risk=0.25,
                priority=7
            )

        else:

            self.action = BusinessAction(
                agent_id="PricingAgent",
                action_type="PRICE_CHANGE",
                operation="MAINTAIN",
                target=product_id,
                value=0,
                unit="PERCENT",
                rationale="Current market conditions do not require a price change",
                confidence=0.65,
                risk=0.10,
                priority=5
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