"""
Provider Discovery Service

Modular service for discovering available models from different LLM providers.
Each provider has its own discovery function that can be extended independently.
"""

import logging
import os
from typing import List, Dict, Optional
import httpx
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ModelInfo:
    """Standardized model information"""
    def __init__(self, name: str, provider: str, display_name: str, **metadata):
        self.name = name
        self.provider = provider
        self.display_name = display_name
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "model": self.name,
            "provider": self.provider,
            "display": self.display_name,
            **self.metadata
        }


class ProviderDiscovery(ABC):
    """Base class for provider discovery"""

    @abstractmethod
    async def discover_models(self) -> List[ModelInfo]:
        """Discover available models from the provider"""
        pass


class OllamaDiscovery(ProviderDiscovery):
    """Ollama provider discovery"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def discover_models(self) -> List[ModelInfo]:
        """
        Fetch available models from Ollama API

        Endpoint: GET /api/tags
        Returns list of locally available Ollama models
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

                models = []
                for model_data in data.get("models", []):
                    model_name = model_data.get("name", "")
                    if not model_name:
                        continue

                    # Extract model details
                    details = model_data.get("details", {})
                    size = model_data.get("size", 0)

                    # Create display name from model name and details
                    family = details.get("family", "")
                    param_size = details.get("parameter_size", "")

                    display_name = model_name
                    if param_size:
                        display_name = f"Ollama - {model_name} ({param_size})"
                    else:
                        display_name = f"Ollama - {model_name}"

                    models.append(ModelInfo(
                        name=model_name,
                        provider="ollama",
                        display_name=display_name,
                        tools_support=False,  # Ollama models typically don't support function calling
                        size=size,
                        family=family,
                        parameter_size=param_size,
                        quantization=details.get("quantization_level", "")
                    ))

                logger.info(f"Discovered {len(models)} Ollama models")
                return models

        except httpx.ConnectError:
            logger.error(f"Could not connect to Ollama at {self.base_url}. Is Ollama running?")
            raise Exception(f"Ollama is not running or not accessible at {self.base_url}")
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Ollama at {self.base_url}")
            raise Exception(f"Timeout connecting to Ollama at {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to discover Ollama models: {str(e)}")
            raise Exception(f"Failed to discover Ollama models: {str(e)}")


