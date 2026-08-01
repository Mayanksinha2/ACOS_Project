from agents.pricing_agent import PricingAgent
from models.business_state import BusinessState
from reasoning.rule_reasoner import RuleReasoner


state = BusinessState(
    market={
        "demand": 80
    },
    metrics={
        "inventory": 15,
        "product_id": "SKU-101"
    }
)

reasoner = RuleReasoner()
agent = PricingAgent(reasoner)

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
print("Evidence:", decision.evidence)