from models.business_action import BusinessAction
from models.commerce_decision import CommerceDecision
from protocols.acnp_message import ACNPMessage
from protocols.serializer import ACNPSerializer
from protocols.validator import ACNPValidator


action = BusinessAction(
    agent_id="PricingAgent",
    action_type="PRICE_CHANGE",
    operation="INCREASE",
    target="SKU-101",
    value=10,
    unit="PERCENT",
    rationale="High demand and low inventory",
    confidence=0.85,
    risk=0.20,
    priority=8
)


decision = CommerceDecision(
    agent_id="PricingAgent",
    goal="Increase Profit",
    business_action=action,
    confidence=action.confidence,
    risk=action.risk,
    evidence=[
        action.rationale
    ]
)


message = ACNPMessage(
    sender="PricingAgent",
    receiver="ACOSKernel",
    message_type="PROPOSAL",
    decision=decision
)


is_valid = ACNPValidator.validate(message)

print("Message Valid:", is_valid)
print(ACNPSerializer.serialize(message))


assert is_valid is True
assert message.sender == "PricingAgent"
assert message.receiver == "ACOSKernel"
assert message.decision.business_action.operation == "INCREASE"

print("ACNP test passed.")