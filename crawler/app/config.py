from dataclasses import dataclass
import os

@dataclass
class CassandraConfig:
    host: str
    port: int
    keyspace: str

@dataclass
class ElasticSearchConfig:
    host: str
    port: int
    index: str

@dataclass
class CrawlerConfig:
    seed_urls: list[str]
    max_pages: int
    crawl_delay: float
    user_agent: str
    timeout: int
    max_retries: int
    backoff_factor: float

@dataclass
class Config:
    cassandra_config: CassandraConfig
    elasticsearch_config: ElasticSearchConfig
    crawler_config: CrawlerConfig

def load_config() -> Config:
    cassandra = CassandraConfig(
        host=os.getenv("CASSANDRA_HOST", "localhost"),
        port=int(os.getenv("CASSANDRA_PORT", 9042)),
        keyspace=os.getenv("CASSANDRA_KEYSPACE", "search")
    )

    elastic_search = ElasticSearchConfig(
        host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
        port=int(os.getenv("ELASTICSEARCH_PORT", 9200)),
        index=os.getenv("ES_INDEX", "pages")
    )

    crawler = CrawlerConfig(
        seed_urls = os.getenv("START_URLS", "https://google.com").split(","),
        max_pages= int(os.getenv("MAX_PAGES", 100)),
        crawl_delay=float(os.getenv("CRAWL_DELAY", 1.0)),
        user_agent=os.getenv("USER_AGENT", "MyCrawler/1.0"),
        timeout=int(os.getenv("TIMEOUT", 10)),
        max_retries=int(os.getenv("MAX_RETRIES", 3)),
        backoff_factor=float(os.getenv("BACKOFF_FACTOR", 0.5))
    )

    return Config(
        cassandra_config=cassandra,
        elasticsearch_config=elastic_search,
        crawler_config=crawler
    )