"""Weather agent (mock, deterministic). See _mock_forecast for how it generates values."""
from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent

CONDITIONS = ["sunny", "partly cloudy", "cloudy", "light rain", "heavy rain",
              "thunderstorm", "snow", "fog"]


def _seed_for(city: str, day: str) -> int:
    h = hashlib.sha256(f"{city.lower()}|{day}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _mock_forecast(city: str, day: str) -> dict[str, Any]:
    rnd = random.Random(_seed_for(city, day))
    base_c = rnd.uniform(-5, 30)
    return {
        "city": city,
        "date": day,
        "condition": rnd.choice(CONDITIONS),
        "temp_c": round(base_c, 1),
        "temp_f": round(base_c * 9 / 5 + 32, 1),
        "humidity_pct": rnd.randint(20, 95),
        "wind_kph": round(rnd.uniform(0, 40), 1),
    }


class WeatherAgent(BaseAgent):
    name = "weather"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store("weather_history.json", default={"queries": []})

    def register(self, mcp: FastMCP) -> None:
        agent = self

        @mcp.tool()
        def weather_current(city: str) -> dict[str, Any]:
            if not city or not city.strip():
                raise ValueError("city cannot be empty")
            today = date.today().isoformat()
            result = _mock_forecast(city.strip(), today)
            def _push(cur):
                cur.setdefault("queries", []).append(
                    {"city": city.strip(), "date": today, "kind": "current"}
                )
                cur["queries"] = cur["queries"][-100:]
                return cur
            agent.store.update(_push)
            return result

        @mcp.tool()
        def weather_forecast(city: str, days: int = 3) -> list[dict[str, Any]]:
            if not city.strip():
                raise ValueError("city cannot be empty")
            if not 1 <= days <= 14:
                raise ValueError("days must be between 1 and 14")
            today = date.today()
            return [_mock_forecast(city.strip(), (today + timedelta(days=i)).isoformat())
                    for i in range(days)]

        @mcp.tool()
        def weather_compare(cities: list[str]) -> list[dict[str, Any]]:
            if not cities:
                raise ValueError("cities list cannot be empty")
            today = date.today().isoformat()
            return [_mock_forecast(c.strip(), today) for c in cities if c.strip()]

        @mcp.tool()
        def weather_history() -> list[dict[str, Any]]:
            return list(agent.store.load().get("queries", []))

        @mcp.prompt()
        def weather_outfit_prompt(city: str) -> str:
            return (f"Use `weather_forecast` with city={city!r} and days=3, "
                    "then suggest an outfit for each day. Be practical, not flowery.")
