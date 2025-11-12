import os
import logging
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

app = FastAPI(title="any-llm Gateway POC")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Constants
GATEWAY_BASE_URL = "http://localhost:8000"
GATEWAY_MASTER_KEY = os.getenv("GATEWAY_MASTER_KEY")
REQUEST_TIMEOUT = 30  # seconds

# Available models (you can configure these based on your Gateway setup)
AVAILABLE_MODELS = [
    {"provider": "gemini", "model": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite"},
    {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "display": "Claude 3.5 Haiku"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "display": "Claude 3.5 Sonnet"},
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


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("Starting any-llm Gateway POC application")
    logger.info(f"Gateway Base URL: {GATEWAY_BASE_URL}")
    if not GATEWAY_MASTER_KEY:
        logger.warning("GATEWAY_MASTER_KEY not configured - API calls will fail")
    else:
        logger.info("GATEWAY_MASTER_KEY configured successfully")
    logger.info(f"Available models: {len(AVAILABLE_MODELS)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("Shutting down any-llm Gateway POC application")


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


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat completion requests"""
    logger.info(f"Chat request - user: {request.user_id}, model: {request.provider}:{request.model}")

    if not GATEWAY_MASTER_KEY:
        logger.error("Chat request failed: GATEWAY_MASTER_KEY not configured")
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        # Call any-llm SDK via Gateway
        response = await acompletion(
            provider="gateway",
            model=f"{request.provider}:{request.model}",
            api_base=f"{GATEWAY_BASE_URL}/v1",
            api_key=GATEWAY_MASTER_KEY,
            messages=[{"role": "user", "content": request.message}],
            user=request.user_id,
        )

        # Extract response and token usage
        content = response.choices[0].message.content
        usage = response.usage

        logger.info(
            f"Chat completion successful - user: {request.user_id}, "
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
        logger.error(f"Chat completion response parsing error - user: {request.user_id}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invalid response format from Gateway: {str(e)}")
    except Exception as e:
        logger.error(f"Chat completion failed - user: {request.user_id}, model: {request.provider}:{request.model}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@app.get("/api/users")
async def get_users():
    """Fetch all users from Gateway API"""
    logger.info("Fetching all users from Gateway")

    if not GATEWAY_MASTER_KEY:
        logger.error("Get users failed: GATEWAY_MASTER_KEY not configured")
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        users = response.json()
        logger.info(f"Successfully fetched {len(users)} users")
        return users

    except requests.Timeout:
        logger.error(f"Request timeout while fetching users (timeout: {REQUEST_TIMEOUT}s)")
        raise HTTPException(status_code=504, detail="Gateway request timed out")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@app.post("/api/users")
async def create_user(user_request: CreateUserRequest):
    """Create a new user in Gateway"""
    logger.info(f"Creating user: {user_request.user_id} (alias: {user_request.alias})")

    if not GATEWAY_MASTER_KEY:
        logger.error("Create user failed: GATEWAY_MASTER_KEY not configured")
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers,
            json={"user_id": user_request.user_id, "alias": user_request.alias},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"Successfully created user: {user_request.user_id}")
        return result

    except requests.Timeout:
        logger.error(f"Request timeout while creating user {user_request.user_id} (timeout: {REQUEST_TIMEOUT}s)")
        raise HTTPException(status_code=504, detail="Gateway request timed out")
    except requests.RequestException as e:
        logger.error(f"Failed to create user {user_request.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@app.get("/api/usage")
async def get_usage(user_id: str = Query(..., description="User ID to fetch usage for")):
    """Fetch total usage for a specific user from Gateway API"""
    logger.info(f"Fetching usage for user: {user_id}")

    if not GATEWAY_MASTER_KEY:
        logger.error("Get usage failed: GATEWAY_MASTER_KEY not configured")
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users/{user_id}/usage",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        usage_data = response.json()

        # Calculate totals
        total_prompt_tokens = sum(item.get("prompt_tokens") or 0 for item in usage_data)
        total_completion_tokens = sum(item.get("completion_tokens") or 0 for item in usage_data)
        total_tokens = sum(item.get("total_tokens") or 0 for item in usage_data)
        total_cost = sum(item.get("cost") or 0 for item in usage_data)

        logger.info(
            f"Successfully fetched usage for user {user_id} - "
            f"requests: {len(usage_data)}, total_tokens: {total_tokens}, cost: ${total_cost:.4f}"
        )

        return {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "request_count": len(usage_data)
        }

    except requests.Timeout:
        logger.error(f"Request timeout while fetching usage for user {user_id} (timeout: {REQUEST_TIMEOUT}s)")
        raise HTTPException(status_code=504, detail="Gateway request timed out")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch usage for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage: {str(e)}")


@app.get("/api/usage/global")
async def get_global_usage():
    """Fetch global usage across all users"""
    logger.info("Fetching global usage across all users")

    if not GATEWAY_MASTER_KEY:
        logger.error("Get global usage failed: GATEWAY_MASTER_KEY not configured")
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        # Get all users
        users_response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        users_response.raise_for_status()
        users = users_response.json()

        logger.info(f"Aggregating usage for {len(users)} users")

        # Aggregate usage from all users
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        total_cost = 0
        total_requests = 0
        failed_users = []

        for user in users:
            user_id = user['user_id']
            try:
                usage_response = requests.get(
                    f"{GATEWAY_BASE_URL}/v1/users/{user_id}/usage",
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                if usage_response.ok:
                    usage_data = usage_response.json()
                    total_prompt_tokens += sum(item.get("prompt_tokens") or 0 for item in usage_data)
                    total_completion_tokens += sum(item.get("completion_tokens") or 0 for item in usage_data)
                    total_tokens += sum(item.get("total_tokens") or 0 for item in usage_data)
                    total_cost += sum(item.get("cost") or 0 for item in usage_data)
                    total_requests += len(usage_data)
                else:
                    logger.warning(f"Failed to fetch usage for user {user_id}: HTTP {usage_response.status_code}")
                    failed_users.append(user_id)
            except requests.Timeout:
                logger.warning(f"Timeout fetching usage for user {user_id}")
                failed_users.append(user_id)
            except Exception as e:
                logger.warning(f"Error fetching usage for user {user_id}: {str(e)}")
                failed_users.append(user_id)

        if failed_users:
            logger.warning(f"Global usage aggregation completed with {len(failed_users)} failures: {failed_users}")
        else:
            logger.info(f"Global usage aggregation successful - total_tokens: {total_tokens}, cost: ${total_cost:.4f}")

        return {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "total_users": len(users)
        }

    except requests.Timeout:
        logger.error(f"Request timeout while fetching global usage (timeout: {REQUEST_TIMEOUT}s)")
        raise HTTPException(status_code=504, detail="Gateway request timed out")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch global usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch global usage: {str(e)}")


@app.get("/api/usage/users")
async def get_all_users_usage():
    """Fetch usage for all users"""
    logger.info("Fetching usage for all users")

    if not GATEWAY_MASTER_KEY:
        logger.error("Get all users usage failed: GATEWAY_MASTER_KEY not configured")
        raise HTTPException(status_code=500, detail="GATEWAY_MASTER_KEY not configured")

    try:
        headers = {
            "X-AnyLLM-Key": f"Bearer {GATEWAY_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        # Get all users
        users_response = requests.get(
            f"{GATEWAY_BASE_URL}/v1/users",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        users_response.raise_for_status()
        users = users_response.json()

        logger.info(f"Fetching individual usage for {len(users)} users")

        # Get usage for each user
        users_usage = []
        failed_users = []

        for user in users:
            user_id = user["user_id"]
            try:
                usage_response = requests.get(
                    f"{GATEWAY_BASE_URL}/v1/users/{user_id}/usage",
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                if usage_response.ok:
                    usage_data = usage_response.json()
                    prompt_tokens = sum(item.get("prompt_tokens") or 0 for item in usage_data)
                    completion_tokens = sum(item.get("completion_tokens") or 0 for item in usage_data)
                    total_tokens = sum(item.get("total_tokens") or 0 for item in usage_data)
                    total_cost = sum(item.get("cost") or 0 for item in usage_data)

                    users_usage.append({
                        "user_id": user_id,
                        "alias": user.get("alias"),
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "cost": total_cost,
                        "request_count": len(usage_data)
                    })
                else:
                    logger.warning(f"Failed to fetch usage for user {user_id}: HTTP {usage_response.status_code}")
                    failed_users.append(user_id)
            except requests.Timeout:
                logger.warning(f"Timeout fetching usage for user {user_id}")
                failed_users.append(user_id)
            except Exception as e:
                logger.warning(f"Error fetching usage for user {user_id}: {str(e)}")
                failed_users.append(user_id)

        if failed_users:
            logger.warning(f"Fetched usage for {len(users_usage)}/{len(users)} users. Failed: {failed_users}")
        else:
            logger.info(f"Successfully fetched usage for all {len(users_usage)} users")

        return users_usage

    except requests.Timeout:
        logger.error(f"Request timeout while fetching users (timeout: {REQUEST_TIMEOUT}s)")
        raise HTTPException(status_code=504, detail="Gateway request timed out")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch users usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users usage: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
