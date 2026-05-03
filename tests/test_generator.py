"""Unit tests for src/ai/generator.py (tasks 7.1–7.5)."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.ai.generator import (
    GenerationError,
    _build_generation_prompt,
    generate_content,
    get_mock_generated_content,
)
from src.models.schemas import GeneratedContent, TrendSummary


def _inject_fake_genai(response_text: str | None = None, side_effect=None) -> MagicMock:
    """
    Inject a fake google.generativeai module into sys.modules so that
    `import google.generativeai as genai` inside generate_content() picks it up.

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
# Task 7.1 — get_mock_generated_content
# ---------------------------------------------------------------------------


class TestGetMockGeneratedContent:
    def test_returns_generated_content_instance(self):
        """get_mock_generated_content() must return a GeneratedContent instance."""
        result = get_mock_generated_content()
        assert isinstance(result, GeneratedContent)

    def test_text_post_is_str_with_valid_length(self):
        """text_post must be a str between 10 and 500 characters."""
        result = get_mock_generated_content()
        assert isinstance(result.text_post, str)
        assert 10 <= len(result.text_post) <= 500

    def test_video_script_is_str_with_min_length(self):
        """video_script must be a str of at least 50 characters."""
        result = get_mock_generated_content()
        assert isinstance(result.video_script, str)
        assert len(result.video_script) >= 50

    def test_image_prompt_is_str_with_min_length(self):
        """image_prompt must be a str of at least 20 characters."""
        result = get_mock_generated_content()
        assert isinstance(result.image_prompt, str)
        assert len(result.image_prompt) >= 20


# ---------------------------------------------------------------------------
# Task 7.2 — _build_generation_prompt
# ---------------------------------------------------------------------------


class TestBuildGenerationPrompt:
    def _sample_trend(self) -> TrendSummary:
        return TrendSummary(
            why_trending="AI regulation bills are gaining momentum in Congress.",
            sentiment="mixed",
            key_joke="'Move fast and break laws' era is officially over.",
        )

    def test_prompt_contains_why_trending(self):
        """The prompt must include the why_trending field value."""
        trend = self._sample_trend()
        prompt = _build_generation_prompt(trend)
        assert trend.why_trending in prompt

    def test_prompt_contains_sentiment(self):
        """The prompt must include the sentiment field value."""
        trend = self._sample_trend()
        prompt = _build_generation_prompt(trend)
        assert trend.sentiment in prompt

    def test_prompt_contains_key_joke(self):
        """The prompt must include the key_joke field value."""
        trend = self._sample_trend()
        prompt = _build_generation_prompt(trend)
        assert trend.key_joke in prompt

    def test_prompt_contains_generated_content_schema(self):
        """The prompt must include the GeneratedContent JSON schema field names."""
        trend = self._sample_trend()
        prompt = _build_generation_prompt(trend)
        schema = GeneratedContent.model_json_schema()
        for key in schema.get("properties", {}):
            assert key in prompt, f"Schema key '{key}' not found in prompt"

    def test_prompt_schema_json_is_embedded(self):
        """The full GeneratedContent JSON schema must be embedded in the prompt."""
        trend = self._sample_trend()
        prompt = _build_generation_prompt(trend)
        schema_json = json.dumps(GeneratedContent.model_json_schema(), indent=2)
        assert schema_json in prompt

    def test_prompt_is_non_empty_string(self):
        """The prompt must be a non-empty string."""
        trend = self._sample_trend()
        prompt = _build_generation_prompt(trend)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ---------------------------------------------------------------------------
# Task 7.3 / 7.4 — generate_content raises GenerationError on bad LLM response
# ---------------------------------------------------------------------------


class TestGenerateContent:
    def _sample_trend(self) -> TrendSummary:
        return TrendSummary(
            why_trending="AI regulation bills are gaining momentum in Congress.",
            sentiment="mixed",
            key_joke="'Move fast and break laws' era is officially over.",
        )

    def _mock_config(self, provider: str = "gemini"):
        mock_config = MagicMock()
        mock_config.llm_provider = provider
        mock_config.gemini_api_key = "fake-gemini-key"
        mock_config.openai_api_key = "fake-openai-key"
        return mock_config

    def test_raises_generation_error_on_malformed_json_gemini(self):
        """generate_content raises GenerationError when Gemini returns malformed JSON."""
        trend = self._sample_trend()
        _inject_fake_genai(response_text="this is not valid json at all!!!")

        with patch("src.ai.generator.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            with pytest.raises(GenerationError):
                generate_content(trend)

    def test_raises_generation_error_on_schema_mismatch_gemini(self):
        """generate_content raises GenerationError when Gemini returns JSON that doesn't match GeneratedContent."""
        trend = self._sample_trend()
        bad_json = json.dumps({"wrong_field": "some value"})
        _inject_fake_genai(response_text=bad_json)

        with patch("src.ai.generator.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            with pytest.raises(GenerationError):
                generate_content(trend)

    def test_raises_generation_error_on_api_exception(self):
        """generate_content raises GenerationError when the LLM API raises an exception."""
        trend = self._sample_trend()
        _inject_fake_genai(side_effect=RuntimeError("API unavailable"))

        with patch("src.ai.generator.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            with pytest.raises(GenerationError):
                generate_content(trend)

    def test_returns_generated_content_on_valid_response_gemini(self):
        """generate_content returns a GeneratedContent when Gemini returns valid JSON."""
        trend = self._sample_trend()
        valid_data = {
            "text_post": "The AI regulation wave is here — is your brand ready? 🤖⚖️",
            "video_script": (
                "[HOOK] Everyone's talking about AI laws — but what does it mean for YOU? "
                "Congress just passed sweeping AI regulation bills, and the tech world is reacting fast."
            ),
            "image_prompt": (
                "A sleek robot standing in a grand courtroom, dramatic cinematic lighting, "
                "scales of justice in the background, editorial photography style."
            ),
        }
        _inject_fake_genai(response_text=json.dumps(valid_data))

        with patch("src.ai.generator.AppConfig") as mock_config_cls:
            mock_config_cls.return_value = self._mock_config("gemini")
            result = generate_content(trend)

        assert isinstance(result, GeneratedContent)
        assert result.text_post == valid_data["text_post"]
