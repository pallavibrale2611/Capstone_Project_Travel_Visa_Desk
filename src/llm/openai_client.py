"""OpenAI client implementation (placeholder for future use)."""

from typing import AsyncIterable
from .base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client implementation."""
    
    def __init__(self, model_name: str = "gpt-4", **kwargs):
        super().__init__(model_name, **kwargs)
        # Initialize OpenAI client here when needed
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI."""
        # Placeholder implementation
        raise NotImplementedError("OpenAI client not implemented yet")
    
    async def stream(self, prompt: str, **kwargs) -> AsyncIterable[str]:
        """Stream text generation using OpenAI."""
        # Placeholder implementation
        raise NotImplementedError("OpenAI streaming not implemented yet")