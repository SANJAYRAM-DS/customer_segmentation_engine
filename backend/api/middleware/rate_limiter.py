"""
Rate Limiting Middleware
Implements API rate limiting to prevent abuse and ensure fair usage
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional
from datetime import datetime, timedelta
import time
from collections import defaultdict
import asyncio


class RateLimiter:
    """
    Token bucket rate limiter
    
    Implements rate limiting using token bucket algorithm:
    - Each client gets a bucket of tokens
    - Tokens refill at a constant rate
    - Each request consumes a token
    - Requests are rejected when bucket is empty
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 50,  # Increased from 10 to allow multiple simultaneous requests
    ):
        """
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            burst_size: Max burst requests
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        # Storage for rate limit tracking
        self.minute_buckets: Dict[str, list] = defaultdict(list)
        self.hour_buckets: Dict[str, list] = defaultdict(list)
        # Initialize burst buckets with lambda to start with full capacity
        self.burst_buckets: Dict[str, int] = defaultdict(lambda: self.burst_size)
        self.last_refill: Dict[str, float] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request
        
        Priority:
        1. API key (if authenticated)
        2. User ID (if logged in)
        3. IP address (fallback)
        """
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Check for user ID (from auth)
        user_id = request.state.__dict__.get("user_id")
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    def _refill_burst_tokens(self, client_id: str):
        """Refill burst tokens based on time elapsed"""
        now = time.time()
        last_refill = self.last_refill.get(client_id, now)
        
        # Refill rate: 1 token per second
        elapsed = now - last_refill
        tokens_to_add = int(elapsed)
        
        if tokens_to_add > 0:
            self.burst_buckets[client_id] = min(
                self.burst_size,
                self.burst_buckets[client_id] + tokens_to_add
            )
            self.last_refill[client_id] = now
    
    def _clean_old_requests(self, bucket: list, window_seconds: int):
        """Remove requests older than window"""
        cutoff = time.time() - window_seconds
        return [ts for ts in bucket if ts > cutoff]
    
    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        Check if request should be rate limited
        
        Returns:
            None if allowed, JSONResponse if rate limited
        """
        client_id = self._get_client_id(request)
        now = time.time()
        
        # Clean old requests
        self.minute_buckets[client_id] = self._clean_old_requests(
            self.minute_buckets[client_id], 60
        )
        self.hour_buckets[client_id] = self._clean_old_requests(
            self.hour_buckets[client_id], 3600
        )
        
        # Check burst limit (token bucket)
        self._refill_burst_tokens(client_id)
        if self.burst_buckets[client_id] <= 0:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests in quick succession",
                    "retry_after": 1,
                },
                headers={"Retry-After": "1"}
            )
        
        # Check minute limit
        if len(self.minute_buckets[client_id]) >= self.requests_per_minute:
            oldest = self.minute_buckets[client_id][0]
            retry_after = int(60 - (now - oldest)) + 1
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Check hour limit
        if len(self.hour_buckets[client_id]) >= self.requests_per_hour:
            oldest = self.hour_buckets[client_id][0]
            retry_after = int(3600 - (now - oldest)) + 1
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_hour} requests per hour",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Allow request - consume token and record
        self.burst_buckets[client_id] -= 1
        self.minute_buckets[client_id].append(now)
        self.hour_buckets[client_id].append(now)
        
        # Add rate limit headers
        request.state.rate_limit_remaining = self.requests_per_minute - len(self.minute_buckets[client_id])
        request.state.rate_limit_reset = int(now + 60)
        
        return None


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=300,  # Increased from 60 to 300 for faster loading
    requests_per_hour=5000,   # Increased from 1000 to 5000
    burst_size=100,           # Increased from 50 to 100 for multiple simultaneous requests
)


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI
    
    Usage:
        app.middleware("http")(rate_limit_middleware)
    """
    # Skip rate limiting for health checks and frequently accessed endpoints
    if request.url.path in ["/health", "/api/health/", "/api/overview/", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Check rate limit
    rate_limit_response = await rate_limiter.check_rate_limit(request)
    
    if rate_limit_response:
        return rate_limit_response
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    if hasattr(request.state, "rate_limit_remaining"):
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
    
    return response


# Decorator for specific endpoints
def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
):
    """
    Decorator for rate limiting specific endpoints
    
    Usage:
        @app.get("/expensive-endpoint")
        @rate_limit(requests_per_minute=10)
        async def expensive_endpoint():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
            )
            
            rate_limit_response = await limiter.check_rate_limit(request)
            if rate_limit_response:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    print("Rate Limiting Middleware")
    print("\nFeatures:")
    print("  - Token bucket algorithm")
    print("  - Per-minute and per-hour limits")
    print("  - Burst protection")
    print("  - Client identification (API key, user, IP)")
    print("  - Rate limit headers")
    print("\nUsage:")
    print("  app.middleware('http')(rate_limit_middleware)")
