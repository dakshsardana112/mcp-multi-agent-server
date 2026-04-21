"""Knowledge-base agent.

A very small Q&A store. You add ``{question, answer, tags}`` entries,
then ``search`` scores them against a query using simple word overlap.
Good enough to show the *shape* of a retrieval tool without pulling in
embeddings or a vector DB.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, List, Optional

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _tokens(s: str) -> set[str]:
    return {t.lower() for t in _WORD_RE.findall(s or "") if len(t) > 1}


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class KnowledgeBaseAgent(BaseAgent):
    name = "kb"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store("knowledge_base.json", default={"entries": []})

    def _all(self) -> list[dict[str, Any]]:
        return list(self.store.load().get("entries", []))

    def _save(self, entries: list[dict[str, Any]]) -> None:
        self.store.save({"entries": entries})

    def register(self, mcp: FastMCP) -> None:
        agent = self

        @mcp.tool()
        def kb_add(
            question: str,
            answer: str,
            tags: Optional[List[str]] = None,
        ) -> dict[str, Any]:
            """Add a new Q&A entry."""
            if not question.strip():
                raise ValueError("question cannot be empty")
            if not answer.strip():
                raise ValueError("answer cannot be empty")
            entry = {
                "id": uuid.uuid4().hex[:8],
                "question": question.strip(),
                "answer": answer.strip(),
                "tags": [t.strip().lower() for t in (tags or []) if t and t.strip()],
                "created_at": _now_iso(),
            }
            entries = agent._all()
            entries.append(entry)
            agent._save(entries)
            return entry

        @mcp.tool()
        def kb_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
            """Word-overlap search. Returns up to ``limit`` entries with scores."""
            if not query.strip():
                raise ValueError("query cannot be empty")
            if not 1 <= limit <= 50:
                raise ValueError("limit must be between 1 and 50")
            q_tokens = _tokens(query)
            scored: list[tuple[float, dict[str, Any]]] = []
            for entry in agent._all():
                e_tokens = _tokens(entry["question"] + " " + entry["answer"])
                e_tokens |= {t.lower() for t in entry.get("tags", [])}
                if not e_tokens:
                    continue
                overlap = len(q_tokens & e_tokens)
                if overlap == 0:
                    continue
                score = overlap / max(len(q_tokens), 1)
                scored.append((score, entry))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [
                {**entry, "score": round(score, 3)} for score, entry in scored[:limit]
            ]

        @mcp.tool()
        def kb_list(tag: Optional[str] = None) -> list[dict[str, Any]]:
            """List all entries, optionally filtered by tag."""
            entries = agent._all()
            if tag:
                tag_l = tag.strip().lower()
                entries = [e for e in entries if tag_l in e.get("tags", [])]
            return entries

        @mcp.tool()
        def kb_get(entry_id: str) -> dict[str, Any]:
            """Fetch a single entry by id."""
            for e in agent._all():
                if e["id"] == entry_id:
                    return e
            raise KeyError(f"no KB entry with id '{entry_id}'")

        @mcp.tool()
        def kb_delete(entry_id: str) -> dict[str, Any]:
            """Delete a KB entry."""
            entries = agent._all()
            new = [e for e in entries if e["id"] != entry_id]
            if len(new) == len(entries):
                raise KeyError(f"no KB entry with id '{entry_id}'")
            agent._save(new)
            return {"deleted": True, "id": entry_id}

        @mcp.resource("kb://all")
        def kb_resource_all() -> str:
            """Resource: JSON dump of every KB entry."""
            import json

            return json.dumps({"entries": agent._all()}, indent=2)

        @mcp.prompt()
        def kb_answer_prompt(question: str) -> str:
            """Prompt: answer using the KB or say you don't know."""
            return (
                f"Call `kb_search` with query={question!r} and use the top hit "
                "to answer. If nothing is relevant, say you don't know and "
                "suggest adding the answer via `kb_add`."
            )
