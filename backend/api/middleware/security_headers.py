"""
Security Headers Middleware
Implements security best practices through HTTP headers
"""

from fastapi import Request, Response
from typing import Callable
import os


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """
    Add security headers to all responses
    
    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    
    Usage:
        app.middleware("http")(security_headers_middleware)
    """
    response = await call_next(request)
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Enable XSS protection (legacy, but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Enforce HTTPS (only in production)
    if os.getenv("ENVIRONMENT", "development") == "production":
        # HSTS: Force HTTPS for 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    
    # Content Security Policy
    # Adjust based on your needs
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust for your needs
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy (formerly Feature-Policy)
    permissions_directives = [
        "geolocation=()",
        "microphone=()",
        "camera=()",
        "payment=()",
        "usb=()",
        "magnetometer=()",
        "gyroscope=()",
        "accelerometer=()",
    ]
    response.headers["Permissions-Policy"] = ", ".join(permissions_directives)
    
    # Remove server header (don't reveal server technology)
    if "Server" in response.headers:
        del response.headers["Server"]
    
    # Add custom security header
    response.headers["X-API-Version"] = os.getenv("APP_VERSION", "1.0.0")
    
    return response


if __name__ == "__main__":
    print("Security Headers Middleware")
    print("\nHeaders added:")
    print("  - X-Content-Type-Options: nosniff")
    print("  - X-Frame-Options: DENY")
    print("  - X-XSS-Protection: 1; mode=block")
    print("  - Strict-Transport-Security (production only)")
    print("  - Content-Security-Policy")
    print("  - Referrer-Policy")
    print("  - Permissions-Policy")
    print("\nUsage:")
    print("  app.middleware('http')(security_headers_middleware)")
