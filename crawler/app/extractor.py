from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def extract(url: str, content: str) -> tuple[str, str, str, list[str]]:
    soup = BeautifulSoup(content, "lxml")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Description
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content") if description_tag else ""

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

        if clean_url and clean_url not in seen:
            seen.add(clean_url)
            links.append(clean_url)

    return title, description, body, links
