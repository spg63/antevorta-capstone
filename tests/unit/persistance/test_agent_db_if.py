import uuid
from collections.abc import Generator, Iterator

import pytest

from wocbots.agents.agent import HOLLYWOOD_WEIGHTS, Agent
from wocbots.agents.persistence.abstractsqlitewrapper import AbstractSqliteWrapper
from wocbots.agents.persistence.agentdbinterface import AgentDbInterface
from wocbots.agents.persistence.agentserialization import AgentSerialization


class LocalSqliteWrapper(AbstractSqliteWrapper):
    def __init__(self, filepath: str = "") -> None:
        self.entries: dict[uuid.UUID, tuple[tuple[str, ...], bytes]] = {}

    def __del__(self) -> None:
        pass

    def read_bytes_from_db(self, uuid: uuid.UUID) -> bytes | None:
        value = self.entries.get(uuid)
        if value is None:
            raise ValueError("Entry not found")
        data: bytes = value[1]
        return data

    def write_bytes_to_db(self, uuid: uuid.UUID, features: tuple[str, ...], data: bytes) -> None:
        self.entries[uuid] = (features, data)

    def read_all_entries(self) -> list[bytes] | None:
        bytes_list: list[bytes] = []
        for entry in list(self.entries):
            local_value = self.entries[entry]
            data = local_value[1]
            bytes_list.append(data)
        return bytes_list

    def read_uuids_per_features(self, features: tuple[str, ...]) -> list[uuid.UUID]:
        uuid_list: list[uuid.UUID] = []
        for entry in list(self.entries):
            local_value = self.entries[entry]
            local_features = local_value[0]
            if features == local_features:
                uuid_list.append(entry)
        return uuid_list


@pytest.fixture(scope="function")
def agent_db_if_under_test() -> Generator[AgentDbInterface, None, None]:
    sqlite_wrapper = LocalSqliteWrapper()
    serialization = AgentSerialization()
    yield AgentDbInterface(sqlite_wrapper=sqlite_wrapper, serialization=serialization)


@pytest.fixture
def agents_under_test() -> Iterator[list[Agent]]:
    agents = [
        Agent(
            features=["str1", "str2"],
            eval_accuracy=0.3,
            eval_precision=0.3,
            eval_recall=0.4,
            confidence_weights=HOLLYWOOD_WEIGHTS,
        ),
        Agent(
            features=["f1", "f2"],
            eval_accuracy=0.2,
            eval_precision=0.4,
            eval_recall=0.4,
            confidence_weights=HOLLYWOOD_WEIGHTS,
        ),
        Agent(
            features=["ag1", "ag2"],
            eval_accuracy=0.4,
            eval_precision=0.3,
            eval_recall=0.3,
            confidence_weights=HOLLYWOOD_WEIGHTS,
        ),
    ]
    yield agents


def test_round_trip_individual(
    agent_db_if_under_test: AgentDbInterface, agents_under_test: list[Agent]
) -> None:
    agent1: Agent = agents_under_test[0]
    agent_db_if_under_test.save_agent(agent=agent1)
    actual_agent = agent_db_if_under_test.load_agent(uuid=agent1.uuid)
    assert agent1 == actual_agent


def test_round_trip_read_all(
    agent_db_if_under_test: AgentDbInterface, agents_under_test: list[Agent]
) -> None:
    agent_db_if_under_test.save_agent(agent=agents_under_test[0])
    agent_db_if_under_test.save_agent(agent=agents_under_test[1])
    agent_db_if_under_test.save_agent(agent=agents_under_test[2])

    agent_list: list[Agent] = agent_db_if_under_test.load_all_agents()

    assert agents_under_test[0] in agent_list
    assert agents_under_test[1] in agent_list
    assert agents_under_test[2] in agent_list


def test_round_trip_save_list(
    agent_db_if_under_test: AgentDbInterface, agents_under_test: list[Agent]
) -> None:
    agent_db_if_under_test.save_agents(agents=agents_under_test)

    agent_list: list[Agent] = agent_db_if_under_test.load_all_agents()

    assert agents_under_test[0] in agent_list
    assert agents_under_test[1] in agent_list
    assert agents_under_test[2] in agent_list
