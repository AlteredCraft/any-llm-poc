import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from any_llm import acompletion

# Load environment variables
load_dotenv()

app = FastAPI(title="any-llm Gateway POC")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Constants
GATEWAY_BASE_URL = "http://localhost:8000"
GATEWAY_MASTER_KEY = os.getenv("GATEWAY_MASTER_KEY")

# Available models (you can configure these based on your Gateway setup)
AVAILABLE_MODELS = [
    {"provider": "gemini", "model": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite"},
    {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "display": "Claude 3.5 Haiku"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "display": "Claude 3.5 Sonnet"},
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
    user_id: str


class CreateUserRequest(BaseModel):
    user_id: str
    alias: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard page"""
    return FileResponse("static/dashboard.html")


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
    if not GATEWAY_MASTER_KEY:
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        # Call any-llm SDK via Gateway with tools
        response = await acompletion(
            provider="gateway",
            model=f"{request.provider}:{request.model}",
            api_base=f"{GATEWAY_BASE_URL}/v1",
            api_key=GATEWAY_MASTER_KEY,
            messages=[{"role": "user", "content": request.message}],
            user=request.user_id,
            tools=[get_weather, divide],  # Pass Python callables as tools
        )

        # Extract response and token usage
        content = response.choices[0].message.content
        usage = response.usage

        return ChatResponse(
            response=content,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@app.get("/api/users")
async def get_users():
    """Fetch all users from Gateway API"""
    if not GATEWAY_MASTER_KEY:
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers
        )
        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@app.post("/api/users")
async def create_user(user_request: CreateUserRequest):
    """Create a new user in Gateway"""
    if not GATEWAY_MASTER_KEY:
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers,
            json={"user_id": user_request.user_id, "alias": user_request.alias}
        )
        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@app.get("/api/usage")
async def get_usage(user_id: str = Query(..., description="User ID to fetch usage for")):
    """Fetch total usage for a specific user from Gateway API"""
    if not GATEWAY_MASTER_KEY:
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users/{user_id}/usage",
            headers=headers
        )
        response.raise_for_status()

        usage_data = response.json()

        # Calculate totals
        total_prompt_tokens = sum(item.get("prompt_tokens") or 0 for item in usage_data)
        total_completion_tokens = sum(item.get("completion_tokens") or 0 for item in usage_data)
        total_tokens = sum(item.get("total_tokens") or 0 for item in usage_data)
        total_cost = sum(item.get("cost") or 0 for item in usage_data)

        return {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "request_count": len(usage_data)
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage: {str(e)}")


@app.get("/api/usage/global")
async def get_global_usage():
    """Fetch global usage across all users"""
    if not GATEWAY_MASTER_KEY:
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        # Get all users
        users_response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers
        )
        users_response.raise_for_status()
        users = users_response.json()

        # Aggregate usage from all users
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        total_cost = 0
        total_requests = 0

        for user in users:
            usage_response = requests.get(
                f"{GATEWAY_BASE_URL}/v1/users/{user['user_id']}/usage",
                headers=headers
            )
            if usage_response.ok:
                usage_data = usage_response.json()
                total_prompt_tokens += sum(item.get("prompt_tokens") or 0 for item in usage_data)
                total_completion_tokens += sum(item.get("completion_tokens") or 0 for item in usage_data)
                total_tokens += sum(item.get("total_tokens") or 0 for item in usage_data)
                total_cost += sum(item.get("cost") or 0 for item in usage_data)
                total_requests += len(usage_data)

        return {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "total_users": len(users)
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch global usage: {str(e)}")


@app.get("/api/usage/users")
async def get_all_users_usage():
    """Fetch usage for all users"""
    if not GATEWAY_MASTER_KEY:
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        # Get all users
        users_response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers
        )
        users_response.raise_for_status()
        users = users_response.json()

        # Get usage for each user
        users_usage = []
        for user in users:
            usage_response = requests.get(
                f"{GATEWAY_BASE_URL}/v1/users/{user['user_id']}/usage",
                headers=headers
            )
            if usage_response.ok:
                usage_data = usage_response.json()
                prompt_tokens = sum(item.get("prompt_tokens") or 0 for item in usage_data)
                completion_tokens = sum(item.get("completion_tokens") or 0 for item in usage_data)
                total_tokens = sum(item.get("total_tokens") or 0 for item in usage_data)
                total_cost = sum(item.get("cost") or 0 for item in usage_data)

                users_usage.append({
                    "user_id": user["user_id"],
                    "alias": user.get("alias"),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": total_cost,
                    "request_count": len(usage_data)
                })

        return users_usage

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users usage: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
