"""Unit tests for src/ai/analyzer.py (tasks 6.1–6.5)."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.ai.analyzer import (
    AnalysisError,
    _build_analysis_prompt,
    analyze_trend,
    get_mock_trend_summary,
)
from src.models.schemas import TrendSummary


def _inject_fake_genai(response_text: str | None = None, side_effect=None) -> MagicMock:
    """
    Inject a fake google.generativeai module into sys.modules so that
    `import google.generativeai as genai` inside analyze_trend() picks it up.

    Returns the fake genai MagicMock so callers can inspect calls if needed.
    """
    fake_genai = MagicMock()
    mock_model_instance = MagicMock()

    if side_effect is not None:
        mock_model_instance.generate_content.side_effect = side_effect
    else:
        mock_response = MagicMock()
        mock_response.text = response_text
        mock_model_instance.generate_content.return_value = mock_response

    fake_genai.GenerativeModel.return_value = mock_model_instance

    # Ensure the google namespace exists in sys.modules
    if "google" not in sys.modules:
        fake_google = MagicMock()
        fake_google.generativeai = fake_genai
        sys.modules["google"] = fake_google
    else:
        sys.modules["google"].generativeai = fake_genai  # type: ignore[attr-defined]

    sys.modules["google.generativeai"] = fake_genai
    return fake_genai


# ---------------------------------------------------------------------------
# Task 6.1 — get_mock_trend_summary
# ---------------------------------------------------------------------------


class TestGetMockTrendSummary:
    def test_returns_trend_summary_instance(self):
        """get_mock_trend_summary() must return a TrendSummary instance."""
        result = get_mock_trend_summary()
        assert isinstance(result, TrendSummary)

    def test_why_trending_is_str_with_min_length(self):
        """why_trending must be a str of at least 10 characters."""
        result = get_mock_trend_summary()
        assert isinstance(result.why_trending, str)
        assert len(result.why_trending) >= 10

    def test_sentiment_is_valid_literal(self):
        """sentiment must be one of the four allowed literals."""
        result = get_mock_trend_summary()
        assert result.sentiment in {"positive", "negative", "neutral", "mixed"}

    def test_key_joke_is_str_with_min_length(self):
        """key_joke must be a str of at least 5 characters."""
        result = get_mock_trend_summary()
        assert isinstance(result.key_joke, str)
        assert len(result.key_joke) >= 5


# ---------------------------------------------------------------------------
# Task 6.2 — _build_analysis_prompt
# ---------------------------------------------------------------------------


class TestBuildAnalysisPrompt:
    def _sample_posts(self):
        return [
            {
                "title": "AI regulation bill passes Senate",
                "score": 1000,
                "num_comments": 200,
                "url": "https://example.com/1",
                "selftext": "",
            },
            {
                "title": "OpenAI releases new model",
                "score": 800,
                "num_comments": 150,
                "url": "https://example.com/2",
                "selftext": "",
            },
            {
                "title": "Tech stocks surge on AI news",
                "score": 600,
                "num_comments": 90,
                "url": "https://example.com/3",
                "selftext": "",
            },
        ]

    def test_prompt_contains_all_post_titles(self):
        """The prompt must include every post title from the input list."""
        posts = self._sample_posts()
        prompt = _build_analysis_prompt(posts)
        for post in posts:
            assert (
                post["title"] in prompt
            ), f"Title not found in prompt: {post['title']}"

    def test_prompt_contains_trend_summary_schema(self):
        """The prompt must include the TrendSummary JSON schema field names."""
        posts = self._sample_posts()
        prompt = _build_analysis_prompt(posts)
        schema = TrendSummary.model_json_schema()
        for key in schema.get("properties", {}):
            assert key in prompt, f"Schema key '{key}' not found in prompt"

    def test_prompt_is_non_empty_string(self):
        """The prompt must be a non-empty string."""
        posts = self._sample_posts()
        prompt = _build_analysis_prompt(posts)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_with_single_post(self):
        """Prompt construction works with a single post."""
        posts = [
            {
                "title": "Single post title here",
                "score": 1,
                "num_comments": 0,
                "url": "https://example.com",
                "selftext": "",
            }
        ]
        prompt = _build_analysis_prompt(posts)
        assert "Single post title here" in prompt

    def test_prompt_schema_json_is_embedded(self):
        """The full TrendSummary JSON schema must be embedded in the prompt."""
        posts = self._sample_posts()
        prompt = _build_analysis_prompt(posts)
        schema_json = json.dumps(TrendSummary.model_json_schema(), indent=2)
        assert schema_json in prompt


# ---------------------------------------------------------------------------
# Task 6.3 / 6.4 — analyze_trend raises AnalysisError on bad LLM response
# ---------------------------------------------------------------------------


class TestAnalyzeTrend:
    def _sample_posts(self):
        return [
            {
                "title": "Breaking: major tech news today",
                "score": 500,
                "num_comments": 100,
                "url": "https://example.com/1",
                "selftext": "",
            },
        ]

    def _mock_config(self, provider: str = "gemini"):
        mock_config = MagicMock()
        mock_config.llm_provider = provider
        mock_config.gemini_api_key = "fake-gemini-key"
        mock_config.openai_api_key = "fake-openai-key"
        return mock_config

    def test_raises_analysis_error_on_malformed_json_gemini(self):
        """analyze_trend raises AnalysisError when Gemini returns malformed JSON."""
        posts = self._sample_posts()
        _inject_fake_genai(response_text="this is not valid json at all!!!")

        with patch("src.ai.analyzer.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            with pytest.raises(AnalysisError):
                analyze_trend(posts)

    def test_raises_analysis_error_on_schema_mismatch_gemini(self):
        """analyze_trend raises AnalysisError when Gemini returns JSON that doesn't match TrendSummary."""
        posts = self._sample_posts()
        bad_json = json.dumps({"wrong_field": "some value"})
        _inject_fake_genai(response_text=bad_json)

        with patch("src.ai.analyzer.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            with pytest.raises(AnalysisError):
                analyze_trend(posts)

    def test_raises_analysis_error_on_malformed_json_openai(self):
        """analyze_trend raises AnalysisError when OpenAI returns malformed JSON."""
        posts = self._sample_posts()

        mock_message = MagicMock()
        mock_message.content = "not json either"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("src.ai.analyzer.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("openai")
            with patch("openai.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai_cls.return_value = mock_client
                with pytest.raises(AnalysisError):
                    analyze_trend(posts)

    def test_raises_analysis_error_on_api_exception(self):
        """analyze_trend raises AnalysisError when the LLM API raises an exception."""
        posts = self._sample_posts()
        _inject_fake_genai(side_effect=RuntimeError("API unavailable"))

        with patch("src.ai.analyzer.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            with pytest.raises(AnalysisError):
                analyze_trend(posts)

    def test_returns_trend_summary_on_valid_response_gemini(self):
        """analyze_trend returns a TrendSummary when Gemini returns valid JSON."""
        posts = self._sample_posts()
        valid_data = {
            "why_trending": "AI regulation is a hot topic in Congress right now.",
            "sentiment": "mixed",
            "key_joke": "Move fast and break laws.",
        }
        _inject_fake_genai(response_text=json.dumps(valid_data))

        with patch("src.ai.analyzer.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            result = analyze_trend(posts)

        assert isinstance(result, TrendSummary)
        assert result.sentiment == "mixed"
