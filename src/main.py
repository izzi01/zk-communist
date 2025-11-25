"""
Main entry point for ZK-Communist Time Liberation Server.

This module provides the main application startup and initialization
logic for the time manipulation service.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from src.services.device_manager import DeviceManager


def setup_logging() -> None:
    """Configure structured JSON logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


@asynccontextmanager
async def application_lifecycle():
    """Application lifecycle manager."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(
        "Starting ZK-Communist Time Liberation Server",
        extra={
            "version": "1.0.0",
            "mode": "production",
        },
    )

    try:
        yield
    finally:
        logger.info("Shutting down ZK-Communist Time Liberation Server")


async def main() -> None:
    """Main application entry point."""
    async with application_lifecycle():
        logger = logging.getLogger(__name__)

        # Get device configuration from environment
        device_ip = os.getenv("DEVICE_IP")
        device_port = int(os.getenv("DEVICE_PORT", "4370"))
        device_password = os.getenv("DEVICE_PASSWORD", "")

        if not device_ip:
            logger.error("DEVICE_IP environment variable is required")
            sys.exit(1)

        # Device credentials
        credentials = {"password": device_password}

        # Create device manager
        device_manager = DeviceManager()

        try:
            # Connect to device
            logger.info(
                "Initializing device connection",
                extra={
                    "device_ip": device_ip,
                    "device_port": device_port,
                },
            )

            success = await device_manager.connect(device_ip, device_port, credentials)

            if success:
                logger.info(
                    "Device connection established successfully",
                    extra={
                        "device_ip": device_ip,
                        "device_port": device_port,
                    },
                )

                # Test device time setting (example operation)
                try:
                    current_time = await device_manager.execute_command("get_time")
                    logger.info(
                        "Device time retrieved successfully",
                        extra={
                            "device_time": str(current_time),
                        },
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to retrieve device time",
                        extra={
                            "error": str(e),
                        },
                    )

                # Keep the service running
                logger.info("Service initialized, keeping connection alive...")

                # Simple heartbeat loop
                while True:
                    await asyncio.sleep(60)
                    status = await device_manager.get_connection_status()
                    logger.debug(
                        "Device status check",
                        extra=status,
                    )

                    if not status.get("authenticated"):
                        logger.warning(
                            "Device connection lost",
                            extra=status,
                        )
                        break

            else:
                logger.error("Failed to connect to device")
                sys.exit(1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(
                "Application error",
                extra={
                    "error": str(e),
                },
            )
            sys.exit(1)
        finally:
            # Cleanup
            await device_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())