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
    {"provider": "gemini", "model": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite", "tools_support": True},
    {"provider": "gemini", "model": "gemini-2.5-flash", "display": "Gemini 2.5 Flash", "tools_support": True},
    {"provider": "anthropic", "model": "claude-sonnet-4-5", "display": "Claude 4.5 Sonnet", "tools_support": True},
    {"provider": "anthropic", "model": "claude-haiku-4-5", "display": "Claude 4.5 Haiku", "tools_support": True},
    {"provider": "ollama", "model": "llama3:latest", "display": "llama3:latest", "tools_support": False},
]


# Tool functions for any-llm
def get_weather(location: str, unit: str = "F") -> str:
    """Get weather information for a location.

    Args:
        location: The city or location to get weather for
        unit: Temperature unit, either 'C' or 'F'

    Returns:
        str: Weather information for the location
    """
    # Pseudo implementation - returns mock weather data
    temp = 75 if unit == "F" else 24
    return f"Weather in {location} is sunny and {temp}{unit}!"


def divide(dividend: float, divisor: float) -> float:
    """Divide two numbers.

    Args:
        dividend: The number to be divided
        divisor: The number to divide by

    Returns:
        float: The result of dividend / divisor

    Raises:
        ValueError: If divisor is zero
    """
    if divisor == 0:
        raise ValueError("Cannot divide by zero")
    return dividend / divisor


# List of available tools
AVAILABLE_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "location": {"type": "string", "description": "The city or location to get weather for"},
            "unit": {"type": "string", "description": "Temperature unit, either 'C' or 'F'", "default": "F"}
        }
    },
    {
        "name": "divide",
        "description": "Divide two numbers",
        "parameters": {
            "dividend": {"type": "number", "description": "The number to be divided"},
            "divisor": {"type": "number", "description": "The number to divide by"}
        }
    }
]


# Request/Response models
class ChatRequest(BaseModel):
    provider: str
    model: str
    message: str
    tools_support: bool


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


@app.get("/api/tools")
async def get_tools():
    """Return list of available tools"""
    return {"tools": AVAILABLE_TOOLS}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat completion requests with tool support"""

    try:
        # Build acompletion kwargs based on tools_support
        completion_kwargs = {
            "provider": request.provider,
            "model": request.model,
            "messages": [{"role": "user", "content": request.message}],
            "max_tokens": 2048,
        }

        # Only add tools if the model supports them
        if request.tools_support:
            completion_kwargs["tools"] = [get_weather, divide]

        # Call any-llm SDK with conditional tool support
        response = await acompletion(**completion_kwargs)

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
