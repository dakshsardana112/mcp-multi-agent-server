"""Tests for the finance agent."""

from __future__ import annotations

from datetime import date

import pytest

from mcp_multi_agent.agents.finance_agent import FinanceAgent
from tests._helpers import build_agent, call


def test_add_expense_normalizes_category():
    _, mcp = build_agent(FinanceAgent)
    e = call(mcp, "finance_add_expense", amount=12.5, category="  Food ")
    assert e["category"] == "food"
    assert e["amount"] == 12.5


def test_add_rejects_non_positive_amount():
    _, mcp = build_agent(FinanceAgent)
    with pytest.raises(ValueError):
        call(mcp, "finance_add_expense", amount=0, category="x")
    with pytest.raises(ValueError):
        call(mcp, "finance_add_expense", amount=-5, category="x")


def test_list_filter_by_category_and_month():
    _, mcp = build_agent(FinanceAgent)
    call(mcp, "finance_add_expense", amount=10, category="food", on_date="2026-01-05")
    call(mcp, "finance_add_expense", amount=20, category="food", on_date="2026-02-05")
    call(mcp, "finance_add_expense", amount=30, category="rent", on_date="2026-02-05")
    jan_food = call(mcp, "finance_list_expenses", category="food", month="2026-01")
    assert len(jan_food) == 1 and jan_food[0]["amount"] == 10
    feb_all = call(mcp, "finance_list_expenses", month="2026-02")
    assert len(feb_all) == 2


def test_budget_set_and_summary():
    _, mcp = build_agent(FinanceAgent)
    month = date.today().isoformat()[:7]
    call(mcp, "finance_set_budget", category="food", monthly_limit=200)
    call(mcp, "finance_add_expense", amount=50, category="food")
    summary = call(mcp, "finance_summary", month=month)
    food = next(c for c in summary["categories"] if c["category"] == "food")
    assert food["spent"] == 50
    assert food["limit"] == 200
    assert food["remaining"] == 150
    assert food["pct_used"] == 25.0


def test_delete_expense():
    _, mcp = build_agent(FinanceAgent)
    e = call(mcp, "finance_add_expense", amount=10, category="food")
    call(mcp, "finance_delete_expense", expense_id=e["id"])
    assert call(mcp, "finance_list_expenses") == []


def test_delete_unknown_raises():
    _, mcp = build_agent(FinanceAgent)
    with pytest.raises(KeyError):
        call(mcp, "finance_delete_expense", expense_id="missing")


def test_bad_month_format():
    _, mcp = build_agent(FinanceAgent)
    with pytest.raises(ValueError):
        call(mcp, "finance_summary", month="2026/01")
