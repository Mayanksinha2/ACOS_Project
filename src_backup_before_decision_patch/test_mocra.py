from models.business_action import BusinessAction
from models.commerce_decision import CommerceDecision
from negotiation.mocra import MOCRA


pricing_action = BusinessAction(
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


marketing_action = BusinessAction(
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


inventory_action = BusinessAction(
    agent_id="InventoryAgent",
    action_type="INVENTORY_POLICY",
    operation="PROTECT_STOCK",
    target="SKU-101",
    value=0,
    unit="UNITS",
    rationale="Inventory is critically low",
    confidence=0.90,
    risk=0.10,
    priority=9,
    metadata={
        "recommended_price_operation": "INCREASE"
    }
)


pricing_decision = CommerceDecision(
    agent_id="PricingAgent",
    goal="Maximize Profit",
    business_action=pricing_action,
    confidence=pricing_action.confidence,
    risk=pricing_action.risk
)


marketing_decision = CommerceDecision(
    agent_id="MarketingAgent",
    goal="Increase Conversion",
    business_action=marketing_action,
    confidence=marketing_action.confidence,
    risk=marketing_action.risk
)


inventory_decision = CommerceDecision(
    agent_id="InventoryAgent",
    goal="Protect Inventory",
    business_action=inventory_action,
    confidence=inventory_action.confidence,
    risk=inventory_action.risk
)


mocra = MOCRA()

result = mocra.resolve([
    pricing_decision,
    marketing_decision,
    inventory_decision
])


print("Winning Agent:", result.winning_decision.agent_id)
print("Winning Score:", result.winning_score)

print("\nRanking:")

for position, entry in enumerate(
    result.ranking,
    start=1
):
    print(
        position,
        entry["decision"].agent_id,
        entry["score_details"]["final_score"]
    )


print("\nExplanation:")

for line in result.explanation:
    print("-", line)


print("\nStatuses:")

print(
    pricing_decision.agent_id,
    pricing_decision.negotiation_status
)

print(
    marketing_decision.agent_id,
    marketing_decision.negotiation_status
)

print(
    inventory_decision.agent_id,
    inventory_decision.negotiation_status
)


assert result.winning_decision.agent_id == "InventoryAgent"
assert result.winning_score == 0.9
assert inventory_decision.negotiation_status == "SELECTED"
assert pricing_decision.negotiation_status == "REJECTED"
assert marketing_decision.negotiation_status == "REJECTED"
assert len(result.ranking) == 3
assert len(result.rejected_decisions) == 2

print("\nMOCRA test passed.")