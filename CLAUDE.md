# CLAUDE.md

Project guidance for Claude Code (claude.ai/code).

## Overview

POC web app demonstrating the [any-llm](https://github.com/mozilla-ai/any-llm) SDK for switching between LLM providers (Anthropic, Gemini) with direct provider calls.

## Quick Start

```bash
# Install
uv sync

# Run
uv run uvicorn app:app --reload
# or
uv run python app.py
```

**Required environment variables** (`.env`):
- `ANTHROPIC_API_KEY` - For Claude models
- `GOOGLE_API_KEY` - For Gemini models

## Architecture

- **Backend**: Single-file FastAPI app (app.py)
- **Frontend**: Vanilla JS in `static/`
- **Pattern**: Direct provider calls via any-llm SDK (no Gateway/proxy)

## Key Files

- `app.py` - FastAPI backend with 3 endpoints: `/`, `/api/models`, `/api/chat`
- `static/index.html` - Chat UI with model selector
- `static/app.js` - Frontend logic and session metrics
- `AVAILABLE_MODELS` (app.py:30) - Configure available models here

## API Pattern

```python
response = await acompletion(
    provider=request.provider,  # "anthropic" or "gemini"
    model=request.model,
    messages=[{"role": "user", "content": request.message}],
    max_tokens=2048,
)
```

Returns token usage (`prompt_tokens`, `completion_tokens`, `total_tokens`) in each response.
