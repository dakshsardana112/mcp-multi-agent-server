# Examples

## `client_demo.py`

A minimal MCP client. Spawns the server as a subprocess, queries it, and
prints results. Intended to be read top-to-bottom as a learning aid.

```bash
python examples/client_demo.py
```

What it does:

1. Lists every tool the server exposes.
2. Calls `ping` as a liveness check.
3. Adds two tasks and lists them back.
4. Fetches mock weather for a city.
5. Enumerates resources (`server://agents`, `task://all`, ...).
6. Enumerates prompts.

If this runs cleanly, your full stack (server ↔ MCP client library) is
working. Use it as a template for building real clients.
