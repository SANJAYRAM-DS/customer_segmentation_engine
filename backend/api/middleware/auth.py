"""
Authentication and Authorization Middleware
Implements JWT-based authentication and role-based access control
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security scheme
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[dict]:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User data from token payload
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # If authentication is disabled, return None
    if not os.getenv("ENABLE_AUTHENTICATION", "false").lower() == "true":
        return None
    
    if credentials is None:
        raise AuthenticationError("Missing authentication token")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    # Extract user information from payload
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")
    
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
    }


def require_auth(func):
    """
    Decorator to require authentication for an endpoint
    
    Usage:
        @app.get("/protected")
        @require_auth
        async def protected_endpoint(request: Request):
            user = request.state.user
            return {"user": user}
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Check if authentication is enabled
        if not os.getenv("ENABLE_AUTHENTICATION", "false").lower() == "true":
            request.state.user = None
            return await func(request, *args, **kwargs)
        
        # Get credentials from request
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        user = decode_token(token)
        
        # Attach user to request state
        request.state.user = user
        
        return await func(request, *args, **kwargs)
    
    return wrapper


def require_roles(required_roles: List[str]):
    """
    Decorator to require specific roles for an endpoint
    
    Args:
        required_roles: List of required role names
        
    Usage:
        @app.get("/admin")
        @require_roles(["admin"])
        async def admin_endpoint(request: Request):
            return {"message": "Admin access granted"}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Check if authentication is enabled
            if not os.getenv("ENABLE_AUTHENTICATION", "false").lower() == "true":
                return await func(request, *args, **kwargs)
            
            # Get user from request state (should be set by require_auth)
            user = getattr(request.state, "user", None)
            if user is None:
                raise AuthenticationError("User not authenticated")
            
            # Check roles
            user_roles = user.get("roles", [])
            if not any(role in user_roles for role in required_roles):
                raise AuthorizationError(
                    f"Required roles: {', '.join(required_roles)}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permissions(required_permissions: List[str]):
    """
    Decorator to require specific permissions for an endpoint
    
    Args:
        required_permissions: List of required permission names
        
    Usage:
        @app.get("/customers")
        @require_permissions(["read:customers"])
        async def get_customers(request: Request):
            return {"customers": []}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Check if authentication is enabled
            if not os.getenv("ENABLE_AUTHENTICATION", "false").lower() == "true":
                return await func(request, *args, **kwargs)
            
            # Get user from request state
            user = getattr(request.state, "user", None)
            if user is None:
                raise AuthenticationError("User not authenticated")
            
            # Check permissions
            user_permissions = user.get("permissions", [])
            if not all(perm in user_permissions for perm in required_permissions):
                raise AuthorizationError(
                    f"Required permissions: {', '.join(required_permissions)}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


async def auth_middleware(request: Request, call_next):
    """
    Authentication middleware for FastAPI
    
    Automatically extracts and validates JWT tokens from requests
    Attaches user information to request.state
    
    Usage:
        app.middleware("http")(auth_middleware)
    """
    # Skip authentication for public endpoints
    public_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    if request.url.path in public_paths:
        return await call_next(request)
    
    # Check if authentication is enabled
    if not os.getenv("ENABLE_AUTHENTICATION", "false").lower() == "true":
        request.state.user = None
        return await call_next(request)
    
    # Try to extract and validate token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            user = decode_token(token)
            request.state.user = user
        except AuthenticationError:
            # Token is invalid, but don't block request
            # Let endpoint decorators handle authentication
            request.state.user = None
    else:
        request.state.user = None
    
    response = await call_next(request)
    return response


# API Key Authentication (simpler alternative to JWT)
def verify_api_key(api_key: str) -> bool:
    """
    Verify API key against environment variable
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        return False
    
    return api_key == expected_key


async def api_key_auth(request: Request) -> bool:
    """
    Check for valid API key in request headers
    
    Usage:
        @app.get("/api/data")
        async def get_data(request: Request):
            if not await api_key_auth(request):
                raise HTTPException(401, "Invalid API key")
            return {"data": []}
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return False
    
    return verify_api_key(api_key)


if __name__ == "__main__":
    print("Authentication Middleware")
    print("\nFeatures:")
    print("  - JWT-based authentication")
    print("  - Role-based access control (RBAC)")
    print("  - Permission-based access control")
    print("  - API key authentication")
    print("  - Configurable via environment variables")
    print("\nUsage:")
    print("  app.middleware('http')(auth_middleware)")
    print("  @require_auth")
    print("  @require_roles(['admin'])")
    print("  @require_permissions(['read:customers'])")
