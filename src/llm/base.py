"""Base classes for LLM clients."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncIterable
from pydantic import BaseModel


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncIterable[str]:
        """Stream text generation from a prompt."""
        pass


class LLMResponse(BaseModel):
    """Standard response format for LLM operations."""
    content: str
    metadata: Dict[str, Any] = {}
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None