"""Tests for the JsonStore persistence layer."""

from __future__ import annotations

import json

import pytest

from mcp_multi_agent.storage import JsonStore


def test_default_initialization(tmp_path):
    p = tmp_path / "x.json"
    s = JsonStore(p, default={"items": []})
    assert p.exists()
    assert s.load() == {"items": []}


def test_save_and_load_roundtrip(tmp_path):
    p = tmp_path / "x.json"
    s = JsonStore(p, default={})
    s.save({"a": 1, "b": [1, 2, 3]})
    assert s.load() == {"a": 1, "b": [1, 2, 3]}


def test_update_callback_atomic(tmp_path):
    p = tmp_path / "x.json"
    s = JsonStore(p, default={"n": 0})

    def inc(d):
        d["n"] += 1
        return d

    for _ in range(5):
        s.update(inc)
    assert s.load() == {"n": 5}


def test_corrupted_file_recovers_to_default(tmp_path):
    p = tmp_path / "x.json"
    s = JsonStore(p, default={"items": []})
    p.write_text("not valid json {[", encoding="utf-8")
    # First load should recover
    assert s.load() == {"items": []}


def test_atomic_write_does_not_leave_partial(tmp_path):
    p = tmp_path / "x.json"
    s = JsonStore(p, default={})
    s.save({"hello": "world"})
    # No leftover temp files
    leftovers = [f for f in tmp_path.iterdir() if f.name.startswith("x.json.")]
    assert leftovers == []
    # File is valid JSON
    assert json.loads(p.read_text(encoding="utf-8")) == {"hello": "world"}
