"""Configuration module for the generative AI code generator."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_name: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent / f"{config_name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file {config_path} not found")
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_model_config() -> Dict[str, Any]:
    """Get model configuration."""
    return load_config("model_config")

def get_prompt_templates() -> Dict[str, Any]:
    """Get prompt templates configuration."""
    return load_config("prompt_templates")

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return load_config("logging_config")