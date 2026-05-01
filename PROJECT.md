# Voyonata — AI Trip Itinerary Planner

## Overview

Voyonata is a full-stack web application that generates personalised, day-wise travel itineraries using a RAG (Retrieval-Augmented Generation) pipeline. Users sign up, describe their trip preferences through a guided wizard, and receive a structured AI-generated itinerary backed by real curated travel data.

---

## Architecture

```
┌─────────────────────────────────────┐
│         Frontend (React)            │  :5173
│  Vite · TypeScript · Tailwind CSS   │
└────────────────┬────────────────────┘
                 │ REST / JSON
     ┌───────────┼───────────┐
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│  Auth   │ │Database │ │  RAG    │
│ Service │ │ Service │ │ Service │
│  :8001  │ │  :8000  │ │  :8002  │
└────┬────┘ └────┬────┘ └────┬────┘
     │           │           │
     └─────┬─────┘     ┌─────┘
           ▼           ▼
       DynamoDB     Pinecone
      (ap-south-1) (us-east-1)
                       │
                    Groq LLM
              (llama-3.3-70b-versatile)
```

Each backend service is fully isolated — its own Python virtualenv, `.env`, and `requirements.txt`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router v6 |
| Auth Service | FastAPI, Python-Jose (JWT), hashlib, boto3 |
| Database Service | FastAPI, boto3 |
| RAG Service | FastAPI, sentence-transformers, Pinecone, Groq LLM |
| Database | AWS DynamoDB (ap-south-1) |
| Vector Store | Pinecone serverless (us-east-1) |
| LLM | Groq — llama-3.3-70b-versatile |
| Containerisation | Docker + Docker Compose |

---

## Services

### Frontend (`frontend/`, port 5173)

React SPA with a dark navy design system and the following pages:

| Route | Page | Access |
|---|---|---|
| `/login` | Login form | Public |
| `/signup` | Signup form | Public |
| `/dashboard` | User dashboard | Protected |
| `/plan` | Trip planning wizard | Protected |
| `/itinerary/:id` | Generated itinerary view | Protected |
| `/trips` | Past trips list | Protected |
| `/profile` | User profile | Protected |

**Trip Planning Wizard** — 3-step form collecting:
1. Destination, start date, end date
2. Activities (Beaches, Culture, Adventure, etc.) and food preferences
3. Budget tier (Budget / Moderate / Luxury) and number of travellers

On submission the wizard calls `POST /itinerary` on the RAG service and displays the structured result.

Auth state is managed via `AuthContext` using `localStorage` for session persistence (JWT token and user object).

---

### Auth Service (`backend/auth-service/`, port 8001)

Handles user registration, login, and JWT-based session management.

**DynamoDB Tables:**
- `users` — stores email (PK), hashed password (sha256 + salt), full name, created_at
- `pending_otps` — reserved for future OTP re-enablement

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/signup` | Register user, return JWT |
| `POST` | `/login` | Verify credentials, return JWT |
| `GET` | `/me` | Return authenticated user info (Bearer token required) |

**Auth Flow:**
1. `POST /signup` with `{email, password, full_name}` → user created in DynamoDB → JWT returned
2. `POST /login` with `{email, password}` → credentials verified → JWT returned
3. `GET /me` with `Authorization: Bearer <token>` → user info returned

JWT expires in 60 minutes (configurable via `JWT_EXPIRE_MINUTES`).

---

### Database Service (`backend/database/`, port 8000)

Manages the `travel_data` DynamoDB table and provides admin endpoints for loading city data.

**DynamoDB Table: `travel_data`**
- Partition key: `city` (String, lowercased)
- Sort key: `category_name` (String, format: `<category>#<name>`)
- Billing: PAY_PER_REQUEST

**Place fields:** `name`, `category` (attraction/restaurant/hotel), `city`, `country`, `lat`, `lon`, plus optional: `address`, `website`, `opening_hours`, `cuisine`, `rating`, `price`, `currency`, `stars`, `phone`, `source`

**Key Endpoint:**
- `POST /admin/load-data` — loads all city JSON files from `data/` into DynamoDB

City data lives in `data/*_final.json`. The loader skips any item missing `name` or `category`.

---

### RAG Service (`backend/rag/`, port 8002)

The core intelligence of the application. Implements a full RAG pipeline:

