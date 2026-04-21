"""Tests for the task agent."""

from __future__ import annotations

import pytest

from mcp_multi_agent.agents.task_agent import TaskAgent
from tests._helpers import build_agent, call


def test_add_and_list_tasks():
    _, mcp = build_agent(TaskAgent)
    t1 = call(mcp, "task_add", title="write tests", priority="high")
    t2 = call(mcp, "task_add", title="read docs")
    assert t1["status"] == "open"
    assert t1["priority"] == "high"
    assert t2["priority"] == "medium"
    listed = call(mcp, "task_list")
    assert len(listed) == 2


def test_add_rejects_blank_title():
    _, mcp = build_agent(TaskAgent)
    with pytest.raises(ValueError):
        call(mcp, "task_add", title="   ")


def test_add_rejects_bad_priority():
    _, mcp = build_agent(TaskAgent)
    with pytest.raises(ValueError):
        call(mcp, "task_add", title="x", priority="urgent")


def test_add_rejects_bad_due():
    _, mcp = build_agent(TaskAgent)
    with pytest.raises(ValueError):
        call(mcp, "task_add", title="x", due="2025-13-40")


def test_complete_task():
    _, mcp = build_agent(TaskAgent)
    t = call(mcp, "task_add", title="x")
    done = call(mcp, "task_complete", task_id=t["id"])
    assert done["status"] == "done"


def test_complete_unknown_raises():
    _, mcp = build_agent(TaskAgent)
    with pytest.raises(KeyError):
        call(mcp, "task_complete", task_id="deadbeef")


def test_update_partial():
    _, mcp = build_agent(TaskAgent)
    t = call(mcp, "task_add", title="x")
    upd = call(mcp, "task_update", task_id=t["id"], priority="low", notes="later")
    assert upd["priority"] == "low"
    assert upd["notes"] == "later"
    assert upd["title"] == "x"


def test_update_no_fields_raises():
    _, mcp = build_agent(TaskAgent)
    t = call(mcp, "task_add", title="x")
    with pytest.raises(ValueError):
        call(mcp, "task_update", task_id=t["id"])


def test_delete():
    _, mcp = build_agent(TaskAgent)
    t = call(mcp, "task_add", title="x")
    out = call(mcp, "task_delete", task_id=t["id"])
    assert out["deleted"] is True
    assert call(mcp, "task_list") == []


def test_filter_by_status_and_priority():
    _, mcp = build_agent(TaskAgent)
    t1 = call(mcp, "task_add", title="a", priority="high")
    t2 = call(mcp, "task_add", title="b", priority="low")
    call(mcp, "task_complete", task_id=t1["id"])
    open_low = call(mcp, "task_list", status="open", priority="low")
    assert len(open_low) == 1 and open_low[0]["id"] == t2["id"]
    done = call(mcp, "task_list", status="done")
    assert len(done) == 1 and done[0]["id"] == t1["id"]


def test_stats_counts_and_overdue():
    _, mcp = build_agent(TaskAgent)
    call(mcp, "task_add", title="past due", due="2020-01-01")
    call(mcp, "task_add", title="fine", due="2099-01-01")
    call(mcp, "task_add", title="no due")
    stats = call(mcp, "task_stats")
    assert stats["total"] == 3
    assert stats["overdue"] == 1
