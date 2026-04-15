"""
Environment-aware configuration.
Every secret comes from .env — nothing is hardcoded.
Works with local Postgres, Supabase, or AWS RDS without code changes.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ────────────────────────────────────────────────────────────────────
    ENV: str = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = ""  # Required — set in .env (Supabase URI with postgresql+asyncpg://)

    # ── Groq ───────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    # llama3-70b-8192 was DECOMMISSIONED April 2026.
    # Current options: llama-3.3-70b-versatile | llama-3.1-8b-instant | mixtral-8x7b-32768
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 4096
    GROQ_TEMPERATURE: float = 0.3

    # ── Pinecone ───────────────────────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_ENV: str = "gcp-starter"
    PINECONE_INDEX: str = "travel-planner"
    PINECONE_TOP_K: int = 10
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── RapidAPI ───────────────────────────────────────────────────────────────
    # Travel Advisor : https://rapidapi.com/apidojo/api/travel-advisor
    # Booking.com    : https://rapidapi.com/DataCrawler/api/booking-com15
    RAPIDAPI_KEY: str = ""
    RAPIDAPI_TRAVEL_ADVISOR_HOST: str = "travel-advisor.p.rapidapi.com"
    RAPIDAPI_BOOKING_HOST: str = "booking-com15.p.rapidapi.com"
    RAPIDAPI_MAX_RESULTS: int = 5
    RAPIDAPI_ENABLED: bool = True

    # ── Weather (optional) ─────────────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""

    # ── Scheduler constraints ──────────────────────────────────────────────────
    MAX_ACTIVITIES_PER_DAY: int = 6
    DAY_START_HOUR: int = 8
    DAY_END_HOUR: int = 22
    TAXI_WAIT_MINUTES: int = 10
    BUFFER_MINUTES: int = 15


settings = Settings()