```
User trip preferences
        │
        ▼
  Embed with sentence-transformers (all-MiniLM-L6-v2, 384-dim)
        │
        ▼
  Vector search in Pinecone (cosine similarity, city-filtered, top-30)
        │
        ▼
  Build prompt with user constraints + retrieved places
        │
        ▼
  Groq LLM (llama-3.3-70b-versatile, JSON mode, temperature=0.3)
        │
        ▼
  Validate & post-process:
    - Sort activities by time
    - Resolve scheduling overlaps (+15 min gap)
    - Recalculate daily costs
    - Derive budget_status (Budget/Moderate/Luxury)
        │
        ▼
  Structured ItineraryResponse
```

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/index` | Embed all DynamoDB places → upsert to Pinecone (idempotent) |
| `POST` | `/search` | Free-text semantic search with optional city/category filters |
| `POST` | `/search/plan` | Trip plan object → auto-generate query → semantic search |
| `POST` | `/itinerary` | Full RAG pipeline → structured day-wise itinerary |

**Pinecone vector IDs** follow the pattern `{city}#{category}#{name}` (ASCII-normalised).

**Budget tier caps (USD per person/day):** Budget ≤ $50 · Moderate ≤ $150 · Luxury = unlimited

---

## Data Flow: Generating an Itinerary

```
1. User fills trip wizard on frontend
   └─ destination, dates, travellers, activities, food preferences, budget

2. Frontend → POST /itinerary (RAG service)
   └─ city, start_date, end_date, num_travelers, budget_tier, activities, food_preferences

3. RAG service embeds the trip plan (sentence-transformers)
   └─ Queries Pinecone for top-30 semantically matching places in that city

4. RAG service builds an LLM prompt
   └─ Includes user constraints + all retrieved place details

5. Groq LLM returns structured JSON
   └─ Day-by-day itinerary with activities, times, costs, descriptions

6. Validator post-processes the response
   └─ Fixes overlaps, recalculates costs, assigns budget_status

7. Frontend renders the ItineraryResponse
   └─ Stored in localStorage for later viewing under /trips
```

---

## Environment Variables

### Auth Service (`.env`)
```
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
OTP_EXPIRE_MINUTES=10
```

### Database Service (`.env`)
```
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### RAG Service (`.env`)
```
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=voyonata-travel
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
```

---

## Running Locally

### Prerequisites
- Python 3.10+, Node.js 18+
- AWS credentials with DynamoDB access (ap-south-1)
- Pinecone account + API key
- Groq API key

### Start all services

```bash
# 1. Database service
cd backend/database
venv\Scripts\activate       # Windows
uvicorn app.main:app --reload --port 8000

# 2. Auth service
cd backend/auth-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001

# 3. RAG service
cd backend/rag
venv\Scripts\activate
uvicorn app.main:app --reload --port 8002

# 4. Frontend
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

### Load data (first-time setup)

```bash
# Load city JSON files into DynamoDB
curl -X POST http://localhost:8000/admin/load-data

# Embed all places and index into Pinecone
curl -X POST http://localhost:8002/index
```

### Docker (alternative)

```bash
docker-compose up --build
```

---

## Project Structure

```
├── frontend/                  React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/             Route-level page components
│   │   ├── components/        Shared UI (Sidebar, etc.)
│   │   ├── context/           AuthContext (JWT + user state)
│   │   ├── services/          api.ts (REST client for all 3 services)
│   │   └── types/             Shared TypeScript types
│   └── Dockerfile
│
├── backend/
│   ├── auth-service/          FastAPI · JWT · DynamoDB users table
│   │   └── app/
│   │       ├── main.py        API routes
│   │       ├── security.py    Password hashing + JWT
│   │       ├── dynamodb.py    DynamoDB user CRUD
│   │       ├── models.py      Pydantic request/response models
│   │       └── config.py      Pydantic settings (reads .env)
│   │
│   ├── database/              FastAPI · DynamoDB travel_data CRUD
│   │   └── app/
│   │       ├── main.py        API routes
│   │       └── loader.py      JSON → DynamoDB bulk loader
│   │
│   └── rag/                   FastAPI · Embeddings · Pinecone · Groq
│       └── app/
│           ├── main.py        API routes
│           ├── embeddings.py  sentence-transformers wrapper
│           ├── pinecone_client.py  Pinecone index management
│           ├── itinerary.py   RAG orchestration + LLM call
│           ├── validator.py   Post-processing (times, costs, budget)
│           ├── groq_client.py Groq API wrapper
│           ├── dynamodb.py    DynamoDB full-scan
│           ├── models.py      Pydantic request/response models
│           └── config.py      Pydantic settings (reads .env)
│
├── data/                      City JSON files (*_final.json)
├── docker-compose.yml
└── README.md
```

---

## Key Design Decisions

- **Microservices isolation** — each service has its own venv and `.env`; no shared Python environment
- **Semantic retrieval** — places are embedded once (`/index`) and reused for all queries; embedding is asymmetric (place documents vs. user query style must match)
- **JSON-mode LLM** — Groq is called with `response_format={"type": "json_object"}` to guarantee parseable output
- **Post-processing validator** — separates LLM concerns from schedule correctness; the LLM focuses on content, the validator enforces constraints
- **CORS** — all services use `allow_origin_regex=r"http://localhost(:\d+)?"` so Vite's auto-port-increment (5173→5174) never breaks requests
