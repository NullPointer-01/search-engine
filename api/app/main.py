import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from .models import SearchResponse
from .search import SearchClient

from .config import ES_HOST, ES_PORT, ES_INDEX, MAX_RESULTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
_search_client: SearchClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _search_client
    _search_client = SearchClient(ES_HOST, ES_PORT, ES_INDEX)
    yield


app = FastAPI(
    title="Search Engine API",
    version="1.0.0",
    description="Search over crawled web pages",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


@app.get("/")
async def home():
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=20, description="Search query"),
    size: int = Query(
        default=10, ge=1, le=MAX_RESULTS, description="Number of results to return"
    ),
):

    assert _search_client is not None

    try:
        hits, total, time_taken_ms = _search_client.search(q, size)
        return SearchResponse(hits=hits, total=total, time_taken_ms=time_taken_ms)
    except Exception as exc:
        logger.error("event=es_search_failed query=%s error=%s", q, exc)
        raise HTTPException(status_code=503, detail="Search service unavailable")
