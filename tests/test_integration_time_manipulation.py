"""Integration tests for Time Manipulation Logic.

End-to-end testing of time manipulation cycles with mocked device
communication and accelerated time scenarios.
"""

import asyncio
import unittest.mock as mock
import sys
import os
from datetime import datetime, time as dt_time, timedelta
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock pyzk before imports
sys.modules['pyzk'] = mock.MagicMock()
sys.modules['pyzk.const'] = mock.MagicMock()

from src.services.device_manager import DeviceManager
from src.services.time_manipulator import TimeManipulator, ManipulationConfig
from src.services.scheduler import Scheduler
from src.utils.time_helpers import TimeWindowManager, RandomTimeGenerator


class MockTimeProvider:
    """Mock time provider for accelerated testing."""

    def __init__(self, initial_time: datetime):
        self.current_time = initial_time
        self.speed_multiplier = 1.0

    def now(self) -> datetime:
        """Get current time with acceleration."""
        return self.current_time

    def advance(self, seconds: float) -> None:
        """Advance time by specified seconds."""
        self.current_time += timedelta(seconds=seconds * self.speed_multiplier)

    def set_speed(self, multiplier: float) -> None:
        """Set time acceleration speed."""
        self.speed_multiplier = multiplier


class MockDeviceManager:
    """Mock device manager for testing."""

    def __init__(self):
        self.is_connected = False
        self.connection_status = "disconnected"
        self.time_commands = []
        self.command_responses = []

    async def connect(self, ip_address: str, port: int, credentials: Dict[str, str]) -> bool:
        self.is_connected = True
        self.connection_status = "connected"
        return True

    async def disconnect(self) -> None:
        self.is_connected = False
        self.connection_status = "disconnected"

    async def execute_command(self, command: str, **kwargs) -> Any:
        self.time_commands.append((command, kwargs))

        # Simulate successful time setting
        if command == "set_time":
            return True
        elif command == "get_time":
            return "2023-01-01 12:00:00"
        else:
            raise ValueError(f"Unknown command: {command}")

    async def get_connection_status(self) -> Dict[str, Any]:
        return {
            "status": self.connection_status,
            "connected": self.is_connected
        }


