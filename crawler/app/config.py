import os

# CASSANDRA
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_PORT = os.getenv("CASSANDRA_PORT", "9042")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "search")

# ELASTICSEARCH
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = os.getenv("ES_PORT", "9200")
ES_INDEX = os.getenv("ES_INDEX", "search")

_seed_urls_raw = os.getenv("SEED_URLS", "http://localhost:20000")
SEED_URLS: list[str] = [url.strip() for url in _seed_urls_raw.split(",") if url.strip()]

_allowed_domains_raw = os.getenv("ALLOWED_DOMAINS", "")
ALLOWED_DOMAINS: set[str] = {
    url.strip() for url in _allowed_domains_raw.split(",") if url.strip()
}

USER_AGENT = os.getenv("USER_AGENT", "MyCrawler/1.0")

# RETRIES
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "1.0"))
MAX_REDIRECTS = int(os.getenv("MAX_REDIRECTS", "5"))
FETCH_TIMEOUT = float(os.getenv("FETCH_TIMEOUT", "10"))

# ROBOTS
ROBOTS_MAX_BYTES = int(os.getenv("ROBOTS_MAX_BYTES", str(512 * 1024)))
ROBOTS_TTL = float(os.getenv("ROBOTS_TTL", "3600"))
ROBOTS_ERROR_TTL = float(os.getenv("ROBOTS_ERROR_TTL", "300"))
