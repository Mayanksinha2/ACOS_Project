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


pricing_agent = PricingAgent(
    RuleReasoner()
)

inventory_agent = InventoryAgent(
    InventoryReasoner()
)


kernel = ACOSKernel()

kernel.register_agent(pricing_agent)
kernel.register_agent(inventory_agent)


agents = [
    pricing_agent,
    inventory_agent
]


for agent in agents:

    agent.observe(state)
    agent.analyze()

    decision = agent.generate_decision()

    message = ACNPMessage(
        sender=agent.agent_name,
        receiver="ACOSKernel",
        message_type="PROPOSAL",
        decision=decision
    )

    response = kernel.submit_message(message)

    print(
        agent.agent_name,
        "Kernel Response:",
        response
    )


pending = (
    kernel.decision_manager
    .get_pending_proposals()
)


print("Registered Agents:", kernel.registry.count())
print("Pending Proposals:", len(pending))


for decision in pending:

    print(
        decision.agent_id,
        "->",
        decision.business_action.operation,
        "->",
        decision.business_action.target
    )


assert kernel.registry.count() == 2
assert len(pending) == 2

assert {
    decision.agent_id
    for decision in pending
} == {
    "PricingAgent",
    "InventoryAgent"
}

print("Multi-agent Kernel test passed.")