"""Time helper utilities for ZK-Communist Time Liberation Server.

This module provides time window detection, random timestamp generation,
and interval management for protecting workers from attendance exploitation.
"""

import random
import time
from datetime import datetime, time as dt_time, timedelta
from typing import Tuple, Optional
import logging
import os


class TimeWindowManager:
    """Manages time window detection and validation for worker protection."""

    def __init__(self,
                 window_start: str = "07:50",
                 window_end: str = "08:10",
                 min_time: str = "07:55",
                 max_time: str = "07:59",
                 timezone: str = "UTC"):
        """Initialize time window manager.

        Args:
            window_start: Start of manipulation window (HH:MM format)
            window_end: End of manipulation window (HH:MM format)
            min_time: Minimum random time to generate (HH:MM format)
            max_time: Maximum random time to generate (HH:MM format)
            timezone: Timezone for time calculations
        """
        self.logger = logging.getLogger(__name__)

        # Parse time strings
        self.window_start = self._parse_time(window_start)
        self.window_end = self._parse_time(window_end)
        self.min_time = self._parse_time(min_time)
        self.max_time = self._parse_time(max_time)
        self.timezone = timezone

        # Validate time ranges
        self._validate_time_ranges()

        self.logger.info(f"TimeWindowManager initialized: window={window_start}-{window_end}, "
                        f"random_range={min_time}-{max_time}, timezone={timezone}")

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string in HH:MM format."""
        try:
            return dt_time.fromisoformat(time_str)
        except ValueError as e:
            raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM format.") from e

    def _validate_time_ranges(self) -> None:
        """Validate that time ranges make sense."""
        if self.window_start >= self.window_end:
            raise ValueError("Window start time must be before end time")

        if self.min_time >= self.max_time:
            raise ValueError("Minimum time must be before maximum time")

        if not (self.window_start <= self.min_time <= self.max_time <= self.window_end):
            self.logger.warning("Random time range extends beyond manipulation window boundaries")

    def is_weekday(self, current_time: Optional[datetime] = None) -> bool:
        """Check if current time is Monday-Saturday.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if Monday-Saturday, False if Sunday
        """
        if current_time is None:
            current_time = datetime.now()

        # Monday=0, Sunday=6
        return current_time.weekday() < 6

    def is_in_manipulation_window(self, current_time: Optional[datetime] = None) -> bool:
        """Check if current time is within manipulation window.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if within 7:50-8:10 AM window on weekday
        """
        if current_time is None:
            current_time = datetime.now()

        # Check if weekday first
        if not self.is_weekday(current_time):
            return False

        # Check if time is within window
        current_time_only = current_time.time()

        return self.window_start <= current_time_only <= self.window_end

    def is_manipulation_active(self, current_time: Optional[datetime] = None) -> bool:
        """Check if manipulation should be active (in window and before 8:00 AM).

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if manipulation should be active
        """
        if current_time is None:
            current_time = datetime.now()

        if not self.is_weekday(current_time):
            return False

        current_time_only = current_time.time()

        # Only active if before 8:00 AM to avoid changing already valid timestamps
        eight_am = dt_time(8, 0)

        return (self.window_start <= current_time_only < eight_am and
                self.is_in_manipulation_window(current_time))

    def get_window_status(self, current_time: Optional[datetime] = None) -> dict:
        """Get detailed window status information.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            Dictionary with window status details
        """
        if current_time is None:
            current_time = datetime.now()

        return {
            "current_time": current_time.isoformat(),
            "is_weekday": self.is_weekday(current_time),
            "in_manipulation_window": self.is_in_manipulation_window(current_time),
            "manipulation_active": self.is_manipulation_active(current_time),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "random_min": self.min_time.isoformat(),
            "random_max": self.max_time.isoformat(),
            "timezone": self.timezone
        }


class RandomTimeGenerator:
    """Generates random timestamps within specified ranges for worker protection."""

    def __init__(self,
                 min_time: str = "07:55",
                 max_time: str = "07:59",
                 min_interval_seconds: int = 30,
                 max_interval_seconds: int = 90):
        """Initialize random time generator.

        Args:
            min_time: Minimum time to generate (HH:MM format)
            max_time: Maximum time to generate (HH:MM format)
            min_interval_seconds: Minimum interval between generations
            max_interval_seconds: Maximum interval between generations
        """
        self.logger = logging.getLogger(__name__)

        # Parse time bounds
        self.min_time = self._parse_time(min_time)
        self.max_time = self._parse_time(max_time)
        self.min_interval = min_interval_seconds
        self.max_interval = max_interval_seconds

        # Track last generated timestamp to avoid repeats
        self._last_generated_time: Optional[dt_time] = None
        self._last_generation_time: Optional[float] = None

        # Validate bounds
        self._validate_bounds()

        self.logger.info(f"RandomTimeGenerator initialized: range={min_time}-{max_time}, "
                        f"interval={min_interval_seconds}-{max_interval_seconds}s")

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string in HH:MM format."""
        try:
            return dt_time.fromisoformat(time_str)
        except ValueError as e:
            raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM format.") from e

    def _validate_bounds(self) -> None:
        """Validate time and interval bounds."""
        if self.min_time >= self.max_time:
            raise ValueError("Minimum time must be before maximum time")

        if self.min_interval <= 0 or self.max_interval <= 0:
            raise ValueError("Intervals must be positive")

        if self.min_interval > self.max_interval:
            raise ValueError("Minimum interval must be <= maximum interval")

    def generate_random_timestamp(self, current_date: Optional[datetime] = None) -> datetime:
        """Generate random timestamp within configured range.

        Args:
            current_date: Date to use for timestamp (defaults to now)

        Returns:
            Random datetime within 7:55-7:59 AM range
        """
        if current_date is None:
            current_date = datetime.now()

        # Calculate total seconds between min and max time
        min_datetime = current_date.replace(
            hour=self.min_time.hour,
            minute=self.min_time.minute,
            second=0,
            microsecond=0
        )

        max_datetime = current_date.replace(
            hour=self.max_time.hour,
            minute=self.max_time.minute,
            second=59,  # Include 59th second
            microsecond=0
        )

        # Calculate total seconds in range
        total_seconds = int((max_datetime - min_datetime).total_seconds()) + 1

        # Generate random offset
        random_offset = random.randint(0, total_seconds - 1)
        random_datetime = min_datetime + timedelta(seconds=random_offset)

        # Avoid generating the exact same time as last time (with some tolerance)
        if self._last_generated_time:
            time_diff = abs((random_datetime.time() - self._last_generated_time).total_seconds())
            if time_diff < 1:  # If difference is less than 1 second
                # Add small random offset to ensure uniqueness
                random_datetime += timedelta(seconds=random.uniform(1, 5))

                # Ensure we don't exceed max time
                if random_datetime > max_datetime:
                    random_datetime = min_datetime  # Reset to min time
                    random_datetime += timedelta(seconds=random_offset)  # Regenerate

        self._last_generated_time = random_datetime.time()
        self._last_generation_time = time.time()

        self.logger.debug(f"Generated random timestamp: {random_datetime.isoformat()}")

        return random_datetime

    def should_generate_new_time(self, check_interval: bool = True) -> bool:
        """Check if enough time has passed to generate new timestamp.

        Args:
            check_interval: Whether to check time interval constraints

        Returns:
            True if ready to generate new timestamp
        """
        if not check_interval:
            return True

        if self._last_generation_time is None:
            return True

        elapsed = time.time() - self._last_generation_time

        # Use minimum interval as baseline
        return elapsed >= self.min_interval

    def calculate_next_interval(self) -> int:
        """Calculate next interval in seconds.

        Returns:
            Random interval between min and max seconds
        """
        interval = random.randint(self.min_interval, self.max_interval)

        self.logger.debug(f"Next interval calculated: {interval} seconds")

        return interval

    def get_generation_stats(self) -> dict:
        """Get statistics about time generation.

        Returns:
            Dictionary with generation statistics
        """
        return {
            "last_generated_time": self._last_generated_time.isoformat() if self._last_generated_time else None,
            "last_generation_timestamp": self._last_generation_time,
            "time_range": f"{self.min_time.isoformat()}-{self.max_time.isoformat()}",
            "interval_range": f"{self.min_interval}-{self.max_interval}s",
            "ready_to_generate": self.should_generate_new_time()
        }


