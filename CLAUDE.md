# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a POC web application demonstrating Mozilla AI's [any-llm](https://github.com/mozilla-ai/any-llm) Gateway, which provides a unified interface for switching between different LLM providers (Anthropic, Gemini, etc.) while tracking usage metrics centrally.

**Key architectural pattern**: The app uses the any-llm Gateway as a proxy layer to abstract away provider differences, allowing seamless model switching while maintaining centralized usage tracking per user.

## Development Commands

**Install dependencies**:
```bash
uv sync
```

**Run the application** (development mode with auto-reload):
```bash
uv run uvicorn app:app --reload
```

Or use the built-in runner:
```bash
uv run python app.py
```

The application runs on **http://localhost:8080**

## Prerequisites

The application requires a running any-llm Gateway instance. Start it with:
```bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  ghcr.io/mozilla-ai/any-llm:latest
```

Set the `GATEWAY_MASTER_KEY` in `.env` to authenticate with the Gateway.

## Architecture

**Single-file FastAPI backend** (app.py:1):
- Serves static frontend from `static/` directory
- All API endpoints are in one file for simplicity
- Uses `any_llm.completion()` SDK for chat completions
- Makes direct HTTP calls to Gateway API for usage metrics

**Frontend stack** (static/):
- Vanilla JavaScript (no framework)
- Session state management in memory
- Real-time metrics updates after each completion

**API Integration Pattern**:
1. Chat completions go through any-llm SDK → Gateway → Provider
2. The Gateway routes requests based on `provider:model` format (e.g., "gemini:gemini-2.5-flash-lite")
3. Usage metrics are fetched directly from Gateway's `/v1/users/{user_id}/usage` endpoint
4. A hardcoded `USER_ID = "user-123"` tracks all usage for this demo

## API Endpoints

- `GET /` - Serves the web interface
- `GET /api/models` - Returns available models from `AVAILABLE_MODELS` list
- `POST /api/chat` - Sends message to any-llm Gateway, returns response with token counts
- `GET /api/usage` - Aggregates total usage from Gateway for the hardcoded user

## Configuration

**Adding new models** (app.py:25-29):
Edit the `AVAILABLE_MODELS` list with the provider, model ID, and display name:
```python
AVAILABLE_MODELS = [
    {"provider": "gemini", "model": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite"},
    {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "display": "Claude 3.5 Haiku"},
    # Add more models here
]
```

**Environment variables**:
- `GATEWAY_MASTER_KEY` - Required for authenticating with the Gateway
- `GATEWAY_BASE_URL` defaults to `http://localhost:8000`

## Key Implementation Details

**Async/await pattern** (app.py:66):
The chat endpoint uses `await completion()` to handle async LLM calls properly.

**Session vs. Gateway metrics**:
- Session metrics (tracked in frontend state) reset when the user switches models
- Gateway total metrics persist across all sessions and model switches

**Token usage extraction** (app.py:76-84):
Response from `completion()` includes a `usage` object with `prompt_tokens`, `completion_tokens`, and `total_tokens` that gets passed to both the frontend and aggregated in Gateway metrics.
