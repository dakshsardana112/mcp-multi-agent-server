"""Agent registry.

The core server doesn't know about individual agents - it just knows there is
a registry of them, and each agent knows how to register its own tools,
resources, and prompts on the FastMCP server. That keeps things microservice-
ish: each agent module is self-contained, you can disable one without touching
the others, and adding a new agent is mechanical.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from mcp.server.fastmcp import FastMCP

from .agents.base import BaseAgent


class AgentRegistry:
    """Maps an agent name -> a factory that produces the agent instance.

    Using factories (rather than instances) means each agent is constructed
    *after* the server and config exist, so agents can grab their data files
    from a known data directory.
    """

    def __init__(self) -> None:
        self._factories: Dict[str, Callable[[], BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}

    def register(self, name: str, factory: Callable[[], BaseAgent]) -> None:
        if name in self._factories:
            raise ValueError(f"Agent '{name}' is already registered")
        self._factories[name] = factory

    def names(self) -> List[str]:
        return sorted(self._factories.keys())

    def build(self, name: str) -> BaseAgent:
        if name not in self._factories:
            raise KeyError(f"No agent named '{name}'")
        if name not in self._instances:
            self._instances[name] = self._factories[name]()
        return self._instances[name]

    def attach_all(self, mcp: FastMCP, only: tuple[str, ...] | None = None) -> List[str]:
        """Build each enabled agent and let it register its MCP capabilities.

        Returns the list of attached agent names so the caller can log it.
        """
        attached: List[str] = []
        for name in self.names():
            if only is not None and name not in only:
                continue
            agent = self.build(name)
            agent.register(mcp)
            attached.append(name)
        return attached


# Module-level singleton. Agents register themselves at import time via
# ``register_default_agents`` below.
registry = AgentRegistry()


def register_default_agents() -> AgentRegistry:
    """Wire up the built-in agents.

    Imports happen lazily inside this function so we can test the registry
    without dragging every agent module into memory.
    """
    from .agents.task_agent import TaskAgent
    from .agents.notes_agent import NotesAgent
    from .agents.weather_agent import WeatherAgent
    from .agents.finance_agent import FinanceAgent
    from .agents.file_agent import FileAgent
    from .agents.kb_agent import KnowledgeBaseAgent

    pairs = [
        ("task", TaskAgent),
        ("notes", NotesAgent),
        ("weather", WeatherAgent),
        ("finance", FinanceAgent),
        ("file", FileAgent),
        ("kb", KnowledgeBaseAgent),
    ]
    for name, cls in pairs:
        if name not in registry._factories:
            registry.register(name, cls)
    return registry
