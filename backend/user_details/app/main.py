from datetime import date
from fastapi import FastAPI, Query, HTTPException
from botocore.exceptions import ClientError

from .models import (
    TripPlanRequest,
    TripPlanResponse,
    AvailableOptionsResponse,
    BudgetOption,
    VALID_ACTIVITY_TAGS,
    VALID_FOOD_TYPES,
)
from .dynamodb import get_city_options

app = FastAPI(title="User Details / Trip Planner Service", version="1.0.0")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BUDGET_OPTIONS = [
    BudgetOption(label="Budget", description="Hostels, street food, public transport"),
    BudgetOption(label="Moderate", description="Mid-range hotels, local restaurants"),
    BudgetOption(label="Luxury", description="Premium hotels, fine dining experiences"),
]


@app.get("/health")
def health():
    return {"status": "ok", "service": "user-details"}


@app.get("/plan", response_model=AvailableOptionsResponse)
def get_plan_options(city: str = Query(..., description="City name, e.g. Goa")):
    """Return available activity tags, food types, and budget options for the city."""
    try:
        options = get_city_options(city)
    except ClientError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e.response['Error']['Message']}")

    # Fall back to the full known tag set if DynamoDB has no data for the city yet
    activity_tags = options["activity_tags"] or sorted(VALID_ACTIVITY_TAGS)
    food_types = options["food_types"] or sorted(VALID_FOOD_TYPES)

    return AvailableOptionsResponse(
        city=city,
        activity_tags=activity_tags,
        food_types=food_types,
        budget_options=BUDGET_OPTIONS,
    )


@app.post("/plan", response_model=TripPlanResponse, status_code=201)
def submit_plan(body: TripPlanRequest):
    """Accept user trip preferences and return a structured trip plan summary."""
    try:
        options = get_city_options(body.city)
    except ClientError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e.response['Error']['Message']}")

    num_days = (body.end_date - body.start_date).days + 1

    # Warn if the city has no data yet but still accept the request
    available_tags = options["activity_tags"] or sorted(VALID_ACTIVITY_TAGS)
    available_food = options["food_types"] or sorted(VALID_FOOD_TYPES)

    return TripPlanResponse(
        city=body.city,
        start_date=body.start_date,
        end_date=body.end_date,
        num_days=num_days,
        num_travelers=body.num_travelers,
        budget_preference=body.budget_preference,
        activity_preferences=body.activity_preferences,
        food_preferences=body.food_preferences,
        available_activity_tags=available_tags,
        available_food_types=available_food,
    )
