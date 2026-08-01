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


results = (
    kernel.decision_manager
    .detect_conflicts()
)


print("Pending Proposals:", (
    kernel.decision_manager.pending_count()
))

print("Conflict Results:", len(results))


for result in results:

    print(
        result.conflict_type,
        "->",
        result.reason
    )


print(
    "Negotiation Required:",
    kernel.decision_manager
    .has_negotiation_required()
)


assert len(results) == 1
assert results[0].conflict_type == "SUPPORTING"

assert (
    kernel.decision_manager
    .has_negotiation_required()
    is False
)

print("Kernel conflict detection test passed.")