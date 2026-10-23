from wocbots.agents.agent import Agent
from wocbots.swarm.observer import BeeObserver

class BeeSubject:
    def __init__(self, agent : Agent) -> None:
        self.observers : list[BeeObserver] = []
        self.agent : Agent = agent

    def register_observer(self, bee_observer:BeeObserver):
        self.observers.append(bee_observer)

    def deregister_observer(self, bee_observer:BeeObserver):
        self.observers.remove(bee_observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.notify(self.agent)