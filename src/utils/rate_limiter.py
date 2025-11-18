"""
Rate limiter for API endpoints
"""

import time
from collections import deque
from threading import Lock
from functools import wraps

class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = Lock()
    
    def __call__(self, func):
        """Decorator to rate limit a function."""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                
                # Remove old calls outside time window
                while self.calls and self.calls[0] < now - self.time_window:
                    self.calls.popleft()
                
                # Check if we've hit the limit
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.time_window - (now - self.calls[0])
                    if sleep_time > 0:
                        raise Exception(f"Rate limit exceeded. Try again in {sleep_time:.0f} seconds")
                
                # Add current call
                self.calls.append(now)
            
            return await func(*args, **kwargs)
        
        return async_wrapper