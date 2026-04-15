"""
RAG Pipeline — Pinecone vector store + sentence-transformer embeddings.

Flow:
  1. On first call: encode all dataset places → upsert into Pinecone
  2. On each request: encode user query → cosine-search Pinecone → return top-k places
  3. Fallback: if Pinecone unavailable → keyword filter on local dataset

This ensures the system NEVER crashes due to missing Pinecone credentials.
"""

import logging
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.dataset import PLACES_DATASET, PLACES_BY_ID

logger = logging.getLogger(__name__)


class RAGService:
    """Lazy-initialised singleton RAG service."""

    _instance: Optional["RAGService"] = None

    def __init__(self):
        self._pc = None
        self._index = None
        self._encoder: Optional[SentenceTransformer] = None
        self._ready = False

    @classmethod
    def get(cls) -> "RAGService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Init ───────────────────────────────────────────────────────────────────

    def _ensure_ready(self):
        if self._ready:
            return
        try:
            from pinecone import Pinecone, ServerlessSpec
            self._encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            existing = [i.name for i in pc.list_indexes()]
            if settings.PINECONE_INDEX not in existing:
                pc.create_index(
                    name=settings.PINECONE_INDEX,
                    dimension=384,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
            self._index = pc.Index(settings.PINECONE_INDEX)
            self._upsert_dataset()
            self._ready = True
            logger.info("RAGService ready (Pinecone)")
        except Exception as e:
            logger.warning(f"RAGService Pinecone init failed — using fallback: {e}")

    def _place_to_text(self, p: Dict[str, Any]) -> str:
        return (
            f"{p['name']} in {p['city']}, {p['country']}. "
            f"Category: {p['category']}. {p['description']} "
            f"Price: ${p['price_usd']}. Duration: {p['duration_min']}–{p['duration_max']} hrs. "
            f"{'Indoor' if p['indoor'] else 'Outdoor'}."
        )

    def _upsert_dataset(self):
        vectors = []
        for p in PLACES_DATASET:
            vec = self._encoder.encode(self._place_to_text(p)).tolist()
            vectors.append({
                "id": p["id"], "values": vec,
                "metadata": {"city": p["city"], "category": p["category"], "name": p["name"]},
            })
        for i in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[i:i+100])
        logger.info(f"Upserted {len(vectors)} places into Pinecone")

    # ── Public ─────────────────────────────────────────────────────────────────

    def retrieve(self, query: str, city_filter: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        self._ensure_ready()
        if not self._ready:
            return self._fallback(city_filter, top_k)
        try:
            vec = self._encoder.encode(query).tolist()
            filt = {"city": {"$eq": city_filter}} if city_filter else None
            res = self._index.query(vector=vec, top_k=top_k, include_metadata=True, filter=filt)
            places = [
                {**PLACES_BY_ID[m.id], "relevance_score": m.score}
                for m in res.matches if m.id in PLACES_BY_ID
            ]
            logger.info(f"RAG retrieved {len(places)} places")
            return places
        except Exception as e:
            logger.warning(f"Pinecone query failed: {e} — using fallback")
            return self._fallback(city_filter, top_k)

    def _fallback(self, city_filter: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        places = PLACES_DATASET
        if city_filter:
            places = [p for p in places if p["city"].lower() == city_filter.lower()]
        return places[:top_k]
