from wocbots.agents.agent import Agent
from wocbots.swarm.observer import BeeObserver
from wocbots.interaction import Encounter
from wocbots.swarm.encounterdata import EncounterData


class WorkerBee(BeeObserver):
    def __init__(self, agent : Agent, encounter_data : EncounterData) -> WorkerBee:
        super().__init__()
        self.agent = agent
        self.encounter_data = encounter_data

    def notify(self, presenter : Agent) -> None:
        encounter = Encounter(a=self.agent,
                              b=presenter,
                              scoring_policy=self.encounter_data.scoring_policy,
                              history_store=self.encounter_data.history_store,
                              interaction_policy=self.encounter_data.interaction_policy
                              )
        encounter.process()