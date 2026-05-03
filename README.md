# Trend-to-Content Automation Engine

A Python-based pipeline that scrapes trending Reddit topics, analyzes them with an LLM, and generates brand-specific marketing assets — text posts, video scripts, and image prompts — via a Streamlit web interface.

## Prerequisites

- Python 3.10 or higher
- [conda](https://docs.conda.io/en/latest/) or `pip` with a virtual environment
- A Gemini or OpenAI API key (optional — mock mode works without any keys)

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd trend-to-content-automation-engine
   ```

2. **Create and activate a Python environment**

   Using conda:
   ```bash
   conda create -n reddit_proj_env python=3.10
   conda activate reddit_proj_env
   ```

   Or using venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your API keys:

   ```dotenv
   # Choose your LLM provider: "gemini" or "openai"
   LLM_PROVIDER=gemini

   # Required when LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-gemini-api-key-here

   # Required when LLM_PROVIDER=openai
   OPENAI_API_KEY=your-openai-api-key-here
   ```

   > **Note**: API keys are optional if you only want to run the app with mock data. The mock pipeline works without any credentials.

## Running the App

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`. Enter a subreddit name in the sidebar (e.g., `technology`) and click **Fetch Trends** to run the pipeline.

## Running Tests

Run the full unit test suite:

```bash
pytest tests/
```

Run integration tests (full mock pipeline end-to-end):

```bash
pytest tests/ -m integration
```

Run all tests including integration:

```bash
pytest tests/ -v
```

Run a specific test file:

```bash
pytest tests/test_integration.py -v
```

## Project Structure

```
.
├── app.py                          # Streamlit UI — orchestrates the pipeline
├── requirements.txt                # Pinned Python dependencies
├── .env.example                    # Environment variable template
├── pytest.ini                      # Pytest configuration and marker registration
├── src/
│   ├── config.py                   # AppConfig — loads settings from .env
│   ├── ingestion/
│   │   └── reddit_scraper.py       # Reddit scraper (crawl4ai) + mock implementation
│   ├── ai/
│   │   ├── analyzer.py             # Trend analysis via LLM → TrendSummary
│   │   ├── generator.py            # Content generation via LLM → GeneratedContent
│   │   └── parser.py               # Shared LLM JSON response parser
│   └── models/
│       └── schemas.py              # Pydantic models: TrendSummary, GeneratedContent
└── tests/
    ├── test_schemas.py             # Schema validation unit tests
    ├── test_config.py              # AppConfig unit tests
    ├── test_reddit_scraper.py      # Scraper unit tests
    ├── test_analyzer.py            # Analyzer unit tests
    ├── test_generator.py           # Generator unit tests
    ├── test_parser.py              # Parser unit tests
    └── test_integration.py         # Integration + property-based tests
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | No | `gemini` | LLM backend to use: `gemini` or `openai` |
| `GEMINI_API_KEY` | When `LLM_PROVIDER=gemini` | — | Google Gemini API key |
| `OPENAI_API_KEY` | When `LLM_PROVIDER=openai` | — | OpenAI API key |

Get a Gemini key at [aistudio.google.com](https://aistudio.google.com/app/apikey) and an OpenAI key at [platform.openai.com](https://platform.openai.com/api-keys).
