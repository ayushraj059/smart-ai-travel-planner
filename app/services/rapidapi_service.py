"""
RapidAPI Service — live travel data enrichment.

APIs:
  1. Travel Advisor  (apidojo)   — real attractions + restaurants near lat/lng
     Subscribe free: https://rapidapi.com/apidojo/api/travel-advisor
  2. Booking.com     (DataCrawler) — real hotel options with live USD pricing
     Subscribe free: https://rapidapi.com/DataCrawler/api/booking-com15

Both APIs have free tiers (~500 req/month each).
One RapidAPI key works for all subscribed APIs.

Fully fault-tolerant — returns None on any failure so the planner
falls back to the local dataset silently.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date, timedelta

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# City coordinate seeds used as the search origin for RapidAPI bounding boxes
CITY_COORDS: Dict[str, Dict[str, float]] = {
    "Paris":      {"lat": 48.8566,  "lng": 2.3522},
    "Rome":       {"lat": 41.9028,  "lng": 12.4964},
    "Dubai":      {"lat": 25.2048,  "lng": 55.2708},
    "Kuta":       {"lat": -8.7184,  "lng": 115.1686},
    "Tabanan":    {"lat": -8.5469,  "lng": 115.0970},
    "Ubud":       {"lat": -8.5069,  "lng": 115.2624},
    "Tokyo":      {"lat": 35.6762,  "lng": 139.6503},
    "Chennai":    {"lat": 13.0827,  "lng": 80.2707},
    "Calangute":  {"lat": 15.5440,  "lng": 73.7553},
    "Old Goa":    {"lat": 15.5009,  "lng": 73.9116},
    "Baga":       {"lat": 15.5564,  "lng": 73.7502},
    "Delhi":      {"lat": 28.6139,  "lng": 77.2090},
}


async def fetch_live_travel_data(
    city: str,
    interests: List[str],
    num_days: int,
) -> Optional[Dict[str, Any]]:
    """
    Fetch live attractions, restaurants, and hotels via RapidAPI.
    Returns None if disabled, key missing, or all calls fail.
    """
    if not settings.RAPIDAPI_ENABLED or not settings.RAPIDAPI_KEY:
        logger.info("RapidAPI disabled or key not set — local dataset only.")
        return None

    coords = CITY_COORDS.get(city)
    if not coords:
        logger.warning(f"No coordinates for '{city}' — skipping RapidAPI.")
        return None

    lat, lng = coords["lat"], coords["lng"]
    ta_headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_TRAVEL_ADVISOR_HOST,
    }
    bk_headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_BOOKING_HOST,
    }

    live: Dict[str, Any] = {"city": city, "attractions": [], "restaurants": [], "hotels": []}

    async with httpx.AsyncClient(timeout=15) as client:

        # ── 1. Attractions ─────────────────────────────────────────────────────
        try:
            live["attractions"] = await _attractions(client, ta_headers, lat, lng, interests)
            logger.info(f"RapidAPI: {len(live['attractions'])} attractions for {city}")
        except Exception as e:
            logger.warning(f"RapidAPI attractions error ({city}): {e}")

        # ── 2. Restaurants ─────────────────────────────────────────────────────
        try:
            live["restaurants"] = await _restaurants(client, ta_headers, lat, lng)
            logger.info(f"RapidAPI: {len(live['restaurants'])} restaurants for {city}")
        except Exception as e:
            logger.warning(f"RapidAPI restaurants error ({city}): {e}")

        # ── 3. Hotels ──────────────────────────────────────────────────────────
        try:
            live["hotels"] = await _hotels(client, bk_headers, city, num_days)
            logger.info(f"RapidAPI: {len(live['hotels'])} hotels for {city}")
        except Exception as e:
            logger.warning(f"RapidAPI hotels error ({city}): {e}")

    total = sum(len(live[k]) for k in ("attractions", "restaurants", "hotels"))
    if total == 0:
        logger.warning("RapidAPI returned nothing — falling back to local dataset.")
        return None

    return live


# ──────────────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ──────────────────────────────────────────────────────────────────────────────

async def _attractions(
    client: httpx.AsyncClient,
    headers: Dict,
    lat: float, lng: float,
    interests: List[str],
) -> List[Dict[str, Any]]:
    """Travel Advisor /attractions/list — bounding-box search."""
    r = await client.get(
        "https://travel-advisor.p.rapidapi.com/attractions/list",
        headers=headers,
        params={
            "bl_latitude":  str(lat - 0.05), "tr_latitude":  str(lat + 0.05),
            "bl_longitude": str(lng - 0.05), "tr_longitude": str(lng + 0.05),
            "language": "en_US", "currency": "USD", "lunit": "km",
            "limit": str(settings.RAPIDAPI_MAX_RESULTS),
        },
    )
    r.raise_for_status()
    out = []
    for item in r.json().get("data", []):
        if not isinstance(item, dict) or not item.get("name"):
            continue
        out.append({
            "id":           f"rapid_attr_{item.get('location_id', '')}",
            "name":         item.get("name", ""),
            "category":     _attraction_category(item, interests),
            "rating":       item.get("rating", "N/A"),
            "price_level":  item.get("price_level", "$"),
            "price_usd":    _price_from_level(item.get("price_level", "$")),
            "address":      item.get("address", ""),
            "lat":          float(item.get("latitude") or lat),
            "lng":          float(item.get("longitude") or lng),
            "description":  item.get("description", ""),
            "indoor":       _guess_indoor(item),
            "duration_min": 1.0, "duration_max": 2.0,
            "source":       "rapidapi_travel_advisor",
            "web_url":      item.get("web_url", ""),
        })
    return out[:settings.RAPIDAPI_MAX_RESULTS]


async def _restaurants(
    client: httpx.AsyncClient,
    headers: Dict,
    lat: float, lng: float,
) -> List[Dict[str, Any]]:
    """Travel Advisor /restaurants/list — bounding-box search."""
    r = await client.get(
        "https://travel-advisor.p.rapidapi.com/restaurants/list",
        headers=headers,
        params={
            "bl_latitude":  str(lat - 0.05), "tr_latitude":  str(lat + 0.05),
            "bl_longitude": str(lng - 0.05), "tr_longitude": str(lng + 0.05),
            "language": "en_US", "currency": "USD", "lunit": "km",
            "limit": str(settings.RAPIDAPI_MAX_RESULTS),
        },
    )
    r.raise_for_status()
    out = []
    for item in r.json().get("data", []):
        if not isinstance(item, dict) or not item.get("name"):
            continue
        out.append({
            "id":           f"rapid_rest_{item.get('location_id', '')}",
            "name":         item.get("name", ""),
            "category":     "restaurant",
            "cuisine":      _cuisines(item),
            "rating":       item.get("rating", "N/A"),
            "price_level":  item.get("price_level", "$"),
            "price_usd":    _price_from_level(item.get("price_level", "$")),
            "address":      item.get("address", ""),
            "lat":          float(item.get("latitude") or lat),
            "lng":          float(item.get("longitude") or lng),
            "indoor":       True,
            "duration_min": 0.75, "duration_max": 1.5,
            "source":       "rapidapi_travel_advisor",
            "web_url":      item.get("web_url", ""),
        })
    return out[:settings.RAPIDAPI_MAX_RESULTS]


async def _hotels(
    client: httpx.AsyncClient,
    headers: Dict,
    city: str,
    num_days: int,
) -> List[Dict[str, Any]]:
    """Booking.com: searchDestination → searchHotels."""
    # Step 1 — resolve destination id
    sr = await client.get(
        "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination",
        headers=headers,
        params={"query": city},
    )
    sr.raise_for_status()
    dest_list = sr.json().get("data", [])
    if not dest_list:
        return []
    dest_id   = dest_list[0].get("dest_id", "")
    dest_type = dest_list[0].get("dest_type", "city")

    # Step 2 — search hotels
    checkin  = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    checkout = (date.today() + timedelta(days=7 + num_days)).strftime("%Y-%m-%d")
    hr = await client.get(
        "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels",
        headers=headers,
        params={
            "dest_id": dest_id, "search_type": dest_type,
            "arrival_date": checkin, "departure_date": checkout,
            "adults": "2", "room_qty": "1",
            "currency_code": "USD", "languagecode": "en-us",
            "sort_by": "popularity",
        },
    )
    hr.raise_for_status()
    raw = hr.json().get("data", {}).get("hotels", [])

    out = []
    for h in raw[:settings.RAPIDAPI_MAX_RESULTS]:
        prop  = h.get("property", {})
        price = float(h.get("priceBreakdown", {}).get("grossPrice", {}).get("value", 80))
        out.append({
            "id":                  f"rapid_hotel_{prop.get('id', '')}",
            "name":                prop.get("name", "Hotel"),
            "category":            "hotel",
            "rating":              prop.get("reviewScore", "N/A"),
            "price_per_night_usd": round(price, 2),
            "total_cost_usd":      round(price * num_days, 2),
            "address":             prop.get("wishlistName", city),
            "lat":                 float(prop.get("latitude", 0)),
            "lng":                 float(prop.get("longitude", 0)),
            "source":              "rapidapi_booking",
            "checkin":             checkin,
            "checkout":            checkout,
        })
    return out


# ── Utility helpers ────────────────────────────────────────────────────────────

def _attraction_category(item: Dict, interests: List[str]) -> str:
    name = (item.get("name") or "").lower()
    subs = " ".join((s.get("key") or "").lower() for s in (item.get("subcategory") or []) if isinstance(s, dict))
    combined = name + " " + subs
    if any(k in combined for k in ["beach", "coast", "sea"]):      return "beach"
    if any(k in combined for k in ["temple", "mosque", "shrine"]): return "temple"
    if any(k in combined for k in ["museum", "gallery"]):          return "museum"
    if any(k in combined for k in ["mall", "market", "shop"]):     return "shopping"
    return "landmark"


def _guess_indoor(item: Dict) -> bool:
    name = (item.get("name") or "").lower()
    if any(k in name for k in ["museum", "gallery", "mall", "aquarium", "cinema"]): return True
    if any(k in name for k in ["beach", "park", "garden", "fort", "hill"]):         return False
    return False


def _price_from_level(level: str) -> float:
    return {"$": 5.0, "$$": 15.0, "$$$": 30.0, "$$$$": 60.0}.get(level, 10.0)


def _cuisines(item: Dict) -> str:
    c = item.get("cuisine", [])
    if isinstance(c, list):
        return ", ".join(x.get("name", "") for x in c[:3] if isinstance(x, dict))
    return ""
