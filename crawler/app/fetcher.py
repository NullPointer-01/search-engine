import asyncio
import aiohttp
import hashlib
import logging
import random
import time

from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from urllib.robotparser import RobotFileParser
from .config import (
    MAX_RETRIES,
    RETRY_BACKOFF,
    FETCH_TIMEOUT,
    USER_AGENT,
    MAX_REDIRECTS,
    ROBOTS_MAX_BYTES,
    ROBOTS_TTL,
    ROBOTS_ERROR_TTL,
    CRAWL_DELAY,
    MAX_CRAWL_DELAY,
)

logger = logging.getLogger(__name__)

_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
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
        # origin -> (parser, expires_at); parser None means "disallow all"
        self._robots: dict[str, tuple[RobotFileParser | None, float]] = {}

        self._crawl_delay: dict[str, float] = {}
        self._last_request_time: dict[str, float] = {}

    def _get_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=FETCH_TIMEOUT)
            headers = {"User-Agent": USER_AGENT}

            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)

        return self._session

    def _origin(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _cache_robots(
        self, origin: str, parser: RobotFileParser | None, ttl: float
    ) -> None:
        self._robots[origin] = (parser, time.monotonic() + ttl)

        delay = parser.crawl_delay(USER_AGENT) if parser is not None else None
        self._crawl_delay[origin] = delay or 0

    async def _load_robots(self, origin: str) -> RobotFileParser | None:
        session = self._get_session()
        try:
            async with session.get(
                f"{origin}/robots.txt",
                allow_redirects=True,
                max_redirects=MAX_REDIRECTS,
            ) as resp:
                status = resp.status

                if status == 200:
                    raw = await resp.content.read(ROBOTS_MAX_BYTES)
                    parser = RobotFileParser()
                    parser.parse(raw.decode("utf-8", errors="ignore").splitlines())
                    self._cache_robots(origin, parser, ROBOTS_TTL)
                    return parser

                # No robots.txt means everything is allowed
                if 400 <= status < 500:
                    parser = RobotFileParser()
                    parser.parse([])
                    self._cache_robots(origin, parser, ROBOTS_TTL)
                    return parser

                logger.warning(
                    "robots.txt unavailable origin=%s status=%s", origin, status
                )

        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            logger.warning("Failed to fetch robots.txt origin=%s error=%s", origin, exc)

        # If unreachable, disallow all, re-check after TTL
        self._cache_robots(origin, None, ROBOTS_ERROR_TTL)
        return None

    async def _throttle(self, origin: str) -> None:
        elapsed = time.monotonic() - self._last_request_time.get(origin, 0)
        delay = max(CRAWL_DELAY, self._crawl_delay.get(origin, 0))

        # Cap delay to avoid indefinite sleep
        delay = min(delay, MAX_CRAWL_DELAY)

        if elapsed < delay:
            wait = delay - elapsed
            await asyncio.sleep(wait)

    async def _is_allowed(self, url: str) -> bool:
        origin = self._origin(url)
        cached = self._robots.get(origin)
        parser = None

        if cached is None or cached[1] < time.monotonic():
            parser = await self._load_robots(origin)
        else:
            parser = cached[0]

        if parser is None:
            return False

        return parser.can_fetch(USER_AGENT, url)

    async def fetch(self, url: str) -> tuple[str, str, int] | None:
        # Check robots.txt
        if not await self._is_allowed(url):
            logger.info("Url disallowed: %s", url)
            return None

        session = self._get_session()
        origin = self._origin(url)

        for attempt in range(MAX_RETRIES + 1):
            status = None
            await self._throttle(origin)
            self._last_request_time[origin] = time.monotonic()

            try:
                async with session.get(
                    url, allow_redirects=True, max_redirects=MAX_REDIRECTS
                ) as resp:
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "")

                    if status == 200 and "text/html" in content_type:
                        content = await resp.text()
                        return content_type, content, status

                    if status not in _RETRY_STATUSES:
                        return None

            except asyncio.TimeoutError as exc:
                logger.warning("Request timed out url=%s error=%s", url, exc)

            except aiohttp.TooManyRedirects:
                logger.warning("Too many redirects url=%s", url)
                return None

            except aiohttp.ClientResponseError as exc:
                logger.warning(
                    "HTTP error url=%s status=%s error=%s", url, exc.status, exc.message
                )

            except aiohttp.ClientError as exc:
                logger.warning("Url fetch failed, url=%s error=%s", url, exc)

            # Skip sleep in last attempt
            if attempt < MAX_RETRIES:
                # Exponential backoff with jitter
                delay = RETRY_BACKOFF * (2**attempt) + random.uniform(0, 0.5)
                logger.warning(
                    "Retrying fetch url=%s status=%s attempt=%d",
                    url,
                    status,
                    attempt + 1,
                )
                await asyncio.sleep(delay)

        logger.error("Fetch failed url=%s", url)
        return None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