class AnthropicDiscovery(ProviderDiscovery):
    """Anthropic provider discovery"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        self.api_version = "2023-06-01"

    async def discover_models(self) -> List[ModelInfo]:
        """
        Fetch available models from Anthropic API

        Endpoint: GET /v1/models
        Returns list of available Anthropic models
        """
        if not self.api_key:
            raise Exception("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")

        try:
            all_models = []
            url = f"{self.base_url}/models"

            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    response = await client.get(
                        url,
                        headers={
                            "x-api-key": self.api_key,
                            "anthropic-version": self.api_version
                        }
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Extract models from response
                    for model_data in data.get("data", []):
                        model_id = model_data.get("id", "")
                        if not model_id:
                            continue

                        display_name = model_data.get("display_name", model_id)
                        created_at = model_data.get("created_at", "")

                        # Create full display name with provider prefix
                        full_display = f"Anthropic - {display_name}"

                        # Most Claude models support tools/function calling
                        # We'll default to True for claude-3 and claude-sonnet-4 models
                        tools_support = "claude-3" in model_id or "claude-sonnet-4" in model_id or "claude-opus-4" in model_id

                        all_models.append(ModelInfo(
                            name=model_id,
                            provider="anthropic",
                            display_name=full_display,
                            tools_support=tools_support,
                            created_at=created_at,
                            model_type=model_data.get("type", "model")
                        ))

                    # Check for pagination
                    if not data.get("has_more", False):
                        break

                    # Handle pagination if needed
                    last_id = data.get("last_id")
                    if last_id:
                        url = f"{self.base_url}/models?after_id={last_id}"
                    else:
                        break

            logger.info(f"Discovered {len(all_models)} Anthropic models")
            return all_models

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Invalid Anthropic API key")
                raise Exception("Invalid Anthropic API key. Please check your ANTHROPIC_API_KEY.")
            elif e.response.status_code == 403:
                logger.error("Anthropic API access forbidden")
                raise Exception("Access forbidden. Your API key may not have permission to list models.")
            else:
                logger.error(f"HTTP error from Anthropic API: {e.response.status_code}")
                raise Exception(f"Anthropic API error: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Anthropic API")
            raise Exception("Timeout connecting to Anthropic API")
        except Exception as e:
            logger.error(f"Failed to discover Anthropic models: {str(e)}")
            raise Exception(f"Failed to discover Anthropic models: {str(e)}")


class GeminiDiscovery(ProviderDiscovery):
    """Gemini provider discovery"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def discover_models(self) -> List[ModelInfo]:
        """
        Fetch available models from Google Gemini API

        Endpoint: GET /v1beta/models
        Returns list of available Gemini models
        """
        if not self.api_key:
            raise Exception("Gemini API key not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    params={"key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()

                models = []
                for model_data in data.get("models", []):
                    model_name = model_data.get("name", "")
                    if not model_name:
                        continue

                    # Extract model ID from full name (e.g., "models/gemini-2.5-flash" -> "gemini-2.5-flash")
                    model_id = model_name.split("/")[-1] if "/" in model_name else model_name

                    display_name = model_data.get("displayName", model_id)
                    description = model_data.get("description", "")

                    # Create full display name with provider prefix
                    full_display = f"Gemini - {display_name}"

                    # Check if model supports content generation (required for chat)
                    supported_methods = model_data.get("supportedGenerationMethods", [])
                    supports_generation = "generateContent" in supported_methods

                    # Only include models that support content generation
                    if not supports_generation:
                        logger.debug(f"Skipping {model_id} - does not support generateContent")
                        continue

                    # Gemini models with "generateContent" typically support function calling
                    tools_support = "generateContent" in supported_methods

                    models.append(ModelInfo(
                        name=model_id,
                        provider="gemini",
                        display_name=full_display,
                        tools_support=tools_support,
                        description=description,
                        version=model_data.get("version", ""),
                        input_token_limit=model_data.get("inputTokenLimit", 0),
                        output_token_limit=model_data.get("outputTokenLimit", 0),
                        supported_methods=supported_methods
                    ))

                logger.info(f"Discovered {len(models)} Gemini models")
                return models

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Invalid Gemini API request")
                raise Exception("Invalid API request. Please check your GEMINI_API_KEY.")
            elif e.response.status_code == 403:
                logger.error("Gemini API access forbidden")
                raise Exception("Access forbidden. Your API key may be invalid or restricted.")
            else:
                logger.error(f"HTTP error from Gemini API: {e.response.status_code}")
                raise Exception(f"Gemini API error: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Gemini API")
            raise Exception("Timeout connecting to Gemini API")
        except Exception as e:
            logger.error(f"Failed to discover Gemini models: {str(e)}")
            raise Exception(f"Failed to discover Gemini models: {str(e)}")


class ProviderDiscoveryService:
    """Main service for coordinating provider discovery"""

    def __init__(self):
        self.providers = {
            "ollama": OllamaDiscovery(),
            "anthropic": AnthropicDiscovery(),
            "gemini": GeminiDiscovery()
        }

    async def discover_models(self, provider: str) -> List[ModelInfo]:
        """
        Discover models for a specific provider

        Args:
            provider: Provider name (ollama, anthropic, gemini)

        Returns:
            List of ModelInfo objects

        Raises:
            ValueError: If provider is not supported
            NotImplementedError: If provider discovery is not yet implemented
        """
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {list(self.providers.keys())}")

        discovery = self.providers[provider]
        return await discovery.discover_models()

    def get_supported_providers(self) -> List[str]:
        """Get list of supported providers"""
        return list(self.providers.keys())
