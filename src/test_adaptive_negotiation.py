from agents.inventory_agent import InventoryAgent
from agents.marketing_agent import MarketingAgent
from agents.pricing_agent import PricingAgent
from models.business_state import BusinessState
from negotiation.adaptive_negotiation import (
    AdaptiveNegotiationEngine
)
from reasoning.inventory_reasoner import InventoryReasoner
from reasoning.marketing_reasoner import MarketingReasoner
from reasoning.rule_reasoner import RuleReasoner


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


agents = [
    PricingAgent(
        RuleReasoner()
    ),
    InventoryAgent(
        InventoryReasoner()
    ),
    MarketingAgent(
        MarketingReasoner()
    )
]


decisions = []


for agent in agents:

    agent.observe(state)
    agent.analyze()

    decision = agent.generate_decision()

    decisions.append(decision)

    print(
        agent.agent_name,
        "proposed",
        decision.business_action.operation,
        decision.business_action.value
    )


engine = AdaptiveNegotiationEngine()

result = engine.negotiate(decisions)


print("\nNegotiation Result")

print("Negotiation ID:", result.negotiation_id)
print("Target:", result.target)
print("Agreement:", result.agreement_reached)
print("Final Operation:", result.final_operation)
print("Final Value:", result.final_value)
print("Unit:", result.unit)
print("Participants:", result.participant_agents)
print("Influence Scores:", result.influence_scores)
print("Rounds:", result.rounds_completed)


print("\nExplanation:")

for line in result.explanation:
    print("-", line)


assert result.agreement_reached is True
assert result.target == "SKU-101"
assert len(result.participant_agents) == 3
assert result.rounds_completed == 1

assert result.final_operation in {
    "INCREASE",
    "DECREASE",
    "MAINTAIN"
}

print("\nAdaptive negotiation test passed.")