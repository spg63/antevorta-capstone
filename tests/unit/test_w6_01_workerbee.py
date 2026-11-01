from collections.abc import Generator

import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.interaction.history import HistoryStore
from wocbots.interaction.policy import ReferenceInteractionPolicy
from wocbots.interaction.scoring import CertaintyFlipScoringPolicy
from wocbots.swarm.encounterdata import EncounterData
from wocbots.swarm.scoutbee import ScoutBee
from wocbots.swarm.workerbee import WorkerBee


@pytest.fixture(scope="function")
def scout_bee_under_test() -> Generator[ScoutBee, None, None]:
    agent = Agent(
        features=("f0",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    agent.current_prediction = 1
    yield ScoutBee(agent=agent)
    

@pytest.fixture(scope="function")
def encounter_data_under_test() -> Generator[EncounterData, None, None]:
    history_store = HistoryStore()
    yield EncounterData(
        history_store=history_store,
        interaction_policy=ReferenceInteractionPolicy(history_store=history_store),
        scoring_policy=CertaintyFlipScoringPolicy(),
    )


@pytest.fixture(scope="function")
def worker_bee_under_test(
    encounter_data_under_test : EncounterData) -> Generator[WorkerBee, None, None]:
    agent = Agent(
        features=("f0",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,)
    agent.current_prediction = 1
    yield WorkerBee(agent = agent,
        encounter_data=encounter_data_under_test)


def test_encounter(scout_bee_under_test: ScoutBee, worker_bee_under_test: WorkerBee) -> None:
    scout_bee_under_test.register_observer(worker_bee_under_test)
    scout_bee_under_test.notify_observers()
