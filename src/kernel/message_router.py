from typing import Any, Callable, Dict

from protocols.acnp_message import ACNPMessage


MessageHandler = Callable[[ACNPMessage], Any]


class MessageRouter:
    """
    Routes ACNP messages to registered ACOS receivers.
    """

    def __init__(self):
        self._receivers: Dict[str, MessageHandler] = {}

    def register_receiver(
        self,
        receiver_name: str,
        handler: MessageHandler
    ) -> None:

        if not receiver_name:
            raise ValueError(
                "Receiver name cannot be empty."
            )

        self._receivers[receiver_name] = handler

    def route(self, message: ACNPMessage) -> Any:
        handler = self._receivers.get(
            message.receiver
        )

        if handler is None:
            raise LookupError(
                f"No receiver registered as "
                f"'{message.receiver}'."
            )

        return handler(message)

    def has_receiver(
        self,
        receiver_name: str
    ) -> bool:

        return receiver_name in self._receivers