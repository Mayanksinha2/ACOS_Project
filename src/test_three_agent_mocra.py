from agents.inventory_agent import InventoryAgent
from agents.marketing_agent import MarketingAgent
from agents.pricing_agent import PricingAgent
from kernel.kernel import ACOSKernel
from models.business_state import BusinessState
from protocols.acnp_message import ACNPMessage
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


kernel = ACOSKernel()


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

    response = kernel.submit_message(message)

    print(
        agent.agent_name,
        "->",
        decision.business_action.operation,
        "->",
        response["status"]
    )


conflicts = (
    kernel.decision_manager
    .detect_conflicts()
)


print("\nConflict Results:")

for conflict in conflicts:
    print(
        conflict.conflict_type,
        "->",
        conflict.reason
    )


print(
    "\nNegotiation Required:",
    kernel.decision_manager
    .has_negotiation_required()
)


result = (
    kernel.decision_manager
    .resolve_pending_proposals()
)


print("\nMOCRA Ranking:")

for position, entry in enumerate(
    result.ranking,
    start=1
):
    print(
        position,
        entry["decision"].agent_id,
        entry["decision"].business_action.operation,
        entry["score_details"]["final_score"]
    )


print(
    "\nWinning Agent:",
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


assert kernel.registry.count() == 3
assert kernel.decision_manager.pending_count() == 3
assert len(conflicts) == 3

assert any(
    conflict.conflict_type == "HARD_CONFLICT"
    for conflict in conflicts
)

assert (
    kernel.decision_manager
    .has_negotiation_required()
    is True
)

assert result.winning_decision.agent_id == "InventoryAgent"
assert result.winning_score == 0.9

print("\nThree-agent MOCRA test passed.")