import pytest
from typing import Generator

from wocbots.agents.persistence.agentserialization import AgentSerialization
from wocbots.agents.agent import Agent, HOLLYWOOD_WEIGHTS

@pytest.fixture(scope="function")
def agent_under_test() -> Generator[Agent, None, None]:
    yield Agent(features=["f0", "f1"],
                eval_accuracy=0.3,
                eval_precision=0.3,
                eval_recall=0.4,
                confidence_weights=HOLLYWOOD_WEIGHTS)

@pytest.fixture(scope="function")
def serializer_under_test() -> Generator[AgentSerialization, None, None]:
    yield AgentSerialization()

def test_basic_round_trip(agent_under_test, serializer_under_test):
    agent_bytes : bytes = serializer_under_test.serialize(agent=agent_under_test)
    actual : Agent = serializer_under_test.deserialize(data=agent_bytes)
    assert actual.eval_accuracy == agent_under_test.eval_accuracy