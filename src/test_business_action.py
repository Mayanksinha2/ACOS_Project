from models.business_action import BusinessAction


action = BusinessAction(
    agent_id="PricingAgent",
    action_type="PRICE_CHANGE",
    operation="INCREASE",
    target="SKU-101",
    value=10,
    unit="PERCENT",
    rationale="High demand and low inventory",
    confidence=0.85,
    risk=0.20,
    priority=8
)

assert action.action_type == "PRICE_CHANGE"
assert action.operation == "INCREASE"
assert action.target == "SKU-101"
assert action.value == 10
assert action.confidence == 0.85

print("BusinessAction test passed.")