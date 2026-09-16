import os

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_PORT = os.getenv("CASSANDRA_PORT", "9042")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "search")

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = os.getenv("ES_PORT", "9200")
ES_INDEX = os.getenv("ES_INDEX", "search")

_seed_urls_raw = os.getenv("SEED_URLS", "http://localhost:20000")
SEED_URLS: list[str] = [url.strip() for url in _seed_urls_raw.split(",") if url.strip()]

_allowed_domains_raw = os.getenv("ALLOWED_DOMAINS", "")
ALLOWED_DOMAINS = [
    url.strip() for url in _allowed_domains_raw.split(",") if url.strip()
]

FETCH_TIMEOUT = float(os.getenv("FETCH_TIMEOUT", "10"))
