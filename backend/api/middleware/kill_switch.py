"""
Kill Switch Middleware
Implements emergency shutdown capability for production incidents
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Optional
import os
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Kill switch configuration file
KILL_SWITCH_FILE = os.getenv("KILL_SWITCH_FILE", "./config/kill_switch.json")


class KillSwitchConfig:
    """
    Kill switch configuration manager
    """
    
    def __init__(self, config_file: str = KILL_SWITCH_FILE):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_config()
    
    def _load_config(self):
        """Load kill switch configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.enabled = data.get("enabled", False)
                    self.message = data.get("message", "Service temporarily unavailable")
                    self.allowed_paths = data.get("allowed_paths", ["/health"])
                    self.enabled_at = data.get("enabled_at")
                    self.enabled_by = data.get("enabled_by")
            except Exception as e:
                logger.error(f"Failed to load kill switch config: {e}")
                self._set_defaults()
        else:
            self._set_defaults()
            self._save_config()
    
    def _set_defaults(self):
        """Set default configuration"""
        self.enabled = False
        self.message = "Service temporarily unavailable"
        self.allowed_paths = ["/health", "/"]
        self.enabled_at = None
        self.enabled_by = None
    
    def _save_config(self):
        """Save kill switch configuration to file"""
        try:
            data = {
                "enabled": self.enabled,
                "message": self.message,
                "allowed_paths": self.allowed_paths,
                "enabled_at": self.enabled_at,
                "enabled_by": self.enabled_by,
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save kill switch config: {e}")
    
    def enable(self, message: str = None, enabled_by: str = "system"):
        """
        Enable kill switch
        
        Args:
            message: Custom message to display
            enabled_by: Who enabled the kill switch
        """
        self.enabled = True
        if message:
            self.message = message
        self.enabled_at = datetime.utcnow().isoformat() + "Z"
        self.enabled_by = enabled_by
        self._save_config()
        
        logger.warning(
            f"Kill switch ENABLED by {enabled_by}",
            extra={
                "event": "kill_switch_enabled",
                "enabled_by": enabled_by,
                "message": self.message,
            }
        )
    
    def disable(self, disabled_by: str = "system"):
        """
        Disable kill switch
        
        Args:
            disabled_by: Who disabled the kill switch
        """
        self.enabled = False
        self._save_config()
        
        logger.info(
            f"Kill switch DISABLED by {disabled_by}",
            extra={
                "event": "kill_switch_disabled",
                "disabled_by": disabled_by,
            }
        )
    
    def is_enabled(self) -> bool:
        """Check if kill switch is enabled"""
        # Reload config to get latest state
        self._load_config()
        return self.enabled
    
    def is_path_allowed(self, path: str) -> bool:
        """Check if path is allowed when kill switch is enabled"""
        return path in self.allowed_paths


# Global kill switch instance
kill_switch = KillSwitchConfig()


async def kill_switch_middleware(request: Request, call_next: Callable) -> Response:
    """
    Kill switch middleware for FastAPI
    
    When enabled, blocks all requests except allowed paths (e.g., /health)
    Useful for emergency shutdowns during incidents
    
    Usage:
        app.middleware("http")(kill_switch_middleware)
    """
    # Check if kill switch feature is enabled
    if not os.getenv("ENABLE_KILL_SWITCH", "false").lower() == "true":
        return await call_next(request)
    
    # Check if kill switch is activated
    if kill_switch.is_enabled():
        # Allow certain paths even when kill switch is on
        if kill_switch.is_path_allowed(request.url.path):
            return await call_next(request)
        
        # Block all other requests
        logger.warning(
            f"Request blocked by kill switch: {request.method} {request.url.path}",
            extra={
                "event": "kill_switch_block",
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service Unavailable",
                "message": kill_switch.message,
                "enabled_at": kill_switch.enabled_at,
                "retry_after": 300,  # 5 minutes
            },
            headers={
                "Retry-After": "300",
                "X-Kill-Switch": "enabled",
            }
        )
    
    # Kill switch is off, proceed normally
    return await call_next(request)


# API endpoints for managing kill switch (should be protected by auth)
def create_kill_switch_routes(app):
    """
    Create API routes for managing kill switch
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/api/admin/kill-switch", tags=["Admin"])
    
    @router.get("/status")
    async def get_kill_switch_status():
        """Get current kill switch status"""
        return {
            "enabled": kill_switch.enabled,
            "message": kill_switch.message,
            "allowed_paths": kill_switch.allowed_paths,
            "enabled_at": kill_switch.enabled_at,
            "enabled_by": kill_switch.enabled_by,
        }
    
    @router.post("/enable")
    async def enable_kill_switch(
        message: Optional[str] = None,
        enabled_by: str = "admin"
    ):
        """Enable kill switch"""
        kill_switch.enable(message=message, enabled_by=enabled_by)
        return {
            "status": "enabled",
            "message": kill_switch.message,
            "enabled_at": kill_switch.enabled_at,
        }
    
    @router.post("/disable")
    async def disable_kill_switch(disabled_by: str = "admin"):
        """Disable kill switch"""
        kill_switch.disable(disabled_by=disabled_by)
        return {
            "status": "disabled",
        }
    
    app.include_router(router)


# CLI functions for emergency use
def enable_kill_switch_cli(message: str = None):
    """
    Enable kill switch from command line
    
    Usage:
        python -m backend.api.middleware.kill_switch enable "Emergency maintenance"
    """
    ks = KillSwitchConfig()
    ks.enable(message=message, enabled_by="cli")
    print(f"✓ Kill switch ENABLED")
    print(f"  Message: {ks.message}")
    print(f"  Enabled at: {ks.enabled_at}")


def disable_kill_switch_cli():
    """
    Disable kill switch from command line
    
    Usage:
        python -m backend.api.middleware.kill_switch disable
    """
    ks = KillSwitchConfig()
    ks.disable(disabled_by="cli")
    print(f"✓ Kill switch DISABLED")


def status_kill_switch_cli():
    """
    Check kill switch status from command line
    
    Usage:
        python -m backend.api.middleware.kill_switch status
    """
    ks = KillSwitchConfig()
    print(f"Kill Switch Status:")
    print(f"  Enabled: {ks.enabled}")
    print(f"  Message: {ks.message}")
    print(f"  Allowed paths: {', '.join(ks.allowed_paths)}")
    if ks.enabled_at:
        print(f"  Enabled at: {ks.enabled_at}")
        print(f"  Enabled by: {ks.enabled_by}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Kill Switch Management")
        print("\nUsage:")
        print("  python -m backend.api.middleware.kill_switch <command>")
        print("\nCommands:")
        print("  status                    - Check kill switch status")
        print("  enable [message]          - Enable kill switch")
        print("  disable                   - Disable kill switch")
        print("\nExamples:")
        print("  python -m backend.api.middleware.kill_switch status")
        print("  python -m backend.api.middleware.kill_switch enable 'Emergency maintenance'")
        print("  python -m backend.api.middleware.kill_switch disable")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        status_kill_switch_cli()
    elif command == "enable":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        enable_kill_switch_cli(message)
    elif command == "disable":
        disable_kill_switch_cli()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
