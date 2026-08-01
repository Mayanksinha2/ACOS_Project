from agents.inventory_agent import InventoryAgent
from agents.pricing_agent import PricingAgent
from models.business_state import BusinessState
from negotiation.conflict_detector import ConflictDetector
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


pricing_agent.observe(state)
pricing_agent.analyze()
pricing_decision = pricing_agent.generate_decision()


inventory_agent.observe(state)
inventory_agent.analyze()
inventory_decision = inventory_agent.generate_decision()


detector = ConflictDetector()

result = detector.compare(
    pricing_decision,
    inventory_decision
)


print("Conflict ID:", result.conflict_id)
print("Conflict Type:", result.conflict_type)
print("Target:", result.target)
print("Reason:", result.reason)
print("Severity:", result.severity)
print(
    "Requires Negotiation:",
    result.requires_negotiation
)


assert result.conflict_type == "SUPPORTING"
assert result.target == "SKU-101"
assert result.severity == 0.0
assert result.requires_negotiation is False

print("Conflict Detector supporting test passed.")