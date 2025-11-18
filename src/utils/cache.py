"""Caching utilities for LLM responses and data."""

import json
import hashlib
import pickle
import time
from typing import Any, Optional, Dict, Union
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class CacheEntry:
    """Represents a cache entry."""
    key: str
    value: Any
    timestamp: float
    ttl: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class BaseCache(ABC):
    """Abstract base class for cache implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryCache(BaseCache):
    """In-memory cache implementation."""
    
    def __init__(self, default_ttl: Optional[float] = None):
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._cleanup_expired()
        
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                del self.cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )
        self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None
    
    def size(self) -> int:
        """Get cache size."""
        self._cleanup_expired()
        return len(self.cache)


class FileCache(BaseCache):
    """File-based cache implementation."""
    
    def __init__(self, cache_dir: Union[str, Path], default_ttl: Optional[float] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Create a safe filename from the key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                entry = pickle.load(f)
            
            if entry.is_expired():
                file_path.unlink()
                return None
            
            return entry.value
        except (pickle.PickleError, FileNotFoundError, EOFError):
            # Remove corrupted cache file
            if file_path.exists():
                file_path.unlink()
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )
        
        file_path = self._get_file_path(key)
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
        except pickle.PickleError:
            # If we can't pickle the value, don't cache it
            pass
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None


class LLMResponseCache:
    """Specialized cache for LLM responses."""
    
    def __init__(self, cache: BaseCache):
        self.cache = cache
    
    def _create_cache_key(self, 
                         prompt: str, 
                         model: str, 
                         parameters: Dict[str, Any] = None) -> str:
        """Create a cache key for LLM request."""
        key_data = {
            "prompt": prompt,
            "model": model,
            "parameters": parameters or {}
        }
        
        # Create a hash of the key data
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get_response(self, 
                    prompt: str, 
                    model: str, 
                    parameters: Dict[str, Any] = None) -> Optional[str]:
        """Get cached LLM response."""
        cache_key = self._create_cache_key(prompt, model, parameters)
        return self.cache.get(cache_key)
    
    def cache_response(self, 
                      prompt: str, 
                      model: str, 
                      response: str,
                      parameters: Dict[str, Any] = None,
                      ttl: Optional[float] = None) -> None:
        """Cache LLM response."""
        cache_key = self._create_cache_key(prompt, model, parameters)
        self.cache.set(cache_key, response, ttl)
    
    def invalidate_model_cache(self, model: str) -> None:
        """Invalidate all cached responses for a specific model."""
        # This is a simple implementation - in practice, you might want
        # to store model information in cache metadata for efficient invalidation
        if hasattr(self.cache, 'cache') and isinstance(self.cache.cache, dict):
            # For MemoryCache
            keys_to_delete = []
            for key, entry in self.cache.cache.items():
                # This is a simplified check - you might want to store model info in metadata
                keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.cache.delete(key)


# Global cache instances
memory_cache = MemoryCache(default_ttl=3600)  # 1 hour default TTL
file_cache = FileCache("data/cache", default_ttl=86400)  # 1 day default TTL
llm_cache = LLMResponseCache(memory_cache)