from fastapi import FastAPI, Query, HTTPException
from contextlib import asynccontextmanager
from .dynamodb import (
    create_table_if_not_exists,
    query_by_city,
    query_by_city_and_category,
    serialize_item,
)
from .models import ExploreResponse, PlacesResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table_if_not_exists()
    yield


app = FastAPI(title="Voyonata Travel Data API", version="1.0.0", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "travel-data"}


@app.get("/explore", response_model=ExploreResponse)
def explore(city: str = Query(..., description="City name, e.g. Goa")):
    items = query_by_city(city)
    if not items:
        raise HTTPException(status_code=404, detail=f"No data found for city '{city}'")
    serialized = [serialize_item(i) for i in items]
    return ExploreResponse(city=city.lower(), total=len(serialized), items=serialized)


@app.get("/places", response_model=PlacesResponse)
def places(
    city: str = Query(..., description="City name, e.g. Goa"),
    category: str = Query(..., description="Category, e.g. restaurant, attraction, hotel"),
):
    items = query_by_city_and_category(city, category)
    if not items:
        raise HTTPException(
            status_code=404,
            detail=f"No '{category}' found in city '{city}'",
        )
    serialized = [serialize_item(i) for i in items]
    return PlacesResponse(
        city=city.lower(), category=category, total=len(serialized), items=serialized
    )


@app.post("/admin/load-data")
def load_data():
    from .loader import load_all_cities
    results = load_all_cities()
    total_written = sum(v["written"] for v in results.values())
    return {
        "message": "Data loaded successfully",
        "cities_processed": len(results),
        "total_records_written": total_written,
        "details": results,
    }
