from models.business_action import BusinessAction
from models.commerce_decision import CommerceDecision
from negotiation.conflict_detector import ConflictDetector


increase_action = BusinessAction(
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


decrease_action = BusinessAction(
    agent_id="MarketingAgent",
    action_type="PRICE_CHANGE",
    operation="DECREASE",
    target="SKU-101",
    value=15,
    unit="PERCENT",
    rationale="Discount required to improve conversion",
    confidence=0.82,
    risk=0.25,
    priority=7
)


increase_decision = CommerceDecision(
    agent_id="PricingAgent",
    goal="Maximize Profit",
    business_action=increase_action,
    confidence=increase_action.confidence,
    risk=increase_action.risk
)


decrease_decision = CommerceDecision(
    agent_id="MarketingAgent",
    goal="Increase Conversion",
    business_action=decrease_action,
    confidence=decrease_action.confidence,
    risk=decrease_action.risk
)


detector = ConflictDetector()

result = detector.compare(
    increase_decision,
    decrease_decision
)


print("Conflict Type:", result.conflict_type)
print("Reason:", result.reason)
print("Severity:", result.severity)
print(
    "Requires Negotiation:",
    result.requires_negotiation
)


assert result.conflict_type == "HARD_CONFLICT"
assert result.severity == 1.0
assert result.requires_negotiation is True

print("Hard conflict test passed.")