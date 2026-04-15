"""
API Routes.
  POST /api/v1/generate-itinerary  — main AI itinerary generation
  GET  /api/v1/health              — liveness + config info
  GET  /api/v1/places              — browse local dataset
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dataset import PLACES_DATASET, SUPPORTED_CITIES
from app.db.database import get_db_optional
from app.models.schemas import ItineraryRequest, ItineraryResponse, HealthResponse, PlaceOut
from app.services.planner_service import create_itinerary

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/generate-itinerary",
    response_model=ItineraryResponse,
    summary="Generate a smart AI itinerary",
    description=(
        "Provide destination, days, budget, travel style, and interests. "
        "The system fetches live hotels/attractions via RapidAPI, checks weather, "
        "then uses Groq (llama-3.3-70b-versatile) to plan a realistic day-by-day "
        "itinerary with exact time slots, travel times, costs, and accommodation. "
        "Database persistence is optional — the itinerary is always returned even "
        "if the database is unavailable."
    ),
    tags=["Itinerary"],
)
async def generate_itinerary(
    request: ItineraryRequest,
    db: Optional[AsyncSession] = Depends(get_db_optional),
):
    try:
        return await create_itinerary(request, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("generate_itinerary failed")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns server status, active Groq model, RapidAPI status, and supported cities.",
    tags=["System"],
)
async def health():
    from app.db.database import _db_available, _get_engine
    db_configured = bool(settings.DATABASE_URL)
    if not db_configured:
        db_status = "disabled"
    elif _db_available is True:
        db_status = "connected"
    elif _db_available is False:
        db_status = "misconfigured"
    else:
        db_status = "unchecked"
    return HealthResponse(
        status="ok",
        env=settings.ENV,
        groq_model=settings.GROQ_MODEL,
        rapidapi_enabled=settings.RAPIDAPI_ENABLED and bool(settings.RAPIDAPI_KEY),
        supported_cities=SUPPORTED_CITIES,
        db_configured=db_configured,
        db_status=db_status,
    )


@router.get(
    "/places",
    response_model=List[PlaceOut],
    summary="List local dataset places",
    description="Browse the curated local dataset. Filter by city and/or category.",
    tags=["Data"],
)
async def list_places(
    city: Optional[str] = Query(None, description="e.g. Chennai, Paris, Dubai"),
    category: Optional[str] = Query(None, description="beach | museum | landmark | temple | shopping | restaurant | activity"),
):
    results = PLACES_DATASET
    if city:
        results = [p for p in results if p["city"].lower() == city.lower()]
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if not results:
        raise HTTPException(status_code=404, detail=f"No places for city='{city}' category='{category}'")
    return results
