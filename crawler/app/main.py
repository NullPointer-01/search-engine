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
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def run_crawler() -> None:
    store = Store(CASSANDRA_HOST, CASSANDRA_PORT, CASSANDRA_KEYSPACE)
    indexer = Indexer(ES_HOST, ES_PORT, ES_INDEX)
    fetcher = Fetcher()

    try:
        queue: deque[str] = deque()
        enqueued: set[str] = set()

        logger.info("Starting crawler")

        # Populate seed urls
        for url in SEED_URLS:
            norm_url = normalize_url(url)
            url_hash = get_url_hash(norm_url)

            if url_hash not in enqueued:
                enqueued.add(url_hash)
                queue.append(norm_url)

        while queue:
            batch: list[tuple[str, str]] = []

            # Populate batch
            while queue and len(batch) < BATCH_SIZE:
                norm_url = queue.popleft()
                url_hash = get_url_hash(norm_url)

                # Skip if domain is restricted
                parsed = urlparse(norm_url)
                if ALLOWED_DOMAINS and parsed.hostname not in ALLOWED_DOMAINS:
                    logger.info(
                        "Skipping restricted domain=%s, url=%s",
                        parsed.hostname,
                        norm_url,
                    )
                    continue

                # Skip duplicates
                try:
                    exists = store.check_exists(url_hash)
                except Exception:
                    logger.exception(
                        "Error while checking url in store, url = %s", norm_url
                    )
                    continue

                if exists:
                    logger.info(
                        "Skipping url = %s since it is already indexed", norm_url
                    )
                    continue

                batch.append((norm_url, url_hash))

            if not batch:
                continue

            # Fetch sites concurrently
            results = await asyncio.gather(
                *[fetcher.fetch(url) for url, _ in batch], return_exceptions=True
            )

            for (norm_url, url_hash), result in zip(batch, results):
                if isinstance(result, BaseException):
                    logger.warning(
                        "Error during fetch url = %s error = %r", norm_url, result
                    )
                    continue

                if result is None:
                    continue

                content_type, content, status_code = result
                try:
                    store.save_raw_page(
                        url_hash, norm_url, content_type, content, status_code
                    )
                except Exception:
                    logger.exception(
                        "Error while saving page in store, url = %s", norm_url
                    )

                try:
                    title, description, body, outgoing_urls = extract(norm_url, content)
                except Exception:
                    logger.exception("Error while extracting page, url = %s", norm_url)
                    continue

                crawled_at = datetime.now(timezone.utc)
                try:
                    indexed = indexer.index_document(
                        norm_url, url_hash, title, description, body, crawled_at
                    )
                    if not indexed:
                        logger.error(
                            "Elasticsearch index document failed, url = %s", norm_url
                        )
                except Exception:
                    logger.exception("Error while indexing page, url = %s", norm_url)

                # Add outgoing links to the queue
                for url in outgoing_urls:
                    link_url = normalize_url(url)
                    link_hash = get_url_hash(link_url)

                    if link_hash not in enqueued:
                        enqueued.add(link_hash)
                        queue.append(link_url)

    finally:
        await fetcher.close()


def main() -> None:
    asyncio.run(run_crawler())


if __name__ == "__main__":
    main()
