"""Base class every agent inherits from.

An "agent" in this project is a small, self-contained module that owns a
single domain (tasks, notes, weather, etc.). The base class only asks for
two things:

    1. ``name``      - short identifier, used as a prefix on tool names.
    2. ``register``  - attach tools / resources / prompts to the FastMCP
                       server.

Everything else (storage, helper methods, data models) is up to the agent.
Keeping the contract tiny means each agent reads top-to-bottom without
jumping around base classes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..config import settings
from ..storage import JsonStore


class BaseAgent(ABC):
    """Abstract base class. Subclasses must set ``name`` and implement
    ``register``."""

    #: Short identifier; used as a prefix on tool names e.g. ``task_add``.
    name: str = ""

    def __init__(self) -> None:
        if not self.name:
            raise ValueError(
                f"{self.__class__.__name__} must set a class-level `name`"
            )
        self.data_dir: Path = settings.ensure_data_dir()

    def make_store(self, filename: str, default) -> JsonStore:
        """Helper: get a JsonStore scoped to this agent's data file."""
        return JsonStore(self.data_dir / filename, default=default)

    @abstractmethod
    def register(self, mcp: FastMCP) -> None:  # pragma: no cover - abstract
        """Attach this agent's tools/resources/prompts to the given server."""
        raise NotImplementedError
