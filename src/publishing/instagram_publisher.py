"""
Instagram publisher module.

Posts text captions as photo captions using the Meta Graph API.
Requires an Instagram Business/Creator account linked to a Facebook Page,
and a long-lived Page access token with instagram_basic + instagram_content_publish permissions.

Note: Instagram does not support text-only posts via the API.
This module posts a caption alongside a publicly accessible image URL.
If no image URL is provided, it uses a default placeholder image.
"""

import urllib.request
import urllib.parse
import urllib.error
import json


class InstagramPublishError(Exception):
    """Raised when posting to Instagram fails."""

    pass


# Default placeholder image (solid gradient — publicly accessible)
DEFAULT_IMAGE_URL = (
    "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=1080&q=80"
)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def post_to_instagram(
    caption: str,
    access_token: str,
    instagram_account_id: str,
    image_url: str = DEFAULT_IMAGE_URL,
) -> str:
    """
    Post a photo with caption to Instagram via Meta Graph API.

    This is a two-step process:
    1. Create a media container with the image URL and caption.
    2. Publish the container.

    Args:
        caption: The post caption text.
        access_token: Long-lived Instagram Graph API access token.
        instagram_account_id: The Instagram Business Account ID.
        image_url: Publicly accessible URL of the image to post.
                   Defaults to a placeholder image.

    Returns:
        URL of the published Instagram post (best-effort; IG doesn't always return a permalink).

    Raises:
        InstagramPublishError: If authentication fails or the post request fails.
    """
    if not all([access_token, instagram_account_id]):
        raise InstagramPublishError(
            "Instagram access token and account ID are required."
        )

    # Step 1: Create media container
    container_id = _create_media_container(
        instagram_account_id=instagram_account_id,
        image_url=image_url,
        caption=caption,
        access_token=access_token,
    )

    # Step 2: Publish the container
    media_id = _publish_media_container(
        instagram_account_id=instagram_account_id,
        container_id=container_id,
        access_token=access_token,
    )

    return f"https://www.instagram.com/p/{media_id}/"


def _graph_post(endpoint: str, params: dict) -> dict:
    """Make a POST request to the Meta Graph API."""
    url = f"{GRAPH_API_BASE}/{endpoint}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(error_body)
            msg = error_data.get("error", {}).get("message", error_body)
            code = error_data.get("error", {}).get("code", exc.code)
        except Exception:
            msg = error_body
            code = exc.code
        raise InstagramPublishError(f"Instagram API error {code}: {msg}") from exc
    except Exception as exc:
        raise InstagramPublishError(
            f"Network error calling Instagram API: {exc}"
        ) from exc


def _create_media_container(
    instagram_account_id: str,
    image_url: str,
    caption: str,
    access_token: str,
) -> str:
    """Create an Instagram media container and return its ID."""
    result = _graph_post(
        endpoint=f"{instagram_account_id}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
    )
    if "id" not in result:
        raise InstagramPublishError(
            f"Failed to create Instagram media container: {result}"
        )
    return result["id"]


def _publish_media_container(
    instagram_account_id: str,
    container_id: str,
    access_token: str,
) -> str:
    """Publish a media container and return the media ID."""
    result = _graph_post(
        endpoint=f"{instagram_account_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": access_token,
        },
    )
    if "id" not in result:
        raise InstagramPublishError(
            f"Failed to publish Instagram media container: {result}"
        )
    return result["id"]
