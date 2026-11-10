# Search Engine

A modular search engine project consisting of three core components: API, Web Crawler, and Storage.

## Architecture

```mermaid
flowchart LR
    seeds([Seed URLs]) --> crawler

    subgraph crawler [Crawler + Indexer]
        direction TB
        fetch[Fetcher<br/>robots.txt, rate limit, retries] --> extract[Extractor<br/>title, description, text, links]
        extract --> index[Indexer]
    end

    web[(Web)] <-->|HTTP| fetch
    crawler -->|"1. dedup check, save raw HTML + state"| cass[(Cassandra<br/>source of truth)]
    index -->|"2. upsert, _id = url_hash"| es[(Elasticsearch<br/>serving layer)]
    extract -.->|"new links"| fetch

    user([Browser / client]) -->|"GET /search"| api[Search API<br/>FastAPI]
    api -->|"BM25 multi_match + highlight"| es
```

## Project Structure

```text
search-engine/
├── api/       # FastAPI service + static UI
├── crawler/   # Fetcher, Extractor, Indexer
├── store/     # Cassandra schema, ES mapping, init script
└── README.md
```

## Core Components

- **API:** Handles client requests and exposes search functionality.
- **Crawler:** Fetches web pages and extracts relevant content.
- **Store:** Manages persistence and retrieval of crawled data.

## Getting started

### Prerequisites

- Python 3.10+
- A running Cassandra (default `localhost:9042`)
- A running Elasticsearch 8.x (default `localhost:9200`)

### 1. Initialize storage

Applies the Cassandra schema and creates the Elasticsearch index. Requires `cqlsh`, `curl`, and `python3` on your path.

```bash
./store/init.sh
```

### 2. Run the crawler

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r crawler/requirements.txt

SEED_URLS="https://example.com" \
ALLOWED_DOMAINS="example.com" \
python -m crawler.app.main
```

### 3. Run the Search API

```bash
pip install -r api/requirements.txt
uvicorn api.app.main:app --port 8000
```

Open <http://localhost:8000> for the UI, or query directly:

```bash
curl "http://localhost:8000/search?q=python&size=10"
```
