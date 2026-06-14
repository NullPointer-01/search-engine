CREATE KEYSPACE IF NOT EXISTS search
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS search.raw_pages (
  url_hash TEXT PRIMARY KEY,
  url TEXT,
  html TEXT,
  content_type TEXT,
  fetched_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search.crawl_state (
  url_hash TEXT PRIMARY KEY,
  url TEXT,
  last_crawled_at TIMESTAMP,
  status INT
);
