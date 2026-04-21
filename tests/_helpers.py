"""Small helpers shared by several test modules."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_multi_agent.agents.base import BaseAgent


def build_agent(cls: type[BaseAgent]) -> tuple[BaseAgent, FastMCP]:
    """Construct an agent, attach it to a fresh FastMCP, return both."""
    mcp = FastMCP("test")
    agent = cls()
    agent.register(mcp)
    return agent, mcp


def call(mcp: FastMCP, tool_name: str, **kwargs: Any) -> Any:
    """Invoke a registered tool by name with its *underlying* Python function.

    Skipping the async ``call_tool`` path keeps tests synchronous and gives
    us the raw return value (rather than MCP-wrapped content blocks).
    """
    tool = mcp._tool_manager._tools[tool_name]
    return tool.fn(**kwargs)
