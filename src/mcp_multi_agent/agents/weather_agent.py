"""Weather agent.

This one doesn't hit a real API - instead it uses a deterministic pseudo-
random generator seeded by (city, date) so the same inputs always give the
same numbers. That keeps the learning project self-contained (no API keys
required) while still demonstrating the *pattern* of an external-data
agent: same interface, different source.

If you later want real data, swap `_mock_forecast` for a call to
openweathermap / open-meteo / whatever, and the tool signatures don't
change. That's the point.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from .base import BaseAgent

CONDITIONS = [
    "sunny",
    "partly cloudy",
    "cloudy",
    "light rain",
    "heavy rain",
    "thunderstorm",
    "snow",
    "fog",
]


def _seed_for(city: str, day: str) -> int:
    h = hashlib.sha256(f"{city.lower()}|{day}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _mock_forecast(city: str, day: str) -> dict[str, Any]:
    rnd = random.Random(_seed_for(city, day))
    base_c = rnd.uniform(-5, 30)  # temperature in C
    temp_c = round(base_c, 1)
    # Derive °F from the *rounded* °C so conversions are self-consistent
    # (callers that round-trip °C → °F → °C shouldn't see drift).
    return {
        "city": city,
        "date": day,
        "condition": rnd.choice(CONDITIONS),
        "temp_c": temp_c,
        "temp_f": round(temp_c * 9 / 5 + 32, 1),
        "humidity_pct": rnd.randint(20, 95),
        "wind_kph": round(rnd.uniform(0, 40), 1),
    }


class WeatherAgent(BaseAgent):
    name = "weather"

    def __init__(self) -> None:
        super().__init__()
        self.store = self.make_store(
            "weather_history.json", default={"queries": []}
        )

    def register(self, mcp: FastMCP) -> None:
        agent = self

        @mcp.tool()
        def weather_current(city: str) -> dict[str, Any]:
            """Get today's weather for a city (mock data, deterministic)."""
            if not city or not city.strip():
                raise ValueError("city cannot be empty")
            today = date.today().isoformat()
            result = _mock_forecast(city.strip(), today)

            # Remember the query so you can see how tool calls are traced.
            def _push(cur):
                cur.setdefault("queries", []).append(
                    {"city": city.strip(), "date": today, "kind": "current"}
                )
                # keep the last 100 queries only
                cur["queries"] = cur["queries"][-100:]
                return cur

            agent.store.update(_push)
            return result

        @mcp.tool()
        def weather_forecast(city: str, days: int = 3) -> list[dict[str, Any]]:
            """Multi-day mock forecast starting today. ``days`` between 1 and 14."""
            if not city.strip():
                raise ValueError("city cannot be empty")
            if not 1 <= days <= 14:
                raise ValueError("days must be between 1 and 14")
            today = date.today()
            return [
                _mock_forecast(city.strip(), (today + timedelta(days=i)).isoformat())
                for i in range(days)
            ]

        @mcp.tool()
        def weather_compare(cities: list[str]) -> list[dict[str, Any]]:
            """Compare today's weather across multiple cities."""
            if not cities:
                raise ValueError("cities list cannot be empty")
            today = date.today().isoformat()
            return [_mock_forecast(c.strip(), today) for c in cities if c.strip()]

        @mcp.tool()
        def weather_history() -> list[dict[str, Any]]:
            """Recently queried cities (last 100). Useful for debugging/demo."""
            return list(agent.store.load().get("queries", []))

        @mcp.prompt()
        def weather_outfit_prompt(city: str) -> str:
            """Prompt template: ask the model to suggest an outfit given the forecast."""
            return (
                f"Use `weather_forecast` with city={city!r} and days=3, "
                "then suggest an outfit for each day. Be practical, not flowery."
            )
