import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from any_llm import acompletion

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="any-llm Direct Provider POC")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Available models
AVAILABLE_MODELS = [
    {"provider": "gemini", "model": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite"},
    {"provider": "gemini", "model": "gemini-2.5-flash", "display": "Gemini 2.5 Flash"},
    {"provider": "anthropic", "model": "claude-sonnet-4-5", "display": "Claude 4.5 Sonnet"},
    {"provider": "anthropic", "model": "claude-haiku-4-5", "display": "Claude 4.5 Haiku"},
]


# Request/Response models
class ChatRequest(BaseModel):
    provider: str
    model: str
    message: str


class ChatResponse(BaseModel):
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("Starting any-llm Direct Provider POC application")
    logger.info(f"Available models: {len(AVAILABLE_MODELS)}")

    # Check for required API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not configured - Anthropic models will fail")
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        logger.warning("GOOGLE_API_KEY/GEMINI_API_KEY not configured - Gemini models will fail")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("Shutting down any-llm Direct Provider POC application")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/api/models")
async def get_models():
    """Return list of available models"""
    return {"models": AVAILABLE_MODELS}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat completion requests"""
    logger.info(f"Chat request - model: {request.provider}:{request.model}")

    try:
        # Call any-llm SDK directly (no Gateway)
        response = await acompletion(
            provider=request.provider,
            model=request.model,
            messages=[{"role": "user", "content": request.message}],
            max_tokens=2048,
        )

        # Extract response and token usage
        content = response.choices[0].message.content
        usage = response.usage

        logger.info(
            f"Chat completion successful - "
            f"tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, "
            f"completion: {usage.completion_tokens})"
        )

        return ChatResponse(
            response=content,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    except AttributeError as e:
        logger.error(f"Chat completion response parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invalid response format: {str(e)}")
    except Exception as e:
        logger.error(f"Chat completion failed - model: {request.provider}:{request.model}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
