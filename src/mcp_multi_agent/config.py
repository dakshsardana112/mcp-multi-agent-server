"""Configuration for the MCP multi-agent server.

Everything that might change between environments lives here so the rest of the
code stays clean. Nothing fancy - just a Settings class with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_data_dir() -> Path:
    """Pick a data directory. Honors MCP_DATA_DIR env var, else ./data."""
    env = os.environ.get("MCP_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (Path(__file__).resolve().parent.parent.parent / "data").resolve()


@dataclass
class Settings:
    """Runtime settings for the server."""

    server_name: str = "mcp-multi-agent-server"
    server_version: str = "0.1.0"
    data_dir: Path = field(default_factory=_default_data_dir)
    enabled_agents: tuple[str, ...] = (
        "task",
        "notes",
        "weather",
        "finance",
        "file",
        "kb",
    )

    def ensure_data_dir(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


# Module-level singleton is fine for a small server like this.
settings = Settings()
