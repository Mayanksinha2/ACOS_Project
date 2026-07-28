from typing import Any, Dict, List, Optional


class AgentRegistry:
    """
    Maintains all agents registered with the ACOS Kernel.
    """

    def __init__(self):
        self._agents: Dict[str, Any] = {}

    def register(self, agent: Any) -> None:
        agent_name = agent.agent_name

        if agent_name in self._agents:
            raise ValueError(
                f"Agent already registered: {agent_name}"
            )

        self._agents[agent_name] = agent

    def unregister(self, agent_name: str) -> None:
        self._agents.pop(agent_name, None)

    def get_agent(
        self,
        agent_name: str
    ) -> Optional[Any]:

        return self._agents.get(agent_name)

    def get_all_agents(self) -> List[Any]:
        return list(self._agents.values())

    def count(self) -> int:
        return len(self._agents)