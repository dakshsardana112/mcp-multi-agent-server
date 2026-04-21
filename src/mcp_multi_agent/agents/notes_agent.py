"""Notes agent.

A lightweight "Evernote for one person". Each note has an id, title, body,
list of tags, and timestamps. Search is naive substring matching across
title + body + tags, which is perfectly fine for a learning project.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _clean_tags(tags: Optional[List[str]]) -> List[str]:
    if not tags:
        return []
    seen = []
    for t in tags:
        t = (t or "").strip().lower()
        if t and t not in seen:
            seen.append(t)
    return seen


class NotesAgent(BaseAgent):
    name = "notes"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store("notes.json", default={"notes": []})

    def _all(self) -> list[dict[str, Any]]:
        return list(self.store.load().get("notes", []))

    def _save(self, notes: list[dict[str, Any]]) -> None:
        self.store.save({"notes": notes})

    def register(self, mcp: FastMCP) -> None:
        agent = self

        @mcp.tool()
        def notes_create(
            title: str,
            body: str,
            tags: Optional[List[str]] = None,
        ) -> dict[str, Any]:
            """Create a new note. Tags are normalized (lowercase, deduped)."""
            if not title.strip():
                raise ValueError("title cannot be empty")
            note = {
                "id": uuid.uuid4().hex[:8],
                "title": title.strip(),
                "body": body,
                "tags": _clean_tags(tags),
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            notes = agent._all()
            notes.append(note)
            agent._save(notes)
            return note

        @mcp.tool()
        def notes_list(tag: Optional[str] = None) -> list[dict[str, Any]]:
            """List all notes. Optional ``tag`` filter (exact match)."""
            notes = agent._all()
            if tag:
                tag_l = tag.strip().lower()
                notes = [n for n in notes if tag_l in n.get("tags", [])]
            notes.sort(key=lambda n: n["updated_at"], reverse=True)
            return notes

        @mcp.tool()
        def notes_search(query: str) -> list[dict[str, Any]]:
            """Case-insensitive substring search across title, body, and tags."""
            q = (query or "").strip().lower()
            if not q:
                raise ValueError("query cannot be empty")
            out = []
            for n in agent._all():
                hay = " ".join(
                    [n["title"], n["body"], " ".join(n.get("tags", []))]
                ).lower()
                if q in hay:
                    out.append(n)
            return out

        @mcp.tool()
        def notes_get(note_id: str) -> dict[str, Any]:
            """Fetch a single note by id."""
            for n in agent._all():
                if n["id"] == note_id:
                    return n
            raise KeyError(f"no note with id '{note_id}'")

        @mcp.tool()
        def notes_update(
            note_id: str,
            title: Optional[str] = None,
            body: Optional[str] = None,
            tags: Optional[List[str]] = None,
        ) -> dict[str, Any]:
            """Partial update on a note."""
            notes = agent._all()
            for n in notes:
                if n["id"] == note_id:
                    if title is not None:
                        if not title.strip():
                            raise ValueError("title cannot be empty")
                        n["title"] = title.strip()
                    if body is not None:
                        n["body"] = body
                    if tags is not None:
                        n["tags"] = _clean_tags(tags)
                    n["updated_at"] = _now_iso()
                    agent._save(notes)
                    return n
            raise KeyError(f"no note with id '{note_id}'")

        @mcp.tool()
        def notes_delete(note_id: str) -> dict[str, Any]:
            """Delete a note. Returns ``{deleted: True, id: ...}``."""
            notes = agent._all()
            new = [n for n in notes if n["id"] != note_id]
            if len(new) == len(notes):
                raise KeyError(f"no note with id '{note_id}'")
            agent._save(new)
            return {"deleted": True, "id": note_id}

        @mcp.tool()
        def notes_tags() -> list[dict[str, Any]]:
            """All tags in use with counts, sorted by frequency."""
            counts: dict[str, int] = {}
            for n in agent._all():
                for t in n.get("tags", []):
                    counts[t] = counts.get(t, 0) + 1
            return sorted(
                [{"tag": k, "count": v} for k, v in counts.items()],
                key=lambda x: (-x["count"], x["tag"]),
            )

        @mcp.resource("notes://all")
        def notes_resource_all() -> str:
            """Resource: full JSON dump of every note."""
            import json

            return json.dumps({"notes": agent._all()}, indent=2)
