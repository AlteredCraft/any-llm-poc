import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from any_llm import acompletion
from tools import AVAILABLE_TOOLS, TOOL_FUNCTIONS, execute_tool_call

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

app = FastAPI(title="any-llm Reseach POC")

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
    logger.info("Starting any-llm Reseach POC application")

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
    logger.info("Shutting down any-llm Reseach POC application")


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


# Helper functions for chat endpoint

def _extract_tokens(usage) -> dict:
    """Safely extract token counts from usage object with None handling"""
    if not usage:
        return {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    return {
        'prompt_tokens': getattr(usage, 'prompt_tokens', 0) or 0,
        'completion_tokens': getattr(usage, 'completion_tokens', 0) or 0,
        'total_tokens': getattr(usage, 'total_tokens', 0) or 0,
    }


def _serialize_tool_calls(tool_calls) -> list[dict]:
    """Convert tool_call objects to API-compatible dicts"""
    return [
        {
            "id": tc.id,
            "type": "function",
            "function": {
                "name": tc.function.name,
                "arguments": tc.function.arguments
            }
        }
        for tc in tool_calls
    ]


async def _handle_tool_calls(
    message,
    messages: list,
    completion_kwargs: dict,
    initial_tokens: dict
) -> tuple[str, dict]:
    """
    Execute tool calls and get final LLM response with accumulated tokens.

    Args:
        message: The assistant message containing tool calls
        messages: The conversation history
        completion_kwargs: The completion API kwargs
        initial_tokens: Token counts from the initial LLM call

    Returns:
        Tuple of (final_content, accumulated_tokens)
    """
    logger.info(f"Tool calls detected: {len(message.tool_calls)} tool(s)")

    # Execute all tool calls
    tool_results = []
    for tool_call in message.tool_calls:
        tool_result = execute_tool_call(tool_call)
        tool_results.append(tool_result)

    # Add assistant's message with tool calls to conversation
    tool_calls_dicts = _serialize_tool_calls(message.tool_calls)
    messages.append({
        "role": "assistant",
        "content": message.content or "",  # Handle None content from tool calls
        "tool_calls": tool_calls_dicts
    })

    # Add tool results to conversation
    messages.extend(tool_results)

    # Call LLM again with tool results to get final response
    logger.info("Calling LLM with tool results")
    completion_kwargs["messages"] = messages

    # Debug logging to inspect message structure
    logger.debug(f"Sending messages with tool results: {json.dumps(messages, default=str)}")

    try:
        final_response = await acompletion(**completion_kwargs)
    except ValidationError as e:
        logger.error(f"Validation error in tool result completion: {e}")
        # Return error message with initial tokens
        return (
            f"Error processing tool results: {str(e)}",
            initial_tokens
        )

    # Extract final response
    final_message = final_response.choices[0].message
    final_content = final_message.content or ""
    final_usage = final_response.usage

    # Accumulate tokens
    final_tokens = _extract_tokens(final_usage)
    accumulated_tokens = {
        'prompt_tokens': initial_tokens['prompt_tokens'] + final_tokens['prompt_tokens'],
        'completion_tokens': initial_tokens['completion_tokens'] + final_tokens['completion_tokens'],
        'total_tokens': initial_tokens['total_tokens'] + final_tokens['total_tokens'],
    }

    logger.info(f"Tool calling flow completed successfully")
    return final_content, accumulated_tokens


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
            "stream": False,  # Disable streaming to get complete response object
        }

        # Only add tools if the model supports them
        if request.tools_support:
            completion_kwargs["tools"] = list(TOOL_FUNCTIONS.values())

        # Call any-llm SDK with conditional tool support
        response = await acompletion(**completion_kwargs)

        # Extract response and token usage
        message = response.choices[0].message
        content = message.content
        usage = response.usage

        # Extract tokens from initial response
        tokens = _extract_tokens(usage)

        # Handle tool calls - execute tools and get final response
        if message.tool_calls:
            content, tokens = await _handle_tool_calls(
                message, messages, completion_kwargs, tokens
            )
        elif content is None:
            # Fallback for unexpected None content
            content = ""
            logger.warning("Response content was None without tool calls")

        logger.info(
            f"Chat completion successful - "
            f"tokens: {tokens['total_tokens']} (prompt: {tokens['prompt_tokens']}, "
            f"completion: {tokens['completion_tokens']})"
        )

        return ChatResponse(
            response=content,
            prompt_tokens=tokens['prompt_tokens'],
            completion_tokens=tokens['completion_tokens'],
            total_tokens=tokens['total_tokens'],
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
