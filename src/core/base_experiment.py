from abc import ABC, abstractmethod


class BaseExperiment(ABC):

    def __init__(self, name):

        self.name = name

        self.results = {}


    @abstractmethod
    def run(self):

        pass


    def save_results(self):

        return self.results