"""Minimal MCP client that spawns the server as a subprocess and runs a
handful of tool calls end-to-end. Purely for learning / smoke-testing.

Run with:
    python examples/client_demo.py

It boots the server via ``python -m mcp_multi_agent`` using stdio transport,
asks the server what tools exist, calls a few of them, and prints the
results. If this script prints sensible output with no tracebacks, the
whole stack is healthy.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Prepend ./src so the subprocess can find the package without install.
    root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_multi_agent"],
        env=env,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. What tools does the server expose
            tools = await session.list_tools()
            print(f"Discovered {len(tools.tools)} tools:")
            for t in tools.tools:
                print(f"  - {t.name}")

            # 2. Quick liveness check
            pong = await session.call_tool("ping", {})
            print("\nping ->", pong.content[0].text if pong.content else pong)

            # 3. Add two tasks, list them
            await session.call_tool(
                "task_add", {"title": "read the README", "priority": "high"}
            )
            await session.call_tool(
                "task_add", {"title": "add your own agent", "priority": "medium"}
            )
            tasks = await session.call_tool("task_list", {})
            print("\ntask_list ->")
            for block in tasks.content:
                print(" ", block.text if hasattr(block, "text") else block)

            # 4. Mock weather
            wx = await session.call_tool("weather_current", {"city": "Jaipur"})
            print("\nweather_current(Jaipur) ->")
            for block in wx.content:
                print(" ", block.text if hasattr(block, "text") else block)

            # 5. List resources too
            resources = await session.list_resources()
            print(f"\nResources exposed: {len(resources.resources)}")
            for r in resources.resources:
                print(f"  - {r.uri}")

            # 6. Prompts
            prompts = await session.list_prompts()
            print(f"\nPrompts available: {len(prompts.prompts)}")
            for p in prompts.prompts:
                print(f"  - {p.name}")


if __name__ == "__main__":
    asyncio.run(main())
