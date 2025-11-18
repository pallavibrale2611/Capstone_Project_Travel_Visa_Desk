"""Error handling utilities and custom exceptions."""

import logging
import traceback
from typing import Dict, Any, Optional, Type
from enum import Enum
from dataclasses import dataclass


class ErrorCode(Enum):
    """Standard error codes for the application."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


@dataclass
class ErrorDetails:
    """Detailed error information."""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "code": self.code.value,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        if self.traceback:
            result["traceback"] = self.traceback
        return result


class BaseAppException(Exception):
    """Base exception for application errors."""
    
    def __init__(self, 
                 message: str, 
                 code: ErrorCode = ErrorCode.INTERNAL_ERROR,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_error_details(self) -> ErrorDetails:
        """Convert to ErrorDetails."""
        return ErrorDetails(
            code=self.code,
            message=self.message,
            details=self.details,
            traceback=traceback.format_exc()
        )


class ValidationError(BaseAppException):
    """Validation error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details)


class AuthenticationError(BaseAppException):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AUTHENTICATION_ERROR, details)


class AuthorizationError(BaseAppException):
    """Authorization error."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AUTHORIZATION_ERROR, details)


class RateLimitError(BaseAppException):
    """Rate limit error."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.RATE_LIMIT_ERROR, details)


class ModelError(BaseAppException):
    """Model/LLM error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.MODEL_ERROR, details)


class NetworkError(BaseAppException):
    """Network error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.NETWORK_ERROR, details)


class NotFoundError(BaseAppException):
    """Not found error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.NOT_FOUND_ERROR, details)


class TimeoutError(BaseAppException):
    """Timeout error."""
    
    def __init__(self, message: str = "Operation timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.TIMEOUT_ERROR, details)


class ErrorHandler:
    """Central error handler for the application."""
    
    def __init__(self, logger_name: str = "error_handler"):
        self.logger = logging.getLogger(logger_name)
    
    def handle_exception(self, 
                        exception: Exception, 
                        context: Optional[Dict[str, Any]] = None) -> ErrorDetails:
        """Handle any exception and return error details."""
        
        if isinstance(exception, BaseAppException):
            error_details = exception.to_error_details()
        else:
            # Handle unexpected exceptions
            error_details = ErrorDetails(
                code=ErrorCode.INTERNAL_ERROR,
                message=str(exception),
                details={"exception_type": type(exception).__name__},
                traceback=traceback.format_exc()
            )
        
        # Add context if provided
        if context:
            if error_details.details is None:
                error_details.details = {}
            error_details.details.update(context)
        
        # Log the error
        self._log_error(error_details, context)
        
        return error_details
    
    def _log_error(self, error_details: ErrorDetails, context: Optional[Dict[str, Any]] = None):
        """Log error details."""
        log_data = {
            "error_code": error_details.code.value,
            "error_message": error_details.message,
        }
        
        if error_details.details:
            log_data.update(error_details.details)
        
        if context:
            log_data.update(context)
        
        # Log with appropriate level based on error type
        if error_details.code in [ErrorCode.VALIDATION_ERROR, ErrorCode.NOT_FOUND_ERROR]:
            self.logger.warning(f"Application error: {error_details.message}", extra=log_data)
        elif error_details.code in [ErrorCode.AUTHENTICATION_ERROR, ErrorCode.AUTHORIZATION_ERROR]:
            self.logger.warning(f"Security error: {error_details.message}", extra=log_data)
        else:
            self.logger.error(f"System error: {error_details.message}", extra=log_data)
            if error_details.traceback:
                self.logger.error(f"Traceback: {error_details.traceback}")


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_error(exception: Exception, 
                context: Optional[Dict[str, Any]] = None) -> ErrorDetails:
    """Convenience function to handle errors."""
    return global_error_handler.handle_exception(exception, context)