"""Integration tests for DeviceManager using standard library.

These tests verify end-to-end functionality and integration patterns
without requiring external testing frameworks.
"""

import asyncio
import sys
import os
import unittest.mock as mock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock pyzk before importing DeviceManager
sys.modules['pyzk'] = mock.MagicMock()
sys.modules['pyzk.const'] = mock.MagicMock()

from src.services.device_manager import DeviceManager, ConnectionStatus
from src.utils.exceptions import (
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceCommandError,
)


class MockZKDevice:
    """Mock ZK device for integration testing."""

    def __init__(self):
        self.is_connected = False
        self.is_enabled = False
        self.authenticated = False
        self.device_time = "2023-01-01 12:00:00"
        self.connect_count = 0

    def connect(self):
        self.connect_count += 1
        self.is_connected = True
        return True

    def disconnect(self):
        self.is_connected = False

    def end_device(self):
        self.is_enabled = False

    def verify(self, user, password):
        self.authenticated = True
        return True

    def enable_device(self):
        self.is_enabled = True
        return True

    def get_device_time(self):
        if not self.is_connected:
            raise Exception("Device not connected")
        return self.device_time

    def set_time(self, time_str):
        if not self.is_connected:
            raise Exception("Device not connected")
        self.device_time = time_str
        return True


