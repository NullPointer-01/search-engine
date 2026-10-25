import logging
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch import ApiError

logger = logging.getLogger(__name__)


class Indexer:
    def __init__(self, host: str, port: str, index: str):
        self._index = index
        self._client = Elasticsearch(f"http://{host}:{port}")

    def index_document(
        self,
        norm_url: str,
        url_hash: str,
        title: str,
        desc: str,
        body: str,
        crawled_at: datetime,
    ) -> bool:
        doc = {
            "url": norm_url,
            "title": title,
            "description": desc,
            "body": body,
            "crawled_at": crawled_at.isoformat(),
        }

        try:
            self._client.index(index=self._index, id=url_hash, document=doc)
            return True
        except ApiError as exc:
            logger.error(
                "Elasticsearch index failed for document url = %s status = %s error = %s",
                norm_url,
                exc.status_code,
                exc.message,
            )
            return False
