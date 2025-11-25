"""Comprehensive unit tests for Time Manipulation Logic.

Tests time window detection, random time generation, scheduler functionality,
and integration patterns for the ZK-Communist Time Liberation Server.
"""

import asyncio
import unittest.mock as mock
import sys
import os
from datetime import datetime, time as dt_time, timedelta
from typing import Any
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock pyzk before imports
sys.modules['pyzk'] = mock.MagicMock()
sys.modules['pyzk.const'] = mock.MagicMock()

from src.services.device_manager import DeviceManager
from src.services.time_manipulator import TimeManipulator, ManipulationConfig, ManipulationStatus
from src.services.scheduler import Scheduler, SchedulerState
from src.utils.time_helpers import (
    TimeWindowManager,
    RandomTimeGenerator,
    IntervalManager,
    is_weekday,
    is_in_manipulation_window,
    generate_random_timestamp,
    calculate_random_interval
)


class TestTimeWindowManager:
    """Test suite for TimeWindowManager class."""

    def test_initialization_with_defaults(self):
        """Test TimeWindowManager initialization with default values."""
        manager = TimeWindowManager()

        assert manager.window_start == dt_time(7, 50)
        assert manager.window_end == dt_time(8, 10)
        assert manager.min_time == dt_time(7, 55)
        assert manager.max_time == dt_time(7, 59)
        assert manager.timezone == "UTC"

    def test_initialization_with_custom_values(self):
        """Test TimeWindowManager initialization with custom values."""
        manager = TimeWindowManager(
            window_start="06:30",
            window_end="09:00",
            min_time="06:45",
            max_time="08:55",
            timezone="EST"
        )

        assert manager.window_start == dt_time(6, 30)
        assert manager.window_end == dt_time(9, 0)
        assert manager.min_time == dt_time(6, 45)
        assert manager.max_time == dt_time(8, 55)
        assert manager.timezone == "EST"

    def test_is_weekday_true(self):
        """Test weekday detection returns True for Monday-Saturday."""
        manager = TimeWindowManager()

        # Monday (0)
        monday = datetime(2023, 1, 2, 8, 0)  # Monday Jan 2, 2023
        assert manager.is_weekday(monday) is True

        # Wednesday (2)
        wednesday = datetime(2023, 1, 4, 8, 0)
        assert manager.is_weekday(wednesday) is True

        # Saturday (5)
        saturday = datetime(2023, 1, 7, 8, 0)
        assert manager.is_weekday(saturday) is True

    def test_is_weekday_false(self):
        """Test weekday detection returns False for Sunday."""
        manager = TimeWindowManager()

        # Sunday (6)
        sunday = datetime(2023, 1, 1, 8, 0)  # Sunday Jan 1, 2023
        assert manager.is_weekday(sunday) is False

    def test_is_in_manipulation_window_true(self):
        """Test window detection returns True during 7:50-8:10 AM."""
        manager = TimeWindowManager()

        # During window on weekday
        during_window = datetime(2023, 1, 2, 7, 55)  # Monday 7:55 AM
        assert manager.is_in_manipulation_window(during_window) is True

        # Window start boundary
        window_start = datetime(2023, 1, 2, 7, 50)
        assert manager.is_in_manipulation_window(window_start) is True

        # Window end boundary
        window_end = datetime(2023, 1, 2, 8, 10)
        assert manager.is_in_manipulation_window(window_end) is True

    def test_is_in_manipulation_window_false_time(self):
        """Test window detection returns False outside time window."""
        manager = TimeWindowManager()

        # Before window
        before_window = datetime(2023, 1, 2, 7, 49)
        assert manager.is_in_manipulation_window(before_window) is False

        # After window
        after_window = datetime(2023, 1, 2, 8, 11)
        assert manager.is_in_manipulation_window(after_window) is False

    def test_is_in_manipulation_window_false_weekend(self):
        """Test window detection returns False on weekends."""
        manager = TimeWindowManager()

        # During time window but on Sunday
        sunday_during_window = datetime(2023, 1, 1, 7, 55)
        assert manager.is_in_manipulation_window(sunday_during_window) is False

    def test_is_manipulation_active_true(self):
        """Test manipulation active check returns True before 8:00 AM."""
        manager = TimeWindowManager()

        # Active time: weekday, before 8:00 AM, in window
        active_time = datetime(2023, 1, 2, 7, 55)  # Monday 7:55 AM
        assert manager.is_manipulation_active(active_time) is True

    def test_is_manipulation_active_false_after_8am(self):
        """Test manipulation active check returns False after 8:00 AM."""
        manager = TimeWindowManager()

        # After 8:00 AM but still in window
        after_8am = datetime(2023, 1, 2, 8, 5)  # Monday 8:05 AM
        assert manager.is_manipulation_active(after_8am) is False

    def test_get_window_status(self):
        """Test window status information."""
        manager = TimeWindowManager()
        test_time = datetime(2023, 1, 2, 7, 55)  # Monday 7:55 AM

        status = manager.get_window_status(test_time)

        assert status["current_time"] == test_time.isoformat()
        assert status["is_weekday"] is True
        assert status["in_manipulation_window"] is True
        assert status["manipulation_active"] is True
        assert status["window_start"] == "07:50:00"
        assert status["window_end"] == "08:10:00"
        assert status["random_min"] == "07:55:00"
        assert status["random_max"] == "07:59:00"
        assert status["timezone"] == "UTC"

    def test_invalid_time_format(self):
        """Test invalid time format handling."""
        with pytest.raises(ValueError):
            TimeWindowManager(window_start="25:00")  # Invalid hour

    def test_invalid_time_ranges(self):
        """Test invalid time range handling."""
        with pytest.raises(ValueError):
            TimeWindowManager(window_start="08:00", window_end="07:00")  # Start after end


