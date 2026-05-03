"""
Tests for src/ai/parser._parse_llm_response

Tasks covered:
  5.3 - Unit tests (valid JSON, malformed JSON, schema-mismatched JSON)
  5.4 - Property-based test (hypothesis): only ValueError or ValidationError raised
"""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.ai.parser import _parse_llm_response
from src.models.schemas import GeneratedContent, TrendSummary

# ---------------------------------------------------------------------------
# Helpers: minimal valid payloads
# ---------------------------------------------------------------------------

VALID_TREND_SUMMARY = {
    "why_trending": "AI regulation bills are gaining momentum in Congress.",
    "sentiment": "mixed",
    "key_joke": "Move fast and break laws.",
}

VALID_GENERATED_CONTENT = {
    "text_post": "The AI regulation wave is here — is your brand ready? 🤖⚖️",
    "video_script": (
        "[HOOK] Everyone's talking about AI laws. "
        "Here's what it means for your business and why you need to act now. "
        "Stay ahead of the curve with our latest insights."
    ),
    "image_prompt": (
        "A robot in a courtroom, dramatic lighting, editorial style, "
        "high resolution photography."
    ),
}


# ---------------------------------------------------------------------------
# Task 5.3 — Unit tests
# ---------------------------------------------------------------------------


class TestValidInputs:
    """Valid JSON inputs that should return the correct model instance."""

    def test_valid_trend_summary_returns_instance(self):
        raw = json.dumps(VALID_TREND_SUMMARY)
        result = _parse_llm_response(raw, TrendSummary)
        assert isinstance(result, TrendSummary)
        assert result.sentiment == "mixed"
        assert result.why_trending == VALID_TREND_SUMMARY["why_trending"]
        assert result.key_joke == VALID_TREND_SUMMARY["key_joke"]

    def test_valid_generated_content_returns_instance(self):
        raw = json.dumps(VALID_GENERATED_CONTENT)
        result = _parse_llm_response(raw, GeneratedContent)
        assert isinstance(result, GeneratedContent)
        assert result.text_post == VALID_GENERATED_CONTENT["text_post"]

    def test_json_fenced_with_json_tag(self):
        """```json\\n...\\n``` fences are stripped before parsing."""
        raw = "```json\n" + json.dumps(VALID_TREND_SUMMARY) + "\n```"
        result = _parse_llm_response(raw, TrendSummary)
        assert isinstance(result, TrendSummary)

    def test_json_fenced_with_plain_backticks(self):
        """Plain ``` ... ``` fences (no 'json' tag) are stripped before parsing."""
        raw = "```\n" + json.dumps(VALID_TREND_SUMMARY) + "\n```"
        result = _parse_llm_response(raw, TrendSummary)
        assert isinstance(result, TrendSummary)

    def test_json_fenced_inline_no_newlines(self):
        """Inline ```json...``` without surrounding newlines."""
        raw = "```json" + json.dumps(VALID_TREND_SUMMARY) + "```"
        result = _parse_llm_response(raw, TrendSummary)
        assert isinstance(result, TrendSummary)

    def test_leading_and_trailing_whitespace_stripped(self):
        raw = "   \n" + json.dumps(VALID_TREND_SUMMARY) + "\n   "
        result = _parse_llm_response(raw, TrendSummary)
        assert isinstance(result, TrendSummary)


class TestMalformedJSON:
    """Inputs that are not valid JSON must raise ValueError."""

    def test_plain_text_raises_value_error(self):
        with pytest.raises(ValueError):
            _parse_llm_response("this is not json", TrendSummary)

    def test_truncated_json_raises_value_error(self):
        with pytest.raises(ValueError):
            _parse_llm_response('{"why_trending": "incomplete', TrendSummary)

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            _parse_llm_response("", TrendSummary)

    def test_whitespace_only_raises_value_error(self):
        with pytest.raises(ValueError):
            _parse_llm_response("   \n\t  ", TrendSummary)

    def test_json_array_instead_of_object_raises_value_error(self):
        """A JSON array is valid JSON but model_validate expects a dict."""
        with pytest.raises((ValueError, ValidationError)):
            _parse_llm_response("[1, 2, 3]", TrendSummary)

    def test_fenced_malformed_json_raises_value_error(self):
        """Malformed JSON inside fences still raises ValueError."""
        with pytest.raises(ValueError):
            _parse_llm_response("```json\nnot json\n```", TrendSummary)


class TestSchemaMismatch:
    """Valid JSON that doesn't match the target schema must raise ValidationError."""

    def test_missing_required_fields_raises_validation_error(self):
        raw = json.dumps({"why_trending": "Something is happening here today."})
        with pytest.raises(ValidationError):
            _parse_llm_response(raw, TrendSummary)

    def test_wrong_sentiment_value_raises_validation_error(self):
        payload = {**VALID_TREND_SUMMARY, "sentiment": "ecstatic"}
        with pytest.raises(ValidationError):
            _parse_llm_response(json.dumps(payload), TrendSummary)

    def test_field_too_short_raises_validation_error(self):
        """why_trending has min_length=10; a short value should fail."""
        payload = {**VALID_TREND_SUMMARY, "why_trending": "Short"}
        with pytest.raises(ValidationError):
            _parse_llm_response(json.dumps(payload), TrendSummary)

    def test_wrong_field_type_raises_validation_error(self):
        """Passing an integer where a string is expected."""
        payload = {**VALID_TREND_SUMMARY, "why_trending": 12345}
        # Pydantic v2 coerces int→str by default, so use a list which can't coerce
        payload["why_trending"] = ["not", "a", "string"]
        with pytest.raises(ValidationError):
            _parse_llm_response(json.dumps(payload), TrendSummary)

    def test_empty_object_raises_validation_error(self):
        with pytest.raises(ValidationError):
            _parse_llm_response("{}", TrendSummary)

    def test_generated_content_missing_fields_raises_validation_error(self):
        raw = json.dumps({"text_post": "Hello world, this is a post!"})
        with pytest.raises(ValidationError):
            _parse_llm_response(raw, GeneratedContent)


# ---------------------------------------------------------------------------
# Task 5.4 — Property-based test
# Validates: Requirements 5.4
# ---------------------------------------------------------------------------


@given(st.text())
@settings(max_examples=500)
def test_parse_llm_response_never_raises_unexpected_exception(raw: str):
    """
    For ANY string input, _parse_llm_response must raise only ValueError or
    pydantic.ValidationError — never any other exception type.

    **Validates: Requirements 5.4**
    """
    try:
        _parse_llm_response(raw, TrendSummary)
    except (ValueError, ValidationError):
        pass  # expected — these are the only allowed exception types
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"_parse_llm_response raised an unexpected exception "
            f"{type(exc).__name__}: {exc!r}\n"
            f"Input was: {raw!r}"
        )
