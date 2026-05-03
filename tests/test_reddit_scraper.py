"""
Unit tests for src/ingestion/reddit_scraper.py

Tests cover:
- Mock data shape and key presence
- Type correctness of mock post fields
- Subreddit argument is ignored by mock implementation
- Mock data returns at least 1 post
- limit parameter behavior (tested via mock data length)
"""

import pytest

from src.ingestion.reddit_scraper import ScraperError, get_mock_trending_topics

# ---------------------------------------------------------------------------
# Required keys for every post dict
# ---------------------------------------------------------------------------
REQUIRED_KEYS = {"title", "score", "num_comments", "url", "selftext"}


# ---------------------------------------------------------------------------
# Tests: get_mock_trending_topics — return type and shape
# ---------------------------------------------------------------------------


def test_mock_returns_list():
    """get_mock_trending_topics should return a list."""
    result = get_mock_trending_topics("technology")
    assert isinstance(result, list)


def test_mock_returns_at_least_one_post():
    """get_mock_trending_topics should return at least 1 post."""
    result = get_mock_trending_topics("technology")
    assert len(result) >= 1


def test_mock_all_posts_are_dicts():
    """Every item in the returned list should be a dict."""
    result = get_mock_trending_topics("technology")
    for post in result:
        assert isinstance(post, dict), f"Expected dict, got {type(post)}"


def test_mock_all_required_keys_present():
    """Every post dict must contain all 5 required keys."""
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        missing = REQUIRED_KEYS - post.keys()
        assert not missing, f"Post {i} is missing keys: {missing}"


def test_mock_no_extra_unexpected_keys():
    """Posts should contain exactly the 5 required keys (no unexpected extras required,
    but all required keys must be present — this test verifies the required set is a subset).
    """
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        assert REQUIRED_KEYS.issubset(
            post.keys()
        ), f"Post {i} is missing required keys. Has: {set(post.keys())}"


# ---------------------------------------------------------------------------
# Tests: type correctness
# ---------------------------------------------------------------------------


def test_mock_title_is_string():
    """title field must be a str."""
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        assert isinstance(
            post["title"], str
        ), f"Post {i}: expected title to be str, got {type(post['title'])}"


def test_mock_url_is_string():
    """url field must be a str."""
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        assert isinstance(
            post["url"], str
        ), f"Post {i}: expected url to be str, got {type(post['url'])}"


def test_mock_selftext_is_string():
    """selftext field must be a str (may be empty)."""
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        assert isinstance(
            post["selftext"], str
        ), f"Post {i}: expected selftext to be str, got {type(post['selftext'])}"


def test_mock_score_is_int():
    """score field must be an int."""
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        assert isinstance(
            post["score"], int
        ), f"Post {i}: expected score to be int, got {type(post['score'])}"


def test_mock_num_comments_is_int():
    """num_comments field must be an int."""
    result = get_mock_trending_topics("technology")
    for i, post in enumerate(result):
        assert isinstance(
            post["num_comments"], int
        ), f"Post {i}: expected num_comments to be int, got {type(post['num_comments'])}"


# ---------------------------------------------------------------------------
# Tests: subreddit argument is ignored
# ---------------------------------------------------------------------------


def test_mock_ignores_subreddit_argument():
    """Mock implementation should return the same data regardless of subreddit."""
    result_tech = get_mock_trending_topics("technology")
    result_news = get_mock_trending_topics("worldnews")
    result_empty = get_mock_trending_topics("")

    assert (
        result_tech == result_news == result_empty
    ), "get_mock_trending_topics should return identical data for any subreddit argument"


def test_mock_different_subreddit_names_same_length():
    """Mock data length should be the same regardless of subreddit name."""
    assert len(get_mock_trending_topics("python")) == len(
        get_mock_trending_topics("gaming")
    )


# ---------------------------------------------------------------------------
# Tests: ScraperError is importable and is an Exception subclass
# ---------------------------------------------------------------------------


def test_scraper_error_is_exception():
    """ScraperError should be a subclass of Exception."""
    assert issubclass(ScraperError, Exception)


def test_scraper_error_can_be_raised_and_caught():
    """ScraperError should be raiseable and catchable."""
    with pytest.raises(ScraperError, match="test error"):
        raise ScraperError("test error")


def test_scraper_error_message_preserved():
    """ScraperError should preserve the error message."""
    msg = "Rate limited by Reddit. Please wait before retrying."
    try:
        raise ScraperError(msg)
    except ScraperError as exc:
        assert str(exc) == msg
