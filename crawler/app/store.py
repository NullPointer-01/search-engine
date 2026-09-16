from cassandra.cluster import Cluster
from datetime import datetime, timezone


class Store:
    def __init__(self, host: str, port: str, keyspace: str):
        self._cluster = Cluster(contact_points=[host], port=port)
        self._session = self._cluster.connect(keyspace)

        self._insert_raw_page = self._session.prepare("""
        INSERT INTO pages (url_hash, url, content_type, content, status_code, created_at, last_crawled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """)

    def save_raw_page(
        self, url_hash: str, url: str, content_type: str, content: str, status_code: int
    ):
        session = self._session
        now = datetime.now(tz=timezone.utc)

        try:
            session.execute(
                self._insert_raw_page,
                (url_hash, url, content_type, content, status_code, now, now),
            )
        except Exception:
            raise
