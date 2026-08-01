from agents.inventory_agent import InventoryAgent
from models.business_state import BusinessState
from reasoning.inventory_reasoner import InventoryReasoner


state = BusinessState(
    market={
        "demand": 80
    },
    metrics={
        "inventory": 15,
        "product_id": "SKU-101"
    }
)


reasoner = InventoryReasoner()
agent = InventoryAgent(reasoner)

agent.observe(state)
agent.analyze()

decision = agent.generate_decision()


print("Proposal ID:", decision.proposal_id)
print("Agent:", decision.agent_id)
print("Goal:", decision.goal)

print(
    "Action Type:",
    decision.business_action.action_type
)

print(
    "Operation:",
    decision.business_action.operation
)

print(
    "Target:",
    decision.business_action.target
)

print(
    "Recommended Price Operation:",
    decision.business_action.metadata[
        "recommended_price_operation"
    ]
)

print("Confidence:", decision.confidence)
print("Risk:", decision.risk)
print("Expected Benefit:", decision.expected_benefit)


assert decision.agent_id == "InventoryAgent"
assert decision.business_action.operation == "PROTECT_STOCK"
assert decision.business_action.target == "SKU-101"

assert (
    decision.business_action.metadata[
        "recommended_price_operation"
    ]
    == "INCREASE"
)

print("Inventory Agent test passed.")