# Requirements Document: Trend-to-Content Automation Engine

## Introduction

This document defines the functional and non-functional requirements for the Trend-to-Content Automation Engine. The system automates the creation of brand-specific marketing content by scraping trending Reddit topics, analyzing them with an LLM, and generating marketing assets. Requirements are derived from the design document.

---

## Requirements

### 1. Data Ingestion

#### 1.1 Reddit Scraper

**User Story**: As a marketer, I want to fetch trending posts from any subreddit so that I can base my content on current, relevant topics.

**Acceptance Criteria**:

- [ ] 1.1.1 `get_trending_topics(subreddit, limit)` returns a list of dicts, each containing the keys `title`, `score`, `num_comments`, `url`, and `selftext`.
- [ ] 1.1.2 The returned list contains at most `limit` items.
- [ ] 1.1.3 All `title`, `url`, and `selftext` values are strings; `score` and `num_comments` are integers.
- [ ] 1.1.4 The function uses `crawl4ai` to crawl `https://www.reddit.com/r/{subreddit}/hot.json` (or the equivalent HTML page) without requiring Reddit API credentials.
- [ ] 1.1.5 When the subreddit does not exist, is inaccessible, or an HTTP error occurs (including HTTP 429 rate limiting), the function raises a `ScraperError` with a descriptive message.
- [ ] 1.1.6 A mock implementation (`get_mock_trending_topics`) is available that returns valid data without making any HTTP requests.

---

### 2. Data Models

#### 2.1 TrendSummary Schema

**User Story**: As a developer, I want all LLM analysis outputs to be strictly typed and validated so that downstream components receive reliable, well-formed data.

**Acceptance Criteria**:

- [ ] 2.1.1 `TrendSummary` is a Pydantic `BaseModel` with fields `why_trending` (str), `sentiment` (Literal), and `key_joke` (str).
- [ ] 2.1.2 `why_trending` must be at least 10 characters; validation raises `ValidationError` if shorter.
- [ ] 2.1.3 `sentiment` must be one of `"positive"`, `"negative"`, `"neutral"`, or `"mixed"`; any other value raises `ValidationError`.
- [ ] 2.1.4 `key_joke` must be at least 5 characters; validation raises `ValidationError` if shorter.
- [ ] 2.1.5 A valid `TrendSummary` can be constructed from a plain dict using `TrendSummary.model_validate(data)`.

#### 2.2 GeneratedContent Schema

**User Story**: As a developer, I want all LLM generation outputs to be strictly typed and validated so that the UI always receives complete, usable marketing assets.

**Acceptance Criteria**:

- [ ] 2.2.1 `GeneratedContent` is a Pydantic `BaseModel` with fields `text_post` (str), `video_script` (str), and `image_prompt` (str).
- [ ] 2.2.2 `text_post` must be between 10 and 500 characters; validation raises `ValidationError` outside this range.
- [ ] 2.2.3 `video_script` must be at least 50 characters; validation raises `ValidationError` if shorter.
- [ ] 2.2.4 `image_prompt` must be at least 20 characters; validation raises `ValidationError` if shorter.
- [ ] 2.2.5 A valid `GeneratedContent` can be constructed from a plain dict using `GeneratedContent.model_validate(data)`.

---

### 3. AI Analysis

#### 3.1 Trend Analyzer

**User Story**: As a marketer, I want the system to automatically summarize why a topic is trending and what its sentiment is so that I understand the cultural context before generating content.

**Acceptance Criteria**:

- [ ] 3.1.1 `analyze_trend(posts)` accepts a non-empty list of post dicts and returns a valid `TrendSummary` instance.
- [ ] 3.1.2 The function builds a prompt that includes all post titles and the `TrendSummary` JSON schema.
- [ ] 3.1.3 The function calls the configured LLM provider (Gemini or OpenAI) using the API key from `AppConfig`.
- [ ] 3.1.4 If the LLM response is not valid JSON or does not match the `TrendSummary` schema, the function raises `AnalysisError`.
- [ ] 3.1.5 A mock implementation (`get_mock_trend_summary`) is available that returns a valid `TrendSummary` without an API call.

---

### 4. AI Content Generation

#### 4.1 Content Generator

**User Story**: As a marketer, I want the system to generate a text post, video script, and image prompt based on the trend analysis so that I have ready-to-use marketing assets.

**Acceptance Criteria**:

- [ ] 4.1.1 `generate_content(trend)` accepts a valid `TrendSummary` and returns a valid `GeneratedContent` instance.
- [ ] 4.1.2 The function builds a prompt that includes all fields of the `TrendSummary` and the `GeneratedContent` JSON schema.
- [ ] 4.1.3 The function calls the configured LLM provider using the API key from `AppConfig`.
- [ ] 4.1.4 If the LLM response is not valid JSON or does not match the `GeneratedContent` schema, the function raises `GenerationError`.
- [ ] 4.1.5 A mock implementation (`get_mock_generated_content`) is available that returns a valid `GeneratedContent` without an API call.

