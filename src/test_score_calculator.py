from models.business_action import BusinessAction
from models.commerce_decision import CommerceDecision
from negotiation.score_calculator import ScoreCalculator


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


decision = CommerceDecision(
    agent_id="PricingAgent",
    goal="Maximize Profit",
    business_action=action,
    confidence=0.85,
    risk=0.20
)


calculator = ScoreCalculator()

result = calculator.calculate(decision)


print("Confidence Score:", result["confidence_score"])
print("Risk Score:", result["risk_score"])
print("Priority Score:", result["priority_score"])
print("Final Score:", result["final_score"])


assert result["confidence_score"] == 0.85
assert result["risk_score"] == 0.8
assert result["priority_score"] == 0.8
assert result["final_score"] == 0.82

print("Score Calculator test passed.")