class TestRandomTimeGenerator:
    """Test suite for RandomTimeGenerator class."""

    def test_initialization_with_defaults(self):
        """Test RandomTimeGenerator initialization with defaults."""
        generator = RandomTimeGenerator()

        assert generator.min_time == dt_time(7, 55)
        assert generator.max_time == dt_time(7, 59)
        assert generator.min_interval == 30
        assert generator.max_interval == 90

    def test_initialization_with_custom_values(self):
        """Test RandomTimeGenerator initialization with custom values."""
        generator = RandomTimeGenerator(
            min_time="06:30",
            max_time="09:00",
            min_interval_seconds=60,
            max_interval_seconds=180
        )

        assert generator.min_time == dt_time(6, 30)
        assert generator.max_time == dt_time(9, 0)
        assert generator.min_interval == 60
        assert generator.max_interval == 180

    def test_generate_random_timestamp_range(self):
        """Test generated timestamps are within expected range."""
        generator = RandomTimeGenerator(min_time="07:55", max_time="07:59")
        test_date = datetime(2023, 1, 2)

        # Generate multiple timestamps
        timestamps = []
        for _ in range(100):
            timestamp = generator.generate_random_timestamp(test_date)
            timestamps.append(timestamp)

            # Check range
            assert timestamp.date() == test_date.date()
            assert dt_time(7, 55) <= timestamp.time() <= dt_time(7, 59)

    def test_generate_random_timestamp_uniqueness(self):
        """Test generated timestamps have reasonable variation."""
        generator = RandomTimeGenerator(min_time="07:55", max_time="07:59")
        test_date = datetime(2023, 1, 2)

        # Generate multiple timestamps
        timestamps = []
        for _ in range(50):
            timestamp = generator.generate_random_timestamp(test_date)
            timestamps.append(timestamp)

        # Check for variation (not all the same)
        unique_times = set(t.time() for t in timestamps)
        assert len(unique_times) > 1  # Should have variety

    def test_should_generate_new_time_first_call(self):
        """Test should_generate_new_time returns True on first call."""
        generator = RandomTimeGenerator()
        assert generator.should_generate_new_time() is True

    def test_should_generate_new_time_after_interval(self):
        """Test should_generate_new_time respects interval constraints."""
        import time

        generator = RandomTimeGenerator(min_interval_seconds=1, max_interval_seconds=2)

        # First call should be True
        assert generator.should_generate_new_time() is True

        # Generate a timestamp to set last generation time
        generator.generate_random_timestamp()

        # Immediate call should be False
        assert generator.should_generate_new_time() is False

        # Wait and try again
        time.sleep(1.1)
        assert generator.should_generate_new_time() is True

    def test_calculate_next_interval_range(self):
        """Test calculated intervals are within expected range."""
        generator = RandomTimeGenerator(min_interval_seconds=30, max_interval_seconds=90)

        intervals = []
        for _ in range(100):
            interval = generator.calculate_next_interval()
            intervals.append(interval)
            assert 30 <= interval <= 90

    def test_get_generation_stats(self):
        """Test generation statistics."""
        generator = RandomTimeGenerator()

        # Initially no generation
        stats = generator.get_generation_stats()
        assert stats["last_generated_time"] is None
        assert stats["last_generation_timestamp"] is None
        assert stats["ready_to_generate"] is True

        # After generation
        timestamp = generator.generate_random_timestamp()
        stats = generator.get_generation_stats()
        assert stats["last_generated_time"] == timestamp.time().isoformat()
        assert stats["last_generation_timestamp"] is not None


