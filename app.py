import os
import json
import logging
from pathlib import Path
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

# Path to models config file
MODELS_CONFIG_FILE = Path(__file__).parent / "models_config.json"

# Global variable to store loaded models
AVAILABLE_MODELS = []


def load_models_config():
    """Load models configuration from JSON file"""
    global AVAILABLE_MODELS
    try:
        if not MODELS_CONFIG_FILE.exists():
            logger.error(f"Models config file not found: {MODELS_CONFIG_FILE}")
            AVAILABLE_MODELS = []
            return

        with open(MODELS_CONFIG_FILE, 'r') as f:
            AVAILABLE_MODELS = json.load(f)
        logger.info(f"Loaded {len(AVAILABLE_MODELS)} models from config file")
    except Exception as e:
        logger.error(f"Failed to load models config: {str(e)}")
        AVAILABLE_MODELS = []


def save_models_config(models: list):
    """Save models configuration to JSON file"""
    try:
        with open(MODELS_CONFIG_FILE, 'w') as f:
            json.dump(models, f, indent=2)
        logger.info(f"Saved {len(models)} models to config file")
        return True
    except Exception as e:
        logger.error(f"Failed to save models config: {str(e)}")
        return False


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
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    provider: str
    model: str
    messages: list[Message]
    tools_support: bool


class ChatResponse(BaseModel):
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ModelConfig(BaseModel):
    provider: str
    model: str
    display: str
    tools_support: bool


class ModelsConfigUpdate(BaseModel):
    models: list[ModelConfig]


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("Starting any-llm Direct Provider POC application")

    # Load models from config file
    load_models_config()
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
        # Convert Pydantic Message models to dicts for any-llm
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Build acompletion kwargs based on tools_support
        completion_kwargs = {
            "provider": request.provider,
            "model": request.model,
            "messages": messages,
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


@app.get("/dashboard")
async def dashboard():
    """Serve the models dashboard page"""
    return FileResponse("static/dashboard.html")


@app.get("/api/admin/models/config")
async def get_models_config():
    """Get current models configuration"""
    return {"models": AVAILABLE_MODELS}


@app.put("/api/admin/models/config")
async def update_models_config(config: ModelsConfigUpdate):
    """Update entire models configuration"""
    try:
        # Convert Pydantic models to dicts
        models_data = [model.model_dump() for model in config.models]

        # Save to file
        if save_models_config(models_data):
            # Reload into memory
            load_models_config()
            return {"success": True, "message": f"Updated {len(models_data)} models"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
    except Exception as e:
        logger.error(f"Failed to update models config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/models/config")
async def add_model(model: ModelConfig):
    """Add a new model to configuration"""
    try:
        # Check if model already exists
        model_dict = model.model_dump()
        for existing in AVAILABLE_MODELS:
            if existing["provider"] == model_dict["provider"] and existing["model"] == model_dict["model"]:
                raise HTTPException(status_code=400, detail="Model already exists")

        # Add model
        models_data = AVAILABLE_MODELS.copy()
        models_data.append(model_dict)

        # Save and reload
        if save_models_config(models_data):
            load_models_config()
            return {"success": True, "message": "Model added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/models/config/{provider}/{model}")
async def delete_model(provider: str, model: str):
    """Delete a model from configuration"""
    try:
        # Find and remove model
        models_data = [
            m for m in AVAILABLE_MODELS
            if not (m["provider"] == provider and m["model"] == model)
        ]

        if len(models_data) == len(AVAILABLE_MODELS):
            raise HTTPException(status_code=404, detail="Model not found")

        # Save and reload
        if save_models_config(models_data):
            load_models_config()
            return {"success": True, "message": "Model deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/models/reload")
async def reload_models():
    """Reload models configuration from file"""
    try:
        load_models_config()
        return {"success": True, "message": f"Reloaded {len(AVAILABLE_MODELS)} models"}
    except Exception as e:
        logger.error(f"Failed to reload models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
