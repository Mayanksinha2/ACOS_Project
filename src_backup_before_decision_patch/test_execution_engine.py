from agents.inventory_agent import InventoryAgent
from agents.marketing_agent import MarketingAgent
from agents.pricing_agent import PricingAgent
from execution.execution_engine import ExecutionEngine
from kernel.kernel import ACOSKernel
from models.business_state import BusinessState
from protocols.acnp_message import ACNPMessage
from reasoning.inventory_reasoner import InventoryReasoner
from reasoning.marketing_reasoner import MarketingReasoner
from reasoning.rule_reasoner import RuleReasoner
from simulator.product import Product


product = Product(
    product_id="SKU-101",
    name="Pink Frock",
    category="Kids Wear",
    cost_price=350,
    selling_price=799,
    inventory=15,
    demand_level="High"
)


state = BusinessState(
    products=[product],
    market={
        "demand": 80,
        "advertising_cost": 120
    },
    metrics={
        "inventory": product.inventory,
        "conversion_rate": 0.03,
        "product_id": product.product_id
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

    kernel.submit_message(message)


final_decision = (
    kernel.decision_manager
    .make_final_decision()
)


print(
    "Final Decision Type:",
    final_decision["decision_type"]
)


execution_engine = ExecutionEngine(
    products={
        product.product_id: product
    }
)


old_price = product.selling_price

execution_result = (
    execution_engine.execute_final_result(
        final_decision
    )
)


print("Execution Success:", execution_result.success)
print("Source:", execution_result.source)
print("Operation:", execution_result.operation)
print("Old Price:", old_price)
print("New Price:", product.selling_price)
print("Message:", execution_result.message)


assert execution_result.success is True
assert execution_result.target == "SKU-101"

assert (
    execution_result.previous_state[
        "selling_price"
    ]
    == old_price
)

assert (
    execution_result.updated_state[
        "selling_price"
    ]
    == product.selling_price
)

print("Execution Engine test passed.")