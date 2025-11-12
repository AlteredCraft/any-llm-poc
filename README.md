# any-llm Gateway POC

A simple web application demonstrating the [any-llm](https://github.com/mozilla-ai/any-llm) Gateway's ability to switch between different LLM providers and models while tracking usage metrics.

## Features

- **Model Selection**: Choose between different LLM providers (Gemini, Claude, etc.)
- **Chat Interface**: Simple, clean chat UI
- **Usage Tracking**:
  - Per-session metrics (prompt tokens, completion tokens, total tokens)
  - Gateway total usage across all sessions
  - Automatic metric updates after each completion
- **Session Management**: Switching models resets the chat and session metrics

## Prerequisites

1. **Python 3.13+** with [uv](https://github.com/astral-sh/uv) installed
2. **any-llm Gateway** running locally:
   ```bash
   docker run -p 8000:8000 \
     -e ANTHROPIC_API_KEY=your_key \
     -e GEMINI_API_KEY=your_key \
     ghcr.io/mozilla-ai/any-llm:latest
   ```

## Setup

1. **Clone the repository**

2. **Create your `.env` file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and add your Gateway master key**:
   ```
   GATEWAY_MASTER_KEY=your_gateway_master_key_here
   ```

4. **Install dependencies** (uv will handle this automatically):
   ```bash
   uv sync
   ```

## Running the Application

Start the FastAPI server:

```bash
uv run uvicorn app:app --reload
```

Or use the built-in runner:

```bash
uv run python app.py
```

The application will be available at: **http://localhost:8080**

## Usage

1. Open your browser to `http://localhost:8080`
2. Select a model from the dropdown
3. Start chatting!
4. Watch the metrics update after each response
5. Switch models to reset the session and start fresh

## Architecture

- **Backend**: FastAPI (single file `app.py`)
- **Frontend**: Vanilla HTML/CSS/JavaScript (in `static/` directory)
- **API Integration**:
  - any-llm SDK for chat completions
  - Direct Gateway API calls for usage metrics

## API Endpoints

- `GET /` - Serve the web interface
- `GET /api/models` - List available models
- `POST /api/chat` - Send a chat message and get completion
- `GET /api/usage` - Fetch total usage from Gateway

## Customization

To add or modify available models, edit the `AVAILABLE_MODELS` list in `app.py`:

```python
AVAILABLE_MODELS = [
    {"provider": "gemini", "model": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite"},
    {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "display": "Claude 3.5 Haiku"},
    # Add more models here
]
```

## Teaching Notes

This POC demonstrates:
- How any-llm abstracts away provider differences
- Real-time usage tracking and cost monitoring
- Simple integration patterns for web applications
- The Gateway's role as a unified proxy for multiple providers
