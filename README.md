# Voyonata — AI Trip Itinerary Planner

Voyonata is a full-stack AI-powered travel planning app. Tell it where you want to go, your dates, budget, and interests — it retrieves real places from a curated database, runs them through a Groq LLM, and returns a day-by-day itinerary tailored to you.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Auth Service | FastAPI, DynamoDB, JWT, Gmail SMTP (OTP) |
| Database Service | FastAPI, DynamoDB (travel data CRUD) |
| RAG Service | FastAPI, sentence-transformers, Pinecone, Groq LLM |
| User Details Service | FastAPI, DynamoDB (trip plan validation) |
| Infrastructure | AWS DynamoDB (`ap-south-1`), Pinecone (serverless), Docker |

---

## Architecture

```
Browser (React)
    │
    ├── POST /signup, /verify-otp, /login, GET /me  ──► auth-service      :8001
    ├── POST /itinerary                              ──► rag-service        :8002
    ├── GET  /plan                                   ──► user-details       :8003
    └── GET  /explore, /places                       ──► database-service   :8000
                                                              │
                                                     AWS DynamoDB (ap-south-1)
                                                              │
                                          rag-service ──► Pinecone ──► Groq LLM
```

Each backend service is fully isolated with its own `venv`, `.env`, and `requirements.txt`.

---

## Prerequisites

- **Docker & Docker Compose** — for containerised setup
- **Node.js 20+** and **Python 3.11+** — for local development
- **AWS account** with DynamoDB access in `ap-south-1`
- **Pinecone account** with a serverless index named `voyonata-travel` (AWS `us-east-1`)
- **Groq API key** — for LLM itinerary generation
- **Gmail account** with an [App Password](https://support.google.com/accounts/answer/185833) — for OTP emails

---

## Environment Setup

Each backend service reads from its own `.env` file. Use `.env.example` at the project root as a reference.

### `backend/database/.env`
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

### `backend/auth-service/.env`
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
JWT_SECRET_KEY=a_random_secret_string
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

### `backend/rag/.env`
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=voyonata-travel
GROQ_API_KEY=your_groq_api_key
```

### `backend/user_details/.env`
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

---

## Running with Docker (recommended)

### 1. Create all `.env` files
Fill in the four `.env` files described above.

### 2. Build and start all services
```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Auth Service | http://localhost:8001 |
| Database Service | http://localhost:8000 |
| RAG Service | http://localhost:8002 |
| User Details Service | http://localhost:8003 |

### 3. Load city data into DynamoDB (first run only)
```bash
curl -X POST http://localhost:8000/admin/load-data
```

### 4. Index places into Pinecone (first run only)
```bash
curl -X POST http://localhost:8002/index
```

Both commands are idempotent — safe to re-run.

---

## Running Locally (without Docker)

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

To override backend URLs, create `frontend/.env.local`:
```env
VITE_AUTH_URL=http://localhost:8001
VITE_RAG_URL=http://localhost:8002
VITE_USER_DETAILS_URL=http://localhost:8003
VITE_DATABASE_URL=http://localhost:8000
```

### Backend Services

Each service follows the same pattern. Run them in separate terminals.

**Database Service** (port 8000)
```bash
cd backend/database
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Auth Service** (port 8001)
```bash
cd backend/auth-service
venv\Scripts\activate   # or source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**RAG Service** (port 8002)
```bash
cd backend/rag
venv\Scripts\activate   # or source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

**User Details Service** (port 8003)
```bash
cd backend/user_details
venv\Scripts\activate   # or source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

---

## First-Time Data Setup

These steps are required once after the services are running:

```bash
# 1. Load curated city JSON files from data/ into DynamoDB
curl -X POST http://localhost:8000/admin/load-data

# 2. Embed all places and upsert vectors into Pinecone
curl -X POST http://localhost:8002/index
```

After this, the app is fully operational.

---

## User Flow

1. **Sign up** — enter name, email, and password; an OTP is emailed to you
2. **Verify OTP** — enter the 6-digit code to activate your account
3. **Log in** — JWT is issued and stored for your session
4. **Plan a trip** — pick destination, dates, travelers, budget, activities, and food preferences
5. **Generate itinerary** — the RAG pipeline retrieves real places and builds a day-by-day plan
6. **View & manage trips** — saved trips are accessible from the My Trips page

---

## API Reference

### Auth Service — `localhost:8001`
| Method | Path | Description |
|---|---|---|
| `POST` | `/signup` | Send OTP to email |
| `POST` | `/verify-otp` | Verify OTP, create account |
| `POST` | `/login` | Returns JWT |
| `GET` | `/me` | Returns profile (Bearer token required) |
| `GET` | `/health` | Health check |

### Database Service — `localhost:8000`
| Method | Path | Description |
|---|---|---|
| `GET` | `/explore?city=goa` | All places for a city |
| `GET` | `/places?city=goa&category=restaurant` | Places filtered by category |
| `POST` | `/admin/load-data` | Bulk load city JSON files |
| `GET` | `/health` | Health check |

### RAG Service — `localhost:8002`
| Method | Path | Description |
|---|---|---|
| `POST` | `/itinerary` | Full AI itinerary generation |
| `POST` | `/search` | Free-text vector search |
| `POST` | `/index` | Index DynamoDB → Pinecone |
| `GET` | `/health` | Health check |

### User Details Service — `localhost:8003`
| Method | Path | Description |
|---|---|---|
| `GET` | `/plan?city=goa` | Available activity tags & food types |
| `POST` | `/plan` | Validate and submit trip preferences |
| `GET` | `/health` | Health check |

---

## Project Structure

```
.
├── docker-compose.yml
├── .env.example
├── data/                        # Curated city JSON files
├── frontend/                    # React + TypeScript app
│   ├── src/
│   │   ├── context/AuthContext.tsx
│   │   ├── pages/
│   │   ├── services/api.ts      # Typed API clients
│   │   └── types/index.ts
│   └── Dockerfile
└── backend/
    ├── auth-service/            # Port 8001
    ├── database/                # Port 8000
    ├── rag/                     # Port 8002
    └── user_details/            # Port 8003
```
