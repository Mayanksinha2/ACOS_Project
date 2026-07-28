from agents.pricing_agent import PricingAgent
from kernel.kernel import ACOSKernel
from reasoning.rule_reasoner import RuleReasoner


kernel = ACOSKernel()

reasoner = RuleReasoner()
pricing_agent = PricingAgent(reasoner)

kernel.register_agent(pricing_agent)


print("Registered Agents:")

for agent in kernel.show_agents():
    print(agent.agent_name)


assert kernel.registry.count() == 1
assert kernel.registry.get_agent("PricingAgent") is pricing_agent

print("Kernel test passed.")