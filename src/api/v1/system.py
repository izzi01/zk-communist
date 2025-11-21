"""
System endpoints for health checks and monitoring.
Provides Kubernetes probe endpoints for service health monitoring.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str  # "healthy" | "unhealthy"
    timestamp: datetime
    version: str
    uptime_seconds: int


class ReadyResponse(BaseModel):
    """Readiness check response model."""
    ready: bool
    timestamp: datetime
    service: str


# Global service start time (simplified for infrastructure setup)
SERVICE_START_TIME = datetime.now()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Liveness probe endpoint for Kubernetes.
    Returns service health status for container orchestration.
    """
    uptime = int((datetime.now() - SERVICE_START_TIME).total_seconds())

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        uptime_seconds=uptime
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """
    Readiness probe endpoint for Kubernetes.
    Indicates if service is ready to accept traffic.
    """
    # In a real implementation, this would check:
    # - Database connectivity
    # - Device connection status
    # - Configuration loading
    # - Required services availability

    return ReadyResponse(
        ready=True,
        timestamp=datetime.now(),
        service="network-monitoring"
    )


@router.get("/status")
async def system_status():
    """
    System status endpoint for monitoring.
    Returns detailed system information for operations.
    """
    return {
        "service": "Network Monitoring Service",
        "status": "operational",
        "uptime_seconds": int((datetime.now() - SERVICE_START_TIME).total_seconds()),
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/api/v1/system/health",
            "ready": "/api/v1/system/ready"
        }
    }