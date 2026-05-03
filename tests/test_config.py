"""Unit tests for AppConfig (src/config.py).

Covers requirements 6.1.1–6.1.4:
  - 6.1.1: BaseSettings subclass reading from .env
  - 6.1.2: Optional gemini_api_key and openai_api_key
  - 6.1.3: llm_provider defaults to "gemini", must be "gemini" or "openai"
  - 6.1.4: No Reddit credentials required
"""

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from src.config import AppConfig


class TestAppConfigDefaults:
    """AppConfig can be instantiated with no environment variables set."""

    def test_is_base_settings_subclass(self):
        config = AppConfig()
        assert isinstance(config, BaseSettings)

    def test_gemini_api_key_defaults_to_none(self):
        config = AppConfig()
        assert config.gemini_api_key is None

    def test_openai_api_key_defaults_to_none(self):
        config = AppConfig()
        assert config.openai_api_key is None

    def test_llm_provider_defaults_to_gemini(self):
        config = AppConfig()
        assert config.llm_provider == "gemini"


class TestAppConfigFieldAssignment:
    """AppConfig accepts valid values for all fields."""

    def test_gemini_api_key_accepts_string(self):
        config = AppConfig(gemini_api_key="test-gemini-key")
        assert config.gemini_api_key == "test-gemini-key"

    def test_openai_api_key_accepts_string(self):
        config = AppConfig(openai_api_key="test-openai-key")
        assert config.openai_api_key == "test-openai-key"

    def test_llm_provider_accepts_gemini(self):
        config = AppConfig(llm_provider="gemini")
        assert config.llm_provider == "gemini"

    def test_llm_provider_accepts_openai(self):
        config = AppConfig(llm_provider="openai")
        assert config.llm_provider == "openai"

    def test_all_fields_set_together(self):
        config = AppConfig(
            gemini_api_key="gkey",
            openai_api_key="okey",
            llm_provider="openai",
        )
        assert config.gemini_api_key == "gkey"
        assert config.openai_api_key == "okey"
        assert config.llm_provider == "openai"


class TestAppConfigValidation:
    """AppConfig raises ValidationError for invalid field values."""

    def test_invalid_llm_provider_raises_validation_error(self):
        with pytest.raises(ValidationError):
            AppConfig(llm_provider="anthropic")  # type: ignore[arg-type]

    def test_empty_string_llm_provider_raises_validation_error(self):
        with pytest.raises(ValidationError):
            AppConfig(llm_provider="")  # type: ignore[arg-type]


class TestAppConfigNoRedditCredentials:
    """AppConfig does not define Reddit credential fields (requirement 6.1.4)."""

    def test_no_reddit_client_id_field(self):
        config = AppConfig()
        assert not hasattr(config, "reddit_client_id")

    def test_no_reddit_client_secret_field(self):
        config = AppConfig()
        assert not hasattr(config, "reddit_client_secret")

    def test_no_reddit_username_field(self):
        config = AppConfig()
        assert not hasattr(config, "reddit_username")
