from models.business_action import BusinessAction
from reasoning.base_reasoner import BaseReasoner


class InventoryReasoner(BaseReasoner):
    """
    Rule-based reasoning strategy for inventory optimization.
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

        inventory = self.business_state.metrics.get(
            "inventory",
            100
        )

        demand = self.business_state.market.get(
            "demand",
            50
        )

        product_id = self.business_state.metrics.get(
            "product_id",
            "UNKNOWN_PRODUCT"
        )

        if inventory < 20:

            self.action = BusinessAction(
                agent_id="InventoryAgent",
                action_type="INVENTORY_POLICY",
                operation="PROTECT_STOCK",
                target=product_id,
                value=0,
                unit="UNITS",
                rationale=(
                    "Inventory is critically low; stock should be "
                    "protected from rapid depletion"
                ),
                confidence=0.90,
                risk=0.10,
                priority=9,
                metadata={
                          "recommended_price_operation": "INCREASE",
                          "recommended_price_value": 5
                     }  
            )

        elif inventory > 100 and demand < 40:

            self.action = BusinessAction(
                agent_id="InventoryAgent",
                action_type="INVENTORY_POLICY",
                operation="CLEAR_STOCK",
                target=product_id,
                value=20,
                unit="PERCENT",
                rationale=(
                    "Inventory is high while demand is low; "
                    "stock clearance is recommended"
                ),
                confidence=0.88,
                risk=0.15,
                priority=8,
                metadata={
                          "recommended_price_operation": "MAINTAIN",
                          "recommended_price_value": 0
                        }
            )

        else:

            self.action = BusinessAction(
                agent_id="InventoryAgent",
                action_type="INVENTORY_POLICY",
                operation="MAINTAIN_STOCK",
                target=product_id,
                value=0,
                unit="UNITS",
                rationale=(
                    "Inventory and demand are within acceptable levels"
                ),
                confidence=0.70,
                risk=0.05,
                priority=5,
                metadata={
                    "recommended_price_operation": "MAINTAIN"
                }
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