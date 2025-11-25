"""
Mock fixtures for ZKTeco device testing.

This module provides mock classes and utilities for testing device communication
without requiring physical hardware.
"""

import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Any, Dict, Optional


class MockZKDevice:
    """Mock ZK device for testing."""

    def __init__(self, connect_should_fail: bool = False, auth_should_fail: bool = False):
        """Initialize mock device with failure options."""
        self.connect_should_fail = connect_should_fail
        self.auth_should_fail = auth_should_fail
        self.is_connected = False
        self.is_enabled = False
        self.device_time = "2023-01-01 12:00:00"
        self.call_count = 0

    def connect(self) -> bool:
        """Mock device connection."""
        self.call_count += 1
        if self.connect_should_fail:
            raise Exception("Mock connection failed")
        self.is_connected = True
        return True

    def disconnect(self) -> None:
        """Mock device disconnection."""
        self.is_connected = False

    def end_device(self) -> None:
        """Mock device end."""
        self.is_enabled = False

    def verify(self, user: str, password: bytes) -> bool:
        """Mock device verification."""
        if self.auth_should_fail:
            raise Exception("Mock authentication failed")
        return True

    def enable_device(self) -> bool:
        """Mock device enable."""
        self.is_enabled = True
        return True

    def get_device_time(self) -> str:
        """Mock get device time."""
        if not self.is_connected:
            raise Exception("Device not connected")
        return self.device_time

    def set_time(self, time_str: str) -> bool:
        """Mock set device time."""
        if not self.is_connected:
            raise Exception("Device not connected")
        self.device_time = time_str
        return True


def create_mock_device_manager() -> Mock:
    """Create a mock DeviceManager for testing."""
    mock_manager = Mock()

    # Configure async methods
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    mock_manager.test_connection = AsyncMock()
    mock_manager.execute_command = AsyncMock()
    mock_manager.get_connection_status = AsyncMock()

    # Configure default return values
    mock_manager.connect.return_value = True
    mock_manager.test_connection.return_value = True
    mock_manager.get_connection_status.return_value = {
        "status": "authenticated",
        "ip_address": "192.168.1.100",
        "port": 4370,
        "authenticated": True,
        "health_monitoring": True,
    }

    return mock_manager


def create_mock_credentials(password: str = "test123") -> Dict[str, str]:
    """Create mock device credentials."""
    return {"password": password}


def create_test_ip_address() -> str:
    """Create test IP address."""
    return "192.168.1.100"


def create_test_port() -> int:
    """Create test port."""
    return 4370