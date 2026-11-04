from typing import Any

from pydantic import BaseModel, Field


class Highlight(BaseModel):
    title: str = ""
    description: str = ""
    body: list[str] = Field(default_factory=list)


class SearchHit(BaseModel):
    url: str
    title: str
    desc: str
    score: float
    highlight: Highlight = Field(default_factory=Highlight)


class SearchResponse(BaseModel):
    total: int
    hits: list[SearchHit]
    time_taken_ms: float
