from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_provider: Literal["gemini", "openai"] = "gemini"
    cloudfare_api_key: str | None = None  # matches CLOUDFARE_API_KEY in .env

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
