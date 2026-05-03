"""
Reddit scraper module for fetching trending posts from subreddits.

Uses crawl4ai for unauthenticated HTTP crawling of Reddit's public JSON endpoints.
"""

import asyncio
import json
from typing import Any


class ScraperError(Exception):
    """Raised when scraping fails due to HTTP errors, rate limiting, or crawl failures."""

    pass


def get_mock_trending_topics(subreddit: str) -> list[dict]:
    """
    Return hardcoded mock trending posts for offline/test use.

    Args:
        subreddit: Name of the subreddit (ignored; mock data is always returned).

    Returns:
        List of dicts with keys: title, score, num_comments, url, selftext.
    """
    return [
        {
            "title": "AI regulation bills are gaining momentum in Congress",
            "score": 45231,
            "num_comments": 1842,
            "url": "https://www.reddit.com/r/technology/comments/abc123/ai_regulation_bills/",
            "selftext": "Several bipartisan bills targeting AI safety and transparency have advanced through committee.",
        },
        {
            "title": "New open-source LLM beats GPT-4 on coding benchmarks",
            "score": 38910,
            "num_comments": 2103,
            "url": "https://www.reddit.com/r/technology/comments/def456/new_open_source_llm/",
            "selftext": "A team of researchers released a new model that outperforms GPT-4 on HumanEval and MBPP.",
        },
        {
            "title": "Major cloud provider suffers 6-hour outage affecting millions",
            "score": 29874,
            "num_comments": 987,
            "url": "https://www.reddit.com/r/technology/comments/ghi789/cloud_outage/",
            "selftext": "",
        },
        {
            "title": "Quantum computing milestone: 1000-qubit processor demonstrated",
            "score": 22456,
            "num_comments": 654,
            "url": "https://www.reddit.com/r/technology/comments/jkl012/quantum_milestone/",
            "selftext": "Researchers demonstrated a 1000-qubit processor with error rates below 0.1%.",
        },
        {
            "title": "Electric vehicle sales surpass gasoline cars in Europe for first time",
            "score": 18732,
            "num_comments": 1231,
            "url": "https://www.reddit.com/r/technology/comments/mno345/ev_sales_europe/",
            "selftext": "Monthly sales data shows EVs now account for 51% of new car registrations across the EU.",
        },
    ]


async def _crawl_url(url: str) -> Any:
    """
    Async helper that uses crawl4ai's AsyncWebCrawler to fetch a URL.

    Args:
        url: The URL to crawl.

    Returns:
        The crawl result object.

    Raises:
        ScraperError: If the crawl fails or returns an error response.
    """
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, bypass_cache=True)

    if not result.success:
        raise ScraperError(f"Failed to crawl URL: {url}")

    return result


def get_trending_topics(subreddit: str, limit: int = 10) -> list[dict]:
    """
    Fetch top posts from the given subreddit using crawl4ai.

    Crawls https://www.reddit.com/r/{subreddit}/hot.json and parses the JSON
    response to extract post data.

    Args:
        subreddit: Name of the subreddit (e.g. "technology").
        limit: Maximum number of posts to return. Must be between 1 and 100.

    Returns:
        List of dicts with keys: title, score, num_comments, url, selftext.
        The list contains at most `limit` items.

    Raises:
        ScraperError: If the subreddit is invalid, the page is inaccessible,
                      an HTTP 429 rate limit is hit, or any other crawl failure occurs.
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"

    try:
        result = asyncio.run(_crawl_url(url))
    except ScraperError:
        raise
    except Exception as exc:
        raise ScraperError(f"Crawl failed for subreddit '{subreddit}': {exc}") from exc

    # Detect HTTP 429 rate limiting from response content
    content = result.html or result.markdown or ""
    if "429" in content or "Too Many Requests" in content.lower():
        raise ScraperError("Rate limited by Reddit. Please wait before retrying.")

    # Detect invalid/private subreddit responses
    if "404" in content or "page not found" in content.lower():
        raise ScraperError(f"Subreddit not found: {subreddit}")

    # Parse the JSON response
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ScraperError(
            f"Failed to parse Reddit JSON response for subreddit '{subreddit}': {exc}"
        ) from exc

    # Navigate the Reddit hot.json structure
    try:
        children = data["data"]["children"]
    except (KeyError, TypeError) as exc:
        raise ScraperError(
            f"Unexpected Reddit JSON structure for subreddit '{subreddit}': {exc}"
        ) from exc

    posts: list[dict] = []
    for child in children[:limit]:
        try:
            post_data = child["data"]
            posts.append(
                {
                    "title": str(post_data.get("title", "")),
                    "score": int(post_data.get("score", 0)),
                    "num_comments": int(post_data.get("num_comments", 0)),
                    "url": str(post_data.get("url", "")),
                    "selftext": str(post_data.get("selftext", "")),
                }
            )
        except (KeyError, TypeError, ValueError):
            # Skip malformed post entries rather than failing the entire request
            continue

    return posts
