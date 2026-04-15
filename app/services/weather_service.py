"""
Weather service.
Uses OpenWeatherMap if OPENWEATHER_API_KEY is set in .env.
Falls back to simulated city-specific weather — works fully offline.
"""

import logging
import random
from typing import Dict, Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Simulated defaults (offline / no API key)
_CITY_WEATHER: Dict[str, str] = {
    "Paris":      "partly cloudy",
    "Rome":       "sunny",
    "Dubai":      "hot and sunny",
    "Kuta":       "tropical showers",
    "Tabanan":    "partly cloudy",
    "Ubud":       "tropical showers",
    "Tokyo":      "mild and clear",
    "Chennai":    "hot and humid",
    "Calangute":  "sunny",
    "Old Goa":    "sunny",
    "Baga":       "sunny",
    "Delhi":      "hazy",
}


async def get_weather(city: str, country: str) -> Dict[str, Any]:
    if settings.OPENWEATHER_API_KEY:
        try:
            return await _fetch_live(city, country)
        except Exception as e:
            logger.warning(f"Live weather failed ({city}): {e} — using simulated.")
    return _simulated(city)


async def _fetch_live(city: str, country: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": f"{city},{country}", "appid": settings.OPENWEATHER_API_KEY, "units": "metric"},
        )
        r.raise_for_status()
        d = r.json()
    desc = d["weather"][0]["description"]
    temp = d["main"]["temp"]
    rain = any(w in desc.lower() for w in ("rain", "storm", "shower", "drizzle"))
    return {"condition": desc, "temp_c": round(temp, 1), "is_raining": rain, "outdoor_friendly": not rain and temp < 38}


def _simulated(city: str) -> Dict[str, Any]:
    condition = _CITY_WEATHER.get(city, "pleasant")
    rain = any(w in condition for w in ("rain", "shower", "storm"))
    hot_cities = {"Chennai", "Dubai"}
    temp = random.randint(28, 38) if city in hot_cities else random.randint(16, 28)
    return {"condition": condition, "temp_c": temp, "is_raining": rain, "outdoor_friendly": not rain}
