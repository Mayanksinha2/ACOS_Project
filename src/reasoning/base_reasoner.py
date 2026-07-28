from abc import ABC, abstractmethod


class BaseReasoner(ABC):
    """
    Abstract base class for all reasoning strategies.
    Every reasoner in ACOS must implement these methods.
    """

    @abstractmethod
    def analyze(self, business_state):
        """
        Analyze the current business state.
        """
        pass

    @abstractmethod
    def generate_actions(self):
        """
        Generate one or more candidate business actions.
        """
        pass

    @abstractmethod
    def estimate_confidence(self):
        """
        Return confidence score (0-1).
        """
        pass

    @abstractmethod
    def estimate_risk(self):
        """
        Return risk score (0-1).
        """
        pass