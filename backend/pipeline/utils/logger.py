import logging
import structlog
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json
import traceback

class StructuredLogger:
    """Enhanced structured logger for the RAG system"""
    
    def __init__(self, name: str = "afyamama_rag"):
        self.logger = structlog.get_logger(name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging configuration"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def log_api_request(
        self, 
        method: str, 
        endpoint: str, 
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log API request"""
        self.logger.info(
            "API request",
            method=method,
            endpoint=endpoint,
            user_id=user_id,
            **kwargs
        )
    
    def log_api_response(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log API response"""
        self.logger.info(
            "API response",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time * 1000,
            user_id=user_id,
            **kwargs
        )
    
    def log_rag_query(
        self,
        query: str,
        answer: str,
        retrieval_score: float,
        chunks_used: int,
        interaction_id: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log RAG query processing"""
        self.logger.info(
            "RAG query processed",
            query=query[:100] + "..." if len(query) > 100 else query,
            answer_length=len(answer),
            retrieval_score=retrieval_score,
            chunks_used=chunks_used,
            interaction_id=interaction_id,
            user_id=user_id,
            **kwargs
        )
    
    def log_document_ingestion(
        self,
        document_id: str,
        title: str,
        source_type: str,
        chunks_created: int,
        processing_time: float,
        **kwargs
    ):
        """Log document ingestion"""
        self.logger.info(
            "Document ingested",
            document_id=document_id,
            title=title,
            source_type=source_type,
            chunks_created=chunks_created,
            processing_time_ms=processing_time * 1000,
            **kwargs
        )
    
    def log_embedding_creation(
        self,
        text_length: int,
        embedding_dim: int,
        processing_time: float,
        **kwargs
    ):
        """Log embedding creation"""
        self.logger.info(
            "Embedding created",
            text_length=text_length,
            embedding_dim=embedding_dim,
            processing_time_ms=processing_time * 1000,
            **kwargs
        )
    
    def log_vector_search(
        self,
        query_length: int,
        results_count: int,
        search_time: float,
        similarity_threshold: float,
        **kwargs
    ):
        """Log vector search operation"""
        self.logger.info(
            "Vector search performed",
            query_length=query_length,
            results_count=results_count,
            search_time_ms=search_time * 1000,
            similarity_threshold=similarity_threshold,
            **kwargs
        )
    
    def log_database_operation(
        self,
        operation: str,
        table: str,
        record_count: int,
        execution_time: float,
        **kwargs
    ):
        """Log database operations"""
        self.logger.info(
            "Database operation",
            operation=operation,
            table=table,
            record_count=record_count,
            execution_time_ms=execution_time * 1000,
            **kwargs
        )
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log errors with full context"""
        self.logger.error(
            "Error occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            error_traceback=traceback.format_exc(),
            context=context,
            user_id=user_id,
            **kwargs
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        **kwargs
    ):
        """Log performance metrics"""
        self.logger.info(
            "Performance metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )
    
    def log_system_event(
        self,
        event: str,
        details: Dict[str, Any],
        **kwargs
    ):
        """Log system events"""
        self.logger.info(
            "System event",
            event=event,
            details=details,
            **kwargs
        )

# Global logger instance
logger = StructuredLogger()

# Convenience functions
def log_api_request(method: str, endpoint: str, **kwargs):
    logger.log_api_request(method, endpoint, **kwargs)

def log_api_response(method: str, endpoint: str, status_code: int, response_time: float, **kwargs):
    logger.log_api_response(method, endpoint, status_code, response_time, **kwargs)

def log_rag_query(query: str, answer: str, retrieval_score: float, chunks_used: int, interaction_id: str, **kwargs):
    logger.log_rag_query(query, answer, retrieval_score, chunks_used, interaction_id, **kwargs)

def log_document_ingestion(document_id: str, title: str, source_type: str, chunks_created: int, processing_time: float, **kwargs):
    logger.log_document_ingestion(document_id, title, source_type, chunks_created, processing_time, **kwargs)

def log_error(error: Exception, context: Dict[str, Any], **kwargs):
    logger.log_error(error, context, **kwargs)

def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **kwargs):
    logger.log_performance_metric(metric_name, value, unit, **kwargs)

def log_system_event(event: str, details: Dict[str, Any], **kwargs):
    logger.log_system_event(event, details, **kwargs)
