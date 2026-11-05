import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import SearchResponse
from .search import SearchClient

from .config import ES_HOST, ES_PORT, ES_INDEX, MAX_RESULTS, MAX_QUERY_LENGTH

_STATIC_DIR = Path(__file__).parent.parent / "static"

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

app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
async def home():
    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
    q: str = Query("", description="Search query"),
    size: int = Query(default=10, description="Number of results to return"),
):
    assert _search_client is not None

    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query must be at most {MAX_QUERY_LENGTH} characters",
        )

    if size < 1 or size > MAX_RESULTS:
        raise HTTPException(
            status_code=400, detail=f"Size must be between 1 and {MAX_RESULTS}"
        )

    try:
        hits, total, time_taken_ms = _search_client.search(q, size)
        return SearchResponse(hits=hits, total=total, time_taken_ms=time_taken_ms)
    except Exception as exc:
        logger.error("event=es_search_failed query=%s error=%s", query, exc)
        raise HTTPException(status_code=503, detail="Search service unavailable")
