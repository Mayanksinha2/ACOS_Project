from models.business_action import BusinessAction
from models.commerce_decision import CommerceDecision


action = BusinessAction(
    agent_id="PricingAgent",
    action_type="PRICE_CHANGE",
    operation="INCREASE",
    target="SKU-101",
    value=10,
    unit="PERCENT",
    rationale="High demand and low inventory",
    confidence=0.85,
    risk=0.20
)


decision = CommerceDecision(
    agent_id="PricingAgent",
    goal="Maximize Business Utility",
    business_action=action,
    confidence=action.confidence,
    risk=action.risk
)


assert decision.agent_id == "PricingAgent"
assert decision.business_action.operation == "INCREASE"
assert decision.business_action.target == "SKU-101"

print("CommerceDecision test passed.")