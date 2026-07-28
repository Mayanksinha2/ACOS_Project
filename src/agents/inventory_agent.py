from agents.base_agent import BaseAgent
from reasoning.proposal_generator import ProposalGenerator


class InventoryAgent(BaseAgent):

    def __init__(self, reasoner):
        super().__init__(
            name="InventoryAgent",
            reasoner=reasoner
        )

        self.business_state = None

    def observe(self, business_state):
        self.business_state = business_state

    def analyze(self):
        if self.business_state is None:
            raise RuntimeError(
                "InventoryAgent has not received a business state."
            )

        return self.reasoner.analyze(
            self.business_state
        )

    def generate_decision(self):
        return ProposalGenerator.generate(
            agent_name=self.name,
            reasoner=self.reasoner,
            goal="Optimize Inventory Health"
        )

    def receive_feedback(self, feedback):
        print(
            f"{self.name} received feedback: {feedback}"
        )