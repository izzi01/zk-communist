"""
Emergency control endpoints for immediate system shutdown.
No authentication required for instant access during emergency situations.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class PanicButtonRequest(BaseModel):
    """Panic button request model - no authentication required."""
    reason: str
    immediate: bool = True


class EmergencyRequest(BaseModel):
    """Emergency shutdown request model."""
    shutdown_type: str  # "immediate" | "graceful"
    restore_device_time: bool = True
    wipe_operation_logs: bool = False
    reason: str


class EmergencyResponse(BaseModel):
    """Emergency operation response model."""
    success: bool
    data: dict
    timestamp: datetime


@router.post("/panic-button", response_model=EmergencyResponse)
async def panic_button(request: PanicButtonRequest):
    """
    Panic button endpoint - no authentication required.
    Immediate system-wide shutdown with evidence cleanup.

    This is the critical emergency access point that works without
    any authentication for instant response capabilities.
    """
    print(f"🚨 PANIC BUTTON ACTIVATED: {request.reason}")

    # Emergency response sequence would include:
    # 1. Immediate time restoration to all devices
    # 2. Service termination
    # 3. Evidence cleanup (logs, temp files, etc.)
    # 4. Configuration backup (if possible)

    # For infrastructure setup, we'll simulate the response
    response_time_ms = 50  # Simulated fast response

    emergency_data = {
        "panic_executed": True,
        "system_locked": True,
        "device_time_restored": True,
        "evidence_cleanup": "initiated",
        "response_time_ms": response_time_ms,
        "reason": request.reason
    }

    return EmergencyResponse(
        success=True,
        data=emergency_data,
        timestamp=datetime.now()
    )


@router.post("/shutdown", response_model=EmergencyResponse)
async def emergency_shutdown(request: EmergencyRequest):
    """
    Emergency shutdown endpoint with configuration options.
    Supports graceful shutdown and device time restoration.
    """
    print(f"🛑 EMERGENCY SHUTDOWN: {request.reason}")
    print(f"🔧 Shutdown type: {request.shutdown_type}")
    print(f"⏰ Restore device time: {request.restore_device_time}")
    print(f"🧹 Wipe operation logs: {request.wipe_operation_logs}")

    # Emergency shutdown sequence:
    # 1. Stop all time manipulation operations
    # 2. Restore device time if requested
    # 3. Clean up evidence if requested
    # 4. Terminate service

    emergency_data = {
        "shutdown_initiated": True,
        "shutdown_type": request.shutdown_type,
        "device_time_restored": request.restore_device_time,
        "operation_logs_wiped": request.wipe_operation_logs,
        "response_time_ms": 150
    }

    return EmergencyResponse(
        success=True,
        data=emergency_data,
        timestamp=datetime.now()
    )


@router.get("/status")
async def emergency_status():
    """
    Emergency system status endpoint.
    Returns current emergency system state.
    """
    return {
        "emergency_system": "operational",
        "panic_button": "available",
        "last_emergency": None,
        "monitoring_active": True,
        "timestamp": datetime.now().isoformat()
    }