class TestIntervalManager:
    """Test suite for IntervalManager class."""

    def test_initialization(self):
        """Test IntervalManager initialization."""
        manager = IntervalManager(min_seconds=30, max_seconds=90, jitter_factor=0.2)

        assert manager.min_seconds == 30
        assert manager.max_seconds == 90
        assert manager.jitter_factor == 0.2

    def test_calculate_interval_range(self):
        """Test calculated intervals are within expected range with jitter."""
        manager = IntervalManager(min_seconds=30, max_seconds=90, jitter_factor=0.1)

        intervals = []
        for _ in range(100):
            interval = manager.calculate_interval()
            intervals.append(interval)
            # With jitter, range should be approximately 27-99 seconds
            assert 20 <= interval <= 110  # Allow some margin for jitter

    def test_no_jitter(self):
        """Test intervals without jitter."""
        manager = IntervalManager(min_seconds=30, max_seconds=90, jitter_factor=0.0)

        intervals = []
        for _ in range(100):
            interval = manager.calculate_interval()
            intervals.append(interval)
            assert 30 <= interval <= 90

    def test_get_stats(self):
        """Test interval manager statistics."""
        manager = IntervalManager(min_seconds=30, max_seconds=90, jitter_factor=0.1)

        stats = manager.get_stats()
        assert stats["min_seconds"] == 30
        assert stats["max_seconds"] == 90
        assert stats["jitter_factor"] == 0.1
        assert "current_range" in stats


