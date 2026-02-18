"""
Structured Logging Middleware
Implements JSON-formatted logging with request tracking and performance monitoring
"""

from fastapi import Request, Response
from typing import Callable
import logging
import json
import time
import uuid
import os
import sys
from datetime import datetime
from pathlib import Path

# Configure logging format
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()
LOG_FILE = os.getenv("LOG_FILE", "./logs/app.log")


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter
    """
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging():
    """
    Setup logging configuration
    """
    # Create logs directory if it doesn't exist
    log_file_path = Path(LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Set formatters
    if LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Initialize logging
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """
    Context manager for request logging
    """
    
    def __init__(self, request_id: str, endpoint: str, method: str):
        self.request_id = request_id
        self.endpoint = endpoint
        self.method = method
        self.start_time = None
        self.logger = get_logger("api.request")
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is None:
            self.log_success(duration_ms)
        else:
            self.log_error(duration_ms, exc_val)
    
    def log_success(self, duration_ms: float):
        """Log successful request"""
        extra = {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "duration_ms": round(duration_ms, 2),
            "status_code": 200,
        }
        self.logger.info(f"Request completed", extra=extra)
    
    def log_error(self, duration_ms: float, error: Exception):
        """Log failed request"""
        extra = {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "duration_ms": round(duration_ms, 2),
            "status_code": 500,
        }
        self.logger.error(f"Request failed: {str(error)}", extra=extra, exc_info=True)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Logging middleware for FastAPI
    
    Features:
    - Generates unique request ID
    - Logs all requests with timing
    - Tracks slow requests
    - Logs errors with context
    
    Usage:
        app.middleware("http")(logging_middleware)
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get user ID if authenticated
    user_id = getattr(request.state, "user", {}).get("user_id", "anonymous")
    
    # Start timing
    start_time = time.time()
    
    # Log request start
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "client_ip": client_ip,
            "user_id": user_id,
        }
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"Response {response.status_code}",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
                "user_id": user_id,
            }
        )
        
        # Log slow requests
        slow_request_threshold = 1000  # ms
        if duration_ms > slow_request_threshold:
            logger.warning(
                f"Slow request detected: {duration_ms:.2f}ms",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                }
            )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log error
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "method": request.method,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
                "user_id": user_id,
            },
            exc_info=True
        )
        
        # Re-raise exception
        raise


def log_security_event(event_type: str, details: dict, severity: str = "INFO"):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event (e.g., "login_attempt", "access_denied")
        details: Event details
        severity: Log level (INFO, WARNING, ERROR)
    """
    security_logger = get_logger("security")
    
    log_data = {
        "event_type": event_type,
        **details
    }
    
    if severity == "ERROR":
        security_logger.error(f"Security event: {event_type}", extra=log_data)
    elif severity == "WARNING":
        security_logger.warning(f"Security event: {event_type}", extra=log_data)
    else:
        security_logger.info(f"Security event: {event_type}", extra=log_data)


def log_audit_event(action: str, resource: str, user_id: str, details: dict = None):
    """
    Log audit trail events
    
    Args:
        action: Action performed (e.g., "create", "update", "delete", "read")
        resource: Resource affected (e.g., "customer", "prediction")
        user_id: User who performed the action
        details: Additional details
    """
    audit_logger = get_logger("audit")
    
    log_data = {
        "action": action,
        "resource": resource,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if details:
        log_data.update(details)
    
    audit_logger.info(f"Audit: {action} {resource}", extra=log_data)


def log_performance_metric(metric_name: str, value: float, tags: dict = None):
    """
    Log performance metrics
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        tags: Additional tags/labels
    """
    metrics_logger = get_logger("metrics")
    
    log_data = {
        "metric": metric_name,
        "value": value,
    }
    
    if tags:
        log_data.update(tags)
    
    metrics_logger.info(f"Metric: {metric_name}={value}", extra=log_data)


if __name__ == "__main__":
    print("Structured Logging Middleware")
    print("\nFeatures:")
    print("  - JSON or text formatted logs")
    print("  - Request ID tracking")
    print("  - Performance monitoring")
    print("  - Slow request detection")
    print("  - Security event logging")
    print("  - Audit trail logging")
    print("\nUsage:")
    print("  app.middleware('http')(logging_middleware)")
    print("  logger = get_logger(__name__)")
    print("  log_security_event('login_attempt', {...})")
    print("  log_audit_event('update', 'customer', user_id)")
