"""
Groq Reasoning Engine — the intelligence core of the travel planner.

Fixed: llama3-70b-8192 was DECOMMISSIONED April 2026.
       Now uses llama-3.3-70b-versatile (override via GROQ_MODEL in .env).

Groq receives:
  • Retrieved dataset places (from RAG)
  • Live places (from RapidAPI: attractions, restaurants, hotels)
  • Weather data
  • User constraints (destination, days, budget, style, interests)

Groq must:
  1. Schedule activities with exact time slots (no instant travel)
  2. Add taxi wait (10 min) + buffer (15 min) between every slot
  3. Suggest food near current location — not near hotel
  4. Replace outdoor activities if is_raining=true
  5. Cluster nearby places on the same day
  6. Keep total_cost ≤ budget_usd (swap expensive places if needed)
  7. Pick one hotel from live data as accommodation
  8. Output STRICT JSON — no markdown, no extra text
"""

import json
import logging
from typing import Dict, Any, List, Optional

from groq import Groq
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = Groq(api_key=settings.GROQ_API_KEY)

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT  (strict — Groq must follow every rule)
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert AI travel planner. You must follow EVERY rule below exactly.

## RULES

### Data
1. Use ONLY places from DATASET or LIVE_DATA. Never invent places.
2. If LIVE_DATA hotels exist, pick the best-value one as accommodation.

### Time
3. Day starts 08:00, ends 22:00.
4. Travel time between every consecutive slot is NEVER zero:
   - Estimate driving distance from coordinates
   - Add: taxi wait 10 min + buffer 15 min on top of drive time
   - Typical city slot-to-slot: 25–45 min total transition
5. Include a travel slot between activities when transition > 20 min.

### Activities
6. Max 5–6 activity slots per day (NOT counting meal or travel slots).
7. Pacing by travel_style:
   - relaxed  → 3–4 activities/day, use duration_max for each
   - moderate → 4–5 activities/day, use midpoint of duration range
   - fast     → 5–6 activities/day, use duration_min for each
8. Category durations (enforce strictly):
   beach → 1.5–2.5 h | museum → 2–3 h | landmark → 1–2 h
   shopping → 3–4 h  | temple → 0.75–1 h | activity → 1–2 h
   restaurant → 0.75–1.5 h
9. Cluster places with nearby_ids together on the same day.
10. No two exhausting activities (e.g. safari + full museum) back-to-back.
    Insert a meal or lighter activity between them.

### Food
11. Suggest a restaurant near the CURRENT activity location, not near hotel.
12. Meal timing: 07:30–10:00 → breakfast | 12:00–14:00 → lunch | 19:00–21:00 → dinner.
13. Use a restaurant from LIVE_DATA restaurants if available and nearby.

### Weather
14. If is_raining=true: replace ALL outdoor activities with indoor alternatives.
    If no indoor alternative exists in dataset/live_data, add a note.

### Budget
15. Sum of all slot costs + accommodation cost MUST be ≤ budget_usd.
16. If over budget: remove the most expensive optional slot first,
    then replace $$$$ restaurants with $$ ones, then pick a cheaper hotel.

## OUTPUT — return ONLY this JSON object, no markdown fences, no extra text

{
  "destination": "string",
  "accommodation": {
    "name": "string",
    "price_per_night_usd": 0.0,
    "total_accommodation_cost_usd": 0.0,
    "source": "rapidapi | dataset | none",
    "notes": "string"
  },
  "days": [
    {
      "day": 1,
      "date_label": "Day 1",
      "weather": "string",
      "slots": [
        {
          "start_time": "08:00",
          "end_time": "09:30",
          "type": "activity | meal | travel",
          "activity_name": "string",
          "place_id": "string or null",
          "category": "string",
          "cost_usd": 0.0,
          "travel_time_to_next_mins": 25,
          "indoor": true,
          "source": "dataset | rapidapi",
          "notes": "string"
        }
      ],
      "day_cost_usd": 0.0
    }
  ],
  "total_cost_usd": 0.0,
  "budget_usd": 0.0,
  "budget_status": "within_budget | over_budget",
  "reasoning": "2–4 sentences explaining key choices",
  "warnings": []
}
"""


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC
# ──────────────────────────────────────────────────────────────────────────────

async def generate_itinerary_with_groq(
    destination: str,
    num_days: int,
    budget_usd: float,
    travel_style: str,
    interests: List[str],
    retrieved_places: List[Dict[str, Any]],
    weather: Dict[str, Any],
    live_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call Groq and return parsed itinerary dict."""
    prompt = _build_prompt(
        destination, num_days, budget_usd, travel_style,
        interests, retrieved_places, weather, live_data,
    )

    logger.info(f"Groq [{settings.GROQ_MODEL}] → {destination} {num_days}d ${budget_usd} {travel_style}")

    resp = _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=settings.GROQ_MAX_TOKENS,
        temperature=settings.GROQ_TEMPERATURE,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content
    logger.debug(f"Groq raw (first 400 chars): {raw[:400]}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Groq returned invalid JSON: {e}\nRaw: {raw[:500]}")


# ──────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ──────────────────────────────────────────────────────────────────────────────

def _build_prompt(
    destination: str, num_days: int, budget_usd: float,
    travel_style: str, interests: List[str],
    retrieved_places: List[Dict[str, Any]],
    weather: Dict[str, Any],
    live_data: Optional[Dict[str, Any]],
) -> str:
    live_section = (
        f"\n## LIVE_DATA (real-time from RapidAPI — prefer these for restaurants and hotels)\n"
        f"{json.dumps(live_data, indent=2)}"
        if live_data
        else "\n## LIVE_DATA\nnot available — use DATASET only"
    )

    return f"""
## USER REQUEST
- Destination   : {destination}
- Days          : {num_days}
- Total budget  : ${budget_usd} USD  (activities + food + hotel combined)
- Travel style  : {travel_style}
- Interests     : {', '.join(interests) if interests else 'general sightseeing'}

## WEATHER
{json.dumps(weather, indent=2)}

## DATASET  (curated local data — always available)
{json.dumps(retrieved_places, indent=2)}
{live_section}

## TASK
Build a complete {num_days}-day itinerary for {destination}.
Apply ALL rules from the system prompt.
Total cost (activities + food + accommodation) must be ≤ ${budget_usd}.
Return ONLY the JSON object — no markdown, no explanation outside the JSON.
"""
