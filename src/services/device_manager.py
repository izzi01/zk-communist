"""
Device Manager for ZK-Communist Time Liberation Server.

This module provides the DeviceManager class for handling communication
with ZKTeco fingerprint devices using the pyzk SDK. Implements async
connection management, retry logic, and health monitoring.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager

from pyzk import ZK, const
from src.utils.exceptions import (
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceCommandError,
    DeviceHealthError,
)


class ConnectionStatus(Enum):
    """Device connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class DeviceManager:
    """
    Manages communication with ZKTeco fingerprint devices.

    Provides async connection methods, retry logic with exponential backoff,
    health monitoring, and structured logging for device operations.
    """

    def __init__(
        self,
        max_retry_attempts: int = 5,
        retry_backoff_base: int = 2,
        connection_timeout: int = 10,
        health_check_interval: int = 30,
    ):
        """Initialize DeviceManager.

        Args:
            max_retry_attempts: Maximum number of connection retry attempts
            retry_backoff_base: Base multiplier for exponential backoff
            connection_timeout: Connection timeout in seconds
            health_check_interval: Health check interval in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.max_retry_attempts = max_retry_attempts
        self.retry_backoff_base = retry_backoff_base
        self.connection_timeout = connection_timeout
        self.health_check_interval = health_check_interval

        # Connection state
        self.device: Optional[ZK] = None
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.ip_address: Optional[str] = None
        self.port: Optional[int] = None
        self.credentials: Optional[Dict[str, str]] = None

        # Connection state tracking
        self._connection_lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

    async def connect(self, ip_address: str, port: int, credentials: Dict[str, str]) -> bool:
        """
        Connect to ZKTeco device with retry logic.

        Args:
            ip_address: Device IP address
            port: Device port (typically 4370)
            credentials: Device authentication credentials

        Returns:
            True if connection successful, False otherwise

        Raises:
            DeviceConnectionError: If connection fails after all retries
            DeviceAuthenticationError: If authentication fails
            DeviceTimeoutError: If connection times out
        """
        async with self._connection_lock:
            self.ip_address = ip_address
            self.port = port
            self.credentials = credentials

            self.logger.info(
                "Attempting to connect to device",
                extra={
                    "ip_address": ip_address,
                    "port": port,
                    "timeout": self.connection_timeout,
                },
            )

            last_exception = None

            for attempt in range(self.max_retry_attempts):
                try:
                    self.connection_status = ConnectionStatus.CONNECTING
                    self.logger.info(
                        f"Connection attempt {attempt + 1}/{self.max_retry_attempts}",
                        extra={
                            "attempt": attempt + 1,
                            "max_attempts": self.max_retry_attempts,
                            "ip_address": ip_address,
                        },
                    )

                    # Attempt connection with timeout
                    self.device = await asyncio.wait_for(
                        self._create_connection(ip_address, port),
                        timeout=self.connection_timeout,
                    )

                    self.connection_status = ConnectionStatus.CONNECTED
                    self.logger.info(
                        "Device connection established",
                        extra={
                            "ip_address": ip_address,
                            "port": port,
                            "attempt": attempt + 1,
                        },
                    )

                    # Authenticate device
                    if await self._authenticate_device():
                        self.connection_status = ConnectionStatus.AUTHENTICATED
                        self.logger.info(
                            "Device authentication successful",
                            extra={"ip_address": ip_address},
                        )

                        # Start health monitoring
                        await self._start_health_monitoring()
                        return True
                    else:
                        raise DeviceAuthenticationError(
                            "Device authentication failed", ip_address=ip_address
                        )

                except asyncio.TimeoutError as e:
                    last_exception = DeviceTimeoutError(
                        f"Connection timeout after {self.connection_timeout} seconds",
                        operation="connect",
                        timeout_seconds=self.connection_timeout,
                    )
                    self.logger.warning(
                        f"Connection attempt {attempt + 1} timed out",
                        extra={
                            "attempt": attempt + 1,
                            "timeout": self.connection_timeout,
                            "ip_address": ip_address,
                        },
                    )

                except DeviceAuthenticationError as e:
                    last_exception = e
                    self.logger.error(
                        f"Authentication failed on attempt {attempt + 1}",
                        extra={
                            "attempt": attempt + 1,
                            "ip_address": ip_address,
                            "error": str(e),
                        },
                    )

                except Exception as e:
                    last_exception = DeviceConnectionError(
                        f"Connection failed: {str(e)}", ip_address=ip_address, port=port
                    )
                    self.logger.warning(
                        f"Connection attempt {attempt + 1} failed",
                        extra={
                            "attempt": attempt + 1,
                            "ip_address": ip_address,
                            "error": str(e),
                        },
                    )

                # Clean up failed connection
                await self._cleanup_connection()

                # Calculate backoff delay
                if attempt < self.max_retry_attempts - 1:
                    delay = self.retry_backoff_base**attempt
                    self.logger.info(
                        f"Waiting {delay} seconds before next attempt",
                        extra={
                            "delay": delay,
                            "attempt": attempt + 1,
                            "next_attempt": attempt + 2,
                        },
                    )
                    await asyncio.sleep(delay)

            # All attempts failed
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(
                "All connection attempts failed",
                extra={
                    "max_attempts": self.max_retry_attempts,
                    "ip_address": ip_address,
                    "final_error": str(last_exception) if last_exception else "Unknown error",
                },
            )
            raise last_exception or DeviceConnectionError(
                "Connection failed after all retry attempts",
                ip_address=ip_address,
                port=port,
            )

    async def disconnect(self) -> None:
        """Disconnect from device and cleanup resources."""
        async with self._connection_lock:
            self.logger.info(
                "Disconnecting from device",
                extra={"ip_address": self.ip_address},
            )

            await self._stop_health_monitoring()
            await self._cleanup_connection()

            self.connection_status = ConnectionStatus.DISCONNECTED
            self.ip_address = None
            self.port = None
            self.credentials = None

            self.logger.info(
                "Device disconnected successfully",
                extra={},
            )

    async def test_connection(self) -> bool:
        """
        Test current device connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.device or self.connection_status != ConnectionStatus.AUTHENTICATED:
            return False

        try:
            # Test device connectivity with a simple command
            device_info = await asyncio.wait_for(
                self._get_device_info(),
                timeout=5,
            )
            return device_info is not None
        except Exception as e:
            self.logger.warning(
                "Connection test failed",
                extra={
                    "ip_address": self.ip_address,
                    "error": str(e),
                },
            )
            return False

    async def execute_command(self, command: str, **kwargs) -> Any:
        """
        Execute command on device.

        Args:
            command: Command to execute
            **kwargs: Additional command parameters

        Returns:
            Command execution result

        Raises:
            DeviceConnectionError: If device not connected
            DeviceCommandError: If command execution fails
            DeviceTimeoutError: If command times out
        """
        if not self.device or self.connection_status != ConnectionStatus.AUTHENTICATED:
            raise DeviceConnectionError(
                "Device not connected or not authenticated", ip_address=self.ip_address
            )

        try:
            self.logger.debug(
                "Executing device command",
                extra={
                    "command": command,
                    "ip_address": self.ip_address,
                    "parameters": kwargs,
                },
            )

            # Execute command with timeout
            result = await asyncio.wait_for(
                self._execute_device_command(command, **kwargs),
                timeout=10,
            )

            self.logger.debug(
                "Command executed successfully",
                extra={
                    "command": command,
                    "ip_address": self.ip_address,
                },
            )

            return result

        except asyncio.TimeoutError:
            error_msg = f"Command '{command}' timed out"
            self.logger.error(
                error_msg,
                extra={
                    "command": command,
                    "ip_address": self.ip_address,
                },
            )
            raise DeviceTimeoutError(error_msg, operation=command, timeout_seconds=10)

        except Exception as e:
            error_msg = f"Command '{command}' failed: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "command": command,
                    "ip_address": self.ip_address,
                    "error": str(e),
                },
            )
            raise DeviceCommandError(error_msg, command=command)

    async def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status and health information.

        Returns:
            Dictionary with connection status details
        """
        return {
            "status": self.connection_status.value,
            "ip_address": self.ip_address,
            "port": self.port,
            "authenticated": self.connection_status == ConnectionStatus.AUTHENTICATED,
            "health_monitoring": self._health_check_task is not None
            and not self._health_check_task.done(),
        }

    # Private methods

    async def _create_connection(self, ip_address: str, port: int) -> ZK:
        """Create connection to ZKTeco device."""
        try:
            # Create ZK connection instance
            zk = ZK(ip_address, port=port, timeout=self.connection_timeout)
            # Note: pyzk uses synchronous operations, so we need to run in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, zk.connect)
            return zk
        except Exception as e:
            raise DeviceConnectionError(
                f"Failed to create ZK connection: {str(e)}", ip_address=ip_address, port=port
            )

    async def _authenticate_device(self) -> bool:
        """Authenticate with device using provided credentials."""
        if not self.device or not self.credentials:
            return False

        try:
            # Extract credentials
            password = self.credentials.get("password", "")
            if isinstance(password, str):
                password = password.encode("utf-8")

            # Authenticate device (run in executor for sync pyzk operation)
            loop = asyncio.get_event_loop()
            authenticated = await loop.run_in_executor(
                None, self.device.verify, "admin", password
            )

            if authenticated:
                # Enable device
                await loop.run_in_executor(None, self.device.enable_device)

            return bool(authenticated)

        except Exception as e:
            self.logger.error(
                "Authentication failed",
                extra={
                    "ip_address": self.ip_address,
                    "error": str(e),
                },
            )
            raise DeviceAuthenticationError(
                f"Device authentication failed: {str(e)}", ip_address=self.ip_address
            )

    async def _get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get device information for health checking."""
        if not self.device:
            return None

        try:
            loop = asyncio.get_event_loop()
            device_info = await loop.run_in_executor(None, self.device.get_device_time)
            return {"device_time": device_info}
        except Exception:
            return None

    async def _execute_device_command(self, command: str, **kwargs) -> Any:
        """Execute command on device (run in executor for sync pyzk operations)."""
        if not self.device:
            raise DeviceConnectionError("No device connection available")

        loop = asyncio.get_event_loop()

        # Map commands to pyzk operations
        if command == "get_time":
            return await loop.run_in_executor(None, self.device.get_device_time)
        elif command == "set_time":
            target_time = kwargs.get("target_time")
            if target_time:
                return await loop.run_in_executor(
                    None, self.device.set_time, target_time
                )
            raise DeviceCommandError("set_time requires target_time parameter")
        else:
            raise DeviceCommandError(f"Unknown command: {command}")

    async def _cleanup_connection(self) -> None:
        """Cleanup device connection resources."""
        if self.device:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.device.disconnect)
                await loop.run_in_executor(None, self.device.end_device)
            except Exception as e:
                self.logger.warning(
                    "Error during connection cleanup",
                    extra={
                        "ip_address": self.ip_address,
                        "error": str(e),
                    },
                )
            finally:
                self.device = None

    async def _start_health_monitoring(self) -> None:
        """Start device health monitoring."""
        if self._health_check_task and not self._health_check_task.done():
            return

        self._health_check_task = asyncio.create_task(self._health_monitoring_loop())
        self.logger.info(
            "Health monitoring started",
            extra={
                "interval": self.health_check_interval,
                "ip_address": self.ip_address,
            },
        )

    async def _stop_health_monitoring(self) -> None:
        """Stop device health monitoring."""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Health monitoring stopped")

    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop for device connectivity."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                if not await self.test_connection():
                    self.logger.warning(
                        "Health check failed, initiating reconnection",
                        extra={"ip_address": self.ip_address},
                    )
                    self.connection_status = ConnectionStatus.RECONNECTING

                    # Start reconnection if not already running
                    if not self._reconnect_task or self._reconnect_task.done():
                        self._reconnect_task = asyncio.create_task(
                            self._attempt_reconnection()
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Health monitoring loop error",
                    extra={
                        "ip_address": self.ip_address,
                        "error": str(e),
                    },
                )

    async def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to device."""
        if not self.ip_address or not self.port or not self.credentials:
            self.logger.error(
                "Cannot reconnect: missing connection parameters",
                extra={"ip_address": self.ip_address},
            )
            return

        try:
            await self.connect(self.ip_address, self.port, self.credentials)
            self.logger.info(
                "Reconnection successful",
                extra={"ip_address": self.ip_address},
            )
        except Exception as e:
            self.logger.error(
                "Reconnection failed",
                extra={
                    "ip_address": self.ip_address,
                    "error": str(e),
                },
            )
            self.connection_status = ConnectionStatus.ERROR

    @asynccontextmanager
    async def device_session(self, ip_address: str, port: int, credentials: Dict[str, str]):
        """
        Context manager for device sessions.

        Args:
            ip_address: Device IP address
            port: Device port
            credentials: Device credentials

        Yields:
            DeviceManager instance with active connection
        """
        await self.connect(ip_address, port, credentials)
        try:
            yield self
        finally:
            await self.disconnect()