"""Test setup.

Every test function gets a fresh ``data_dir`` (via tmp_path) so tests
don't leak state between each other. We do that by overriding the
``settings.data_dir`` before constructing any agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `src/` importable without installing the package.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp_multi_agent.config import settings  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    """Point settings.data_dir at a temp dir for every test."""
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    settings.ensure_data_dir()
    yield tmp_path
