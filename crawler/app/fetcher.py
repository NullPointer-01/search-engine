import asyncio
import aiohttp
import hashlib
import logging
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from .config import FETCH_TIMEOUT

logger = logging.getLogger(__name__)

_STRIPPED_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "ref",
    }
)


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""
    params_dict = parse_qs(parsed.query, keep_blank_values=False)
    filtered = {k: v for k, v in params_dict.items() if k not in _STRIPPED_PARAMS}
    clean_query = urlencode(sorted(filtered.items()), doseq=True)

    return urlunparse((scheme, netloc, path, "", clean_query, ""))


def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


class Fetcher:
    def __init__(self):
        self._session: aiohttp.ClientSession = None

    def _get_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=FETCH_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)

        return self._session

    async def fetch(self, url: str) -> tuple[str, str, str] | None:
        session = self._get_session()
        async with session.get(url, allow_redirects=True) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")

            if status == 200 and "text/html" in content_type:
                content = await resp.text()
                return content_type, content, status

            return None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
