from pickle import dumps, loads

from wocbots.agents.agent import Agent


class AgentSerialization:
    def serialize(this, agent: Agent) -> bytes:
        return dumps(obj=agent, protocol=5)

    def deserialize(this, data: bytes) -> Agent:
        agent: Agent
        try:
            agent = loads(data)
            return agent
        except TypeError:
            raise TypeError(f"Deserialized object was not an Agent -- ${type(agent)}") from TypeError
