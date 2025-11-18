"""Utilities for LLM operations."""

import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from config import get_model_config


def create_gemini_client(model_name: Optional[str] = None, **kwargs) -> ChatGoogleGenerativeAI:
    """Create a Gemini client with configuration."""
    config = get_model_config()
    
    if model_name is None:
        model_name = config["models"]["gemini"]["name"]
    
    api_key = os.getenv(config["models"]["gemini"]["api_key_env"])
    if not api_key:
        raise ValueError(f"Missing API key: {config['models']['gemini']['api_key_env']}")
    
    client_config = {
        "model": model_name,
        "thinking_budget": config["models"]["gemini"].get("thinking_budget", -1),
        **kwargs
    }
    
    return ChatGoogleGenerativeAI(**client_config)


def get_model_client(model_type: str = "gemini", **kwargs):
    """Get a model client based on type."""
    if model_type == "gemini":
        return create_gemini_client(**kwargs)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")