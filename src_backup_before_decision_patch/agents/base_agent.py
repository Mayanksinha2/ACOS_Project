from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Common lifecycle interface for all ACOS agents.
    """

    def __init__(self, name: str, reasoner: Any):
        self.name = name
        self.reasoner = reasoner

    @property
    def agent_name(self) -> str:
        """
        Backward-compatible alias used by older ACOS modules.
        """
        return self.name

    @abstractmethod
    def observe(self, business_state: Any) -> None:
        pass

    @abstractmethod
    def analyze(self) -> Any:
        pass

    @abstractmethod
    def generate_decision(self) -> Any:
        pass

    @abstractmethod
    def receive_feedback(self, feedback: Any) -> None:
        pass