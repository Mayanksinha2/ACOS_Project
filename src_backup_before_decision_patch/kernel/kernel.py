from typing import Any, Dict, List

from kernel.decision_manager import DecisionManager
from kernel.message_router import MessageRouter
from kernel.registry import AgentRegistry
from protocols.acnp_message import ACNPMessage
from protocols.validator import ACNPValidator


class ACOSKernel:
    """
    Central orchestration component of ACOS.
    """

    KERNEL_ID = "ACOSKernel"

    def __init__(self):
        self.registry = AgentRegistry()
        self.decision_manager = DecisionManager()
        self.message_router = MessageRouter()

        self.message_router.register_receiver(
            self.KERNEL_ID,
            self._receive_message
        )

    def register_agent(self, agent: Any) -> None:
        self.registry.register(agent)

    def show_agents(self) -> List[Any]:
        return self.registry.get_all_agents()

    def submit_message(
        self,
        message: ACNPMessage
    ) -> Dict[str, Any]:

        return self.message_router.route(message)

    def _receive_message(
        self,
        message: ACNPMessage
    ) -> Dict[str, Any]:

        ACNPValidator.validate_or_raise(message)

        if message.message_type == "PROPOSAL":
            decision = self.decision_manager.add_proposal(
                message.decision
            )

            return {
                "status": "ACCEPTED",
                "message_id": message.message_id,
                "proposal_id": decision.proposal_id,
                "negotiation_status":
                    decision.negotiation_status
            }

        return {
            "status": "RECEIVED",
            "message_id": message.message_id,
            "message_type": message.message_type
        }