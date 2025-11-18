"""Token counting utilities for LLM usage tracking."""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    model: Optional[str] = None
    cost_estimate: Optional[float] = None
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


class TokenCounter:
    """Utility for counting and tracking token usage."""
    
    # Approximate token counts (rough estimates)
    CHARS_PER_TOKEN = {
        "gpt-3.5": 4,
        "gpt-4": 4,
        "gemini": 4,
        "claude": 5,
        "default": 4
    }
    
    # Cost per 1K tokens (approximate, update with current pricing)
    COST_PER_1K_TOKENS = {
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
        "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    }
    
    def __init__(self):
        self.usage_history: list[TokenUsage] = []
        self.session_usage: Dict[str, TokenUsage] = {}
    
    def estimate_tokens(self, text: str, model: str = "default") -> int:
        """Estimate token count for text."""
        if not text:
            return 0
        
        chars_per_token = self.CHARS_PER_TOKEN.get(model, self.CHARS_PER_TOKEN["default"])
        
        # Simple estimation based on character count
        # This is rough - actual tokenizers would be more accurate
        char_count = len(text)
        estimated_tokens = max(1, char_count // chars_per_token)
        
        return estimated_tokens
    
    def estimate_cost(self, usage: TokenUsage) -> float:
        """Estimate cost for token usage."""
        if not usage.model or usage.model not in self.COST_PER_1K_TOKENS:
            return 0.0
        
        pricing = self.COST_PER_1K_TOKENS[usage.model]
        
        input_cost = (usage.input_tokens / 1000) * pricing["input"]
        output_cost = (usage.output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def record_usage(self, 
                    input_tokens: int, 
                    output_tokens: int, 
                    model: str = None,
                    session_id: str = None) -> TokenUsage:
        """Record token usage."""
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model
        )
        
        usage.cost_estimate = self.estimate_cost(usage)
        
        # Add to history
        self.usage_history.append(usage)
        
        # Update session usage
        if session_id:
            if session_id not in self.session_usage:
                self.session_usage[session_id] = TokenUsage(model=model)
            
            session_usage = self.session_usage[session_id]
            session_usage.input_tokens += input_tokens
            session_usage.output_tokens += output_tokens
            session_usage.total_tokens += input_tokens + output_tokens
            if usage.cost_estimate:
                session_usage.cost_estimate = (session_usage.cost_estimate or 0) + usage.cost_estimate
        
        return usage
    
    def get_total_usage(self) -> TokenUsage:
        """Get total usage across all sessions."""
        total = TokenUsage()
        
        for usage in self.usage_history:
            total.input_tokens += usage.input_tokens
            total.output_tokens += usage.output_tokens
            total.total_tokens += usage.total_tokens
            if usage.cost_estimate:
                total.cost_estimate = (total.cost_estimate or 0) + usage.cost_estimate
        
        return total
    
    def get_session_usage(self, session_id: str) -> Optional[TokenUsage]:
        """Get usage for a specific session."""
        return self.session_usage.get(session_id)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of usage statistics."""
        total = self.get_total_usage()
        
        # Group by model
        model_usage = {}
        for usage in self.usage_history:
            model = usage.model or "unknown"
            if model not in model_usage:
                model_usage[model] = TokenUsage(model=model)
            
            model_stats = model_usage[model]
            model_stats.input_tokens += usage.input_tokens
            model_stats.output_tokens += usage.output_tokens
            model_stats.total_tokens += usage.total_tokens
            if usage.cost_estimate:
                model_stats.cost_estimate = (model_stats.cost_estimate or 0) + usage.cost_estimate
        
        return {
            "total_usage": total,
            "model_breakdown": model_usage,
            "session_count": len(self.session_usage),
            "request_count": len(self.usage_history)
        }
    
    def reset_session(self, session_id: str):
        """Reset usage for a specific session."""
        if session_id in self.session_usage:
            del self.session_usage[session_id]
    
    def clear_history(self):
        """Clear all usage history."""
        self.usage_history.clear()
        self.session_usage.clear()


# Global token counter instance
global_token_counter = TokenCounter()


def count_tokens_in_text(text: str, model: str = "default") -> int:
    """Convenience function to count tokens in text."""
    return global_token_counter.estimate_tokens(text, model)


def record_llm_usage(input_tokens: int, 
                    output_tokens: int, 
                    model: str = None,
                    session_id: str = None) -> TokenUsage:
    """Convenience function to record LLM usage."""
    return global_token_counter.record_usage(input_tokens, output_tokens, model, session_id)