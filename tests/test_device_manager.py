"""
Unit tests for DeviceManager functionality.

This module tests device connection, authentication, retry logic,
health monitoring, and command execution using mocked devices.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import logging

from src.services.device_manager import DeviceManager, ConnectionStatus
from src.utils.exceptions import (
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceCommandError,
)
from tests.fixtures.device_mocks import (
    MockZKDevice,
    create_mock_credentials,
    create_test_ip_address,
    create_test_port,
)


class TestDeviceManager:
    """Test suite for DeviceManager class."""

    @pytest.fixture
    def device_manager(self):
        """Create DeviceManager instance for testing."""
        return DeviceManager(
            max_retry_attempts=3,
            retry_backoff_base=2,
            connection_timeout=5,
            health_check_interval=30,
        )

    @pytest.fixture
    def test_credentials(self):
        """Create test device credentials."""
        return create_mock_credentials("test123")

    @pytest.fixture
    def test_ip_address(self):
        """Create test IP address."""
        return create_test_ip_address()

    @pytest.fixture
    def test_port(self):
        """Create test port."""
        return create_test_port()

    class TestConnectionMethods:
        """Test connection-related methods."""

        @pytest.mark.asyncio
        async def test_successful_connection(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test successful device connection with authentication."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                # Mock ZK device
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                # Mock executor calls
                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # Mock connect, verify, and enable_device
                    mock_loop_instance.run_in_executor.side_effect = [
                        True,  # connect
                        True,  # verify
                        True,  # enable_device
                    ]

                    result = await device_manager.connect(test_ip_address, test_port, test_credentials)

                    assert result is True
                    assert device_manager.connection_status == ConnectionStatus.AUTHENTICATED
                    assert device_manager.ip_address == test_ip_address
                    assert device_manager.port == test_port
                    assert device_manager.credentials == test_credentials

        @pytest.mark.asyncio
        async def test_connection_authentication_failure(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test connection failure due to authentication."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice(auth_should_fail=True)
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # Mock successful connect but failed verification
                    mock_loop_instance.run_in_executor.side_effect = [
                        True,  # connect
                        Exception("Authentication failed"),  # verify
                    ]

                    with pytest.raises(DeviceAuthenticationError):
                        await device_manager.connect(test_ip_address, test_port, test_credentials)

        @pytest.mark.asyncio
        async def test_connection_timeout(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test connection timeout scenario."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # Mock connect that takes too long
                    async def slow_connect(*args, **kwargs):
                        await asyncio.sleep(10)  # Longer than timeout
                        return True

                    mock_loop_instance.run_in_executor.side_effect = slow_connect

                    with pytest.raises(DeviceTimeoutError) as exc_info:
                        await device_manager.connect(test_ip_address, test_port, test_credentials)

                    assert "Connection timeout" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_connection_retry_logic(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test exponential backoff retry logic."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop, \
                     patch('asyncio.sleep') as mock_sleep:

                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # First attempt fails, second succeeds
                    call_count = 0
                    def simulate_retry(*args, **kwargs):
                        nonlocal call_count
                        call_count += 1
                        if call_count == 1:
                            raise Exception("First attempt failed")
                        return True  # Success on second attempt

                    mock_loop_instance.run_in_executor.side_effect = [
                        Exception("First attempt failed"),  # connect fails
                        True,  # connect succeeds
                        True,  # verify succeeds
                        True,  # enable_device succeeds
                    ]

                    result = await device_manager.connect(test_ip_address, test_port, test_credentials)

                    assert result is True
                    assert mock_sleep.call_count == 1  # Should sleep once between retries
                    mock_sleep.assert_called_with(1)  # First backoff should be 2^0 = 1 second

        @pytest.mark.asyncio
        async def test_connection_max_attempts_exceeded(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test failure after max retry attempts."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop, \
                     patch('asyncio.sleep') as mock_sleep:

                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # All attempts fail
                    mock_loop_instance.run_in_executor.side_effect = Exception("Connection failed")

                    with pytest.raises(DeviceConnectionError):
                        await device_manager.connect(test_ip_address, test_port, test_credentials)

                    # Should retry max_attempts - 1 times (sleep called between retries)
                    assert mock_sleep.call_count == device_manager.max_retry_attempts - 1

        @pytest.mark.asyncio
        async def test_disconnect_cleanup(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test proper cleanup during disconnection."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # Mock successful connection
                    mock_loop_instance.run_in_executor.side_effect = [
                        True,  # connect
                        True,  # verify
                        True,  # enable_device
                        None,  # disconnect
                        None,  # end_device
                    ]

                    # Connect first
                    await device_manager.connect(test_ip_address, test_port, test_credentials)

                    # Verify connected state
                    assert device_manager.connection_status == ConnectionStatus.AUTHENTICATED

                    # Now disconnect
                    await device_manager.disconnect()

                    # Verify cleanup
                    assert device_manager.connection_status == ConnectionStatus.DISCONNECTED
                    assert device_manager.ip_address is None
                    assert device_manager.port is None
                    assert device_manager.credentials is None

    class TestCommandExecution:
        """Test command execution methods."""

        @pytest.mark.asyncio
        async def test_execute_command_success(self, device_manager):
            """Test successful command execution."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED
            device_manager.ip_address = "192.168.1.100"

            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = AsyncMock()
                mock_loop.return_value = mock_loop_instance
                mock_loop_instance.run_in_executor.return_value = "2023-01-01 12:00:00"

                result = await device_manager.execute_command("get_time")

                assert result == "2023-01-01 12:00:00"

        @pytest.mark.asyncio
        async def test_execute_command_not_connected(self, device_manager):
            """Test command execution when device not connected."""
            device_manager.device = None
            device_manager.connection_status = ConnectionStatus.DISCONNECTED

            with pytest.raises(DeviceConnectionError) as exc_info:
                await device_manager.execute_command("get_time")

            assert "Device not connected" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_execute_command_timeout(self, device_manager):
            """Test command execution timeout."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED
            device_manager.ip_address = "192.168.1.100"

            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = AsyncMock()
                mock_loop.return_value = mock_loop_instance

                # Mock slow command execution
                async def slow_command(*args, **kwargs):
                    await asyncio.sleep(15)  # Longer than command timeout
                    return "result"

                mock_loop_instance.run_in_executor.side_effect = slow_command

                with pytest.raises(DeviceTimeoutError) as exc_info:
                    await device_manager.execute_command("get_time")

                assert "Command 'get_time' timed out" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_execute_set_time_command(self, device_manager):
            """Test set_time command execution."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED
            device_manager.ip_address = "192.168.1.100"

            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = AsyncMock()
                mock_loop.return_value = mock_loop_instance
                mock_loop_instance.run_in_executor.return_value = True

                result = await device_manager.execute_command("set_time", target_time="2023-01-01 08:00:00")

                assert result is True

        @pytest.mark.asyncio
        async def test_execute_set_time_missing_parameter(self, device_manager):
            """Test set_time command without target_time parameter."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED
            device_manager.ip_address = "192.168.1.100"

            with pytest.raises(DeviceCommandError) as exc_info:
                await device_manager.execute_command("set_time")

                assert "set_time requires target_time parameter" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_execute_unknown_command(self, device_manager):
            """Test execution of unknown command."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED
            device_manager.ip_address = "192.168.1.100"

            with pytest.raises(DeviceCommandError) as exc_info:
                await device_manager.execute_command("unknown_command")

                assert "Unknown command" in str(exc_info.value)

    class TestConnectionStatus:
        """Test connection status methods."""

        @pytest.mark.asyncio
        async def test_get_connection_status(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test getting connection status information."""
            # Set up device state
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED
            device_manager.ip_address = test_ip_address
            device_manager.port = test_port

            status = await device_manager.get_connection_status()

            assert status["status"] == "authenticated"
            assert status["ip_address"] == test_ip_address
            assert status["port"] == test_port
            assert status["authenticated"] is True
            assert isinstance(status["health_monitoring"], bool)

        @pytest.mark.asyncio
        async def test_test_connection_success(self, device_manager):
            """Test successful connection test."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED

            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = AsyncMock()
                mock_loop.return_value = mock_loop_instance
                mock_loop_instance.run_in_executor.return_value = {"device_time": "2023-01-01 12:00:00"}

                result = await device_manager.test_connection()

                assert result is True

        @pytest.mark.asyncio
        async def test_test_connection_not_connected(self, device_manager):
            """Test connection test when device not connected."""
            device_manager.device = None
            device_manager.connection_status = ConnectionStatus.DISCONNECTED

            result = await device_manager.test_connection()

            assert result is False

        @pytest.mark.asyncio
        async def test_test_connection_failure(self, device_manager):
            """Test connection test failure."""
            # Mock connected device
            device_manager.device = MockZKDevice()
            device_manager.connection_status = ConnectionStatus.AUTHENTICATED

            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = AsyncMock()
                mock_loop.return_value = mock_loop_instance
                mock_loop_instance.run_in_executor.side_effect = Exception("Device error")

                result = await device_manager.test_connection()

                assert result is False

    class TestContextManager:
        """Test device session context manager."""

        @pytest.mark.asyncio
        async def test_device_session_context_manager(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test device session context manager."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # Mock connection and disconnection
                    mock_loop_instance.run_in_executor.side_effect = [
                        True,  # connect
                        True,  # verify
                        True,  # enable_device
                        None,  # disconnect
                        None,  # end_device
                    ]

                    async with device_manager.device_session(test_ip_address, test_port, test_credentials) as session:
                        assert session is device_manager
                        assert device_manager.connection_status == ConnectionStatus.AUTHENTICATED

                    # Verify cleanup after context exit
                    assert device_manager.connection_status == ConnectionStatus.DISCONNECTED

        @pytest.mark.asyncio
        async def test_device_session_context_manager_exception(self, device_manager, test_ip_address, test_port, test_credentials):
            """Test device session context manager with exception."""
            with patch('src.services.device_manager.ZK') as mock_zk_class:
                mock_zk_device = MockZKDevice()
                mock_zk_class.return_value = mock_zk_device

                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop_instance = AsyncMock()
                    mock_loop.return_value = mock_loop_instance

                    # Mock connection and disconnection
                    mock_loop_instance.run_in_executor.side_effect = [
                        True,  # connect
                        True,  # verify
                        True,  # enable_device
                        None,  # disconnect
                        None,  # end_device
                    ]

                    try:
                        async with device_manager.device_session(test_ip_address, test_port, test_credentials) as session:
                            assert device_manager.connection_status == ConnectionStatus.AUTHENTICATED
                            raise ValueError("Test exception")
                    except ValueError:
                        pass  # Expected exception

                    # Verify cleanup despite exception
                    assert device_manager.connection_status == ConnectionStatus.DISCONNECTED