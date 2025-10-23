import asyncio
import traceback
from typing import Any, Dict, Optional, Callable
from functools import wraps
import logging
from datetime import datetime

from backend.pipeline.utils.logger import log_error, log_system_event

logger = logging.getLogger(__name__)

class RAGError(Exception):
    """Base exception for RAG system errors"""
    def __init__(self, message: str, error_code: str = "RAG_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(RAGError):
    """Database-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

class EmbeddingError(RAGError):
    """Embedding-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBEDDING_ERROR", details)

class RetrievalError(RAGError):
    """Retrieval-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RETRIEVAL_ERROR", details)

class GenerationError(RAGError):
    """Text generation-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "GENERATION_ERROR", details)

class DocumentError(RAGError):
    """Document processing errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_ERROR", details)

class ValidationError(RAGError):
    """Input validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

def handle_errors(
    error_type: type = RAGError,
    return_value: Any = None,
    log_error: bool = True,
    reraise: bool = False
):
    """Decorator for error handling"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except error_type as e:
                if log_error:
                    log_error(e, {
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    })
                
                if reraise:
                    raise
                return return_value
            except Exception as e:
                if log_error:
                    log_error(e, {
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    })
                
                if reraise:
                    raise
                return return_value
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if log_error:
                    log_error(e, {
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    })
                
                if reraise:
                    raise
                return return_value
            except Exception as e:
                if log_error:
                    log_error(e, {
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    })
                
                if reraise:
                    raise
                return return_value
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

class ErrorHandler:
    """Centralized error handling for the RAG system"""
    
    @staticmethod
    def handle_database_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database-related errors"""
        log_error(error, context)
        
        if "connection" in str(error).lower():
            return {
                "error": "Database connection failed",
                "error_code": "DB_CONNECTION_ERROR",
                "message": "Unable to connect to the database. Please try again later.",
                "retry_after": 30
            }
        elif "timeout" in str(error).lower():
            return {
                "error": "Database operation timeout",
                "error_code": "DB_TIMEOUT_ERROR",
                "message": "Database operation took too long. Please try again.",
                "retry_after": 10
            }
        else:
            return {
                "error": "Database error",
                "error_code": "DB_ERROR",
                "message": "A database error occurred. Please try again later.",
                "retry_after": 5
            }
    
    @staticmethod
    def handle_embedding_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle embedding-related errors"""
        log_error(error, context)
        
        if "model" in str(error).lower():
            return {
                "error": "Embedding model error",
                "error_code": "EMBEDDING_MODEL_ERROR",
                "message": "Embedding model is not available. Please try again later.",
                "retry_after": 60
            }
        elif "memory" in str(error).lower():
            return {
                "error": "Insufficient memory for embeddings",
                "error_code": "EMBEDDING_MEMORY_ERROR",
                "message": "Not enough memory to process embeddings. Please try with smaller text.",
                "retry_after": 30
            }
        else:
            return {
                "error": "Embedding processing error",
                "error_code": "EMBEDDING_ERROR",
                "message": "Failed to create embeddings. Please try again.",
                "retry_after": 10
            }
    
    @staticmethod
    def handle_retrieval_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle retrieval-related errors"""
        log_error(error, context)
        
        if "vector" in str(error).lower():
            return {
                "error": "Vector search error",
                "error_code": "VECTOR_SEARCH_ERROR",
                "message": "Vector similarity search failed. Please try again.",
                "retry_after": 5
            }
        elif "index" in str(error).lower():
            return {
                "error": "Vector index error",
                "error_code": "VECTOR_INDEX_ERROR",
                "message": "Vector index is not available. Please try again later.",
                "retry_after": 30
            }
        else:
            return {
                "error": "Retrieval error",
                "error_code": "RETRIEVAL_ERROR",
                "message": "Failed to retrieve relevant documents. Please try again.",
                "retry_after": 5
            }
    
    @staticmethod
    def handle_generation_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text generation errors"""
        log_error(error, context)
        
        if "model" in str(error).lower():
            return {
                "error": "Language model error",
                "error_code": "LLM_MODEL_ERROR",
                "message": "Language model is not available. Please try again later.",
                "retry_after": 60
            }
        elif "token" in str(error).lower():
            return {
                "error": "Token limit exceeded",
                "error_code": "TOKEN_LIMIT_ERROR",
                "message": "Input is too long. Please try with a shorter query.",
                "retry_after": 0
            }
        else:
            return {
                "error": "Text generation error",
                "error_code": "GENERATION_ERROR",
                "message": "Failed to generate response. Please try again.",
                "retry_after": 10
            }
    
    @staticmethod
    def handle_document_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document processing errors"""
        log_error(error, context)
        
        if "format" in str(error).lower():
            return {
                "error": "Unsupported document format",
                "error_code": "DOCUMENT_FORMAT_ERROR",
                "message": "The document format is not supported. Please use PDF, text, or URL.",
                "retry_after": 0
            }
        elif "size" in str(error).lower():
            return {
                "error": "Document too large",
                "error_code": "DOCUMENT_SIZE_ERROR",
                "message": "The document is too large to process. Please use a smaller document.",
                "retry_after": 0
            }
        else:
            return {
                "error": "Document processing error",
                "error_code": "DOCUMENT_ERROR",
                "message": "Failed to process document. Please try again.",
                "retry_after": 5
            }
    
    @staticmethod
    def handle_validation_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle input validation errors"""
        log_error(error, context)
        
        return {
            "error": "Input validation error",
            "error_code": "VALIDATION_ERROR",
            "message": str(error),
            "retry_after": 0
        }
    
    @staticmethod
    def get_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get appropriate error response based on error type"""
        error_type = type(error).__name__
        
        if "Database" in error_type or "Connection" in error_type:
            return ErrorHandler.handle_database_error(error, context)
        elif "Embedding" in error_type:
            return ErrorHandler.handle_embedding_error(error, context)
        elif "Retrieval" in error_type:
            return ErrorHandler.handle_retrieval_error(error, context)
        elif "Generation" in error_type:
            return ErrorHandler.handle_generation_error(error, context)
        elif "Document" in error_type:
            return ErrorHandler.handle_document_error(error, context)
        elif "Validation" in error_type:
            return ErrorHandler.handle_validation_error(error, context)
        else:
            # Generic error handling
            log_error(error, context)
            return {
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "retry_after": 10
            }

# Global error handler instance
error_handler = ErrorHandler()

# Convenience functions
def handle_database_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return error_handler.handle_database_error(error, context)

def handle_embedding_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return error_handler.handle_embedding_error(error, context)

def handle_retrieval_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return error_handler.handle_retrieval_error(error, context)

def handle_generation_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return error_handler.handle_generation_error(error, context)

def handle_document_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return error_handler.handle_document_error(error, context)

def get_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return error_handler.get_error_response(error, context)
