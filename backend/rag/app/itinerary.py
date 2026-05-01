import json
import logging
import re
from datetime import datetime, timedelta

from .embeddings import embed_user_plan
from .pinecone_client import query_index
from .groq_client import call_groq
from .models import ItineraryResponse, ItineraryDay, ItineraryActivity, ItinerarySummary, HotelRecommendation, DestinationOverview

log = logging.getLogger(__name__)

_JSON_SCHEMA = """{
  "destination_overview": {
    "weather_summary": "1-2 sentences on weather for these specific trip dates and one practical packing tip",
    "must_visit_places": ["iconic landmark or area 1", "iconic landmark or area 2", "iconic landmark or area 3"],
    "local_dishes": ["famous local dish 1", "famous local dish 2", "famous local dish 3"],
    "culture_insight": "1-2 sentences on local culture, customs, vibe, and what makes this destination unique"
  },
  "city": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "num_days": <integer>,
  "num_travelers": <integer>,
  "budget_preference": "Budget|Moderate|Luxury",
  "days": [
    {
      "day": <1-based integer>,
      "date": "YYYY-MM-DD",
      "theme": "short theme like 'Beaches & Sunsets'",
      "activities": [
        {
          "time": "HH:MM",
          "place_name": "exact name from provided places or well-known landmark",
          "category": "attraction|restaurant",
          "duration_hours": <float>,
          "notes": "brief tip or description",
          "estimated_cost_per_person": <float — cost for ONE person, already divided>,
          "currency": "local currency code e.g. INR, USD, EUR, THB",
          "cuisine": "cuisine type for restaurants e.g. North Indian, Thai, Italian — null for non-restaurants",
          "rating": <float 1.0-5.0 using actual place rating if available, else a realistic estimate — null for non-restaurants>,
          "famous_dishes": ["signature dish 1", "signature dish 2"]
        }
      ],
      "daily_cost_per_person": <float — must equal sum of activity costs>
    }
  ],
  "recommended_hotels": [
    {
      "name": "hotel name from the provided places or a well-known property",
      "notes": "why it suits the budget and trip style",
      "estimated_cost_per_person_per_night": <float — per person per night, already divided>,
      "currency": "local currency code",
      "stars": <integer 1-5>
    }
  ],
  "summary": {
    "total_estimated_cost_per_person": <float>,
    "total_estimated_cost": <float — per_person * num_travelers>,
    "currency": "primary currency",
    "budget_status": "within budget|over budget|under budget",
    "highlights": ["highlight 1", "highlight 2", "highlight 3"]
  }
}"""


