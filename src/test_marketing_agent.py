from agents.marketing_agent import MarketingAgent
from models.business_state import BusinessState
from reasoning.marketing_reasoner import MarketingReasoner


state = BusinessState(
    market={
        "demand": 80,
        "advertising_cost": 120
    },
    metrics={
        "inventory": 15,
        "conversion_rate": 0.03,
        "product_id": "SKU-101"
    }
)


reasoner = MarketingReasoner()
agent = MarketingAgent(reasoner)

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
    "Value:",
    decision.business_action.value,
    decision.business_action.unit
)

print("Confidence:", decision.confidence)
print("Risk:", decision.risk)
print("Expected Benefit:", decision.expected_benefit)


assert decision.agent_id == "MarketingAgent"
assert decision.business_action.operation == "DECREASE"
assert decision.business_action.target == "SKU-101"
assert decision.expected_benefit["conversion"] == 0.15

print("Marketing Agent test passed.")