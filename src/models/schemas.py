from typing import Literal

from pydantic import BaseModel, Field


class TrendSummary(BaseModel):
    why_trending: str = Field(
        ...,
        description="A concise explanation of why this topic is trending.",
        min_length=10,
    )
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ...,
        description="Overall sentiment of the trend.",
    )
    key_joke: str = Field(
        ...,
        description="The central meme, joke, or cultural reference driving the trend.",
        min_length=5,
    )


class GeneratedContent(BaseModel):
    text_post: str = Field(
        ...,
        description="A short social media text post (tweet/caption style).",
        min_length=10,
        max_length=500,
    )
    video_script: str = Field(
        ...,
        description="A short video script (30–60 seconds) referencing the trend.",
        min_length=50,
    )
    image_prompt: str = Field(
        ...,
        description="A detailed prompt for an AI image generator.",
        min_length=20,
    )


class TopicPost(BaseModel):
    """Per-topic social post with a text caption and image prompt."""

    text_post: str = Field(
        ...,
        description="A catchy social media caption for this specific topic.",
        min_length=10,
        max_length=500,
    )
    image_prompt: str = Field(
        ...,
        description="A detailed AI image generator prompt for this topic.",
        min_length=20,
    )
