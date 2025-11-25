"""
Unit tests for custom exception classes.

This module tests all custom exception classes and their
initialization with various parameters.
"""

import pytest

from src.utils.exceptions import (
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceCommandError,
    DeviceHealthError,
)


class TestDeviceConnectionError:
    """Test DeviceConnectionError exception."""

    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = DeviceConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.ip_address is None
        assert error.port is None

    def test_initialization_with_ip_and_port(self):
        """Test initialization with IP address and port."""
        error = DeviceConnectionError(
            "Connection failed",
            ip_address="192.168.1.100",
            port=4370
        )
        assert str(error) == "Connection failed"
        assert error.ip_address == "192.168.1.100"
        assert error.port == 4370

    def test_inheritance(self):
        """Test exception inheritance."""
        error = DeviceConnectionError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, DeviceConnectionError)


class TestDeviceAuthenticationError:
    """Test DeviceAuthenticationError exception."""

    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = DeviceAuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert error.ip_address is None

    def test_initialization_with_ip_address(self):
        """Test initialization with IP address."""
        error = DeviceAuthenticationError(
            "Auth failed",
            ip_address="192.168.1.100"
        )
        assert str(error) == "Auth failed"
        assert error.ip_address == "192.168.1.100"

    def test_inheritance(self):
        """Test exception inheritance."""
        error = DeviceAuthenticationError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, DeviceAuthenticationError)


class TestDeviceTimeoutError:
    """Test DeviceTimeoutError exception."""

    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = DeviceTimeoutError("Operation timed out")
        assert str(error) == "Operation timed out"
        assert error.operation is None
        assert error.timeout_seconds is None

    def test_initialization_with_operation_and_timeout(self):
        """Test initialization with operation and timeout."""
        error = DeviceTimeoutError(
            "Connection timed out",
            operation="connect",
            timeout_seconds=10
        )
        assert str(error) == "Connection timed out"
        assert error.operation == "connect"
        assert error.timeout_seconds == 10

    def test_inheritance(self):
        """Test exception inheritance."""
        error = DeviceTimeoutError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, DeviceTimeoutError)


class TestDeviceCommandError:
    """Test DeviceCommandError exception."""

    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = DeviceCommandError("Command failed")
        assert str(error) == "Command failed"
        assert error.command is None
        assert error.response_code is None

    def test_initialization_with_command_and_response_code(self):
        """Test initialization with command and response code."""
        error = DeviceCommandError(
            "Command failed",
            command="get_time",
            response_code=500
        )
        assert str(error) == "Command failed"
        assert error.command == "get_time"
        assert error.response_code == 500

    def test_inheritance(self):
        """Test exception inheritance."""
        error = DeviceCommandError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, DeviceCommandError)


class TestDeviceHealthError:
    """Test DeviceHealthError exception."""

    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = DeviceHealthError("Health check failed")
        assert str(error) == "Health check failed"
        assert error.health_check is None

    def test_initialization_with_health_check(self):
        """Test initialization with health check type."""
        error = DeviceHealthError(
            "Health check failed",
            health_check="connectivity"
        )
        assert str(error) == "Health check failed"
        assert error.health_check == "connectivity"

    def test_inheritance(self):
        """Test exception inheritance."""
        error = DeviceHealthError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, DeviceHealthError)


class TestExceptionHierarchy:
    """Test that all exceptions are properly related."""

    def test_all_exceptions_inherit_from_exception(self):
        """Test that all custom exceptions inherit from base Exception."""
        exceptions = [
            DeviceConnectionError,
            DeviceAuthenticationError,
            DeviceTimeoutError,
            DeviceCommandError,
            DeviceHealthError,
        ]

        for exception_class in exceptions:
            assert issubclass(exception_class, Exception)

    def test_exception_uniqueness(self):
        """Test that all exception classes are distinct."""
        exception_classes = [
            DeviceConnectionError,
            DeviceAuthenticationError,
            DeviceTimeoutError,
            DeviceCommandError,
            DeviceHealthError,
        ]

        # Ensure all classes are unique
        assert len(exception_classes) == len(set(exception_classes))

    def test_exception_instantiation(self):
        """Test that all exceptions can be instantiated."""
        exceptions = [
            DeviceConnectionError("Test"),
            DeviceAuthenticationError("Test"),
            DeviceTimeoutError("Test"),
            DeviceCommandError("Test"),
            DeviceHealthError("Test"),
        ]

        for exception in exceptions:
            assert isinstance(exception, Exception)
            assert isinstance(exception, type(exception).__bases__[0])