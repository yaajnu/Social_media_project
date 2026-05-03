"""
Twitter/X publisher module.

Posts text content using the Twitter API v2 via tweepy.
Requires a Twitter Developer account with OAuth 1.0a credentials.
"""

import tweepy


class TwitterPublishError(Exception):
    """Raised when posting to Twitter fails."""

    pass


def post_to_twitter(
    text: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
) -> str:
    """
    Post a text tweet using Twitter API v2.

    Args:
        text: The tweet text (max 280 characters).
        api_key: Twitter API key (Consumer Key).
        api_secret: Twitter API secret (Consumer Secret).
        access_token: OAuth access token.
        access_token_secret: OAuth access token secret.

    Returns:
        URL of the posted tweet.

    Raises:
        TwitterPublishError: If authentication fails or the post request fails.
    """
    if not all([api_key, api_secret, access_token, access_token_secret]):
        raise TwitterPublishError("All four Twitter credentials are required.")

    # Truncate to 280 chars if needed
    if len(text) > 280:
        text = text[:277] + "..."

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        # Fetch the username to build the URL
        me = client.get_me()
        username = me.data.username if me and me.data else "i"
        return f"https://twitter.com/{username}/status/{tweet_id}"
    except tweepy.errors.Unauthorized as exc:
        raise TwitterPublishError(
            "Twitter authentication failed. Check your API key, secret, access token, and access token secret."
        ) from exc
    except tweepy.errors.Forbidden as exc:
        raise TwitterPublishError(
            f"Twitter posting forbidden: {exc}. Ensure your app has 'Read and Write' permissions."
        ) from exc
    except tweepy.errors.TweepyException as exc:
        raise TwitterPublishError(f"Twitter API error: {exc}") from exc
    except Exception as exc:
        raise TwitterPublishError(
            f"Unexpected error posting to Twitter: {exc}"
        ) from exc
