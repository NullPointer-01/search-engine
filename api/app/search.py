from elasticsearch import Elasticsearch
from .models import Highlight, SearchHit

from .config import (
    HIGHLIGHT_FRAGMENTS_COUNT,
    HIGHLIGHT_FRAGMENTS_SIZE,
    HIGHLIGHT_MAX_ANALYZED_CHARS,
)


class SearchClient:
    def __init__(self, host: str, port: str, index: str):
        self._index = index
        self._client = Elasticsearch(f"http://{host}:{port}")

    def search(self, query: str, size: int) -> tuple[list[SearchHit], int, float]:
        q = {
            "multi_match": {
                "query": query,
                "fields": ["url", "title^3", "description^2", "body"],
            }
        }
        source = {"includes": ["url", "title", "description"]}
        highlight_options = {
            "encoder": "html",
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "max_analyzed_offset": HIGHLIGHT_MAX_ANALYZED_CHARS,
            "fields": {
                "title": {"number_of_fragments": 0},  # Zero brings the entire text
                "description": {"number_of_fragments": 0},
                "body": {
                    "number_of_fragments": HIGHLIGHT_FRAGMENTS_COUNT,
                    "fragment_size": HIGHLIGHT_FRAGMENTS_SIZE,
                },
            },
        }

        resp = self._client.search(
            index=self._index,
            query=q,
            source=source,
            highlight=highlight_options,
            size=size,
        )

        hits: list[SearchHit] = []

        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            url = src["url"]
            title = src.get("title", "")
            desc = src.get("description", "")
            score = hit["_score"]

            matched = hit.get("highlight", {})
            highlight = Highlight(
                title=_first(matched, "title"),
                description=_first(matched, "description"),
                body=matched.get("body", []),
            )

            hits.append(
                SearchHit(
                    url=url, title=title, desc=desc, score=score, highlight=highlight
                )
            )

        total = resp["hits"]["total"]["value"]
        time_taken_ms = resp["took"]

        return hits, total, time_taken_ms


def _first(matched: dict, field: str) -> str:
    fragments = matched.get(field)
    return fragments[0] if fragments else ""
