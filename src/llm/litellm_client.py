
"""
LiteLLM Client for unified LLM access
Compliant with Section 6: LLM Integration Standards
"""

import yaml
from typing import Optional, Dict, Any, List
from litellm import completion, embedding
import os
from pathlib import Path

class LiteLLMClient:
    def __init__(self, config_path: str = "config/model_config.yaml"):
        """Initialize LiteLLM client with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.api_key = os.getenv("LITELLM_API_KEY")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from YAML."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate(
        self,
        prompt: str,
        model_type: str = "primary",
        **kwargs
    ) -> str:
        """
        Generate text using LiteLLM.
        
        Args:
            prompt: Input prompt
            model_type: Type of model to use (primary, precise, creative)
            **kwargs: Additional parameters to override config
        
        Returns:
            Generated text
        """
        model_config = self.config['models'].get(model_type, self.config['models']['primary'])
        
        # Merge config with kwargs
        params = {
            'model': model_config['model_name'],
            'messages': [{"role": "user", "content": prompt}],
            'temperature': model_config.get('temperature', 0.7),
            'max_tokens': model_config.get('max_tokens', 2048),
            'top_p': model_config.get('top_p', 0.95),
            **kwargs
        }
        
        try:
            response = completion(**params)
            return response.choices[0].message.content
        except Exception as e:
            # Try fallback models
            for fallback_model in self.config['api_settings'].get('fallback_models', []):
                try:
                    params['model'] = fallback_model
                    response = completion(**params)
                    return response.choices[0].message.content
                except:
                    continue
            raise e
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model_type: str = "primary",
        **kwargs
    ) -> str:
        """
        Chat with context using LiteLLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_type: Type of model to use
            **kwargs: Additional parameters
        
        Returns:
            Assistant's response
        """
        model_config = self.config['models'].get(model_type, self.config['models']['primary'])
        
        params = {
            'model': model_config['model_name'],
            'messages': messages,
            'temperature': model_config.get('temperature', 0.7),
            'max_tokens': model_config.get('max_tokens', 2048),
            **kwargs
        }
        
        response = completion(**params)
        return response.choices[0].message.content
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get text embedding using configured model.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        embedding_config = self.config['embedding']
        response = embedding(
            model=embedding_config['model_name'],
            input=[text]
        )
        return response.data[0]['embedding']
    
    def batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        embedding_config = self.config['embedding']
        batch_size = embedding_config.get('batch_size', 32)
        
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = embedding(
                model=embedding_config['model_name'],
                input=batch
            )
            all_embeddings.extend([item['embedding'] for item in response.data])
        
        return all_embeddings
