"""Tests for the notes agent."""

from __future__ import annotations

import pytest

from mcp_multi_agent.agents.notes_agent import NotesAgent
from tests._helpers import build_agent, call


def test_create_and_get():
    _, mcp = build_agent(NotesAgent)
    n = call(mcp, "notes_create", title="Ideas", body="build cool stuff", tags=["Work", "work", "ideas"])
    # tags normalised
    assert n["tags"] == ["work", "ideas"]
    got = call(mcp, "notes_get", note_id=n["id"])
    assert got["id"] == n["id"]


def test_empty_title_rejected():
    _, mcp = build_agent(NotesAgent)
    with pytest.raises(ValueError):
        call(mcp, "notes_create", title="  ", body="x")


def test_search_substring_case_insensitive():
    _, mcp = build_agent(NotesAgent)
    call(mcp, "notes_create", title="Groceries", body="buy Milk", tags=["shopping"])
    call(mcp, "notes_create", title="Ideas", body="maybe later", tags=["brainstorm"])
    hits = call(mcp, "notes_search", query="milk")
    assert len(hits) == 1 and hits[0]["title"] == "Groceries"
    # tag match
    hits2 = call(mcp, "notes_search", query="brainstorm")
    assert len(hits2) == 1


def test_search_empty_query_raises():
    _, mcp = build_agent(NotesAgent)
    with pytest.raises(ValueError):
        call(mcp, "notes_search", query="  ")


def test_update_and_delete():
    _, mcp = build_agent(NotesAgent)
    n = call(mcp, "notes_create", title="T", body="B")
    upd = call(mcp, "notes_update", note_id=n["id"], body="new body", tags=["x"])
    assert upd["body"] == "new body"
    assert upd["tags"] == ["x"]
    out = call(mcp, "notes_delete", note_id=n["id"])
    assert out["deleted"] is True
    with pytest.raises(KeyError):
        call(mcp, "notes_get", note_id=n["id"])


def test_tags_aggregation():
    _, mcp = build_agent(NotesAgent)
    call(mcp, "notes_create", title="a", body="a", tags=["x", "y"])
    call(mcp, "notes_create", title="b", body="b", tags=["x"])
    tags = call(mcp, "notes_tags")
    as_dict = {t["tag"]: t["count"] for t in tags}
    assert as_dict == {"x": 2, "y": 1}
