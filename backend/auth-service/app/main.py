from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError
from botocore.exceptions import ClientError

from .dynamodb import (
    create_table_if_not_exists, get_user, create_user,
    create_itinerary_table_if_not_exists,
    upsert_itinerary, delete_itinerary_record, list_itineraries, get_itinerary_data,
)
from .security import hash_password, verify_password, create_access_token, decode_access_token
from .models import SignupRequest, LoginRequest, TokenResponse, UserResponse, SaveItineraryRequest, ItinerarySummary


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table_if_not_exists()
    create_itinerary_table_if_not_exists()
    yield


app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan, debug=True)
bearer_scheme = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}


@app.post("/signup", response_model=TokenResponse, status_code=201)
def signup(body: SignupRequest):
    try:
        existing = get_user(body.email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB read error: {e}")

    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_pw = hash_password(body.password)
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        create_user(
            email=body.email,
            hashed_password=hashed_pw,
            full_name=body.full_name,
            created_at=created_at,
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"DB write error: {code} - {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    token = create_access_token({"sub": body.email.lower()})
    return TokenResponse(access_token=token)


@app.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = get_user(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user["email"]})
    return TokenResponse(access_token=token)


def _require_email(credentials: HTTPAuthorizationCredentials) -> str:
    try:
        payload = decode_access_token(credentials.credentials)
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/me", response_model=UserResponse)
def me(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload = decode_access_token(credentials.credentials)
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(email=user["email"], full_name=user["full_name"], created_at=user["created_at"])


# ── Itinerary CRUD ─────────────────────────────────────────────────────────────

@app.get("/itineraries", response_model=list[ItinerarySummary])
def get_itineraries(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    email = _require_email(credentials)
    return list_itineraries(email)


@app.post("/itineraries", status_code=201)
def save_itinerary(body: SaveItineraryRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    email = _require_email(credentials)
    upsert_itinerary(email, body.itinerary_id, body.data)
    return {"itinerary_id": body.itinerary_id}


@app.put("/itineraries/{itinerary_id}")
def update_itinerary(itinerary_id: str, body: SaveItineraryRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    email = _require_email(credentials)
    upsert_itinerary(email, itinerary_id, body.data)
    return {"message": "updated"}


@app.delete("/itineraries/{itinerary_id}")
def delete_itinerary(itinerary_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    email = _require_email(credentials)
    delete_itinerary_record(email, itinerary_id)
    return {"message": "deleted"}
