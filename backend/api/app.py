from dotenv import load_dotenv
import os
from fastapi import FastAPI

# Load environment variables from .env
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import (
    overview,
    segments,
    risk,
    value,
    health,
    customers,
    alerts,
    export
)

# Initialize FastAPI app
app = FastAPI(title="Customer Intelligence API", version="1.0")

# ----------------------
# CORS Middleware (PRODUCTION-READY)
# ----------------------
# Get allowed origins from environment variable
# Default to localhost for development
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Restricted origins from environment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ----------------------
# Rate Limiting Middleware
# ----------------------
from backend.api.middleware.rate_limiter import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)

# ----------------------
# API Routes
# ----------------------
app.include_router(overview.router, prefix="/api/overview", tags=["Overview"])
app.include_router(segments.router, prefix="/api/segments", tags=["Segmentation"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk"])
app.include_router(value.router, prefix="/api/value", tags=["Value"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])

# ----------------------
# Root Route
# ----------------------
@app.get("/")
def root():
    return {"message": "Customer Intelligence API is running!"}

# ----------------------
# Health Check
# ----------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}
