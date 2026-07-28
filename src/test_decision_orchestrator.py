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

kernel = ACOSKernel()

agents = [
    PricingAgent(RuleReasoner()),
    InventoryAgent(InventoryReasoner()),
    MarketingAgent(MarketingReasoner())
]

for agent in agents:

    kernel.register_agent(agent)

    agent.observe(state)
    agent.analyze()

    decision = agent.generate_decision()

    kernel.submit_message(
        ACNPMessage(
            sender=agent.agent_name,
            receiver="ACOSKernel",
            message_type="PROPOSAL",
            decision=decision
        )
    )

result = (
    kernel.decision_manager.make_final_decision()
)

print("\nDecision Type:")
print(result["decision_type"])

print("\nResult:")
print(result["result"])