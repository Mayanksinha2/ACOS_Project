from protocols.acnp_message import ACNPMessage


class ACNPValidationError(ValueError):
    """
    Raised when an ACNP message does not satisfy protocol rules.
    """


class ACNPValidator:
    """
    Validates ACNP messages before they enter the ACOS Kernel.
    """

    ALLOWED_MESSAGE_TYPES = {
        "PROPOSAL",
        "COUNTER_PROPOSAL",
        "ACCEPT",
        "REJECT",
        "FEEDBACK"
    }

    @classmethod
    def validate(cls, message: ACNPMessage) -> bool:
        if not isinstance(message, ACNPMessage):
            return False

        if not message.message_id:
            return False

        if not message.sender:
            return False

        if not message.receiver:
            return False

        if message.message_type not in cls.ALLOWED_MESSAGE_TYPES:
            return False

        if message.decision is None:
            return False

        if not message.decision.agent_id:
            return False

        if message.decision.business_action is None:
            return False

        action = message.decision.business_action

        if not action.action_type:
            return False

        if not action.operation:
            return False

        if not action.target:
            return False

        return True

    @classmethod
    def validate_or_raise(cls, message: ACNPMessage) -> None:
        if not cls.validate(message):
            raise ACNPValidationError(
                "The ACNP message failed protocol validation."
            )