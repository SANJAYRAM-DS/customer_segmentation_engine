from dotenv import load_dotenv
import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
# Global Exception Handler — returns JSON instead of plain-text 500
# ----------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "path": str(request.url.path),
        }
    )

# ----------------------
# CORS Middleware (PRODUCTION-READY)
# ----------------------
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,
)

# ----------------------
# Rate Limiting Middleware (disabled — uncomment to re-enable)
# ----------------------
# from backend.api.middleware.rate_limiter import rate_limit_middleware
# app.middleware("http")(rate_limit_middleware)

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

# ----------------------
# Debug Endpoint — exposes data loading status to diagnose Render 500s
# ----------------------
@app.get("/debug")
def debug_info():
    from pathlib import Path
    from backend.caching.loader import loader, OUTPUTS_DIR, SNAPSHOTS_DIR

    output_dirs = [d.name for d in OUTPUTS_DIR.glob("snapshot_date=*")] if OUTPUTS_DIR.exists() else []
    snapshot_dirs = [d.name for d in SNAPSHOTS_DIR.glob("snapshot_date=*")] if SNAPSHOTS_DIR.exists() else []

    snapshot_status = "not_loaded"
    snapshot_cols = []
    snapshot_rows = 0
    error_msg = None
    try:
        df = loader.get_customer_snapshot()
        snapshot_rows = len(df)
        snapshot_cols = list(df.columns[:15])
        snapshot_status = "ok" if not df.empty else "empty"
    except Exception as e:
        snapshot_status = "error"
        error_msg = f"{type(e).__name__}: {str(e)}"

    return {
        "python_version": sys.version,
        "outputs_dir": str(OUTPUTS_DIR),
        "outputs_dir_exists": OUTPUTS_DIR.exists(),
        "snapshots_dir": str(SNAPSHOTS_DIR),
        "snapshots_dir_exists": SNAPSHOTS_DIR.exists(),
        "output_dirs": output_dirs,
        "snapshot_dirs": snapshot_dirs,
        "loader_latest_date": loader._latest_snapshot_date,
        "snapshot_status": snapshot_status,
        "snapshot_rows": snapshot_rows,
        "snapshot_cols_sample": snapshot_cols,
        "error": error_msg,
    }
