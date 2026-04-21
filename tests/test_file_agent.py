"""Tests for the file agent."""

from __future__ import annotations

import pytest

from mcp_multi_agent.agents.file_agent import FileAgent
from tests._helpers import build_agent, call


def _make_files(root):
    (root / "a.txt").write_text("hi")
    (root / "b.pdf").write_bytes(b"%PDF-1.4 ...")
    (root / "c.py").write_text("print('hi')")
    (root / "d.weirdext").write_text("?")
    sub = root / "sub"
    sub.mkdir()
    (sub / "nested.png").write_bytes(b"\x89PNG")


def test_scan_non_recursive(tmp_path):
    _, mcp = build_agent(FileAgent)
    _make_files(tmp_path)
    out = call(mcp, "file_scan", path=str(tmp_path), recursive=False)
    names = {f["name"] for f in out["files"]}
    assert "a.txt" in names
    assert "nested.png" not in names


def test_scan_recursive(tmp_path):
    _, mcp = build_agent(FileAgent)
    _make_files(tmp_path)
    out = call(mcp, "file_scan", path=str(tmp_path), recursive=True)
    names = {f["name"] for f in out["files"]}
    assert {"a.txt", "b.pdf", "c.py", "d.weirdext", "nested.png"} <= names


def test_summary_categorization(tmp_path):
    _, mcp = build_agent(FileAgent)
    _make_files(tmp_path)
    s = call(mcp, "file_summary", path=str(tmp_path), recursive=True)
    cats = s["by_category"]
    assert cats["documents"]["count"] >= 1  # a.txt
    assert cats["images"]["count"] >= 1      # nested.png
    assert cats["code"]["count"] >= 1        # c.py
    assert cats["other"]["count"] >= 1       # d.weirdext


def test_search_substring(tmp_path):
    _, mcp = build_agent(FileAgent)
    _make_files(tmp_path)
    hits = call(mcp, "file_search", path=str(tmp_path), name_contains="nest", recursive=True)
    assert len(hits) == 1 and hits[0]["name"] == "nested.png"


def test_scan_missing_path_raises(tmp_path):
    _, mcp = build_agent(FileAgent)
    with pytest.raises(FileNotFoundError):
        call(mcp, "file_scan", path=str(tmp_path / "nope"))


def test_scan_on_file_not_dir(tmp_path):
    _, mcp = build_agent(FileAgent)
    f = tmp_path / "a.txt"
    f.write_text("hi")
    with pytest.raises(NotADirectoryError):
        call(mcp, "file_scan", path=str(f))


def test_categories_helper():
    _, mcp = build_agent(FileAgent)
    cats = call(mcp, "file_categories")
    assert ".pdf" in cats["documents"]
    assert ".png" in cats["images"]
