"""
Application configuration.

Loads secrets from AWS Secrets Manager when running on EC2 (preferred),
with fallback to a local .env file for local development.
"""

import json
import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Name of the secret in AWS Secrets Manager
_SECRET_NAME = "trend-content-app/config"
_SECRET_REGION = "ap-south-1"


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


@lru_cache(maxsize=1)
def _get_secrets() -> dict:
    """Cached secret fetch — only calls Secrets Manager once per process."""
    return _load_from_secrets_manager()


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

        # Map secret keys to field names
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
