"""
FastAPI application entry point for ZK-Communist Time Liberation Server.
Disguised as network monitoring service for stealth operations.
"""

import os
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.api.v1 import system, emergency, device, config
from src.core.config_manager import ConfigurationManager
from src.utils.logging import setup_stealth_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events."""
    # Startup
    print("🚀 Initializing Network Monitoring Service")

    # Check if running in Kubernetes environment
    k8s_env = os.getenv('KUBERNETES_ENVIRONMENT', 'false')
    if k8s_env == 'true':
        print("🔥 Kubernetes environment detected")
        print("📡 FastAPI running on port 8012")

    # Initialize configuration manager
    config_manager = ConfigurationManager()
    await config_manager.initialize()

    # Setup stealth logging
    setup_stealth_logging()

    # Check operation mode
    operation_mode = os.getenv('OPERATION_MODE', 'standalone')
    if operation_mode == 'activate':
        print("🚀 CronJob activation mode")
    else:
        print("🔄 Standalone mode - using internal scheduling")

    yield

    # Shutdown
    print("🛑 Network Monitoring Service shutting down")


# FastAPI app with stealth configuration
app = FastAPI(
    title="Network Monitoring Service",
    description="Internal network monitoring and diagnostics",
    version="1.0.0",
    docs_url=None,  # Disable OpenAPI docs for stealth
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

# Include API routers
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(emergency.router, prefix="/api/v1/emergency", tags=["emergency"])
app.include_router(device.router, prefix="/api/v1/device", tags=["device"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])


@app.get("/")
async def root():
    """Root endpoint - returns stealth service description."""
    return {
        "service": "Network Monitoring Service",
        "status": "operational",
        "description": "Internal network diagnostics and monitoring"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8012,
        reload=False,  # Disable reload in production for stealth
        log_level="warning"  # Minimal logging for stealth
    )