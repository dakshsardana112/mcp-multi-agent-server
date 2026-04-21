"""Task / todo agent.

Owns a list of tasks. Each task has an id, title, status, priority,
optional due date, and timestamps. Tools cover the full lifecycle:
add, list (with filters), complete, update, delete.
"""

from __future__ import annotations

import time
import uuid
from datetime import date, datetime
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent

VALID_STATUS = ("open", "in_progress", "done")
VALID_PRIORITY = ("low", "medium", "high")


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _parse_due(value: Optional[str]) -> Optional[str]:
    """Accept YYYY-MM-DD or full ISO; return canonical YYYY-MM-DD. None -> None."""
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError as e:
        raise ValueError(
            f"due date '{value}' is not a valid YYYY-MM-DD date"
        ) from e


class TaskAgent(BaseAgent):
    name = "task"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store("tasks.json", default={"tasks": []})

    # ------------------------------------------------------------- internals
    def _all(self) -> list[dict[str, Any]]:
        return list(self.store.load().get("tasks", []))

    def _save(self, tasks: list[dict[str, Any]]) -> None:
        self.store.save({"tasks": tasks})

    # -------------------------------------------------------------- register
    def register(self, mcp: FastMCP) -> None:
        agent = self  # captured by closures below

        @mcp.tool()
        def task_add(
            title: str,
            priority: str = "medium",
            due: Optional[str] = None,
            notes: str = "",
        ) -> dict[str, Any]:
            """Create a new task. Returns the created task.

            Args:
                title: Short description of what needs to be done.
                priority: One of low, medium, high. Default medium.
                due: Optional due date as YYYY-MM-DD.
                notes: Optional free-text notes.
            """
            if not title or not title.strip():
                raise ValueError("title cannot be empty")
            if priority not in VALID_PRIORITY:
                raise ValueError(
                    f"priority must be one of {VALID_PRIORITY}, got {priority!r}"
                )
            task = {
                "id": uuid.uuid4().hex[:8],
                "title": title.strip(),
                "status": "open",
                "priority": priority,
                "due": _parse_due(due),
                "notes": notes,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            tasks = agent._all()
            tasks.append(task)
            agent._save(tasks)
            return task

        @mcp.tool()
        def task_list(
            status: Optional[str] = None,
            priority: Optional[str] = None,
        ) -> list[dict[str, Any]]:
            """List tasks, optionally filtered by status and/or priority."""
            if status is not None and status not in VALID_STATUS:
                raise ValueError(f"status must be one of {VALID_STATUS}")
            if priority is not None and priority not in VALID_PRIORITY:
                raise ValueError(f"priority must be one of {VALID_PRIORITY}")
            results = agent._all()
            if status is not None:
                results = [t for t in results if t["status"] == status]
            if priority is not None:
                results = [t for t in results if t["priority"] == priority]
            # Sort: open first, then by priority (high→low), then by due date.
            order = {"open": 0, "in_progress": 1, "done": 2}
            pri = {"high": 0, "medium": 1, "low": 2}
            results.sort(
                key=lambda t: (
                    order.get(t["status"], 9),
                    pri.get(t["priority"], 9),
                    t.get("due") or "9999-12-31",
                )
            )
            return results

        @mcp.tool()
        def task_complete(task_id: str) -> dict[str, Any]:
            """Mark a task as done. Returns the updated task."""
            return _mutate(agent, task_id, {"status": "done"})

        @mcp.tool()
        def task_update(
            task_id: str,
            title: Optional[str] = None,
            status: Optional[str] = None,
            priority: Optional[str] = None,
            due: Optional[str] = None,
            notes: Optional[str] = None,
        ) -> dict[str, Any]:
            """Partial update. Only fields you pass are changed."""
            patch: dict[str, Any] = {}
            if title is not None:
                if not title.strip():
                    raise ValueError("title cannot be empty")
                patch["title"] = title.strip()
            if status is not None:
                if status not in VALID_STATUS:
                    raise ValueError(f"status must be one of {VALID_STATUS}")
                patch["status"] = status
            if priority is not None:
                if priority not in VALID_PRIORITY:
                    raise ValueError(f"priority must be one of {VALID_PRIORITY}")
                patch["priority"] = priority
            if due is not None:
                patch["due"] = _parse_due(due) if due != "" else None
            if notes is not None:
                patch["notes"] = notes
            if not patch:
                raise ValueError("no fields supplied to update")
            return _mutate(agent, task_id, patch)

        @mcp.tool()
        def task_delete(task_id: str) -> dict[str, Any]:
            """Delete a task by id. Returns ``{deleted: True, id: ...}``."""
            tasks = agent._all()
            new_tasks = [t for t in tasks if t["id"] != task_id]
            if len(new_tasks) == len(tasks):
                raise KeyError(f"no task with id '{task_id}'")
            agent._save(new_tasks)
            return {"deleted": True, "id": task_id}

        @mcp.tool()
        def task_stats() -> dict[str, Any]:
            """Aggregate counts: total, by status, by priority, overdue."""
            tasks = agent._all()
            today = date.today().isoformat()
            by_status = {s: 0 for s in VALID_STATUS}
            by_priority = {p: 0 for p in VALID_PRIORITY}
            overdue = 0
            for t in tasks:
                by_status[t["status"]] = by_status.get(t["status"], 0) + 1
                by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
                if t["status"] != "done" and t.get("due") and t["due"] < today:
                    overdue += 1
            return {
                "total": len(tasks),
                "by_status": by_status,
                "by_priority": by_priority,
                "overdue": overdue,
            }

        @mcp.resource("task://all")
        def task_resource_all() -> str:
            """Resource: full JSON dump of every task."""
            import json

            return json.dumps({"tasks": agent._all()}, indent=2)

        @mcp.prompt()
        def task_review_prompt() -> str:
            """Prompt template that asks the model to review the task list."""
            return (
                "Review my open tasks (call `task_list` with status='open'). "
                "Suggest which 3 to tackle first based on priority and due date, "
                "and explain your reasoning briefly."
            )


def _mutate(agent: TaskAgent, task_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    """Apply a patch to the task with id ``task_id``. Returns the new record."""
    tasks = agent._all()
    for t in tasks:
        if t["id"] == task_id:
            t.update(patch)
            t["updated_at"] = _now_iso()
            agent._save(tasks)
            return t
    raise KeyError(f"no task with id '{task_id}'")
