# Architecture

## Guiding principles

1. **Agents are independent.** Each agent is a single file and knows nothing about the others. You can delete `weather_agent.py` and the rest keeps working.
2. **Core server is dumb.** `server.py` just wires things up. No business logic lives there.
3. **Everything persists to simple JSON files.** No DB server, no Docker, no fuss. Trade-off: not suitable for concurrent multi-writer workloads — but perfect for a learning project.
4. **Tests are offline.** The mock weather agent is deterministic on purpose so the suite stays reproducible.

## Components

```
┌──────────────────────────────────────────────────────┐
│                    FastMCP server                    │
│                      (server.py)                     │
└──────────────────────┬───────────────────────────────┘
                       │ "attach everything"
                       ▼
┌──────────────────────────────────────────────────────┐
│                  AgentRegistry                       │
│                   (registry.py)                      │
│   register_default_agents() → [task, notes, ...]     │
└──────┬────────┬────────┬────────┬────────┬────────┬──┘
       │        │        │        │        │        │
       ▼        ▼        ▼        ▼        ▼        ▼
    ┌─────┐ ┌─────┐ ┌──────┐ ┌────────┐ ┌────┐ ┌────┐
    │task │ │notes│ │weathr│ │finance │ │file│ │ kb │
    └──┬──┘ └──┬──┘ └──┬───┘ └───┬────┘ └────┘ └──┬─┘
       │       │       │         │                │
       └───────┴───────┴─────────┴────────────────┘
                         │
                         ▼
               ┌──────────────────┐
               │     JsonStore    │
               │   (storage.py)   │
               └──────────────────┘
                         │
                         ▼
                    data/*.json
```

### server.py
Builds a `FastMCP` instance, asks the registry to attach every enabled agent, then adds two server-level tools (`server_info`, `ping`), one resource (`server://agents`), and a starter prompt (`getting_started`).

### registry.py
Holds a map of `name → factory`. Lazy: agents are only constructed when attached. This is what makes the "microservices" story work — each agent is a cleanly separable unit you can enable/disable at runtime through `settings.enabled_agents`.

### storage.py
A thread-safe JSON file store with atomic writes (tempfile + rename). Each agent gets its own file.

### agents/base.py
Abstract class with two contracts: `name` and `register(mcp)`. Subclasses pick how they persist data, what tools they expose, etc. Tiny surface area on purpose.

### agents/*.py
The actual work. Each agent:
1. Initialises its own `JsonStore` in `__init__`.
2. In `register(mcp)`, defines closures decorated with `@mcp.tool()` / `@mcp.resource()` / `@mcp.prompt()` and attaches them to the server.

Because the decorators capture `self` (as `agent = self`) in a closure, agents stay object-oriented inside while looking like flat functions to MCP.

## Data flow for a single tool call

```
client calls "task_add"
        │
        ▼
FastMCP dispatches to the closure defined in task_agent.register
        │
        ▼
closure validates args → mutates task list → calls JsonStore.save
        │
        ▼
JsonStore writes to data/tasks.json atomically (tempfile + rename)
        │
        ▼
closure returns the new task dict → FastMCP serialises → client receives
```

## Why JSON files and not SQLite?

For a learning project, opening `data/tasks.json` in a text editor is worth more than performance or transaction safety. If you outgrow this, swap `JsonStore` for a SQLite-backed equivalent and keep the `.load()` / `.save()` / `.update()` contract; nothing above the store needs to change.

## Concurrency

Per agent, `JsonStore._lock` serialises writes. Across agents there's no global lock because they don't share state. If you add an agent that reads from *another* agent's file, wrap the read+write in an `update()` callback or refactor the shared data into a third store.
