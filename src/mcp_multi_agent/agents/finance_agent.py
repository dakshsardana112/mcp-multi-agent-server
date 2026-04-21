"""Finance agent.

Personal-finance toy. Track expenses by category, set monthly budgets,
and get quick summaries. Amounts are plain floats (no currency conversion,
no decimal-vs-float pedantry) because this is a learning project.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent


def _today() -> str:
    return date.today().isoformat()


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class FinanceAgent(BaseAgent):
    name = "finance"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store(
            "finance.json",
            default={"expenses": [], "budgets": {}},
        )

    # -------------------------------------------------------------- helpers
    def _load(self) -> dict[str, Any]:
        data = self.store.load()
        data.setdefault("expenses", [])
        data.setdefault("budgets", {})
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.store.save(data)

    # ------------------------------------------------------------- register
    def register(self, mcp: FastMCP) -> None:
        agent = self

        @mcp.tool()
        def finance_add_expense(
            amount: float,
            category: str,
            note: str = "",
            on_date: Optional[str] = None,
        ) -> dict[str, Any]:
            """Log an expense. ``on_date`` defaults to today (YYYY-MM-DD)."""
            if amount <= 0:
                raise ValueError("amount must be positive")
            if not category.strip():
                raise ValueError("category cannot be empty")
            if on_date:
                try:
                    date.fromisoformat(on_date)
                except ValueError as e:
                    raise ValueError(f"on_date must be YYYY-MM-DD, got {on_date!r}") from e
            data = agent._load()
            expense = {
                "id": uuid.uuid4().hex[:8],
                "amount": round(float(amount), 2),
                "category": category.strip().lower(),
                "note": note,
                "date": on_date or _today(),
                "created_at": _now_iso(),
            }
            data["expenses"].append(expense)
            agent._save(data)
            return expense

        @mcp.tool()
        def finance_list_expenses(
            category: Optional[str] = None,
            month: Optional[str] = None,
        ) -> list[dict[str, Any]]:
            """List expenses, optionally filtered by category and/or ``YYYY-MM`` month."""
            expenses = agent._load()["expenses"]
            if category:
                expenses = [e for e in expenses if e["category"] == category.strip().lower()]
            if month:
                if len(month) != 7 or month[4] != "-":
                    raise ValueError("month must be in YYYY-MM format")
                expenses = [e for e in expenses if e["date"].startswith(month)]
            return sorted(expenses, key=lambda e: e["date"], reverse=True)

        @mcp.tool()
        def finance_set_budget(category: str, monthly_limit: float) -> dict[str, Any]:
            """Set (or replace) the monthly budget cap for a category."""
            if monthly_limit < 0:
                raise ValueError("monthly_limit cannot be negative")
            if not category.strip():
                raise ValueError("category cannot be empty")
            cat = category.strip().lower()
            data = agent._load()
            data["budgets"][cat] = round(float(monthly_limit), 2)
            agent._save(data)
            return {"category": cat, "monthly_limit": data["budgets"][cat]}

        @mcp.tool()
        def finance_summary(month: Optional[str] = None) -> dict[str, Any]:
            """Totals for the given month (defaults to current month). Includes
            per-category spend, budget usage %, and remaining budget."""
            if month is None:
                month = _today()[:7]
            if len(month) != 7 or month[4] != "-":
                raise ValueError("month must be in YYYY-MM format")
            data = agent._load()
            expenses = [e for e in data["expenses"] if e["date"].startswith(month)]
            by_cat: dict[str, float] = {}
            for e in expenses:
                by_cat[e["category"]] = round(by_cat.get(e["category"], 0.0) + e["amount"], 2)
            budgets = data["budgets"]
            usage = []
            for cat in sorted(set(list(by_cat.keys()) + list(budgets.keys()))):
                spent = round(by_cat.get(cat, 0.0), 2)
                limit = budgets.get(cat)
                entry: dict[str, Any] = {
                    "category": cat,
                    "spent": spent,
                    "limit": limit,
                }
                if limit is not None:
                    entry["remaining"] = round(limit - spent, 2)
                    entry["pct_used"] = round(100.0 * spent / limit, 1) if limit > 0 else None
                usage.append(entry)
            return {
                "month": month,
                "total_spent": round(sum(by_cat.values()), 2),
                "expense_count": len(expenses),
                "categories": usage,
            }

        @mcp.tool()
        def finance_delete_expense(expense_id: str) -> dict[str, Any]:
            """Remove a single expense by id."""
            data = agent._load()
            new = [e for e in data["expenses"] if e["id"] != expense_id]
            if len(new) == len(data["expenses"]):
                raise KeyError(f"no expense with id '{expense_id}'")
            data["expenses"] = new
            agent._save(data)
            return {"deleted": True, "id": expense_id}

        @mcp.resource("finance://summary/current")
        def finance_current_summary_resource() -> str:
            """Resource: JSON summary for the current month."""
            import json
            month = _today()[:7]
            data = agent._load()
            expenses = [e for e in data["expenses"] if e["date"].startswith(month)]
            return json.dumps(
                {
                    "month": month,
                    "total": round(sum(e["amount"] for e in expenses), 2),
                    "count": len(expenses),
                },
                indent=2,
            )
