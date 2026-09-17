from elasticsearch import Elasticsearch
from .models import SearchHit, SearchResponse


class SearchClient:
    def __init__(self, host: str, port: str, index: str):
        self._index = index
        self._client = Elasticsearch(f"http://{host}:{port}")

    def search(self, query: str, size: int) -> tuple[list[SearchHit], int, float]:
        q = {
            "multi_match": {
                "query": query,
                "fields": ["url", "title^3", "description^2"],
            }
        }
        source = {"includes": ["url", "title", "description"]}
        resp = self._client.search(index=self._index, query=q, source=source, size=size)

        hits: list[SearchHit] = []

        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            url = src["url"]
            title = src.get("title", "")
            desc = src.get("description", "")
            score = hit["_score"]

            hits.append(SearchHit(url=url, title=title, desc=desc, score=score))

        total = resp["hits"]["total"]["value"]
        time_taken_ms = resp["took"]

        return hits, total, time_taken_ms
