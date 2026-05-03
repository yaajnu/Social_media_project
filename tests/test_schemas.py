"""Unit tests for TrendSummary and GeneratedContent Pydantic schemas.

Validates: Requirements 2.1, 2.2
"""

import pytest
from pydantic import ValidationError

from src.models.schemas import GeneratedContent, TrendSummary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TREND_DATA = {
    "why_trending": "This topic is trending because of a viral video.",
    "sentiment": "positive",
    "key_joke": "Funny meme here",
}

VALID_CONTENT_DATA = {
    "text_post": "Check out this amazing trend!",
    "video_script": (
        "Welcome to our channel! Today we are talking about the latest trend "
        "that has taken the internet by storm. Stay tuned for more!"
    ),
    "image_prompt": "A vibrant digital illustration of a trending meme.",
}


# ---------------------------------------------------------------------------
# TrendSummary tests
# ---------------------------------------------------------------------------


class TestTrendSummaryValid:
    def test_valid_construction_with_all_fields(self):
        trend = TrendSummary(**VALID_TREND_DATA)
        assert trend.why_trending == VALID_TREND_DATA["why_trending"]
        assert trend.sentiment == "positive"
        assert trend.key_joke == VALID_TREND_DATA["key_joke"]

    def test_model_validate_from_dict(self):
        trend = TrendSummary.model_validate(VALID_TREND_DATA)
        assert trend.why_trending == VALID_TREND_DATA["why_trending"]

    def test_sentiment_positive(self):
        data = {**VALID_TREND_DATA, "sentiment": "positive"}
        trend = TrendSummary(**data)
        assert trend.sentiment == "positive"

    def test_sentiment_negative(self):
        data = {**VALID_TREND_DATA, "sentiment": "negative"}
        trend = TrendSummary(**data)
        assert trend.sentiment == "negative"

    def test_sentiment_neutral(self):
        data = {**VALID_TREND_DATA, "sentiment": "neutral"}
        trend = TrendSummary(**data)
        assert trend.sentiment == "neutral"

    def test_sentiment_mixed(self):
        data = {**VALID_TREND_DATA, "sentiment": "mixed"}
        trend = TrendSummary(**data)
        assert trend.sentiment == "mixed"


class TestTrendSummaryInvalid:
    def test_why_trending_too_short_raises(self):
        data = {**VALID_TREND_DATA, "why_trending": "Too short"}  # 9 chars
        with pytest.raises(ValidationError):
            TrendSummary(**data)

    def test_key_joke_too_short_raises(self):
        data = {**VALID_TREND_DATA, "key_joke": "Hi"}  # 2 chars
        with pytest.raises(ValidationError):
            TrendSummary(**data)

    def test_invalid_sentiment_raises(self):
        data = {**VALID_TREND_DATA, "sentiment": "happy"}
        with pytest.raises(ValidationError):
            TrendSummary(**data)

    def test_empty_sentiment_raises(self):
        data = {**VALID_TREND_DATA, "sentiment": ""}
        with pytest.raises(ValidationError):
            TrendSummary(**data)


# ---------------------------------------------------------------------------
# GeneratedContent tests
# ---------------------------------------------------------------------------


class TestGeneratedContentValid:
    def test_valid_construction_with_all_fields(self):
        content = GeneratedContent(**VALID_CONTENT_DATA)
        assert content.text_post == VALID_CONTENT_DATA["text_post"]
        assert content.video_script == VALID_CONTENT_DATA["video_script"]
        assert content.image_prompt == VALID_CONTENT_DATA["image_prompt"]

    def test_model_validate_from_dict(self):
        content = GeneratedContent.model_validate(VALID_CONTENT_DATA)
        assert content.text_post == VALID_CONTENT_DATA["text_post"]

    def test_text_post_at_min_boundary(self):
        data = {**VALID_CONTENT_DATA, "text_post": "A" * 10}
        content = GeneratedContent(**data)
        assert len(content.text_post) == 10

    def test_text_post_at_max_boundary(self):
        data = {**VALID_CONTENT_DATA, "text_post": "A" * 500}
        content = GeneratedContent(**data)
        assert len(content.text_post) == 500


class TestGeneratedContentInvalid:
    def test_text_post_too_short_raises(self):
        data = {**VALID_CONTENT_DATA, "text_post": "Short"}  # 5 chars
        with pytest.raises(ValidationError):
            GeneratedContent(**data)

    def test_text_post_too_long_raises(self):
        data = {**VALID_CONTENT_DATA, "text_post": "A" * 501}
        with pytest.raises(ValidationError):
            GeneratedContent(**data)

    def test_video_script_too_short_raises(self):
        data = {**VALID_CONTENT_DATA, "video_script": "Too short script."}  # < 50 chars
        with pytest.raises(ValidationError):
            GeneratedContent(**data)

    def test_image_prompt_too_short_raises(self):
        data = {**VALID_CONTENT_DATA, "image_prompt": "Short prompt."}  # < 20 chars
        with pytest.raises(ValidationError):
            GeneratedContent(**data)
