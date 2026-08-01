from abc import ABC, abstractmethod


class BaseAgent(ABC):

    def __init__(self, agent_name, objective):

        self.agent_name = agent_name
        self.objective = objective

        self.memory = []

        self.confidence = 0.5


    @abstractmethod
    def observe(self, environment):
        pass


    @abstractmethod
    def analyze(self):
        pass


    @abstractmethod
    def propose(self):
        pass


    def learn(self, decision, reward):

        self.memory.append({

            "decision": decision,

            "reward": reward

        })
