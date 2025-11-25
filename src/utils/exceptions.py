"""
Custom exception classes for ZK-Communist device communication.

This module defines specific exception types for different device error scenarios
including connection, authentication, timeout, and command failures.
"""


class DeviceConnectionError(Exception):
    """Exception raised when device connection fails.

    This exception is used when the device cannot be reached or the connection
    cannot be established due to network issues or device unavailability.
    """

    def __init__(self, message: str, ip_address: str = None, port: int = None):
        """Initialize device connection error.

        Args:
            message: Human-readable error message
            ip_address: Device IP address (optional)
            port: Device port (optional)
        """
        self.ip_address = ip_address
        self.port = port
        super().__init__(message)


class DeviceAuthenticationError(Exception):
    """Exception raised when device authentication fails.

    This exception is used when the device credentials are invalid or
    authentication cannot be completed successfully.
    """

    def __init__(self, message: str, ip_address: str = None):
        """Initialize device authentication error.

        Args:
            message: Human-readable error message
            ip_address: Device IP address (optional)
        """
        self.ip_address = ip_address
        super().__init__(message)


class DeviceTimeoutError(Exception):
    """Exception raised when device operations timeout.

    This exception is used when device communication exceeds the configured
    timeout period for connection or command execution.
    """

    def __init__(self, message: str, operation: str = None, timeout_seconds: int = None):
        """Initialize device timeout error.

        Args:
            message: Human-readable error message
            operation: Operation that timed out (optional)
            timeout_seconds: Timeout duration in seconds (optional)
        """
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(message)


class DeviceCommandError(Exception):
    """Exception raised when device command execution fails.

    This exception is used when the device rejects a command or when
    command execution encounters an error.
    """

    def __init__(self, message: str, command: str = None, response_code: int = None):
        """Initialize device command error.

        Args:
            message: Human-readable error message
            command: Command that failed (optional)
            response_code: Device response code (optional)
        """
        self.command = command
        self.response_code = response_code
        super().__init__(message)


class DeviceHealthError(Exception):
    """Exception raised when device health check fails.

    This exception is used when the device health monitoring indicates
    the device is not responding properly or has critical issues.
    """

    def __init__(self, message: str, health_check: str = None):
        """Initialize device health error.

        Args:
            message: Human-readable error message
            health_check: Type of health check that failed (optional)
        """
        self.health_check = health_check
        super().__init__(message)