from datetime import date
from pydantic import BaseModel
from typing import Optional, Literal


class IndexResponse(BaseModel):
    message: str
    total_fetched: int
    total_upserted: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    city: Optional[str] = None
    category: Optional[str] = None


class TripPlanSearchRequest(BaseModel):
    """Same shape as user_details TripPlanRequest — used to drive RAG search."""
    city: str
    start_date: date
    end_date: date
    num_travelers: int
    budget_preference: Literal["Budget", "Moderate", "Luxury"]
    activity_preferences: list[str]
    food_preferences: list[str]
    top_k: int = 10
    category: Optional[str] = None


class PlaceResult(BaseModel):
    score: float
    name: str
    city: str
    country: str
    category: str
    rating: Optional[float] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    cuisine: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[PlaceResult]


# ── Itinerary models ──────────────────────────────────────────────────────────

class DestinationOverview(BaseModel):
    weather_summary: str
    must_visit_places: list[str]
    local_dishes: list[str]
    culture_insight: str

class ItineraryActivity(BaseModel):
    time: str
    place_name: str
    category: str
    duration_hours: float
    notes: str
    estimated_cost_per_person: float
    currency: str
    cuisine: Optional[str] = None
    rating: Optional[float] = None
    famous_dishes: list[str] = []


class ItineraryDay(BaseModel):
    day: int
    date: str
    theme: str
    activities: list[ItineraryActivity]
    daily_cost_per_person: float


class ItinerarySummary(BaseModel):
    total_estimated_cost_per_person: float
    total_estimated_cost: float
    currency: str
    budget_status: str
    highlights: list[str]


class HotelRecommendation(BaseModel):
    name: str
    notes: str
    estimated_cost_per_person_per_night: float
    currency: str
    stars: Optional[int] = None


class ItineraryResponse(BaseModel):
    city: str
    start_date: str
    end_date: str
    num_days: int
    num_travelers: int
    budget_preference: str
    days: list[ItineraryDay]
    summary: ItinerarySummary
    recommended_hotels: list[HotelRecommendation] = []
    destination_overview: Optional[DestinationOverview] = None


class WeatherForecastDay(BaseModel):
    date: str
    description: str
    icon: str
    temp_max: float
    temp_min: float


class ItineraryRequest(BaseModel):
    """Full trip preferences — same shape as user_details TripPlanRequest."""
    city: str
    start_date: date
    end_date: date
    num_travelers: int
    budget_preference: Literal["Budget", "Moderate", "Luxury"]
    activity_preferences: list[str]
    food_preferences: list[str]
    weather_forecast: list[WeatherForecastDay] = []
