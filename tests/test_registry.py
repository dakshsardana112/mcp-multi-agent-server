"""Tests for the agent registry."""

from __future__ import annotations

import pytest

from mcp.server.fastmcp import FastMCP

from mcp_multi_agent.agents.base import BaseAgent
from mcp_multi_agent.registry import AgentRegistry, register_default_agents


class _Dummy(BaseAgent):
    name = "dummy"

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool()
        def dummy_ping() -> str:
            return "dummy-ok"


def test_register_and_build():
    reg = AgentRegistry()
    reg.register("dummy", _Dummy)
    assert reg.names() == ["dummy"]
    a = reg.build("dummy")
    assert a.name == "dummy"
    # Idempotent - same instance returned
    assert reg.build("dummy") is a


def test_duplicate_registration_raises():
    reg = AgentRegistry()
    reg.register("dummy", _Dummy)
    with pytest.raises(ValueError):
        reg.register("dummy", _Dummy)


def test_build_unknown_raises():
    reg = AgentRegistry()
    with pytest.raises(KeyError):
        reg.build("nope")


def test_attach_all_with_filter():
    reg = AgentRegistry()
    reg.register("dummy", _Dummy)
    mcp = FastMCP("t")
    attached = reg.attach_all(mcp, only=("dummy",))
    assert attached == ["dummy"]
    # Filtering excludes
    mcp2 = FastMCP("t2")
    assert reg.attach_all(mcp2, only=()) == []


def test_default_agents_registration():
    reg = register_default_agents()
    for n in ("task", "notes", "weather", "finance", "file", "kb"):
        assert n in reg.names()