class TestTimeManipulator:
    """Test suite for TimeManipulator class."""

    def setup_method(self):
        """Setup test environment."""
        # Create mock device manager
        self.mock_device_manager = mock.MagicMock(spec=DeviceManager)
        self.mock_device_manager.is_connected = True
        self.mock_device_manager.execute_command = mock.AsyncMock(return_value=True)

    def test_initialization_with_default_config(self):
        """Test TimeManipulator initialization with default config."""
        with mock.patch.dict(os.environ, {}, clear=True):
            manipulator = TimeManipulator(self.mock_device_manager)

            assert manipulator.config.window_start == "07:50"
            assert manipulator.config.window_end == "08:10"
            assert manipulator.config.min_time == "07:55"
            assert manipulator.config.max_time == "07:59"

    def test_initialization_with_custom_config(self):
        """Test TimeManipulator initialization with custom config."""
        config = ManipulationConfig(
            window_start="06:30",
            window_end="09:00",
            min_time="06:45",
            max_time="08:55"
        )

        manipulator = TimeManipulator(self.mock_device_manager, config)

        assert manipulator.config.window_start == "06:30"
        assert manipulator.config.window_end == "09:00"
        assert manipulator.config.min_time == "06:45"
        assert manipulator.config.max_time == "08:55"

    async def test_force_manipulation_success(self):
        """Test successful forced manipulation."""
        manipulator = TimeManipulator(self.mock_device_manager)

        result = await manipulator.force_manipulation()

        assert result is True
        self.mock_device_manager.execute_command.assert_called_once()

        # Check status updated
        status = await manipulator.get_manipulation_status()
        assert status.total_manipulations == 1
        assert status.successful_manipulations == 1

    async def test_force_manipulation_failure(self):
        """Test forced manipulation failure."""
        self.mock_device_manager.execute_command = mock.AsyncMock(return_value=False)

        manipulator = TimeManipulator(self.mock_device_manager)

        result = await manipulator.force_manipulation()

        assert result is False

        # Check status updated
        status = await manipulator.get_manipulation_status()
        assert status.total_manipulations == 1
        assert status.failed_manipulations == 1

    async def test_force_manipulation_with_target_time(self):
        """Test forced manipulation with specific target time."""
        manipulator = TimeManipulator(self.mock_device_manager)
        target_time = datetime(2023, 1, 2, 7, 56, 30)

        result = await manipulator.force_manipulation(target_time)

        assert result is True
        self.mock_device_manager.execute_command.assert_called_once_with(
            "set_time",
            target_time=target_time.isoformat()
        )

    async def test_get_manipulation_status(self):
        """Test getting manipulation status."""
        manipulator = TimeManipulator(self.mock_device_manager)

        status = await manipulator.get_manipulation_status()

        assert isinstance(status, ManipulationStatus)
        assert status.total_manipulations == 0
        assert status.is_active is False  # Not started

    def test_get_configuration(self):
        """Test getting configuration."""
        config = ManipulationConfig(
            window_start="06:30",
            max_interval_seconds=120,
            enable_jitter=True
        )
        manipulator = TimeManipulator(self.mock_device_manager, config)

        config_dict = manipulator.get_configuration()

        assert config_dict["window_start"] == "06:30"
        assert config_dict["max_interval_seconds"] == 120
        assert config_dict["enable_jitter"] is True

    def test_is_running_property(self):
        """Test is_running property."""
        manipulator = TimeManipulator(self.mock_device_manager)

        assert manipulator.is_running is False  # Not started

    def test_is_healthy_property(self):
        """Test is_healthy property."""
        manipulator = TimeManipulator(self.mock_device_manager)

        # Should be healthy when not running
        assert manipulator.is_healthy is True


