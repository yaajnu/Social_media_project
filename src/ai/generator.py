import json

from pydantic import ValidationError

from src.ai.parser import _parse_llm_response
from src.config import AppConfig
from src.models.schemas import GeneratedContent, TopicPost, TrendSummary


class GenerationError(Exception):
    """Raised when the LLM response cannot be parsed into a GeneratedContent."""


def get_mock_generated_content() -> GeneratedContent:
    """
    Return a hardcoded valid GeneratedContent for offline/test use.

    All fields satisfy their length constraints:
    - text_post: 10–500 characters
    - video_script: ≥50 characters
    - image_prompt: ≥20 characters
    """
    return GeneratedContent(
        text_post="The AI regulation wave is here — is your brand ready? 🤖⚖️ #AILaw #TechPolicy",
        video_script=(
            "[HOOK] Everyone's talking about AI laws — but what does it mean for YOU?\n"
            "[BODY] Congress just passed sweeping AI regulation bills, and the tech world is reacting fast. "
            "From startups to Big Tech, nobody is immune. Here's what you need to know in 30 seconds.\n"
            "[CTA] Follow for daily tech breakdowns. Drop a comment: are you for or against AI regulation?"
        ),
        image_prompt=(
            "A sleek robot standing in a grand courtroom, dramatic cinematic lighting, "
            "scales of justice in the background, editorial photography style, high contrast, "
            "photorealistic, 4K resolution."
        ),
    )


def _build_generation_prompt(trend: TrendSummary, news_context: str = "") -> str:
    """
    Build a structured prompt asking the LLM to return JSON matching GeneratedContent.

    Args:
        trend: A validated TrendSummary containing why_trending, sentiment, and key_joke.
        news_context: Optional formatted news articles to ground the content.

    Returns:
        A prompt string that includes all TrendSummary field values and the
        GeneratedContent JSON schema.
    """
    news_section = ""
    if news_context:
        news_section = f"""
Recent news articles about this topic:
{news_context}

Use these articles to make the content factually grounded and specific.
"""

    prompt = f"""You are a viral social media content writer. Based on the trend summary and news research below, generate marketing assets.

Trend Summary:
- Why it's trending: {trend.why_trending}
- Sentiment: {trend.sentiment}
- Key joke / cultural reference: {trend.key_joke}
{news_section}
---
REFERENCE EXAMPLES — study these high-performing post styles and use them as inspiration:

Style 1 (Curiosity gap + stat):
"Nobody's talking about this: EV sales just overtook gas cars in Europe for the first time ever. 51% of new registrations. The shift isn't coming — it already happened. 🔋"

Style 2 (Hot take / contrarian):
"Unpopular opinion: the cloud outage wasn't a disaster. It was a $10B reminder that every company needs a backup plan. Downtime is the new marketing."

Style 3 (Relatable + humour):
"AI regulation passed and suddenly every tech bro who said 'move fast and break things' is very quiet. Very. Quiet. 🤫"

Style 4 (News hook + question):
"A 1000-qubit quantum processor just dropped. Scientists say error rates are below 0.1%. So… when do we start worrying about encryption? 👀"

Style 5 (List / punchy):
"3 things that happened this week that nobody expected:
→ Quantum hit 1000 qubits
→ EVs outsold gas cars in Europe
→ AI got regulated
We're living in the future and it's chaotic. 🌀"

---
Rules for the text_post:
- Must be between 10 and 500 characters
- Use one of the styles above as a template — adapt it to the actual trend
- Include at least one specific fact or detail from the news articles
- End with a relevant emoji or punchy one-liner
- NO generic filler like "In today's fast-paced world..."

Return a single flat JSON object with EXACTLY these three keys:
- "text_post": catchy social media caption (10–500 chars) inspired by the reference styles above
- "video_script": a single plain string (≥50 chars) — NOT a nested object. Write it as one continuous script with the words HOOK:, BODY:, and CTA: inline as labels within the string, e.g. "HOOK: ... BODY: ... CTA: ..."
- "image_prompt": detailed AI image generator prompt (≥20 chars)

Return ONLY the JSON object. No markdown fences, no extra keys, no nested objects, no explanation.
{{
  "text_post": "...",
  "video_script": "HOOK: One surprising fact. BODY: Here is what it means for you. CTA: Follow for more.",
  "image_prompt": "..."
}}"""
    return prompt