---

### 5. LLM Response Parsing

#### 5.1 Robust JSON Parsing

**User Story**: As a developer, I want LLM responses to be parsed safely so that malformed outputs never crash the application unexpectedly.

**Acceptance Criteria**:

- [ ] 5.1.1 `_parse_llm_response(raw, model_cls)` strips markdown code fences (` ```json ... ``` `) before parsing.
- [ ] 5.1.2 If `raw` is not valid JSON, the function raises `ValueError` (not any other exception type).
- [ ] 5.1.3 If the parsed JSON does not match `model_cls`'s schema, the function raises `pydantic.ValidationError`.
- [ ] 5.1.4 For any string input, the function raises only `ValueError` or `ValidationError` — no unexpected exceptions propagate.
- [ ] 5.1.5 If `raw` is valid JSON matching the schema, the function returns a fully validated model instance.

---

### 6. Configuration

#### 6.1 Environment-Based Configuration

**User Story**: As a developer, I want all secrets and settings to be loaded from environment variables so that credentials are never hardcoded in source code.

**Acceptance Criteria**:

- [ ] 6.1.1 `AppConfig` is a Pydantic `BaseSettings` subclass that reads from a `.env` file.
- [ ] 6.1.2 `AppConfig` accepts optional `gemini_api_key` and `openai_api_key` fields.
- [ ] 6.1.3 `llm_provider` defaults to `"gemini"` and must be one of `"gemini"` or `"openai"`.
- [ ] 6.1.4 `AppConfig` does not require Reddit API credentials; `crawl4ai` performs unauthenticated HTTP crawling.
- [ ] 6.1.5 If any required environment variable is missing, `AppConfig` raises `ValidationError` at instantiation time.
- [ ] 6.1.6 A `.env.example` file is present in the repository root with placeholder values for `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `LLM_PROVIDER`.

---

### 7. User Interface

#### 7.1 Streamlit Application

**User Story**: As a marketer, I want a simple web interface where I can enter a subreddit and see the generated marketing content so that I can use the tool without writing code.

**Acceptance Criteria**:

- [ ] 7.1.1 The app renders a sidebar containing a text input for the subreddit name and a "Fetch Trends" button.
- [ ] 7.1.2 When the button is clicked, the app shows a spinner while the pipeline runs.
- [ ] 7.1.3 After a successful run, the app displays the `TrendSummary` fields (`why_trending`, `sentiment`, `key_joke`) in a collapsible expander labeled "Trend Analysis".
- [ ] 7.1.4 After a successful run, the app displays the `GeneratedContent` fields (`text_post`, `video_script`, `image_prompt`) in a collapsible expander labeled "Generated Content".
- [ ] 7.1.5 If any pipeline stage raises an exception (`ScraperError`, `AnalysisError`, `GenerationError`), the app displays a user-friendly error message via `st.error` without crashing.
- [ ] 7.1.6 The subreddit input defaults to a sensible example value (e.g., `"technology"`).

---

### 8. Pipeline Orchestration

#### 8.1 End-to-End Pipeline

**User Story**: As a developer, I want the three pipeline stages (ingest, analyze, generate) to be orchestrated in a clear sequence so that the system is easy to understand, test, and extend.

**Acceptance Criteria**:

- [ ] 8.1.1 The pipeline calls `get_trending_topics`, then `analyze_trend`, then `generate_content` in that order.
- [ ] 8.1.2 The output of `get_trending_topics` is passed directly as input to `analyze_trend`.
- [ ] 8.1.3 The output of `analyze_trend` is passed directly as input to `generate_content`.
- [ ] 8.1.4 The pipeline returns both the `TrendSummary` and `GeneratedContent` to the caller.
- [ ] 8.1.5 Any exception raised by a pipeline stage propagates to the caller without being silently swallowed.

---

### 9. Project Structure and Extensibility

#### 9.1 Module Layout

**User Story**: As a developer, I want the codebase to follow the defined directory structure so that it is easy to navigate and extend with new scrapers or LLM providers.

**Acceptance Criteria**:

- [ ] 9.1.1 The project follows the defined directory structure: `app.py`, `src/config.py`, `src/ingestion/reddit_scraper.py`, `src/ai/analyzer.py`, `src/ai/generator.py`, `src/models/schemas.py`.
- [ ] 9.1.2 Each directory under `src/` contains an `__init__.py` file.
- [ ] 9.1.3 A `requirements.txt` file lists all dependencies with pinned versions.
- [ ] 9.1.4 The ingestion layer is designed so that additional scrapers (e.g., Twitter, TikTok) can be added without modifying existing modules.
- [ ] 9.1.5 The LLM integration is designed so that switching between Gemini and OpenAI requires only a configuration change, not code changes.
