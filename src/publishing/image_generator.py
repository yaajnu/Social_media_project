"""
Cloudflare Worker image generation module.

Calls the custom Cloudflare Worker endpoint to generate images from text prompts.
Returns raw image bytes that can be displayed directly in Streamlit.

Endpoint: POST https://llm-chat-app-template.yaajnusubramanian.workers.dev/api/generate
Auth:      X-API-Key header
Body:      {"prompt": "<text>"}
Response:  raw image bytes (PNG)
"""

import requests


WORKER_URL = "https://llm-chat-app-template.yaajnusubramanian.workers.dev/api/generate"

# Browser-like headers to avoid Cloudflare bot detection (error 1010)
_HEADERS_BASE = {
    "Content-Type": "application/json",
    "Accept": "image/png,image/*,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin": "https://llm-chat-app-template.yaajnusubramanian.workers.dev",
    "Referer": "https://llm-chat-app-template.yaajnusubramanian.workers.dev/",
}


class ImageGenerationError(Exception):
    """Raised when image generation fails."""

    pass


def generate_image(prompt: str, api_key: str) -> bytes:
    """
    Generate an image from a text prompt using the Cloudflare Worker endpoint.

    Args:
        prompt: The image generation prompt.
        api_key: Cloudflare Worker API key (X-API-Key header).

    Returns:
        Raw PNG image bytes.

    Raises:
        ImageGenerationError: On auth failure, network error, or bad response.
    """
    if not api_key:
        raise ImageGenerationError(
            "CLOUDFARE_API_KEY is not set. Add it to your .env file."
        )
    if not prompt or not prompt.strip():
        raise ImageGenerationError("Image prompt cannot be empty.")

    headers = {**_HEADERS_BASE, "X-API-Key": api_key}

    try:
        response = requests.post(
            WORKER_URL,
            headers=headers,
            json={"prompt": prompt},
            timeout=60,
        )
    except requests.exceptions.ConnectionError as exc:
        raise ImageGenerationError(
            f"Network error calling image generation endpoint: {exc}"
        ) from exc
    except requests.exceptions.Timeout:
        raise ImageGenerationError(
            "Image generation request timed out after 60 seconds."
        ) from None
    except Exception as exc:
        raise ImageGenerationError(
            f"Unexpected error during image generation: {exc}"
        ) from exc

    if response.status_code in (401, 403):
        raise ImageGenerationError(
            f"Authentication failed (HTTP {response.status_code}). "
            f"Check your CLOUDFARE_API_KEY. Response: {response.text[:300]}"
        )
    if not response.ok:
        raise ImageGenerationError(
            f"HTTP {response.status_code} from image generation endpoint: {response.text[:300]}"
        )

    image_bytes = response.content
    if not image_bytes:
        raise ImageGenerationError("Image generation endpoint returned empty response.")

    return image_bytes
