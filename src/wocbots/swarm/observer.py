from abc import ABC, abstractmethod

from wocbots.agents.agent import Agent

class BeeObserver(ABC):

    @abstractmethod
    def notify(self, presenter : Agent):
        pass