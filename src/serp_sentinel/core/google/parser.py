from dataclasses import dataclass, field
from urllib.parse import parse_qs, unquote, urlparse

from selectolax.parser import HTMLParser


@dataclass(slots=True)
class OrganicResult:
    position: int
    title: str
    url: str
    displayed_url: str = ""
    snippet: str = ""
    page: int = 1


@dataclass(slots=True)
class ParsedSerp:
    results: list[OrganicResult] = field(default_factory=list)
    features: set[str] = field(default_factory=set)
    parse_suspect: bool = False


def _unwrap(href: str) -> str:
    if href.startswith("/url?"):
        q = parse_qs(urlparse(href).query)
        return unquote((q.get("q") or q.get("url") or [href])[0])
    return href


def parse_serp(html: str, page: int = 1, start: int = 0) -> ParsedSerp:
    tree = HTMLParser(html)
    out = ParsedSerp()
    text = tree.text(separator=" ").lower()
    feature_words = {
        "people_also_ask": "people also ask",
        "ai_overview": "ai overview",
        "shopping": "shopping",
        "top_stories": "top stories",
        "images": "images",
        "videos": "videos",
    }
    for key, value in feature_words.items():
        if value in text:
            out.features.add(key)

    seen: set[str] = set()
    pos = start
    for node in tree.css("div.MjjYud, div.g"):
        classes = node.attributes.get("class") or ""
        if any(value in classes for value in ["commercial-unit", "pla-unit"]):
            continue

        link = node.css_first("a")
        heading = node.css_first("h3")
        if not link or not heading:
            continue

        href = _unwrap(link.attributes.get("href") or "")
        if not href.startswith("http") or "google." in (urlparse(href).hostname or ""):
            continue
        if href in seen:
            continue

        seen.add(href)
        pos += 1
        snippet_node = node.css_first("div.VwiC3b") or node.css_first("span")
        out.results.append(
            OrganicResult(
                position=pos,
                title=heading.text(strip=True),
                url=href,
                displayed_url=href,
                snippet=snippet_node.text(strip=True) if snippet_node else "",
                page=page,
            )
        )

    out.parse_suspect = page == 1 and len(out.results) < 5
    return out
