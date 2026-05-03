# Implementation Tasks: Trend-to-Content Automation Engine

## Overview

These tasks implement the Trend-to-Content Automation Engine as defined in the design and requirements documents. Tasks are ordered to build the foundation first (project structure, models, config) before higher-level components (ingestion, AI, UI).

---

## Tasks

- [x] 1 Set up project structure and dependencies
  - [x] 1.1 Create the directory structure: `src/`, `src/ingestion/`, `src/ai/`, `src/models/` with `__init__.py` in each
  - [x] 1.2 Create `requirements.txt` with pinned versions for all dependencies: `streamlit`, `crawl4ai`, `google-generativeai`, `openai`, `pydantic`, `pydantic-settings`, `python-dotenv`, `hypothesis`, `pytest`
  - [x] 1.3 Create `.env.example` with placeholder values for `GEMINI_API_KEY`, `OPENAI_API_KEY`, `LLM_PROVIDER`

- [x] 2 Implement Pydantic schemas (`src/models/schemas.py`)
  - [x] 2.1 Implement `TrendSummary` with fields `why_trending` (str, min_length=10), `sentiment` (Literal["positive","negative","neutral","mixed"]), `key_joke` (str, min_length=5)
  - [x] 2.2 Implement `GeneratedContent` with fields `text_post` (str, min_length=10, max_length=500), `video_script` (str, min_length=50), `image_prompt` (str, min_length=20)
  - [x] 2.3 Write unit tests for schema validation: valid construction, min/max length violations, invalid sentiment literal

- [x] 3 Implement configuration (`src/config.py`)
  - [x] 3.1 Implement `AppConfig` as a Pydantic `BaseSettings` subclass loading from `.env`
  - [x] 3.2 Add optional fields: `gemini_api_key`, `openai_api_key`, and `llm_provider` (default `"gemini"`); no Reddit credential fields are needed since `crawl4ai` performs unauthenticated crawling
  - [x] 3.3 Write unit tests verifying `ValidationError` is raised when required fields are missing

- [x] 4 Implement Reddit scraper (`src/ingestion/reddit_scraper.py`)
  - [x] 4.1 Implement `get_mock_trending_topics(subreddit: str) -> list[dict]` returning hardcoded mock data with all required keys
  - [x] 4.2 Implement `get_trending_topics(subreddit: str, limit: int = 10) -> list[dict]` using `crawl4ai` to crawl `https://www.reddit.com/r/{subreddit}/hot.json`; parse the JSON response and normalize posts to plain dicts with keys `title`, `score`, `num_comments`, `url`, `selftext`
  - [x] 4.3 Add error handling: catch HTTP errors (including HTTP 429 rate limiting) and crawl failures; re-raise as `ScraperError`
  - [x] 4.4 Write unit tests for mock data shape, key presence, type correctness, and `limit` parameter behavior

- [x] 5 Implement LLM response parser (shared utility)
  - [x] 5.1 Implement `_parse_llm_response(raw: str, model_cls: type[BaseModel]) -> BaseModel` that strips markdown fences, parses JSON, and validates against the model
  - [x] 5.2 Ensure only `ValueError` or `pydantic.ValidationError` propagate (no unexpected exceptions)
  - [x] 5.3 Write unit tests with valid JSON, malformed JSON, and schema-mismatched JSON inputs
  - [x] 5.4 Write a property-based test (hypothesis) verifying that for any string input, only `ValueError` or `ValidationError` are raised

- [x] 6 Implement AI analyzer (`src/ai/analyzer.py`)
  - [x] 6.1 Implement `get_mock_trend_summary() -> TrendSummary` returning a hardcoded valid `TrendSummary`
  - [x] 6.2 Implement `_build_analysis_prompt(posts: list[dict]) -> str` that includes all post titles and the `TrendSummary` JSON schema
  - [x] 6.3 Implement `analyze_trend(posts: list[dict]) -> TrendSummary` calling the configured LLM and parsing the response via `_parse_llm_response`
  - [x] 6.4 Catch LLM API errors and `_parse_llm_response` exceptions; re-raise as `AnalysisError`
  - [x] 6.5 Write unit tests for mock summary validity, prompt construction (titles present, schema present), and `AnalysisError` on bad LLM response

- [x] 7 Implement AI generator (`src/ai/generator.py`)
  - [x] 7.1 Implement `get_mock_generated_content() -> GeneratedContent` returning a hardcoded valid `GeneratedContent`
  - [x] 7.2 Implement `_build_generation_prompt(trend: TrendSummary) -> str` that includes all `TrendSummary` fields and the `GeneratedContent` JSON schema
  - [x] 7.3 Implement `generate_content(trend: TrendSummary) -> GeneratedContent` calling the configured LLM and parsing the response via `_parse_llm_response`
  - [x] 7.4 Catch LLM API errors and `_parse_llm_response` exceptions; re-raise as `GenerationError`
  - [x] 7.5 Write unit tests for mock content validity, prompt construction, and `GenerationError` on bad LLM response

- [x] 8 Implement Streamlit UI (`app.py`)
  - [x] 8.1 Add sidebar with subreddit text input (default: `"technology"`) and "Fetch Trends" button
  - [x] 8.2 On button click, run the full pipeline inside `st.spinner("Analyzing trends...")`
  - [x] 8.3 Display `TrendSummary` fields in a `st.expander("Trend Analysis")` with labeled fields
  - [x] 8.4 Display `GeneratedContent` fields in a `st.expander("Generated Content")` with labeled fields
  - [x] 8.5 Catch `ScraperError`, `AnalysisError`, and `GenerationError` and display via `st.error`

- [x] 9 Integration and end-to-end validation
  - [x] 9.1 Write an integration test (marked `@pytest.mark.integration`) that runs the full pipeline with mock implementations and verifies output types
  - [x] 9.2 Write a property-based test (hypothesis) verifying that for any valid `TrendSummary`, `get_mock_generated_content` returns a `GeneratedContent` satisfying all field constraints
  - [x] 9.3 Verify the app runs locally with `streamlit run app.py` using mock data (no API keys required)
  - [x] 9.4 Confirm `.env.example` covers all keys referenced in `AppConfig` (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `LLM_PROVIDER`) and add a `README.md` with setup instructions
