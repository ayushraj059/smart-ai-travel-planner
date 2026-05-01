import logging
import traceback
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .dynamodb import scan_all_places
from .embeddings import build_document, embed_texts, embed_one, embed_user_plan, build_user_query
from .pinecone_client import upsert_places, query_index
from .itinerary import build_itinerary
from .validator import validate_and_fix
from .models import (
    IndexResponse, SearchRequest, TripPlanSearchRequest, SearchResponse,
    PlaceResult, ItineraryRequest, ItineraryResponse,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("RAG service starting up")
    yield


app = FastAPI(title="Voyonata RAG Pipeline", version="1.0.0", lifespan=lifespan)

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
    return {"status": "ok", "service": "rag"}


@app.post("/index", response_model=IndexResponse)
def index_data():
    """
    Pull every place from DynamoDB, embed with sentence-transformers,
    and upsert into Pinecone. Safe to call multiple times (upsert is idempotent).
    """
    try:
        log.info("Scanning DynamoDB travel_data table...")
        places = scan_all_places()
        if not places:
            raise HTTPException(status_code=404, detail="No data found in DynamoDB travel_data table")
        log.info(f"Fetched {len(places)} places from DynamoDB")

        log.info("Building documents and generating embeddings...")
        documents = [build_document(p) for p in places]
        vectors = embed_texts(documents)
        log.info(f"Generated {len(vectors)} embedding vectors")

        log.info("Upserting vectors to Pinecone...")
        upserted = upsert_places(places, vectors)
        log.info(f"Upserted {upserted} vectors to Pinecone")

        return IndexResponse(
            message="Indexing complete",
            total_fetched=len(places),
            total_upserted=upserted,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Index failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    """
    Embed the query and perform a vector search against Pinecone.
    Optionally filter by city and/or category using Pinecone metadata filters.
    """
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="Query must not be empty")

    try:
        query_vec = embed_one(req.query)

        pinecone_filter = None
        conditions = {}
        if req.city:
            conditions["city"] = {"$eq": req.city.lower()}
        if req.category:
            conditions["category"] = {"$eq": req.category.lower()}
        if conditions:
            pinecone_filter = conditions

        raw = query_index(vector=query_vec, top_k=req.top_k, filter=pinecone_filter)

        results = []
        for r in raw:
            try:
                results.append(PlaceResult(**r))
            except Exception:
                continue

        return SearchResponse(query=req.query, total=len(results), results=results)
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Search failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/plan", response_model=SearchResponse)
def search_by_plan(req: TripPlanSearchRequest):
    """
    Accept a full user trip plan (same shape as user_details POST /plan),
    convert it to a natural-language query via build_user_query(), embed it,
    and return semantically matched places from Pinecone.
    """
    try:
        plan = req.model_dump()
        query_text = build_user_query(plan)
        log.info(f"Plan query: '{query_text}'")

        query_vec = embed_user_plan(plan)

        pinecone_filter = {"city": {"$eq": req.city.lower()}}
        if req.category:
            pinecone_filter["category"] = {"$eq": req.category.lower()}

        raw = query_index(vector=query_vec, top_k=req.top_k, filter=pinecone_filter)

        results = []
        for r in raw:
            try:
                results.append(PlaceResult(**r))
            except Exception:
                continue

        return SearchResponse(query=query_text, total=len(results), results=results)
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Plan search failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/itinerary", response_model=ItineraryResponse)
def generate_itinerary(req: ItineraryRequest):
    """
    Full RAG pipeline endpoint:
      1. Embed user trip plan → retrieve top-30 relevant places from Pinecone
      2. Pass retrieved places + constraints to Groq LLM → day-wise itinerary JSON
      3. Validate: sort by time, resolve overlaps, recalculate costs & budget_status
      4. Return structured ItineraryResponse
    """
    try:
        plan = req.model_dump()
        log.info(f"Generating itinerary for {req.city} ({req.start_date} → {req.end_date})")

        itinerary = build_itinerary(plan)
        itinerary = validate_and_fix(itinerary, plan)

        log.info(
            f"Itinerary ready — {itinerary.num_days} days, "
            f"{sum(len(d.activities) for d in itinerary.days)} activities, "
            f"status={itinerary.summary.budget_status}"
        )
        return itinerary
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Itinerary generation failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
