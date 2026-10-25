from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

_DESCRIPTION_FALLBACK_CHARS = 200


def extract(url: str, content: str) -> tuple[str, str, str, list[str]]:
    if not content:
        return "", "", "", []

    soup = BeautifulSoup(content, "lxml")

    # Extract title if present, else fallback to first h1
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    if not title:
        h1_tag = soup.find("h1")
        title = h1_tag.get_text(strip=True) if h1_tag else ""

    # Description
    description_tag = soup.find(
        "meta", attrs={"name": lambda name: name and name.lower() == "description"}
    )
    description = (
        (description_tag.get("content") or "").strip() if description_tag else ""
    )

    # Body
    for tag in soup(["script", "style", "noscript", "nav", "footer", "iframe", "head"]):
        tag.decompose()

    body = " ".join(soup.get_text(separator=" ").split())

    links: list[str] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href = tag.get("href").strip()
        if not href:
            continue

        full_url = urljoin(url, href)
        clean_url = full_url.split("#")[0]

        # Only http/https links
        if urlparse(clean_url).scheme not in ("http", "https"):
            continue

        if clean_url not in seen:
            seen.add(clean_url)
            links.append(clean_url)

    # Extract description from body if not present
    if not description:
        description = body[:_DESCRIPTION_FALLBACK_CHARS]

    return title, description, body, links
