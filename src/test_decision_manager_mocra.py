from agents.inventory_agent import InventoryAgent
from agents.pricing_agent import PricingAgent
from kernel.kernel import ACOSKernel
from models.business_state import BusinessState
from protocols.acnp_message import ACNPMessage
from reasoning.inventory_reasoner import InventoryReasoner
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


kernel = ACOSKernel()


agents = [
    PricingAgent(
        RuleReasoner()
    ),
    InventoryAgent(
        InventoryReasoner()
    )
]


for agent in agents:

    kernel.register_agent(agent)

    agent.observe(state)
    agent.analyze()

    decision = agent.generate_decision()

    message = ACNPMessage(
        sender=agent.agent_name,
        receiver="ACOSKernel",
        message_type="PROPOSAL",
        decision=decision
    )

    kernel.submit_message(message)


conflicts = (
    kernel.decision_manager
    .detect_conflicts()
)


result = (
    kernel.decision_manager
    .resolve_pending_proposals()
)


print("Conflict Count:", len(conflicts))

print(
    "Winning Agent:",
    result.winning_decision.agent_id
)

print(
    "Winning Action:",
    result.winning_decision
    .business_action.operation
)

print(
    "Winning Score:",
    result.winning_score
)


assert len(conflicts) == 1
assert result.winning_decision.agent_id == "InventoryAgent"
assert result.winning_score == 0.9

print("Decision Manager MOCRA test passed.")