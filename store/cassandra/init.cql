CREATE KEYSPACE IF NOT EXISTS search
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS search.pages (
  url_hash TEXT PRIMARY KEY,
  url TEXT,
  content_type TEXT,
  content TEXT,
  status_code INT,
  created_at TIMESTAMP,
  last_crawled_at TIMESTAMP
);