class TestDeviceManagerIntegration:
    """Integration tests for DeviceManager."""

    async def test_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        print("Testing connection lifecycle...")

        manager = DeviceManager(max_retry_attempts=3, connection_timeout=5)

        test_credentials = {"password": "test123"}
        test_ip = "192.168.1.100"
        test_port = 4370

        with mock.patch('src.services.device_manager.ZK') as mock_zk_class:
            mock_device = MockZKDevice()
            mock_zk_class.return_value = mock_device

            with mock.patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = mock.AsyncMock()
                mock_loop.return_value = mock_loop_instance

                # Mock successful operations
                mock_loop_instance.run_in_executor.side_effect = [
                    True,  # connect
                    True,  # verify
                    True,  # enable_device
                    "2023-01-01 12:00:00",  # get_device_time
                ]

                # Test connection
                result = await manager.connect(test_ip, test_port, test_credentials)
                assert result is True
                assert manager.connection_status == ConnectionStatus.AUTHENTICATED
                assert manager.ip_address == test_ip
                assert manager.port == test_port

                # Test connection status
                status = await manager.get_connection_status()
                assert status["status"] == "authenticated"
                assert status["ip_address"] == test_ip
                assert status["authenticated"] is True

                # Test command execution
                mock_loop_instance.run_in_executor.return_value = "2023-01-01 12:00:00"
                command_result = await manager.execute_command("get_time")
                assert command_result == "2023-01-01 12:00:00"

                # Test disconnection
                mock_loop_instance.run_in_executor.side_effect = [None, None]  # disconnect, end_device
                await manager.disconnect()
                assert manager.connection_status == ConnectionStatus.DISCONNECTED
                assert manager.ip_address is None

        print("✅ Connection lifecycle test passed")

    async def test_retry_logic(self):
        """Test retry logic with exponential backoff."""
        print("Testing retry logic...")

        manager = DeviceManager(max_retry_attempts=3, retry_backoff_base=2)
        test_credentials = {"password": "test123"}

        with mock.patch('src.services.device_manager.ZK') as mock_zk_class:
            mock_device = MockZKDevice()
            mock_zk_class.return_value = mock_device

            with mock.patch('asyncio.get_event_loop') as mock_loop, \
                 mock.patch('asyncio.sleep') as mock_sleep:

                mock_loop_instance = mock.AsyncMock()
                mock_loop.return_value = mock_loop_instance

                call_count = 0
                def mock_executor(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("First attempt failed")
                    elif call_count == 2:
                        return True  # connect succeeds
                    elif call_count == 3:
                        return True  # verify succeeds
                    elif call_count == 4:
                        return True  # enable_device succeeds
                    return True

                mock_loop_instance.run_in_executor.side_effect = mock_executor

                result = await manager.connect("192.168.1.100", 4370, test_credentials)

                assert result is True
                assert mock_sleep.call_count == 1
                mock_sleep.assert_called_with(1)  # 2^0 = 1 second

        print("✅ Retry logic test passed")

    async def test_authentication_failure(self):
        """Test authentication failure handling."""
        print("Testing authentication failure...")

        manager = DeviceManager(max_retry_attempts=2)
        test_credentials = {"password": "wrong_password"}

        with mock.patch('src.services.device_manager.ZK') as mock_zk_class:
            mock_device = MockZKDevice()
            mock_zk_class.return_value = mock_device

            with mock.patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = mock.AsyncMock()
                mock_loop.return_value = mock_loop_instance

                # Mock successful connect but failed verify
                mock_loop_instance.run_in_executor.side_effect = [
                    True,  # connect succeeds
                    Exception("Authentication failed"),  # verify fails
                ]

                try:
                    await manager.connect("192.168.1.100", 4370, test_credentials)
                    assert False, "Should have raised DeviceAuthenticationError"
                except DeviceAuthenticationError:
                    assert manager.connection_status == ConnectionStatus.ERROR

        print("✅ Authentication failure test passed")

    async def test_command_timeout(self):
        """Test command timeout handling."""
        print("Testing command timeout...")

        manager = DeviceManager()

        # Mock connected device
        manager.device = MockZKDevice()
        manager.connection_status = ConnectionStatus.AUTHENTICATED
        manager.ip_address = "192.168.1.100"

        with mock.patch('asyncio.get_event_loop') as mock_loop:
            mock_loop_instance = mock.AsyncMock()
            mock_loop.return_value = mock_loop_instance

            # Mock slow command that times out
            async def slow_command(*args, **kwargs):
                await asyncio.sleep(15)
                return "result"

            mock_loop_instance.run_in_executor.side_effect = slow_command

            try:
                await manager.execute_command("get_time")
                assert False, "Should have raised DeviceTimeoutError"
            except DeviceTimeoutError as e:
                assert "get_time" in str(e)

        print("✅ Command timeout test passed")

    async def test_health_monitoring(self):
        """Test health monitoring functionality."""
        print("Testing health monitoring...")

        manager = DeviceManager(health_check_interval=1)  # 1 second interval

        with mock.patch('src.services.device_manager.ZK') as mock_zk_class:
            mock_device = MockZKDevice()
            mock_zk_class.return_value = mock_device

            with mock.patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = mock.AsyncMock()
                mock_loop.return_value = mock_loop_instance

                # Mock successful connection
                mock_loop_instance.run_in_executor.side_effect = [
                    True,  # connect
                    True,  # verify
                    True,  # enable_device
                    {"device_time": "2023-01-01 12:00:00"},  # get_device_time for health check
                ]

                await manager.connect("192.168.1.100", 4370, {"password": "test123"})

                # Health monitoring task should be created
                assert manager._health_check_task is not None
                assert not manager._health_check_task.done()

                # Test health check
                result = await manager.test_connection()
                assert result is True

                # Stop health monitoring
                await manager._stop_health_monitoring()
                assert manager._health_check_task.cancelled()

        print("✅ Health monitoring test passed")

    async def test_context_manager(self):
        """Test device session context manager."""
        print("Testing context manager...")

        manager = DeviceManager()
        test_credentials = {"password": "test123"}

        with mock.patch('src.services.device_manager.ZK') as mock_zk_class:
            mock_device = MockZKDevice()
            mock_zk_class.return_value = mock_device

            with mock.patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = mock.AsyncMock()
                mock_loop.return_value = mock_loop_instance

                # Mock connection and disconnection operations
                mock_loop_instance.run_in_executor.side_effect = [
                    True,  # connect
                    True,  # verify
                    True,  # enable_device
                    None,  # disconnect
                    None,  # end_device
                ]

                async with manager.device_session("192.168.1.100", 4370, test_credentials) as session:
                    assert session is manager
                    assert manager.connection_status == ConnectionStatus.AUTHENTICATED

                # Verify cleanup after context exit
                assert manager.connection_status == ConnectionStatus.DISCONNECTED

        print("✅ Context manager test passed")

    async def test_error_recovery(self):
        """Test error recovery and graceful degradation."""
        print("Testing error recovery...")

        manager = DeviceManager(max_retry_attempts=2)

        with mock.patch('src.services.device_manager.ZK') as mock_zk_class:
            mock_device = MockZKDevice()
            mock_zk_class.return_value = mock_device

            with mock.patch('asyncio.get_event_loop') as mock_loop:
                mock_loop_instance = mock.AsyncMock()
                mock_loop.return_value = mock_loop_instance

                # Test initial failure then success
                call_count = 0
                def mock_executor_with_recovery(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count <= 2:
                        raise Exception("Connection failed")
                    elif call_count == 3:
                        return True  # connect succeeds
                    elif call_count == 4:
                        return True  # verify succeeds
                    elif call_count == 5:
                        return True  # enable_device succeeds
                    return True

                mock_loop_instance.run_in_executor.side_effect = mock_executor_with_recovery

                # First attempt should fail
                try:
                    await manager.connect("192.168.1.100", 4370, {"password": "test123"})
                    assert False, "Should have failed on first attempt"
                except DeviceConnectionError:
                    assert manager.connection_status == ConnectionStatus.ERROR

                # Reset for second attempt
                manager.connection_status = ConnectionStatus.DISCONNECTED
                call_count = 0

                # Second attempt should succeed
                result = await manager.connect("192.168.1.100", 4370, {"password": "test123"})
                assert result is True
                assert manager.connection_status == ConnectionStatus.AUTHENTICATED

        print("✅ Error recovery test passed")


async def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting DeviceManager Integration Tests")
    print("=" * 50)

    test_instance = TestDeviceManagerIntegration()

    tests = [
        test_instance.test_connection_lifecycle,
        test_instance.test_retry_logic,
        test_instance.test_authentication_failure,
        test_instance.test_command_timeout,
        test_instance.test_health_monitoring,
        test_instance.test_context_manager,
        test_instance.test_error_recovery,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1

    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    # Run integration tests
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)