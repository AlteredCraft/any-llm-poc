"""
Provider Discovery Service

Modular service for discovering available models from different LLM providers.
Each provider has its own discovery function that can be extended independently.
"""

import logging
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
    """Anthropic provider discovery (placeholder for future implementation)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def discover_models(self) -> List[ModelInfo]:
        """
        Placeholder for Anthropic model discovery

        Anthropic doesn't have a public API for listing models,
        so we'll need to maintain a curated list or fetch from documentation.
        """
        logger.info("Anthropic discovery not yet implemented")
        raise NotImplementedError("Anthropic model discovery not yet implemented")


class GeminiDiscovery(ProviderDiscovery):
    """Gemini provider discovery (placeholder for future implementation)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def discover_models(self) -> List[ModelInfo]:
        """
        Placeholder for Gemini model discovery

        Will use Google's API to list available models.
        """
        logger.info("Gemini discovery not yet implemented")
        raise NotImplementedError("Gemini model discovery not yet implemented")


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