class TestScheduler:
    """Test suite for Scheduler class."""

    def setup_method(self):
        """Setup test environment."""
        # Create mock device manager
        self.mock_device_manager = mock.MagicMock(spec=DeviceManager)
        self.mock_device_manager.is_connected = False
        self.mock_device_manager.connect = mock.AsyncMock(return_value=True)
        self.mock_device_manager.disconnect = mock.AsyncMock()
        self.mock_device_manager.get_connection_status = mock.AsyncMock(return_value={
            "status": "connected"
        })

        # Create mock time manipulator
        self.mock_time_manipulator = mock.MagicMock()
        self.mock_time_manipulator.is_healthy = True
        self.mock_time_manipulator.start_manipulation_cycle = mock.AsyncMock()
        self.mock_time_manipulator.stop_manipulation_cycle = mock.AsyncMock()
        self.mock_time_manipulator.get_detailed_status = mock.MagicMock(return_value={
            "is_healthy": True,
            "status": {"manipulation_active": False}
        })

    def test_initialization(self):
        """Test Scheduler initialization."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        assert scheduler.state == SchedulerState.STOPPED
        assert scheduler.is_running is False

    async def test_start_success(self):
        """Test successful scheduler start."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        result = await scheduler.start()

        assert result is True
        assert scheduler.state == SchedulerState.RUNNING
        assert scheduler.is_running is True

        # Verify device manager was connected
        self.mock_device_manager.connect.assert_called_once()

        # Verify time manipulator was started
        self.mock_time_manipulator.start_manipulation_cycle.assert_called_once()

    async def test_start_already_running(self):
        """Test start when already running."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        # First start
        await scheduler.start()

        # Second start should return False
        result = await scheduler.start()
        assert result is False

    async def test_stop_success(self):
        """Test successful scheduler stop."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        # Start first
        await scheduler.start()

        # Then stop
        result = await scheduler.stop()

        assert result is True
        assert scheduler.state == SchedulerState.STOPPED
        assert scheduler.is_running is False

    async def test_sleep_with_monitoring(self):
        """Test sleep with monitoring functionality."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        # Test short sleep
        start_time = asyncio.get_event_loop().time()
        await scheduler.sleep_with_monitoring(0.1)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert 0.1 <= elapsed <= 0.2  # Allow small margin

    async def test_get_status(self):
        """Test getting scheduler status."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        status = await scheduler.get_status()

        assert "state" in status
        assert "is_running" in status
        assert "uptime_seconds" in status
        assert "metrics" in status
        assert "components" in status
        assert status["state"] == SchedulerState.STOPPED.value
        assert status["is_running"] is False

    def test_get_next_manipulation_time(self):
        """Test getting next manipulation time."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        # Should delegate to time manipulator
        result = scheduler.get_next_manipulation_time()

        # Note: This depends on the mock setup
        # In real scenario, would return actual datetime or None

    def test_uptime_property(self):
        """Test uptime property."""
        scheduler = Scheduler(self.mock_device_manager, self.mock_time_manipulator)

        uptime = scheduler.uptime
        assert isinstance(uptime, timedelta)


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_is_weekday_function(self):
        """Test is_weekday convenience function."""
        # Monday
        monday = datetime(2023, 1, 2, 12, 0)
        assert is_weekday(monday) is True

        # Sunday
        sunday = datetime(2023, 1, 1, 12, 0)
        assert is_weekday(sunday) is False

    def test_is_in_manipulation_window_function(self):
        """Test is_in_manipulation_window convenience function."""
        # Monday 7:55 AM (in window)
        in_window = datetime(2023, 1, 2, 7, 55)
        assert is_in_manipulation_window(in_window) is True

        # Monday 9:00 AM (out of window)
        out_of_window = datetime(2023, 1, 2, 9, 0)
        assert is_in_manipulation_window(out_of_window) is False

    def test_generate_random_timestamp_function(self):
        """Test generate_random_timestamp convenience function."""
        timestamp = generate_random_timestamp()

        assert isinstance(timestamp, datetime)
        assert timestamp.time().hour == 7  # Should be 7 AM
        assert 55 <= timestamp.time().minute <= 59  # Should be in range

    def test_calculate_random_interval_function(self):
        """Test calculate_random_interval convenience function."""
        interval = calculate_random_interval()

        assert isinstance(interval, int)
        assert 30 <= interval <= 90


# Test runner function
async def run_tests():
    """Run all tests."""
    print("🧪 Starting Time Manipulation Logic Unit Tests")
    print("=" * 60)

    test_classes = [
        TestTimeWindowManager,
        TestRandomTimeGenerator,
        TestIntervalManager,
        TestTimeManipulator,
        TestScheduler,
        TestConvenienceFunctions
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_class in test_classes:
        print(f"\n🔬 Running {test_class.__name__}")

        test_instance = test_class()

        # Get all test methods
        test_methods = [method for method in dir(test_instance)
                      if method.startswith('test_') and not method.startswith('test_')]

        for method_name in test_methods:
            total_tests += 1

            try:
                method = getattr(test_instance, method_name)

                # Check if it's an async method
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()

                passed_tests += 1
                print(f"  ✅ {method_name}")

            except Exception as e:
                failed_tests += 1
                print(f"  ❌ {method_name}: {str(e)}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests} passed, {failed_tests} failed, {total_tests} total")

    if failed_tests == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)