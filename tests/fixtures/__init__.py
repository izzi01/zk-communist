"""
Test fixtures and mocks for ZK-Communist Time Liberation Server.

This package contains mock classes, test utilities, and fixtures for
testing device communication without requiring physical hardware.
"""

from .device_mocks import (
    MockZKDevice,
    create_mock_device_manager,
    create_mock_credentials,
    create_test_ip_address,
    create_test_port,
)

__all__ = [
    "MockZKDevice",
    "create_mock_device_manager",
    "create_mock_credentials",
    "create_test_ip_address",
    "create_test_port",
]