"""
Travel Planner Orchestration Service.

Pipeline per request:
  1. RAG    → retrieve relevant places from Pinecone (or local fallback)
  2. API    → fetch live attractions / restaurants / hotels via RapidAPI
  3. WX     → get weather (live or simulated)
  4. Groq   → reason over all data, produce structured itinerary JSON
  5. Parse  → validate + build ItineraryResponse
  6. DB     → persist to Supabase / Postgres (optional — never blocks response)

FIXES applied here:
  - user_id is validated as a real UUID before DB insert.
    Swagger UI sends the placeholder literal "string" which is not a valid UUID.
    Any non-UUID user_id is silently set to None (anonymous save).
  - _save() is wrapped in try/except so a DB error NEVER raises a 500.
    The itinerary is always returned to the caller.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schemas import ItineraryRequest, ItineraryResponse
from app.models.models import Itinerary
from app.services.rag_service import RAGService
from app.services.groq_service import generate_itinerary_with_groq
from app.services.weather_service import get_weather
from app.services.rapidapi_service import fetch_live_travel_data

logger = logging.getLogger(__name__)


def _coerce_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    """
    Convert a string to uuid.UUID, or return None if invalid.

    This handles the common case where Swagger UI sends the placeholder
    literal "string" as the user_id, which is not a valid UUID and would
    cause asyncpg to raise a DataError on INSERT.
    """
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        logger.debug(f"user_id '{value}' is not a valid UUID — saving as anonymous.")
        return None


async def create_itinerary(
    request: ItineraryRequest,
    db: Optional[AsyncSession] = None,
) -> ItineraryResponse:

    # ── 1. RAG ────────────────────────────────────────────────────────────────
    rag   = RAGService.get()
    query = (
        f"{request.travel_style} trip {request.destination} "
        f"{' '.join(request.interests or [])} "
        f"${request.budget_usd} {request.num_days} days"
    )
    places = rag.retrieve(query=query, city_filter=request.destination, top_k=settings.PINECONE_TOP_K)
    if not places:
        raise ValueError(f"No dataset places found for '{request.destination}'.")

    country = places[0].get("country", "")

    # ── 2. RapidAPI enrichment ─────────────────────────────────────────────────
    live_data = await fetch_live_travel_data(
        city=request.destination,
        interests=request.interests or [],
        num_days=request.num_days,
    )
    if live_data:
        n = sum(len(live_data.get(k, [])) for k in ("attractions", "restaurants", "hotels"))
        logger.info(f"RapidAPI: {n} live items for {request.destination}")

    # ── 3. Weather ────────────────────────────────────────────────────────────
    weather = await get_weather(request.destination, country)
    logger.info(f"Weather [{request.destination}]: {weather['condition']} {weather['temp_c']}°C")

    # ── 4. Groq reasoning ─────────────────────────────────────────────────────
    groq_out = await generate_itinerary_with_groq(
        destination=request.destination,
        num_days=request.num_days,
        budget_usd=request.budget_usd,
        travel_style=request.travel_style,
        interests=request.interests or [],
        retrieved_places=places,
        weather=weather,
        live_data=live_data,
    )

    # ── 5. Parse ──────────────────────────────────────────────────────────────
    response = _parse(groq_out, request, weather)

    # ── 6. Persist (best-effort — never blocks the response) ──────────────────
    if db is not None:
        try:
            response.itinerary_id = await _save(db, request, response, groq_out)
        except Exception as e:
            # Log the failure but ALWAYS return the itinerary to the user.
            logger.warning(f"DB save failed (itinerary still returned): {type(e).__name__}: {e}")

    return response


# ─────────────────────────────────────────────────────────────────────────────

def _parse(groq: dict, req: ItineraryRequest, wx: dict) -> ItineraryResponse:
    warnings = list(groq.get("warnings") or [])
    cost     = float(groq.get("total_cost_usd") or 0.0)
    if cost > req.budget_usd:
        warnings.append(f"Total ${cost:.2f} exceeds budget ${req.budget_usd:.2f}.")
    return ItineraryResponse(
        destination    = groq.get("destination", req.destination),
        accommodation  = groq.get("accommodation"),
        days           = groq.get("days", []),
        total_cost_usd = cost,
        budget_usd     = req.budget_usd,
        budget_status  = groq.get("budget_status", "within_budget"),
        reasoning      = groq.get("reasoning"),
        warnings       = warnings,
        weather_summary= f"{wx.get('condition','')} | {wx.get('temp_c','?')}°C",
    )


async def _save(
    db: AsyncSession,
    req: ItineraryRequest,
    resp: ItineraryResponse,
    raw: dict,
) -> str:
    """
    Persist itinerary to DB. Returns the new itinerary UUID as a string.

    user_id is coerced to a real UUID object (or None) before insert.
    This prevents asyncpg DataError when Swagger sends "string" as user_id.
    """
    iid     = str(uuid.uuid4())
    user_uuid = _coerce_uuid(req.user_id)   # None if invalid / placeholder

    db.add(Itinerary(
        id             = uuid.UUID(iid),
        user_id        = user_uuid,          # None for anonymous requests
        destination    = req.destination,
        num_days       = req.num_days,
        budget_usd     = req.budget_usd,
        total_cost_usd = resp.total_cost_usd,
        travel_style   = req.travel_style,
        itinerary_data = raw,
        reasoning      = resp.reasoning,
        weather_summary= resp.weather_summary,
    ))
    await db.flush()
    logger.info(f"Itinerary saved: {iid} (user_id={user_uuid})")
    return iid