class IntervalManager:
    """Manages variable intervals between time manipulation operations."""

    def __init__(self,
                 min_seconds: int = 30,
                 max_seconds: int = 90,
                 jitter_factor: float = 0.1):
        """Initialize interval manager.

        Args:
            min_seconds: Minimum interval duration
            max_seconds: Maximum interval duration
            jitter_factor: Random jitter factor (0.0-1.0) for added unpredictability
        """
        self.logger = logging.getLogger(__name__)

        if min_seconds <= 0 or max_seconds <= 0:
            raise ValueError("Interval durations must be positive")

        if min_seconds > max_seconds:
            raise ValueError("Minimum interval must be <= maximum interval")

        if not 0.0 <= jitter_factor <= 1.0:
            raise ValueError("Jitter factor must be between 0.0 and 1.0")

        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self.jitter_factor = jitter_factor

        self.logger.info(f"IntervalManager initialized: {min_seconds}-{max_seconds}s "
                        f"with jitter factor {jitter_factor}")

    def calculate_interval(self) -> int:
        """Calculate next interval with jitter.

        Returns:
            Interval duration in seconds
        """
        # Calculate base interval
        base_interval = random.randint(self.min_seconds, self.max_seconds)

        # Apply jitter
        jitter_range = int(base_interval * self.jitter_factor)
        jitter = random.randint(-jitter_range, jitter_range)

        # Calculate final interval
        final_interval = max(1, base_interval + jitter)  # Ensure at least 1 second

        self.logger.debug(f"Calculated interval: base={base_interval}s, jitter={jitter}s, "
                        f"final={final_interval}s")

        return final_interval

    def get_stats(self) -> dict:
        """Get interval manager statistics.

        Returns:
            Dictionary with interval statistics
        """
        return {
            "min_seconds": self.min_seconds,
            "max_seconds": self.max_seconds,
            "jitter_factor": self.jitter_factor,
            "current_range": f"{self.max_seconds - int(self.max_seconds * self.jitter_factor)}-"
                           f"{self.max_seconds + int(self.max_seconds * self.jitter_factor)}s"
        }


