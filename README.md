# Smart AI Travel Planner v2.0

Groq-powered itinerary engine · RapidAPI live data · Pinecone RAG · **Supabase PostgreSQL**

---

## Architecture

```
POST /generate-itinerary
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI (uvicorn)                  │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   Pinecone        RapidAPI       OpenWeather     Groq LLM
  (vector RAG)  (hotels/attractions) (weather)  (reasoning)
        │              │              │              │
        └──────────────┴──────────────┴──────┬───────┘
                                             │
                                      Itinerary JSON
                                             │
                                             ▼
                                    Supabase PostgreSQL
                                    (persist itinerary)
```

---

## Database: Supabase

This project uses **Supabase** as the sole database — hosted PostgreSQL, free tier, no local installation needed.

### Get your Supabase DATABASE_URL

1. Go to **https://supabase.com** and sign up (free)
2. Click **New Project** — set a name, a strong password, choose a region
3. Wait ~2 minutes for provisioning
4. Go to: **Project Settings → Database → Connection string → URI**
5. Copy the URI — it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcxyz.supabase.co:5432/postgres
   ```
6. Change `postgresql://` → `postgresql+asyncpg://`
7. Replace `[YOUR-PASSWORD]` with your actual password
8. This is your `DATABASE_URL`

> **Free tier note:** Supabase pauses projects after 1 week of inactivity.
> If connection fails, go to your dashboard and click **"Restore project"**.

---

## Quick Start

```bash
# 1. Clone / unzip the project
cd smart-travel-planner

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env
copy .env.example .env        # Windows
cp .env.example .env          # Mac/Linux

# 4. Fill in .env (see API Keys section below)

# 5. Validate everything
python check_setup.py

# 6. Create tables in Supabase
alembic upgrade head

# 7. Start the server
python run.py

# 8. Open Swagger UI
http://localhost:8000/docs
```

---

## Using Docker

Docker runs the FastAPI app only — Supabase is still your database (no local Postgres container).

```bash
# Fill in .env first (must have valid DATABASE_URL pointing to Supabase)
docker-compose up --build

# Swagger UI
http://localhost:8000/docs
```

---

## API Keys You Need

| Service | Required | Free? | Where to get |
|---------|----------|-------|--------------|
| **Supabase** | ✅ | ✅ Free | https://supabase.com |
| **Groq** | ✅ | ✅ Free | https://console.groq.com → API Keys |
| **Pinecone** | Recommended | ✅ Free | https://app.pinecone.io → API Keys |
| **RapidAPI** | Recommended | ✅ Free tier | https://rapidapi.com |
| └ Travel Advisor | | 500 req/mo | https://rapidapi.com/apidojo/api/travel-advisor |
| └ Booking.com | | 500 req/mo | https://rapidapi.com/DataCrawler/api/booking-com15 |
| OpenWeatherMap | Optional | ✅ Free | https://openweathermap.org/api |

> Pinecone and RapidAPI are non-critical — the app falls back to the local dataset if they are unavailable.

---

## Groq Model

`llama3-70b-8192` was **decommissioned April 2026** — it returns a 400 error.

Default is now `llama-3.3-70b-versatile`. Set in `.env`:
```
GROQ_MODEL=llama-3.3-70b-versatile    # default — best quality
GROQ_MODEL=llama-3.1-8b-instant       # faster / lower cost
```

---

## Alembic Migrations (Supabase)

```bash
# Apply migrations → creates users + itineraries tables in your Supabase project
alembic upgrade head

# After changing models, generate a new migration
alembic revision --autogenerate -m "describe_change"

# Rollback one step
alembic downgrade -1
```

Tables are created directly in your Supabase PostgreSQL database.
You can verify in: **Supabase dashboard → Table Editor**.

---

## Endpoints

### `POST /api/v1/generate-itinerary`
```json
{
  "destination": "Chennai",
  "num_days": 2,
  "budget_usd": 200,
  "travel_style": "relaxed",
  "interests": ["beach", "temple", "food"]
}
```
`travel_style`: `relaxed` | `moderate` | `fast`

Supported cities: Paris, Rome, Dubai, Kuta, Tabanan, Ubud, Tokyo,
Chennai, Calangute, Old Goa, Baga, Delhi

### `GET /api/v1/health`
Returns: server status, Groq model, RapidAPI enabled, supported cities.

### `GET /api/v1/places?city=Chennai&category=beach`
Returns: local dataset entries filtered by city / category.

---

## Project Structure

```
smart-travel-planner/
├── app/
│   ├── main.py                      # FastAPI app, CORS, lifespan
│   ├── api/routes.py                # 3 endpoints
│   ├── core/
│   │   ├── config.py                # All settings from .env
│   │   └── dataset.py               # 35 curated places, 12 cities
│   ├── models/
│   │   ├── models.py                # SQLAlchemy ORM (User, Itinerary)
│   │   └── schemas.py               # Pydantic request/response schemas
│   ├── services/
│   │   ├── groq_service.py          # Groq LLM reasoning engine
│   │   ├── rag_service.py           # Pinecone RAG (+ local fallback)
│   │   ├── rapidapi_service.py      # Live hotels / attractions / restaurants
│   │   ├── planner_service.py       # Orchestration pipeline
│   │   └── weather_service.py       # Weather (live or simulated)
│   └── db/database.py               # Async SQLAlchemy → Supabase
├── alembic/
│   ├── env.py                       # Async Alembic config → Supabase
│   └── versions/0001_initial.py     # Initial schema
├── alembic.ini
├── check_setup.py                   # Pre-flight validation
├── run.py                           # Start server
├── Dockerfile
├── docker-compose.yml               # API only — uses Supabase, no local db
├── requirements.txt
└── .env.example                     # Full config template
```
