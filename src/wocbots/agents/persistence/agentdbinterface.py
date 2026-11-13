from wocbots.agents.agent import Agent
from wocbots.agents.persistence.abstractsqlitewrapper import AbstractSqliteWrapper
from wocbots.agents.persistence.agentserialization import AgentSerialization


class AgentDbInterface:
    def __init__(self, sqlite_wrapper: AbstractSqliteWrapper, serialization: AgentSerialization) -> None:
        self.sqlite_wrapper = sqlite_wrapper
        self.serialization = serialization

    def load_agent(self, features: tuple[str, ...]) -> Agent | None:
        agent_bytes: bytes | None = self.sqlite_wrapper.read_bytes_from_db(features=features)
        if agent_bytes is not None:
            agent: Agent = self.serialization.deserialize(agent_bytes)
            return agent
        return None

    def load_all_agents(self) -> list[Agent]:
        agent_bytes_list: list[bytes] | None = self.sqlite_wrapper.read_all_entries()
        if agent_bytes_list is not None:
            agents: list[Agent] = [
                self.serialization.deserialize(data=agent_bytes) for agent_bytes in agent_bytes_list
            ]
            return agents
        return []

    def save_agent(self, agent: Agent) -> None:
        agent_bytes: bytes = self.serialization.serialize(agent=agent)
        features: tuple[str, ...] = agent.features
        self.sqlite_wrapper.write_bytes_to_db(features=features, data=agent_bytes)

    def save_agents(self, agents: list[Agent]) -> None:
        for agent in agents:
            self.save_agent(agent=agent)
