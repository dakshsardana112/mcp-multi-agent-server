"""Core MCP server.

We use the FastMCP helper from the official MCP SDK because it gives us a
clean decorator-based API for tools, resources, and prompts. The server
itself is intentionally tiny - all the *interesting* logic lives in the
agent modules under ``mcp_multi_agent.agents``.

Run with:  python -m mcp_multi_agent
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import settings
from .registry import register_default_agents


def build_server() -> FastMCP:
    """Construct the FastMCP server, attach every enabled agent.

    Returns the FastMCP instance so callers (incl. tests) can inspect it.
    """
    settings.ensure_data_dir()

    mcp = FastMCP(settings.server_name)

    reg = register_default_agents()
    attached = reg.attach_all(mcp, only=settings.enabled_agents)

    # A couple of "meta" tools / resources at the server level so a client
    # can discover what's wired up without trial-and-error.
    @mcp.tool()
    def server_info() -> dict[str, Any]:
        """Return server name, version, and the list of attached agents."""
        return {
            "name": settings.server_name,
            "version": settings.server_version,
            "agents": attached,
            "data_dir": str(settings.data_dir),
        }

    @mcp.tool()
    def ping() -> str:
        """Simple liveness check. Returns the literal string 'pong'."""
        return "pong"

    @mcp.resource("server://agents")
    def list_agents_resource() -> str:
        """Resource listing every attached agent (JSON)."""
        return json.dumps({"agents": attached}, indent=2)

    @mcp.prompt()
    def getting_started() -> str:
        """A starter prompt explaining how to use this server."""
        return (
            "You are connected to the mcp-multi-agent-server. "
            "It hosts several small domain agents: "
            f"{', '.join(attached)}. "
            "Call `server_info` to inspect the server, then use the agents' "
            "tools (each prefixed by its agent name) to do work."
        )

    return mcp


def main() -> None:
    """Entry point for `python -m mcp_multi_agent` and the console script."""
    mcp = build_server()
    # FastMCP defaults to stdio transport - exactly what an MCP client expects.
    mcp.run()


if __name__ == "__main__":
    main()
