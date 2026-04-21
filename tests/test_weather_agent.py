"""Tests for the weather agent (deterministic mock data)."""

from __future__ import annotations

import pytest

from mcp_multi_agent.agents.weather_agent import WeatherAgent
from tests._helpers import build_agent, call


def test_current_weather_is_deterministic():
    _, mcp = build_agent(WeatherAgent)
    a = call(mcp, "weather_current", city="Mumbai")
    b = call(mcp, "weather_current", city="Mumbai")
    # Same day + same city → identical forecast (shape + values)
    for k in ("condition", "temp_c", "humidity_pct", "wind_kph"):
        assert a[k] == b[k]
    assert a["temp_f"] == round(a["temp_c"] * 9 / 5 + 32, 1)


def test_forecast_length():
    _, mcp = build_agent(WeatherAgent)
    f = call(mcp, "weather_forecast", city="Delhi", days=5)
    assert len(f) == 5
    assert {x["city"] for x in f} == {"Delhi"}


def test_forecast_days_bounds():
    _, mcp = build_agent(WeatherAgent)
    with pytest.raises(ValueError):
        call(mcp, "weather_forecast", city="X", days=0)
    with pytest.raises(ValueError):
        call(mcp, "weather_forecast", city="X", days=20)


def test_compare_multiple_cities():
    _, mcp = build_agent(WeatherAgent)
    out = call(mcp, "weather_compare", cities=["A", "B", "C"])
    assert {o["city"] for o in out} == {"A", "B", "C"}


def test_compare_empty_list_raises():
    _, mcp = build_agent(WeatherAgent)
    with pytest.raises(ValueError):
        call(mcp, "weather_compare", cities=[])


def test_history_records_queries():
    _, mcp = build_agent(WeatherAgent)
    call(mcp, "weather_current", city="Jaipur")
    call(mcp, "weather_current", city="Pune")
    hist = call(mcp, "weather_history")
    cities = [h["city"] for h in hist]
    assert "Jaipur" in cities and "Pune" in cities