def generate_content(trend: TrendSummary, news_context: str = "") -> GeneratedContent:
    """
    Generate marketing content based on a trend summary using an LLM.

    Args:
        trend: Validated TrendSummary from analyze_trend().

    Returns:
        GeneratedContent with text_post, video_script, and image_prompt fields.

    Raises:
        GenerationError: If the LLM response cannot be parsed into GeneratedContent,
                         or if the API call fails.
    """
    prompt = _build_generation_prompt(trend, news_context=news_context)
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

        return _parse_llm_response(raw, GeneratedContent)  # type: ignore[return-value]

    except (ValueError, ValidationError, Exception) as exc:
        raise GenerationError(f"Failed to generate content: {exc}") from exc


def _build_topic_post_prompt(topic_title: str, news_context: str = "") -> str:
    """Build a prompt for generating a single topic-specific text post + image prompt."""
    news_section = ""
    if news_context:
        news_section = f"""
Recent news articles:
{news_context}

Use specific facts from these articles to make the post credible and grounded.
"""

    return f"""You are a viral social media content writer. Write a post specifically about this trending topic.

Topic: {topic_title}
{news_section}
---
REFERENCE STYLES — pick one and adapt it to this topic:

Style 1 (Curiosity gap + stat):
"Nobody's talking about this: EV sales just overtook gas cars in Europe for the first time. 51% of new registrations. The shift already happened. 🔋"

Style 2 (Hot take):
"Unpopular opinion: the cloud outage wasn't a disaster. It was a $10B reminder that every company needs a backup plan."

Style 3 (Relatable + humour):
"AI regulation passed and suddenly every tech bro who said 'move fast and break things' is very quiet. 🤫"

Style 4 (News hook + question):
"A 1000-qubit quantum processor just dropped. Error rates below 0.1%. So… when do we start worrying about encryption? 👀"

Style 5 (Punchy list):
"3 things nobody expected this week:
→ Quantum hit 1000 qubits
→ EVs outsold gas cars in Europe
→ AI got regulated
We're living in the future. 🌀"

---
Rules:
- text_post must be 10–500 characters
- Include at least one specific fact from the news if available
- End with a relevant emoji or punchy line
- NO generic filler phrases

Return a single flat JSON object with EXACTLY these two keys:
- "text_post": catchy caption (10–500 chars)
- "image_prompt": detailed AI image generator prompt (≥20 chars) that visually represents this topic

Return ONLY the JSON. No markdown, no extra keys, no nested objects.
{{
  "text_post": "...",
  "image_prompt": "..."
}}"""


def generate_topic_post(
    topic_title: str,
    news_context: str = "",
) -> TopicPost:
    """
    Generate a text post and image prompt for a single trending topic.

    Args:
        topic_title: The trending topic title.
        news_context: Formatted news articles for this topic.

    Returns:
        TopicPost with text_post and image_prompt fields.

    Raises:
        GenerationError: If the LLM call or parsing fails.
    """
    prompt = _build_topic_post_prompt(topic_title, news_context=news_context)
    config = AppConfig()

    try:
        if config.llm_provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=config.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw = response.text
        else:
            from openai import OpenAI

            client = OpenAI(api_key=config.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content

        return _parse_llm_response(raw, TopicPost)  # type: ignore[return-value]

    except (ValueError, ValidationError, Exception) as exc:
        raise GenerationError(
            f"Failed to generate post for '{topic_title}': {exc}"
        ) from exc
