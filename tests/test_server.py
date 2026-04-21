"""Smoke tests for the top-level server assembly."""

from __future__ import annotations

from mcp_multi_agent.server import build_server
from tests._helpers import call


def test_build_server_registers_all_agents():
    mcp = build_server()
    tool_names = set(mcp._tool_manager._tools.keys())
    # A few tools from each agent
    expected = {
        "server_info", "ping",
        "task_add", "task_list", "task_complete", "task_update", "task_delete",
        "notes_create", "notes_search",
        "weather_current", "weather_forecast",
        "finance_add_expense", "finance_summary",
        "file_scan", "file_summary",
        "kb_add", "kb_search",
    }
    missing = expected - tool_names
    assert not missing, f"missing tools: {missing}"


def test_server_info_reports_agents():
    mcp = build_server()
    info = call(mcp, "server_info")
    assert info["name"] == "mcp-multi-agent-server"
    for a in ("task", "notes", "weather", "finance", "file", "kb"):
        assert a in info["agents"], f"agent {a} not attached"


def test_ping():
    mcp = build_server()
    assert call(mcp, "ping") == "pong"
