"""Tests for the knowledge-base agent."""

from __future__ import annotations

import pytest

from mcp_multi_agent.agents.kb_agent import KnowledgeBaseAgent
from tests._helpers import build_agent, call


def test_add_and_search():
    _, mcp = build_agent(KnowledgeBaseAgent)
    call(mcp, "kb_add",
         question="What is MCP?",
         answer="Model Context Protocol is an open standard for connecting tools to models.",
         tags=["mcp", "protocol"])
    call(mcp, "kb_add",
         question="How do I install Python?",
         answer="Go to python.org and download the latest release.",
         tags=["python"])
    hits = call(mcp, "kb_search", query="model context protocol")
    assert len(hits) >= 1
    assert "MCP" in hits[0]["question"]
    assert hits[0]["score"] > 0


def test_search_zero_matches_returns_empty():
    _, mcp = build_agent(KnowledgeBaseAgent)
    call(mcp, "kb_add", question="Q", answer="A")
    assert call(mcp, "kb_search", query="xyz-nonexistent-term") == []


def test_add_empty_question_rejected():
    _, mcp = build_agent(KnowledgeBaseAgent)
    with pytest.raises(ValueError):
        call(mcp, "kb_add", question="   ", answer="ans")


def test_search_empty_query_rejected():
    _, mcp = build_agent(KnowledgeBaseAgent)
    with pytest.raises(ValueError):
        call(mcp, "kb_search", query="")


def test_search_limit_bounds():
    _, mcp = build_agent(KnowledgeBaseAgent)
    with pytest.raises(ValueError):
        call(mcp, "kb_search", query="x", limit=0)
    with pytest.raises(ValueError):
        call(mcp, "kb_search", query="x", limit=999)


def test_delete_entry():
    _, mcp = build_agent(KnowledgeBaseAgent)
    e = call(mcp, "kb_add", question="q?", answer="a")
    call(mcp, "kb_delete", entry_id=e["id"])
    with pytest.raises(KeyError):
        call(mcp, "kb_get", entry_id=e["id"])


def test_list_filter_by_tag():
    _, mcp = build_agent(KnowledgeBaseAgent)
    call(mcp, "kb_add", question="q1", answer="a1", tags=["x"])
    call(mcp, "kb_add", question="q2", answer="a2", tags=["y"])
    x_only = call(mcp, "kb_list", tag="x")
    assert len(x_only) == 1 and x_only[0]["tags"] == ["x"]
