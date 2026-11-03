import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from .fetcher import Fetcher, normalize_url, get_url_hash
from .extractor import extract
from .store import Store
from .indexer import Indexer
from urllib.parse import urlparse

from .config import (
    CASSANDRA_HOST,
    CASSANDRA_PORT,
    CASSANDRA_KEYSPACE,
    ES_HOST,
    ES_PORT,
    ES_INDEX,
    SEED_URLS,
    ALLOWED_DOMAINS,
    BATCH_SIZE,
    INDEX_MAX_RETRIES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, store: Store, indexer: Indexer, fetcher: Fetcher):
        self._store = store
        self._indexer = indexer
        self._fetcher = fetcher

        self._queue: deque[str] = deque()
        self._enqueued: set[str] = set()

        # (norm_url, url_hash, retry count)
        self._retry_queue: deque[tuple[str, str, int]] = deque()

    async def run(self) -> None:
        logger.info("Starting crawler")

        for url in SEED_URLS:
            self._enqueue(url)

        while self._queue or self._retry_queue:
            # Retry failed sites if main queue is empty
            if not self._queue:
                self._retry_indexing()
                continue

            batch = self._next_batch()
            if not batch:
                continue

            # Fetch sites concurrently
            results = await asyncio.gather(
                *[self._fetcher.fetch(norm_url) for norm_url, _ in batch],
                return_exceptions=True,
            )

            for (norm_url, url_hash), result in zip(batch, results):
                self._process_result(norm_url, url_hash, result)

    def _enqueue(self, url: str) -> None:
        norm_url = normalize_url(url)
        url_hash = get_url_hash(norm_url)

        if url_hash not in self._enqueued:
            self._enqueued.add(url_hash)
            self._queue.append(norm_url)

    def _next_batch(self) -> list[tuple[str, str]]:
        batch: list[tuple[str, str]] = []

        while self._queue and len(batch) < BATCH_SIZE:
            norm_url = self._queue.popleft()
            url_hash = get_url_hash(norm_url)

            if not self._should_skip(norm_url, url_hash):
                batch.append((norm_url, url_hash))

        return batch

    def _should_skip(self, norm_url: str, url_hash: str) -> bool:
        # Skip if domain is restricted
        hostname = urlparse(norm_url).hostname
        if ALLOWED_DOMAINS and hostname not in ALLOWED_DOMAINS:
            logger.info("Skipping restricted domain=%s, url=%s", hostname, norm_url)
            return True

        try:
            page = self._store.get_page(url_hash)
        except Exception:
            logger.exception("Error while checking url in store, url = %s", norm_url)
            return True

        if page is not None and page["indexed_at"] is not None:
            logger.info("Skipping url = %s since it is already indexed", norm_url)
            return True

        return False

    def _process_result(self, norm_url: str, url_hash: str, result) -> None:
        if isinstance(result, BaseException):
            logger.warning("Error during fetch url = %s error = %r", norm_url, result)
            return

        if result is None:
            return

        content_type, content, status_code = result

        try:
            self._store.save_raw_page(
                url_hash, norm_url, content_type, content, status_code
            )
            saved = True
        except Exception:
            saved = False
            logger.exception("Error while saving page in store, url = %s", norm_url)

        try:
            title, description, body, outgoing_urls = extract(norm_url, content)
        except Exception:
            logger.exception("Error while extracting page, url = %s", norm_url)
            return

        if saved:
            self._index_page(
                norm_url,
                url_hash,
                title,
                description,
                body,
                datetime.now(timezone.utc),
            )

        # Enqueue outgoing links regardless of indexing status
        for url in outgoing_urls:
            self._enqueue(url)

    def _index_page(
        self,
        norm_url: str,
        url_hash: str,
        title: str,
        description: str,
        body: str,
        crawled_at: datetime,
        retries: int = 0,
    ) -> None:
        indexed = False
        try:
            indexed = self._indexer.index_document(
                norm_url, url_hash, title, description, body, crawled_at
            )
        except Exception:
            logger.exception(
                "Error while indexing page, url = %s, retry_attempt = %s",
                norm_url,
                retries,
            )

        if not indexed:
            if retries < INDEX_MAX_RETRIES:
                self._retry_queue.append((norm_url, url_hash, retries + 1))
            return

        try:
            self._store.mark_indexed(url_hash)
        except Exception:
            logger.exception("Error while marking page as indexed, url = %s", norm_url)

    def _retry_indexing(self) -> None:
        while self._retry_queue:
            norm_url, url_hash, retries = self._retry_queue.popleft()

            try:
                page = self._store.get_page(url_hash)
            except Exception:
                logger.exception("Error while reading stored page, url = %s", norm_url)
                continue

            if page is None or page["indexed_at"] is not None:
                continue

            try:
                title, description, body, _ = extract(norm_url, page["content"])
            except Exception:
                logger.exception("Error while extracting page, url = %s", norm_url)
                continue

            self._index_page(
                norm_url,
                url_hash,
                title,
                description,
                body,
                page["last_crawled_at"] or datetime.now(timezone.utc),
                retries,
            )


async def run_crawler() -> None:
    store = Store(CASSANDRA_HOST, CASSANDRA_PORT, CASSANDRA_KEYSPACE)
    indexer = Indexer(ES_HOST, ES_PORT, ES_INDEX)
    fetcher = Fetcher()
    crawler = Crawler(store, indexer, fetcher)

    try:
        await crawler.run()
    finally:
        await fetcher.close()


def main() -> None:
    asyncio.run(run_crawler())


if __name__ == "__main__":
    main()
