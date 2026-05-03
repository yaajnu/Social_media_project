"""
News researcher module.

Fetches relevant news articles for a given topic using the Google News RSS feed.
No API key required — uses the public GNews RSS endpoint.
"""

import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass


class ResearchError(Exception):
    """Raised when news research fails."""

    pass


@dataclass
class NewsArticle:
    """A news article with title, source, and snippet."""

    title: str
    source: str
    snippet: str
    url: str
    pub_date: str


def _parse_traffic(t: dict) -> float:
    raw = t.get("traffic", "0").replace(",", "").replace("+", "").strip()
    try:
        if raw.upper().endswith("M"):
            return float(raw[:-1]) * 1_000_000
        if raw.upper().endswith("K"):
            return float(raw[:-1]) * 1_000
        return float(raw) if raw else 0.0
    except ValueError:
        return 0.0


def pick_top_topic(topics: list[dict]) -> dict:
    """Pick the single most trending topic by traffic."""
    if not topics:
        raise ResearchError("No topics provided to pick_top_topic.")
    return pick_top_topics(topics, n=1)[0]


def pick_top_topics(topics: list[dict], n: int = 5) -> list[dict]:
    """
    Pick the top-n trending topics sorted by traffic (descending).

    Args:
        topics: List of topic dicts with at least a 'title' key.
        n: Number of top topics to return.

    Returns:
        List of up to n topic dicts, sorted highest traffic first.
    """
    if not topics:
        raise ResearchError("No topics provided to pick_top_topics.")
    return sorted(topics, key=_parse_traffic, reverse=True)[:n]


def fetch_news_articles(topic: str, limit: int = 5) -> list[NewsArticle]:
    """
    Fetch recent news articles about a topic from Google News RSS.

    Args:
        topic: The search query / topic title.
        limit: Maximum number of articles to return.

    Returns:
        List of NewsArticle objects.

    Raises:
        ResearchError: On HTTP errors or parse failures.
    """
    query = urllib.parse.quote(topic)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_xml = resp.read()
    except urllib.error.HTTPError as exc:
        raise ResearchError(
            f"HTTP {exc.code} fetching news for '{topic}': {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ResearchError(
            f"Network error fetching news for '{topic}': {exc.reason}"
        ) from exc
    except Exception as exc:
        raise ResearchError(f"Failed to fetch news for '{topic}': {exc}") from exc

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise ResearchError(f"Failed to parse Google News RSS: {exc}") from exc

    articles: list[NewsArticle] = []
    for item in root.findall(".//item")[:limit]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pubdate_el = item.find("pubDate")
        source_el = item.find("source")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        url_val = link_el.text.strip() if link_el is not None and link_el.text else ""
        pub_date = (
            pubdate_el.text.strip()
            if pubdate_el is not None and pubdate_el.text
            else ""
        )
        source = (
            source_el.text.strip()
            if source_el is not None and source_el.text
            else "Unknown"
        )

        # Strip HTML tags from description
        raw_desc = desc_el.text or "" if desc_el is not None else ""
        snippet = _strip_html(raw_desc).strip()

        if title:
            articles.append(
                NewsArticle(
                    title=title,
                    source=source,
                    snippet=snippet[:300],  # cap snippet length
                    url=url_val,
                    pub_date=pub_date,
                )
            )

    return articles


def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    import re

    return re.sub(r"<[^>]+>", "", text)


def format_articles_for_prompt(articles: list[NewsArticle]) -> str:
    """Format a list of articles into a readable block for LLM prompts."""
    if not articles:
        return "No news articles found."
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. [{a.source}] {a.title}")
        if a.snippet:
            lines.append(f"   {a.snippet}")
    return "\n".join(lines)
