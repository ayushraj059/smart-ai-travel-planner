"""
Pydantic v2 schemas — request validation + response serialization.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# REQUEST
# ──────────────────────────────────────────────────────────────────────────────

class ItineraryRequest(BaseModel):
    destination: str = Field(
        ...,
        description="City to visit — must be in the supported dataset",
        examples=["Chennai", "Paris", "Dubai", "Tokyo", "Delhi"],
    )
    num_days: int = Field(
        ..., ge=1, le=14,
        description="Number of trip days (1–14)",
    )
    budget_usd: float = Field(
        ..., gt=0,
        description="Total trip budget in USD (activities + food + hotel)",
        examples=[200.0, 500.0, 1500.0],
    )
    travel_style: str = Field(
        default="moderate",
        description="Pacing: relaxed | moderate | fast",
    )
    interests: Optional[List[str]] = Field(
        default=None,
        description="Your interests — beach, museum, temple, shopping, food, adventure, etc.",
        examples=[["beach", "food"], ["museum", "landmark", "shopping"]],
    )
    user_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional user UUID for DB persistence. "            "Must be a valid UUID (e.g. \"550e8400-e29b-41d4-a716-446655440000\"). "            "Leave blank or omit to generate an anonymous itinerary. "            "The Swagger UI default placeholder 'string' is intentionally ignored."
        ),
        examples=["550e8400-e29b-41d4-a716-446655440000", None],
    )

    @field_validator("travel_style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        allowed = {"relaxed", "moderate", "fast"}
        if v.lower() not in allowed:
            raise ValueError(f"travel_style must be one of {allowed}")
        return v.lower()

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: str) -> str:
        from app.core.dataset import SUPPORTED_CITIES
        match = next((c for c in SUPPORTED_CITIES if c.lower() == v.lower()), None)
        if not match:
            raise ValueError(
                f"'{v}' is not supported. "
                f"Call GET /api/v1/health to see supported cities."
            )
        return match


# ──────────────────────────────────────────────────────────────────────────────
# RESPONSE  sub-models
# ──────────────────────────────────────────────────────────────────────────────

class AccommodationInfo(BaseModel):
    name: str = ""
    price_per_night_usd: float = 0.0
    total_accommodation_cost_usd: float = 0.0
    source: str = "none"          # rapidapi | dataset | none
    notes: Optional[str] = None


class ItinerarySlot(BaseModel):
    start_time: str
    end_time: str
    type: str                     # activity | meal | travel
    activity_name: str
    place_id: Optional[str] = None
    category: Optional[str] = None
    cost_usd: float = 0.0
    travel_time_to_next_mins: Optional[int] = None
    indoor: Optional[bool] = None
    source: Optional[str] = "dataset"    # dataset | rapidapi
    notes: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    date_label: str
    weather: Optional[str] = None
    slots: List[ItinerarySlot]
    day_cost_usd: float


class ItineraryResponse(BaseModel):
    itinerary_id: Optional[str] = None
    destination: str
    accommodation: Optional[AccommodationInfo] = None
    days: List[DayPlan]
    total_cost_usd: float
    budget_usd: float
    budget_status: str            # within_budget | over_budget
    reasoning: Optional[str] = None
    warnings: List[str] = []
    weather_summary: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# MISC
# ──────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    env: str
    groq_model: str
    rapidapi_enabled: bool
    supported_cities: List[str]
    db_configured: bool = False
    db_status: str = "unknown"  # connected | misconfigured | disabled


class PlaceOut(BaseModel):
    id: str
    name: str
    city: str
    country: str
    category: str
    lat: float
    lng: float
    duration_min: float
    duration_max: float
    price_usd: float
    popularity: int
    indoor: bool
    description: str
    nearby_ids: List[str]
