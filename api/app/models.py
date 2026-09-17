from typing import Any

from pydantic import BaseModel


class SearchHit(BaseModel):
    url: str
    title: str
    desc: str
    score: float


class SearchResponse(BaseModel):
    total: int
    hits: list[SearchHit]
    time_taken_ms: float