# Convenience functions for backward compatibility and ease of use
def is_weekday(current_time: Optional[datetime] = None) -> bool:
    """Check if current time is Monday-Saturday."""
    manager = TimeWindowManager()
    return manager.is_weekday(current_time)


def is_in_manipulation_window(current_time: Optional[datetime] = None) -> bool:
    """Check if current time is within manipulation window."""
    manager = TimeWindowManager()
    return manager.is_in_manipulation_window(current_time)


def generate_random_timestamp() -> datetime:
    """Generate random timestamp between 7:55-7:59 AM."""
    generator = RandomTimeGenerator()
    return generator.generate_random_timestamp()


def calculate_random_interval(min_seconds: int = 30, max_seconds: int = 90) -> int:
    """Calculate random interval between min and max seconds."""
    manager = IntervalManager(min_seconds, max_seconds)
    return manager.calculate_interval()


# Environment-based configuration
def get_config_from_env() -> dict:
    """Load time manipulation configuration from environment variables.

    Returns:
        Dictionary with configuration values
    """
    config = {
        "window_start": os.getenv("MANIPULATION_WINDOW_START", "07:50"),
        "window_end": os.getenv("MANIPULATION_WINDOW_END", "08:10"),
        "time_range_min": os.getenv("TIME_RANGE_MIN", "07:55"),
        "time_range_max": os.getenv("TIME_RANGE_MAX", "07:59"),
        "min_interval_seconds": int(os.getenv("MIN_INTERVAL_SECONDS", 30)),
        "max_interval_seconds": int(os.getenv("MAX_INTERVAL_SECONDS", 90)),
        "timezone": os.getenv("TIMEZONE", "UTC")
    }

    return config