from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_provider: Literal["gemini", "openai"] = "gemini"
    cloudfare_api_key: str | None = None  # matches CLOUDFARE_API_KEY in .env

    # AWS Cognito — defaults baked in, can be overridden via .env
    cognito_user_pool_id: str = "ap-south-1_5Q3RctZU3"
    cognito_client_id: str = "35fjgoi410072v30np301mo8o5"
    cognito_region: str = "ap-south-1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
