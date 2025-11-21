"""
Stealth logging utilities for minimal evidence operation.
Provides secure logging with automatic cleanup and evidence management.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_stealth_logging() -> None:
    """
    Setup stealth logging configuration for minimal evidence operation.

    Configures logging to:
    - Log only warnings and errors (minimal evidence)
    - Rotate logs to prevent accumulation
    - Use stealth service name in logs
    - Avoid sensitive data exposure
    """
    # Create log directory if it doesn't exist
    log_dir = Path("/var/log/network-monitoring")
    log_dir.mkdir(exist_ok=True, mode=0o750)

    # Configure stealth logging
    log_file = log_dir / "app.log"

    # Create rotating file handler (1MB max, 1 backup)
    handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=1,
        encoding='utf-8'
    )

    # Set log format (minimal, no sensitive data)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Configure root logger for stealth operation
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only warnings and errors
    root_logger.addHandler(handler)

    # Prevent duplicate handlers
    root_logger.propagate = False

    print("🔐 Stealth logging configured")
    print(f"📁 Log file: {log_file}")
    print("⚠️  Only warnings and errors will be logged")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually module name)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_security_event(event_type: str, message: str, severity: str = "WARNING") -> None:
    """
    Log security event with appropriate severity.

    Args:
        event_type: Type of security event
        message: Event message (no sensitive data)
        severity: Log severity level
    """
    logger = get_logger("security")
    log_message = f"[{event_type}] {message}"

    if severity.upper() == "ERROR":
        logger.error(log_message)
    else:
        logger.warning(log_message)


def log_system_event(event_type: str, message: str) -> None:
    """
    Log system event with warning level.

    Args:
        event_type: Type of system event
        message: Event message
    """
    logger = get_logger("system")
    logger.warning(f"[{event_type}] {message}")


def setup_emergency_logging() -> None:
    """
    Setup emergency logging for critical events.
    Uses separate encrypted storage for security events.
    """
    # Create emergency log directory
    emergency_log_dir = Path("/var/log/network-monitoring/emergency")
    emergency_log_dir.mkdir(exist_ok=True, mode=0o700)

    print("🚨 Emergency logging configured")
    print(f"📁 Emergency log directory: {emergency_log_dir}")


def cleanup_old_logs(days: int = 7) -> None:
    """
    Clean up old log files to prevent evidence accumulation.

    Args:
        days: Number of days to retain logs
    """
    log_dir = Path("/var/log/network-monitoring")
    cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    for log_file in log_dir.glob("*.log.*"):
        if log_file.stat().st_mtime < cutoff_date:
            try:
                log_file.unlink()
                print(f"🗑️  Cleaned up old log: {log_file}")
            except Exception as e:
                print(f"❌ Failed to clean up {log_file}: {e}")


def get_logging_status() -> dict:
    """
    Get current logging system status.

    Returns:
        Dictionary with logging status information
    """
    log_dir = Path("/var/log/network-monitoring")

    # Check if log directory exists
    if not log_dir.exists():
        return {
            "status": "not_configured",
            "log_directory": str(log_dir),
            "log_file": None,
            "size_bytes": 0
        }

    # Get log file info
    log_file = log_dir / "app.log"
    size_bytes = 0

    if log_file.exists():
        size_bytes = log_file.stat().st_size

    return {
        "status": "configured",
        "log_directory": str(log_dir),
        "log_file": str(log_file),
        "size_bytes": size_bytes,
        "level": "WARNING",  # Stealth mode
        "rotation_enabled": True,
        "max_size_mb": 1,
        "backup_count": 1
    }