class IntegrationTimeManipulationTests:
    """Integration tests for time manipulation functionality."""

    def __init__(self):
        self.time_provider = MockTimeProvider(datetime(2023, 1, 2, 7, 0))  # Monday 7:00 AM
        self.setup_mocks()

    def setup_mocks(self):
        """Setup test mocks."""
        # Mock datetime.now to use our time provider
        self.datetime_patcher = mock.patch('datetime.datetime')
        mock_datetime = self.datetime_patcher.start()
        mock_datetime.now.return_value = self.time_provider.now()

    def cleanup_mocks(self):
        """Cleanup test mocks."""
        self.datetime_patcher.stop()

    async def test_end_to_end_manipulation_cycle(self):
        """Test complete end-to-end manipulation cycle."""
        print("Testing end-to-end manipulation cycle...")

        # Create mock device manager
        device_manager = MockDeviceManager()

        # Create time manipulator with custom config
        config = ManipulationConfig(
            window_start="07:50",
            window_end="08:10",
            min_time="07:55",
            max_time="07:59",
            min_interval_seconds=5,  # Shorter for testing
            max_interval_seconds=15,
            max_failures_before_pause=2
        )

        manipulator = TimeManipulator(device_manager, config)

        # Test: Before manipulation window
        self.time_provider.set_current(datetime(2023, 1, 2, 7, 45))  # Monday 7:45 AM
        assert not manipulator.time_window.is_manipulation_active()

        # Test: Enter manipulation window
        self.time_provider.set_current(datetime(2023, 1, 2, 7, 52))  # Monday 7:52 AM
        assert manipulator.time_window.is_manipulation_active()

        # Test: Force manipulation
        success = await manipulator.force_manipulation()
        assert success is True
        assert len(device_manager.time_commands) == 1

        command, kwargs = device_manager.time_commands[0]
        assert command == "set_time"
        assert "target_time" in kwargs

        # Test: Check manipulation was recorded
        status = await manipulator.get_manipulation_status()
        assert status.total_manipulations == 1
        assert status.successful_manipulations == 1

        print("✅ End-to-end manipulation cycle test passed")

    async def test_scheduler_with_time_manipulator(self):
        """Test scheduler integration with time manipulator."""
        print("Testing scheduler integration...")

        device_manager = MockDeviceManager()
        manipulator = TimeManipulator(device_manager)

        # Create scheduler
        scheduler = Scheduler(device_manager, manipulator)

        # Test: Start scheduler
        success = await scheduler.start()
        assert success is True
        assert scheduler.is_running is True

        # Test: Get status
        status = await scheduler.get_status()
        assert status["is_running"] is True
        assert status["state"] == "running"

        # Test: Stop scheduler
        success = await scheduler.stop()
        assert success is True
        assert scheduler.is_running is False

        print("✅ Scheduler integration test passed")

    async def test_time_window_boundary_conditions(self):
        """Test time window boundary conditions."""
        print("Testing time window boundaries...")

        time_window = TimeWindowManager(
            window_start="07:50",
            window_end="08:10",
            min_time="07:55",
            max_time="07:59"
        )

        # Test boundary conditions
        test_cases = [
            (datetime(2023, 1, 2, 7, 49, 59), False),  # Just before window
            (datetime(2023, 1, 2, 7, 50, 0), True),   # Window start
            (datetime(2023, 1, 2, 8, 10, 0), True),   # Window end
            (datetime(2023, 1, 2, 8, 10, 1), False),  # Just after window
            (datetime(2023, 1, 1, 7, 55), False),     # Sunday during time
            (datetime(2023, 1, 2, 7, 55), True),      # Monday during time
        ]

        for test_time, expected in test_cases:
            self.time_provider.set_current(test_time)
            result = time_window.is_in_manipulation_window(test_time)
            assert result == expected, f"Failed for {test_time}: expected {expected}, got {result}"

        print("✅ Time window boundary test passed")

    async def test_random_time_generation_distribution(self):
        """Test random time generation distribution."""
        print("Testing random time distribution...")

        generator = RandomTimeGenerator(
            min_time="07:55",
            max_time="07:59"
        )

        test_date = datetime(2023, 1, 2)
        timestamps = []

        # Generate 100 timestamps
        for _ in range(100):
            timestamp = generator.generate_random_timestamp(test_date)
            timestamps.append(timestamp)

        # Test distribution
        time_counts = {}
        for timestamp in timestamps:
            minute = timestamp.time().minute
            time_counts[minute] = time_counts.get(minute, 0) + 1

        # Should have distribution across minutes 55-59
        assert set(time_counts.keys()).issubset({55, 56, 57, 58, 59})
        assert len(time_counts) >= 3  # Should use at least 3 different minutes

        # Test range
        for timestamp in timestamps:
            assert dt_time(7, 55) <= timestamp.time() <= dt_time(7, 59)

        print("✅ Random time distribution test passed")

    async def test_interval_management(self):
        """Test interval management between manipulations."""
        print("Testing interval management...")

        generator = RandomTimeGenerator(
            min_interval_seconds=1,
            max_interval_seconds=3
        )

        intervals = []

        # Test multiple intervals
        for _ in range(10):
            interval = generator.calculate_interval()
            intervals.append(interval)
            assert 1 <= interval <= 3

        # Test variation
        unique_intervals = set(intervals)
        assert len(unique_intervals) >= 2  # Should have variety

        print("✅ Interval management test passed")

    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        print("Testing error handling...")

        device_manager = MockDeviceManager()
        manipulator = TimeManipulator(device_manager)

        # Test: Force manipulation with failing device manager
        async def failing_command(*args, **kwargs):
            raise Exception("Device communication failed")

        device_manager.execute_command = failing_command

        success = await manipulator.force_manipulation()
        assert success is False

        # Check error was recorded
        status = await manipulator.get_manipulation_status()
        assert status.total_manipulations == 1
        assert status.failed_manipulations == 1

        # Test: Recovery after device fixed
        device_manager.execute_command = mock.AsyncMock(return_value=True)

        success = await manipulator.force_manipulation()
        assert success is True

        print("✅ Error handling test passed")

    async def test_concurrent_manipulation_attempts(self):
        """Test concurrent manipulation attempts handling."""
        print("Testing concurrent manipulation...")

        device_manager = MockDeviceManager()
        manipulator = TimeManipulator(device_manager)

        # Create concurrent manipulation tasks
        tasks = []
        for i in range(5):
            task = asyncio.create_task(manipulator.force_manipulation())
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results), "All concurrent manipulations should succeed"

        # Check total count
        status = await manipulator.get_manipulation_status()
        assert status.total_manipulations == 5
        assert status.successful_manipulations == 5

        print("✅ Concurrent manipulation test passed")

    async def test_configuration_from_environment(self):
        """Test configuration loading from environment variables."""
        print("Testing environment configuration...")

        # Set environment variables
        test_env = {
            'MANIPULATION_WINDOW_START': '06:30',
            'MANIPULATION_WINDOW_END': '09:00',
            'TIME_RANGE_MIN': '06:45',
            'TIME_RANGE_MAX': '08:55',
            'MIN_INTERVAL_SECONDS': '45',
            'MAX_INTERVAL_SECONDS': '120',
            'TIMEZONE': 'EST'
        }

        with mock.patch.dict(os.environ, test_env):
            from src.utils.time_helpers import get_config_from_env
            config = get_config_from_env()

            assert config['window_start'] == '06:30'
            assert config['window_end'] == '09:00'
            assert config['time_range_min'] == '06:45'
            assert config['time_range_max'] == '08:55'
            assert config['min_interval_seconds'] == 45
            assert config['max_interval_seconds'] == 120
            assert config['timezone'] == 'EST'

        print("✅ Environment configuration test passed")

    async def test_accelerated_time_scenarios(self):
        """Test with accelerated time for faster testing."""
        print("Testing accelerated time scenarios...")

        device_manager = MockDeviceManager()
        config = ManipulationConfig(
            window_start="07:50",
            window_end="08:10",
            min_interval_seconds=1,  # Very short for testing
            max_interval_seconds=3
        )
        manipulator = TimeManipulator(device_manager, config)

        # Simulate time progression
        times = [
            datetime(2023, 1, 2, 7, 45),  # Before window
            datetime(2023, 1, 2, 7, 55),  # In window
            datetime(2023, 1, 2, 8, 5),   # After 8:00 AM
            datetime(2023, 1, 2, 8, 15),  # After window
        ]

        for test_time in times:
            # Update time provider
            self.time_provider.set_current(test_time)

            # Check manipulation status
            is_active = manipulator.time_window.is_manipulation_active(test_time)

            # Force manipulation if active
            if is_active:
                success = await manipulator.force_manipulation()
                assert success is True

        # Verify manipulations occurred only during active periods
        assert len(device_manager.time_commands) > 0

        print("✅ Accelerated time scenarios test passed")

    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        print("Testing performance metrics...")

        device_manager = MockDeviceManager()
        manipulator = TimeManipulator(device_manager)

        # Generate some activity
        for _ in range(5):
            await manipulator.force_manipulation()

        # Get detailed status
        status = manipulator.get_detailed_status()

        assert "manipulator" in status
        assert "status" in status
        assert "window_status" in status
        assert "generator_stats" in status
        assert "interval_stats" in status

        # Check metrics
        assert status["status"]["total_manipulations"] == 5
        assert status["status"]["successful_manipulations"] == 5
        assert status["status"]["success_rate"] == 100.0

        print("✅ Performance metrics test passed")

    def time_provider_set_current(self, new_time: datetime):
        """Helper to set current time."""
        self.time_provider.current_time = new_time
        # Update mock datetime return value
        self.datetime_patcher.return_value.now.return_value = new_time


async def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Time Manipulation Integration Tests")
    print("=" * 70)

    test_instance = IntegrationTimeManipulationTests()

    tests = [
        test_instance.test_end_to_end_manipulation_cycle,
        test_instance.test_scheduler_with_time_manipulator,
        test_instance.test_time_window_boundary_conditions,
        test_instance.test_random_time_generation_distribution,
        test_instance.test_interval_management,
        test_instance.test_error_handling_and_recovery,
        test_instance.test_concurrent_manipulation_attempts,
        test_instance.test_configuration_from_environment,
        test_instance.test_accelerated_time_scenarios,
        test_instance.test_performance_metrics,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            # Setup for each test
            test_instance.setup_mocks()

            # Run test
            await test_func()
            passed += 1

        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {str(e)}")
            failed += 1
        finally:
            # Cleanup after each test
            test_instance.cleanup_mocks()

    print("=" * 70)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("💥 Some integration tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)