def _format_places(places: list[dict]) -> str:
    lines = []
    for i, p in enumerate(places, 1):
        parts = [f"{i}. [{p.get('category', 'place').upper()}] {p.get('name', 'Unknown')}"]
        if p.get("rating"):
            parts.append(f"rating={p['rating']}")
        if p.get("cuisine"):
            parts.append(f"cuisine={p['cuisine']}")
        if p.get("price"):
            cur = p.get("currency", "")
            parts.append(f"price={p['price']} {cur}".strip())
        if p.get("address"):
            parts.append(f"address={p['address']}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _weather_advice(description: str) -> str:
    d = description.lower()
    if any(x in d for x in ["storm", "thunder"]):
        return "stay indoors — malls, museums, indoor attractions only"
    if any(x in d for x in ["rain", "shower", "drizzle"]):
        return "prefer covered/indoor venues; carry umbrella; avoid beaches"
    if any(x in d for x in ["snow"]):
        return "pack warm layers; limit prolonged outdoor exposure"
    if any(x in d for x in ["fog"]):
        return "reduced visibility; avoid elevated viewpoints; favour indoor"
    if any(x in d for x in ["overcast", "cloudy"]):
        return "mild outdoor activities fine; no beach unless warm enough"
    return "great for outdoor sightseeing and activities"


def _format_weather_section(weather: list[dict], num_days: int) -> str:
    if not weather:
        return ""
    lines = ["", "WEATHER FORECAST (adjust activity selection to suit conditions):"]
    for w in weather[:num_days]:
        advice = _weather_advice(w.get("description", ""))
        lines.append(
            f"  {w.get('date', '')} {w.get('icon', '')} {w.get('description', '')} "
            f"{w.get('temp_max', '?')}°C / {w.get('temp_min', '?')}°C  →  {advice}"
        )
    lines.append("Apply these weather notes per day: schedule indoor alternatives on bad-weather days.")
    lines.append("")
    return "\n".join(lines)


def _build_prompt(plan: dict, places: list[dict]) -> str:
    start = plan.get("start_date", "")
    end = plan.get("end_date", "")
    num_days = _count_days(start, end)

    activities = ", ".join(plan.get("activity_preferences") or []) or "General sightseeing"
    food = ", ".join(plan.get("food_preferences") or []) or "No preference"
    weather_section = _format_weather_section(plan.get("weather_forecast", []), num_days)

    return f"""Create a {num_days}-day travel itinerary for the following trip:

TRIP DETAILS:
- Destination: {plan.get('city', '').title()}
- Dates: {start} to {end} ({num_days} days)
- Travelers: {plan.get('num_travelers', 1)}
- Budget: {plan.get('budget_preference', 'Moderate')}
- Activity interests: {activities}
- Food preferences: {food}
{weather_section}
RETRIEVED PLACES (ranked by relevance — use these as the primary source):
{_format_places(places)}

Generate the full {num_days}-day itinerary strictly following this JSON schema:
{_JSON_SCHEMA}

MANDATORY FIELD CHECK — your JSON object MUST contain ALL of these top-level keys:
  ✓ destination_overview  (object with: weather_summary, must_visit_places, local_dishes, culture_insight)
  ✓ days                  (array of day objects)
  ✓ recommended_hotels    (array of hotel objects)
  ✓ summary               (object with totals and highlights)
Do NOT omit destination_overview — it is required for every response."""


def _count_days(start, end) -> int:
    try:
        s = datetime.strptime(str(start), "%Y-%m-%d")
        e = datetime.strptime(str(end), "%Y-%m-%d")
        return max(1, (e - s).days + 1)
    except Exception:
        return 1


def _repair_json(raw: str) -> str:
    """Fix the most common LLM JSON mistake: a numeric value followed by an inline annotation.
    e.g.  38000.0, "/ 3,   →  12666.67,
    We evaluate the expression if it's a simple division, otherwise zero it out.
    """
    def _fix_annotated_number(m: re.Match) -> str:
        number = float(m.group(1))
        divisor_str = m.group(2).strip().lstrip("/").strip()
        try:
            result = number / float(divisor_str)
            return f"{result:.2f}"
        except Exception:
            return str(number)

    # Pattern: <number>, "<optional text>/ <divisor><optional text>
    raw = re.sub(
        r'(-?\d+(?:\.\d+)?)\s*,\s*"[^"]*?/\s*(\d+(?:\.\d+)?)[^"]*"',
        _fix_annotated_number,
        raw,
    )
    return raw


def _parse_response(raw: str) -> dict:
    """Extract JSON from LLM output, tolerating markdown fences and inline annotations."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raw = _repair_json(raw)
        return json.loads(raw)


def retrieve_places(plan: dict, top_k: int = 30) -> list[dict]:
    """Embed the user plan and retrieve top-K places from Pinecone."""
    vector = embed_user_plan(plan)
    city = plan.get("city", "").lower()
    raw = query_index(vector=vector, top_k=top_k, filter={"city": {"$eq": city}})
    # Strip score — LLM doesn't need it
    return [{k: v for k, v in r.items() if k != "score"} for r in raw]


def build_itinerary(plan: dict) -> ItineraryResponse:
    """
    Full pipeline:
      1. Retrieve top-30 semantically relevant places from Pinecone
      2. Build a structured prompt with user constraints + places
      3. Call Groq LLM with JSON-mode enabled
      4. Parse and validate the response into ItineraryResponse
    """
    log.info("Retrieving places from Pinecone...")
    places = retrieve_places(plan, top_k=30)
    log.info(f"Retrieved {len(places)} places")

    prompt = _build_prompt(plan, places)
    raw_json = call_groq(prompt)
    log.info("Received LLM response")

    data = _parse_response(raw_json)
    return _to_model(data)


def _to_model(data: dict) -> ItineraryResponse:
    days = []
    for d in data.get("days", []):
        activities = []
        for a in d.get("activities", []):
            activities.append(ItineraryActivity(
                time=a.get("time", "09:00"),
                place_name=a.get("place_name", ""),
                category=a.get("category", "attraction"),
                duration_hours=float(a.get("duration_hours", 1.0)),
                notes=a.get("notes", ""),
                estimated_cost_per_person=float(a.get("estimated_cost_per_person", 0.0)),
                currency=a.get("currency", ""),
                cuisine=a.get("cuisine"),
                rating=float(a["rating"]) if a.get("rating") is not None else None,
                famous_dishes=a.get("famous_dishes", []),
            ))
        days.append(ItineraryDay(
            day=int(d.get("day", 1)),
            date=str(d.get("date", "")),
            theme=d.get("theme", ""),
            activities=activities,
            daily_cost_per_person=float(d.get("daily_cost_per_person", 0.0)),
        ))

    s = data.get("summary", {})
    summary = ItinerarySummary(
        total_estimated_cost_per_person=float(s.get("total_estimated_cost_per_person", 0.0)),
        total_estimated_cost=float(s.get("total_estimated_cost", 0.0)),
        currency=s.get("currency", ""),
        budget_status=s.get("budget_status", "within budget"),
        highlights=s.get("highlights", []),
    )

    hotels = []
    for h in data.get("recommended_hotels", []):
        try:
            hotels.append(HotelRecommendation(
                name=h.get("name", ""),
                notes=h.get("notes", ""),
                estimated_cost_per_person_per_night=float(h.get("estimated_cost_per_person_per_night", 0.0)),
                currency=h.get("currency", ""),
                stars=h.get("stars"),
            ))
        except Exception:
            continue

    ov = data.get("destination_overview", {})
    overview = DestinationOverview(
        weather_summary=ov.get("weather_summary", ""),
        must_visit_places=ov.get("must_visit_places", []),
        local_dishes=ov.get("local_dishes", []),
        culture_insight=ov.get("culture_insight", ""),
    ) if ov else None

    return ItineraryResponse(
        city=data.get("city", ""),
        start_date=str(data.get("start_date", "")),
        end_date=str(data.get("end_date", "")),
        num_days=int(data.get("num_days", len(days))),
        num_travelers=int(data.get("num_travelers", 1)),
        budget_preference=data.get("budget_preference", "Moderate"),
        days=days,
        summary=summary,
        recommended_hotels=hotels,
        destination_overview=overview,
    )
