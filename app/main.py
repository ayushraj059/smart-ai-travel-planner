"""
Smart AI Travel Planner — FastAPI application entry point.
Database: Supabase PostgreSQL (managed via Alembic migrations).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings


app = FastAPI(
    title="Smart AI Travel Planner",
    description=(
        "Groq-powered travel itinerary generator with RAG pipeline, "
        "RapidAPI live data (hotels, attractions, restaurants), "
        "Supabase PostgreSQL storage, budget optimisation, "
        "weather awareness, and real-world time constraints."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
