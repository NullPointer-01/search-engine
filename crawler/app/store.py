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

        self._check_page_exists = self._session.prepare("""
        SELECT url_hash FROM pages WHERE url_hash = ?
        """)

        self._select_page = self._session.prepare("""
        SELECT url_hash, url, content, last_crawled_at, indexed_at FROM pages WHERE url_hash = ?
        """)

        self._update_indexed_at = self._session.prepare("""
        UPDATE pages SET indexed_at = ? WHERE url_hash = ?
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

    def check_exists(self, url_hash: str) -> bool:
        session = self._session
        try:
            rows = session.execute(self._check_page_exists, (url_hash,))
            return rows.one() is not None
        except Exception:
            raise

    def get_page(self, url_hash: str) -> dict | None:
        session = self._session

        try:
            row = session.execute(self._select_page, (url_hash,)).one()
            if not row:
                return None

            return {
                "url": row.url,
                "content": row.content,
                "last_crawled_at": _as_utc(row.last_crawled_at),
                "indexed_at": _as_utc(row.indexed_at),
            }
        except Exception:
            raise

    def mark_indexed(self, url_hash: str) -> None:
        session = self._session
        now = datetime.now(tz=timezone.utc)

        try:
            session.execute(self._update_indexed_at, (now, url_hash))
        except Exception:
            raise


# Helper methods
def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

    return value
