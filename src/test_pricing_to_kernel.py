from agents.pricing_agent import PricingAgent
from kernel.kernel import ACOSKernel
from models.business_state import BusinessState
from protocols.acnp_message import ACNPMessage
from reasoning.rule_reasoner import RuleReasoner


# -------------------------------------------------
# 1. Create current business state
# -------------------------------------------------

state = BusinessState(
    market={
        "demand": 80
    },
    metrics={
        "inventory": 15,
        "product_id": "SKU-101"
    }
)


# -------------------------------------------------
# 2. Create Pricing Agent
# -------------------------------------------------

reasoner = RuleReasoner()
pricing_agent = PricingAgent(reasoner)


# -------------------------------------------------
# 3. Create ACOS Kernel and register agent
# -------------------------------------------------

kernel = ACOSKernel()
kernel.register_agent(pricing_agent)


# -------------------------------------------------
# 4. Agent observes and analyzes state
# -------------------------------------------------

pricing_agent.observe(state)
pricing_agent.analyze()


# -------------------------------------------------
# 5. Agent generates CommerceDecision
# -------------------------------------------------

decision = pricing_agent.generate_decision()


# -------------------------------------------------
# 6. Package decision inside ACNP message
# -------------------------------------------------

message = ACNPMessage(
    sender=pricing_agent.agent_name,
    receiver="ACOSKernel",
    message_type="PROPOSAL",
    decision=decision
)


# -------------------------------------------------
# 7. Submit message to Kernel
# -------------------------------------------------

response = kernel.submit_message(message)


# -------------------------------------------------
# 8. Validate result
# -------------------------------------------------

print("Kernel Response:", response)

print(
    "Registered Agents:",
    kernel.registry.count()
)

print(
    "Pending Proposals:",
    kernel.decision_manager.pending_count()
)


pending = (
    kernel.decision_manager
    .get_pending_proposals()
)

stored_decision = pending[0]

print(
    "Stored Agent:",
    stored_decision.agent_id
)

print(
    "Stored Action:",
    stored_decision.business_action.operation
)

print(
    "Stored Target:",
    stored_decision.business_action.target
)

print(
    "Negotiation Status:",
    stored_decision.negotiation_status
)


assert response["status"] == "ACCEPTED"
assert kernel.registry.count() == 1
assert kernel.decision_manager.pending_count() == 1
assert stored_decision.agent_id == "PricingAgent"
assert stored_decision.business_action.operation == "INCREASE"
assert stored_decision.business_action.target == "SKU-101"
assert stored_decision.negotiation_status == "QUEUED"

print(
    "Pricing Agent to Kernel integration test passed."
)