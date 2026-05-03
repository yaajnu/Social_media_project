"""
Google Trends scraper module for fetching daily trending searches.

Uses the public Google Trends RSS/JSON feed — no API key or authentication required.
Endpoint: https://trends.google.com/trending/rss?geo={geo}
"""

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime


class ScraperError(Exception):
    """Raised when scraping fails due to HTTP errors or parse failures."""

    pass


# Geo codes supported by Google Trends daily trending RSS
GEO_OPTIONS = {
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
    "Australia": "AU",
    "India": "IN",
    "Germany": "DE",
    "France": "FR",
    "Japan": "JP",
    "Brazil": "BR",
    "Mexico": "MX",
}


def get_mock_trending_topics(geo: str = "US") -> list[dict]:
    """
    Return hardcoded mock trending topics for offline/test use.

    Args:
        geo: Country geo code (ignored; mock data is always returned).

    Returns:
        List of dicts with keys: title, traffic, description, url, pub_date.
    """
    return [
        {
            "title": "AI regulation bills gaining momentum in Congress",
            "traffic": "500K+",
            "description": "Several bipartisan AI safety bills have advanced through committee.",
            "url": "https://news.google.com/search?q=AI+regulation",
            "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        },
        {
            "title": "New open-source LLM beats GPT-4 on benchmarks",
            "traffic": "200K+",
            "description": "Researchers released a model outperforming GPT-4 on HumanEval.",
            "url": "https://news.google.com/search?q=open+source+LLM",
            "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        },
        {
            "title": "Major cloud outage affects millions of users",
            "traffic": "300K+",
            "description": "A leading cloud provider suffered a 6-hour outage.",
            "url": "https://news.google.com/search?q=cloud+outage",
            "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        },
        {
            "title": "Quantum computing milestone: 1000-qubit processor",
            "traffic": "150K+",
            "description": "Researchers demonstrated a 1000-qubit processor with sub-0.1% error rates.",
            "url": "https://news.google.com/search?q=quantum+computing",
            "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        },
        {
            "title": "Electric vehicles outsell gasoline cars in Europe",
            "traffic": "250K+",
            "description": "EVs now account for 51% of new car registrations across the EU.",
            "url": "https://news.google.com/search?q=electric+vehicles+Europe",
            "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        },
    ]


def get_trending_topics(geo: str = "US", limit: int = 10) -> list[dict]:
    """
    Fetch daily trending searches from Google Trends RSS feed.

    Args:
        geo: Country geo code (e.g. "US", "GB", "IN"). Defaults to "US".
        limit: Maximum number of trending topics to return.

    Returns:
        List of dicts with keys: title, traffic, description, url, pub_date.

    Raises:
        ScraperError: On HTTP errors, network failures, or parse errors.
    """
    url = f"https://trends.google.com/trending/rss?geo={geo}"

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
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 429:
                raise ScraperError(
                    "Rate limited by Google Trends. Please wait before retrying."
                )
            if response.status == 404:
                raise ScraperError(f"Google Trends feed not found for geo: {geo}")
            if response.status != 200:
                raise ScraperError(
                    f"HTTP {response.status} from Google Trends for geo: {geo}"
                )
            raw_xml = response.read()
    except ScraperError:
        raise
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise ScraperError(
                "Rate limited by Google Trends. Please wait before retrying."
            ) from exc
        raise ScraperError(
            f"HTTP {exc.code} fetching Google Trends for geo '{geo}': {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ScraperError(
            f"Network error fetching Google Trends for geo '{geo}': {exc.reason}"
        ) from exc
    except Exception as exc:
        raise ScraperError(
            f"Failed to fetch Google Trends for geo '{geo}': {exc}"
        ) from exc

    # Parse the RSS XML
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise ScraperError(f"Failed to parse Google Trends RSS XML: {exc}") from exc

    # Google Trends RSS namespace for traffic data
    ht_ns = "https://trends.google.com/trending/rss"

    items = root.findall(".//item")
    if not items:
        raise ScraperError(
            f"No trending topics found in Google Trends feed for geo: {geo}"
        )

    topics: list[dict] = []
    for item in items[:limit]:
        title_el = item.find("title")
        desc_el = item.find("description")
        link_el = item.find("link")
        pubdate_el = item.find("pubDate")
        traffic_el = item.find(f"{{{ht_ns}}}approx_traffic")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        description = (
            desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        )
        url = link_el.text.strip() if link_el is not None and link_el.text else ""
        pub_date = (
            pubdate_el.text.strip()
            if pubdate_el is not None and pubdate_el.text
            else ""
        )
        traffic = (
            traffic_el.text.strip()
            if traffic_el is not None and traffic_el.text
            else "N/A"
        )

        if title:
            topics.append(
                {
                    "title": title,
                    "traffic": traffic,
                    "description": description,
                    "url": url,
                    "pub_date": pub_date,
                }
            )

    return topics
