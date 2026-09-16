import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from .fetcher import Fetcher, normalize_url, get_url_hash
from .extractor import extract
from .store import Store
from .indexer import Indexer

from .config import (
    CASSANDRA_HOST,
    CASSANDRA_PORT,
    CASSANDRA_KEYSPACE,
    ES_HOST,
    ES_PORT,
    ES_INDEX,
    SEED_URLS,
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

        for url in SEED_URLS:
            norm_url = normalize_url(url)
            urL_hash = get_url_hash(norm_url)

            if urL_hash not in enqueued:
                enqueued.add(urL_hash)
                queue.append(norm_url)

        while queue:
            norm_url = queue.popleft()
            url_hash = get_url_hash(norm_url)
            result = await fetcher.fetch(norm_url)

            if result is None:
                continue

            content_type, content, status_code = result
            try:
                store.save_raw_page(
                    url_hash, norm_url, content_type, content, status_code
                )
            except:
                pass

            title, description, body, outgoing_urls = extract(norm_url, content)

            crawled_at = datetime.now(timezone.utc)
            indexed = indexer.index_document(
                norm_url, url_hash, title, description, body, crawled_at
            )

            for url in outgoing_urls:
                norm_url = normalize_url(url)
                urL_hash = get_url_hash(norm_url)

                if norm_url not in enqueued:
                    enqueued.add(norm_url)
                    queue.append(norm_url)

    finally:
        await fetcher.close()


def main() -> None:
    asyncio.run(run_crawler())


if __name__ == "__main__":
    main()
