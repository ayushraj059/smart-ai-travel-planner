# Database Service — Voyonata Travel Data API

This microservice is responsible for seeding and querying the AWS DynamoDB `travel_data` table. It exposes a REST API for other services to fetch travel places (attractions, restaurants, hotels, etc.) by city and category.

---

## Responsibilities

- Creates and manages the `travel_data` DynamoDB table
- Batch-loads city travel data from JSON files into DynamoDB
- Exposes query endpoints consumed by other microservices (e.g., itinerary planner, search)

---

## Tech Stack

| Layer       | Technology                     |
|-------------|-------------------------------|
| Framework   | FastAPI                        |
| Database    | AWS DynamoDB (PAY_PER_REQUEST) |
| AWS Client  | boto3                          |
| Config      | pydantic-settings (.env)       |
| Server      | uvicorn                        |

---

## DynamoDB Schema

**Table:** `travel_data`  
**Region:** `ap-south-1`

| Attribute       | Type   | Role       |
|----------------|--------|------------|
| `city`          | String | Partition Key (HASH) |
| `category_name` | String | Sort Key (RANGE) — format: `{category}#{name}` |

Additional attributes stored per item: `name`, `category`, `country`, `lat`, `lon`, `address`, `formatted_address`, `website`, `source`.

---

## Endpoints

| Method | Path                   | Description                              |
|--------|------------------------|------------------------------------------|
| GET    | `/health`              | Health check                             |
| GET    | `/explore?city=`       | All places for a given city              |
| GET    | `/places?city=&category=` | Places filtered by city + category   |
| POST   | `/admin/load-data`     | Load all city JSON files into DynamoDB   |

### Example Requests

```bash
# Health check
curl http://localhost:8000/health

# All places in Goa
curl "http://localhost:8000/explore?city=Goa"

# Restaurants in Goa
curl "http://localhost:8000/places?city=Goa&category=restaurant"

# Seed the database from /data JSON files
curl -X POST http://localhost:8000/admin/load-data
```

---

## Project Structure

```
database/
├── app/
│   ├── __init__.py       # Package init
│   ├── config.py         # AWS credentials via pydantic-settings
│   ├── dynamodb.py       # Table creation, batch writes, queries
│   ├── loader.py         # JSON → DynamoDB pipeline
│   ├── main.py           # FastAPI app + endpoints
│   └── models.py         # Pydantic response models
├── .env                  # Local secrets (never commit)
├── .env.example          # Template for environment variables
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Setup & Running

### 1. Create and activate a virtual environment

```bash
cd backend/database
python -m venv venv
source venv/Scripts/activate   # Windows (bash)
# or
source venv/bin/activate        # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your AWS credentials:

```bash
cp .env.example .env
```

`.env.example`:
```
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 4. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Load data into DynamoDB

After the server is running, seed the database:

```bash
curl -X POST http://localhost:8000/admin/load-data
```

This reads all `.json` files from the `/data` directory (two levels up from this folder) and writes them to DynamoDB in batches of 25.

---

## Data Format

Each city JSON file in `/data` must follow this structure:

```json
{
  "city": "Goa",
  "data": [
    {
      "name": "Baga Beach",
      "category": "attraction",
      "country": "India",
      "lat": 15.5553,
      "lon": 73.7527
    }
  ]
}
```

The `data` field can also be a nested dict (e.g., `{"attractions": [...], "restaurants": [...]}`). Both formats are handled automatically by the loader.

---

## Notes

- All city names are stored and queried in **lowercase**.
- Writes are idempotent — re-running `/admin/load-data` overwrites existing records (no duplicates).
- `lat`/`lon` values are stored as `Decimal` in DynamoDB and returned as `float` in API responses.
- Do **not** commit `.env` to version control. Add it to `.gitignore`.
