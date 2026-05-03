"""
Application configuration.

Loads secrets from AWS Secrets Manager when running on EC2 (preferred),
with fallback to a local .env file for local development.

Secrets are cached for 5 minutes so rotated values are picked up
automatically without requiring a service restart.
"""

import json
import time
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Name of the secret in AWS Secrets Manager
_SECRET_NAME = "trend-content-app/config"
_SECRET_REGION = "ap-south-1"

# TTL cache state
_SECRET_CACHE: dict = {}
_SECRET_CACHE_TTL: float = 300.0  # 5 minutes
_SECRET_CACHE_FETCHED_AT: float = 0.0


def _load_from_secrets_manager() -> dict:
    """
    Fetch secrets from AWS Secrets Manager.
    Returns an empty dict if unavailable (e.g. running locally without IAM role).
    """
    try:
        import boto3

        client = boto3.client("secretsmanager", region_name=_SECRET_REGION)
        response = client.get_secret_value(SecretId=_SECRET_NAME)
        return json.loads(response["SecretString"])
    except Exception:
        return {}


def _get_secrets() -> dict:
    """
    Return secrets with a 5-minute TTL cache.
    Automatically picks up rotated values without a service restart.
    """
    global _SECRET_CACHE, _SECRET_CACHE_FETCHED_AT
    now = time.monotonic()
    if not _SECRET_CACHE or (now - _SECRET_CACHE_FETCHED_AT) > _SECRET_CACHE_TTL:
        fresh = _load_from_secrets_manager()
        if fresh:  # only update cache if fetch succeeded
            _SECRET_CACHE = fresh
            _SECRET_CACHE_FETCHED_AT = now
    return _SECRET_CACHE


class AppConfig(BaseSettings):
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_provider: Literal["gemini", "openai"] = "gemini"
    cloudfare_api_key: str | None = None

    # AWS Cognito
    cognito_user_pool_id: str = "ap-south-1_5Q3RctZU3"
    cognito_client_id: str = "35fjgoi410072v30np301mo8o5"
    cognito_region: str = "ap-south-1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def model_post_init(self, __context) -> None:
        """
        After Pydantic loads from .env, overlay any values from Secrets Manager.
        Secrets Manager values take precedence over .env values.
        """
        secrets = _get_secrets()
        if not secrets:
            return  # Running locally without IAM role — use .env as-is

        mapping = {
            "GEMINI_API_KEY": "gemini_api_key",
            "OPENAI_API_KEY": "openai_api_key",
            "LLM_PROVIDER": "llm_provider",
            "CLOUDFARE_API_KEY": "cloudfare_api_key",
            "COGNITO_USER_POOL_ID": "cognito_user_pool_id",
            "COGNITO_CLIENT_ID": "cognito_client_id",
            "COGNITO_REGION": "cognito_region",
        }
        for secret_key, field_name in mapping.items():
            if secret_key in secrets and secrets[secret_key]:
                object.__setattr__(self, field_name, secrets[secret_key])
