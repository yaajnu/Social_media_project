import json

from pydantic import ValidationError

from src.ai.parser import _parse_llm_response
from src.config import AppConfig
from src.models.schemas import TrendSummary


class AnalysisError(Exception):
    """Raised when the LLM response cannot be parsed into a TrendSummary."""


def get_mock_trend_summary() -> TrendSummary:
    """
    Return a hardcoded valid TrendSummary for offline/test use.

    All fields satisfy their min_length constraints.
    """
    return TrendSummary(
        why_trending="AI regulation bills are gaining momentum in Congress, sparking widespread debate.",
        sentiment="mixed",
        key_joke="'Move fast and break laws' era is officially over.",
    )


def _build_analysis_prompt(posts: list[dict]) -> str:
    """
    Build a structured prompt asking the LLM to return JSON matching TrendSummary.

    Args:
        posts: Raw topic dicts, each containing at least a 'title' key.
               May also contain 'traffic', 'description', and other fields.

    Returns:
        A prompt string that includes all topic titles and the TrendSummary JSON schema.
    """
    topic_lines = []
    for p in posts:
        line = f"- {p['title']}"
        if p.get("traffic") and p["traffic"] != "N/A":
            line += f" (search volume: {p['traffic']})"
        if p.get("description"):
            line += f" — {p['description']}"
        topic_lines.append(line)
    topics_text = "\n".join(topic_lines)

    prompt = f"""You are a social media trend analyst. Analyze the following trending topics as a whole and produce ONE combined summary.

Trending topics:
{topics_text}

Return a single flat JSON object with EXACTLY these three keys:
- "why_trending": a string (minimum 10 characters) explaining why these topics are trending overall
- "sentiment": one of exactly these four values: "positive", "negative", "neutral", or "mixed"
- "key_joke": a string (minimum 5 characters) with the central meme, joke, or cultural reference

Example of the EXACT format required:
{{
  "why_trending": "Sports rivalries and travel content are dominating social feeds this week.",
  "sentiment": "positive",
  "key_joke": "Everyone's a travel blogger until the flight gets cancelled."
}}

Return ONLY the JSON object. No markdown fences, no extra keys, no nested objects, no explanation."""
    return prompt


def analyze_trend(posts: list[dict]) -> TrendSummary:
    """
    Analyze a list of Reddit posts and summarize the trend using an LLM.

    Args:
        posts: Raw post dicts from get_trending_topics().

    Returns:
        TrendSummary with why_trending, sentiment, and key_joke fields.

    Raises:
        AnalysisError: If the LLM response cannot be parsed into TrendSummary,
                       or if the API call fails.
    """
    prompt = _build_analysis_prompt(posts)
    config = AppConfig()

    try:
        if config.llm_provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=config.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw = response.text
        else:  # openai
            from openai import OpenAI

            client = OpenAI(api_key=config.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content

        return _parse_llm_response(raw, TrendSummary)  # type: ignore[return-value]

    except (ValueError, ValidationError, Exception) as exc:
        raise AnalysisError(f"Failed to analyze trend: {exc}") from exc
