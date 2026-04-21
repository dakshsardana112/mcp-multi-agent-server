# Adding a new agent

This walkthrough adds a toy **"quotes"** agent that stores inspirational quotes and lets you fetch a random one. It mirrors the shape of the existing six so you can use it as a template.

## 1. Create the agent file

`src/mcp_multi_agent/agents/quotes_agent.py`:

```python
from __future__ import annotations

import random
import uuid
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent


class QuotesAgent(BaseAgent):
    name = "quotes"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store("quotes.json", default={"quotes": []})

    def register(self, mcp: FastMCP) -> None:
        agent = self

        @mcp.tool()
        def quotes_add(text: str, author: str = "unknown") -> dict[str, Any]:
            """Save a new quote."""
            if not text.strip():
                raise ValueError("text cannot be empty")
            data = agent.store.load()
            q = {"id": uuid.uuid4().hex[:8], "text": text.strip(), "author": author}
            data["quotes"].append(q)
            agent.store.save(data)
            return q

        @mcp.tool()
        def quotes_random() -> Optional[dict[str, Any]]:
            """Return a random stored quote, or None if empty."""
            data = agent.store.load()
            if not data["quotes"]:
                return None
            return random.choice(data["quotes"])

        @mcp.tool()
        def quotes_list() -> list[dict[str, Any]]:
            """Return every stored quote."""
            return list(agent.store.load()["quotes"])
```

## 2. Register it in the registry

Edit `src/mcp_multi_agent/registry.py`, inside `register_default_agents`:

```python
from .agents.quotes_agent import QuotesAgent
...
pairs = [
    ("task", TaskAgent),
    ...,
    ("quotes", QuotesAgent),       # ← new
]
```

And in `src/mcp_multi_agent/config.py` add `"quotes"` to `enabled_agents`.

## 3. Write tests

`tests/test_quotes_agent.py`:

```python
import pytest
from mcp_multi_agent.agents.quotes_agent import QuotesAgent
from tests._helpers import build_agent, call


def test_add_and_list():
    _, mcp = build_agent(QuotesAgent)
    call(mcp, "quotes_add", text="be kind", author="me")
    assert len(call(mcp, "quotes_list")) == 1


def test_random_returns_none_when_empty():
    _, mcp = build_agent(QuotesAgent)
    assert call(mcp, "quotes_random") is None
```

Run `pytest -q` — you should have 60+ tests passing.

## 4. Update docs

Add your agent to the "six agents" table in the `README.md`, and mention it in `CHANGELOG.md` / `CHANGELOG.csv`.

That's it. The agent is now live the next time the server boots.

## Tips

- Keep all validation in the tool closures. Raise `ValueError` / `KeyError` — MCP will surface the message to the client.
- Prefer small, composable tools over one god-tool. Models pick better when each tool does one thing.
- Docstrings are schema documentation — they're what the model reads to decide *when* to call your tool. Write them for the model, not just humans.
- Use `JsonStore.update(fn)` whenever you do read-modify-write; it's the only way to stay atomic across concurrent calls.
