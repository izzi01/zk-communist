"""Time Manipulator for ZK-Communist Time Liberation Server.

This module implements the core time manipulation functionality that protects
workers from unjust attendance penalties by randomly setting device time
during critical morning windows.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..services.device_manager import DeviceManager
from ..utils.time_helpers import (
    TimeWindowManager,
    RandomTimeGenerator,
    IntervalManager,
    get_config_from_env
)


@dataclass
class ManipulationStatus:
    """Current manipulation status information."""
    is_active: bool = False
    in_window: bool = False
    is_weekday: bool = False
    current_time: Optional[datetime] = None
    last_manipulation_time: Optional[datetime] = None
    total_manipulations: int = 0
    successful_manipulations: int = 0
    failed_manipulations: int = 0
    next_manipulation_time: Optional[datetime] = None


@dataclass
class ManipulationConfig:
    """Configuration for time manipulation."""
    window_start: str = "07:50"
    window_end: str = "08:10"
    min_time: str = "07:55"
    max_time: str = "07:59"
    min_interval_seconds: int = 30
    max_interval_seconds: int = 90
    timezone: str = "UTC"
    enable_jitter: bool = True
    jitter_factor: float = 0.1
    max_failures_before_pause: int = 3
    failure_pause_duration: int = 300  # 5 minutes


class TimeManipulator:
    """Core time manipulation service for worker protection.

    Intelligently manipulates device time during 7:50-8:10 AM window
    on weekdays to protect workers from attendance exploitation.
    """

    def __init__(self,
                 device_manager: DeviceManager,
                 config: Optional[ManipulationConfig] = None):
        """Initialize time manipulator.

        Args:
            device_manager: Device manager for setting device time
            config: Optional configuration (uses environment variables if None)
        """
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)

        # Load configuration
        if config is None:
            env_config = get_config_from_env()
            self.config = ManipulationConfig(**env_config)
        else:
            self.config = config

        # Initialize components
        self.time_window = TimeWindowManager(
            window_start=self.config.window_start,
            window_end=self.config.window_end,
            min_time=self.config.min_time,
            max_time=self.config.max_time,
            timezone=self.config.timezone
        )

        self.time_generator = RandomTimeGenerator(
            min_time=self.config.min_time,
            max_time=self.config.max_time,
            min_interval_seconds=self.config.min_interval_seconds,
            max_interval_seconds=self.config.max_interval_seconds
        )

        self.interval_manager = IntervalManager(
            min_seconds=self.config.min_interval_seconds,
            max_seconds=self.config.max_interval_seconds,
            jitter_factor=self.config.jitter_factor if self.config.enable_jitter else 0.0
        )

        # Status tracking
        self.status = ManipulationStatus()
        self._running = False
        self._manipulation_task: Optional[asyncio.Task] = None
        self._consecutive_failures = 0

        self.logger.info("TimeManipulator initialized with config: "
                        f"window={self.config.window_start}-{self.config.window_end}, "
                        f"random_range={self.config.min_time}-{self.config.max_time}")

    async def start_manipulation_cycle(self) -> None:
        """Start continuous manipulation cycle."""
        if self._running:
            self.logger.warning("Manipulation cycle already running")
            return

        self._running = True
        self._consecutive_failures = 0
        self.status.is_active = True

        self.logger.info("Starting time manipulation cycle")

        self._manipulation_task = asyncio.create_task(self._manipulation_loop())

    async def stop_manipulation_cycle(self) -> None:
        """Stop manipulation cycle and cleanup."""
        if not self._running:
            return

        self.logger.info("Stopping time manipulation cycle")
        self._running = False
        self.status.is_active = False

        if self._manipulation_task:
            self._manipulation_task.cancel()
            try:
                await self._manipulation_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Time manipulation cycle stopped")

    async def _manipulation_loop(self) -> None:
        """Main manipulation loop."""
        self.logger.info("Manipulation loop started")

        try:
            while self._running:
                current_time = datetime.now()

                # Update status
                self._update_status(current_time)

                # Check if manipulation should be active
                if self.time_window.is_manipulation_active(current_time):
                    await self._perform_manipulation(current_time)
                elif self.time_window.is_in_manipulation_window(current_time):
                    # In window but after 8:00 AM - wait for window to end
                    self.logger.debug("In manipulation window but after 8:00 AM - waiting")
                    await self._sleep_until_window_end(current_time)
                else:
                    # Not in window - sleep until next window
                    self.logger.debug("Not in manipulation window - sleeping until next")
                    await self._sleep_until_next_window(current_time)

        except asyncio.CancelledError:
            self.logger.info("Manipulation loop cancelled")
        except Exception as e:
            self.logger.error(f"Manipulation loop error: {e}")
            raise

    async def _perform_manipulation(self, current_time: datetime) -> None:
        """Perform time manipulation if needed.

        Args:
            current_time: Current time for decision making
        """
        # Check if enough time has passed since last manipulation
        if not self.time_generator.should_generate_new_time():
            self.logger.debug("Not enough time elapsed since last manipulation")
            return

        # Check if we've had too many failures
        if self._consecutive_failures >= self.config.max_failures_before_pause:
            self.logger.warning(f"Too many consecutive failures ({self._consecutive_failures}), "
                              f"pausing for {self.config.failure_pause_duration} seconds")
            await asyncio.sleep(self.config.failure_pause_duration)
            self._consecutive_failures = 0

        try:
            # Generate random timestamp
            random_time = self.time_generator.generate_random_timestamp(current_time)

            self.logger.info(f"Setting device time to: {random_time.isoformat()}")

            # Set device time via device manager
            success = await self.device_manager.execute_command(
                "set_time",
                target_time=random_time.isoformat()
            )

            if success:
                self._consecutive_failures = 0
                self.status.last_manipulation_time = current_time
                self.status.successful_manipulations += 1
                self.logger.info(f"Successfully set device time to {random_time.isoformat()}")
            else:
                self._consecutive_failures += 1
                self.status.failed_manipulations += 1
                self.logger.error("Failed to set device time")

        except Exception as e:
            self._consecutive_failures += 1
            self.status.failed_manipulations += 1
            self.logger.error(f"Error during manipulation: {e}")

        self.status.total_manipulations += 1

        # Calculate next interval and sleep
        if self._running:
            interval = self.interval_manager.calculate_interval()
            self.status.next_manipulation_time = current_time + timedelta(seconds=interval)
            await asyncio.sleep(interval)

    async def _sleep_until_window_end(self, current_time: datetime) -> None:
        """Sleep until manipulation window ends.

        Args:
            current_time: Current time
        """
        # Calculate time until window end
        window_end_datetime = current_time.replace(
            hour=self.time_window.window_end.hour,
            minute=self.time_window.window_end.minute,
            second=0,
            microsecond=0
        )

        sleep_duration = (window_end_datetime - current_time).total_seconds()

        if sleep_duration > 0:
            self.logger.debug(f"Sleeping {sleep_duration:.1f} seconds until window end")
            await asyncio.sleep(sleep_duration)

    async def _sleep_until_next_window(self, current_time: datetime) -> None:
        """Sleep until next manipulation window.

        Args:
            current_time: Current time
        """
        # Calculate time until next window (tomorrow if after today's window)
        tomorrow = current_time + timedelta(days=1)
        next_window_start = tomorrow.replace(
            hour=self.time_window.window_start.hour,
            minute=self.time_window.window_start.minute,
            second=0,
            microsecond=0
        )

        sleep_duration = (next_window_start - current_time).total_seconds()

        if sleep_duration > 0:
            hours = int(sleep_duration // 3600)
            minutes = int((sleep_duration % 3600) // 60)
            self.logger.info(f"Sleeping {hours}h {minutes}m until next manipulation window")
            await asyncio.sleep(sleep_duration)

    def _update_status(self, current_time: datetime) -> None:
        """Update manipulation status.

        Args:
            current_time: Current time for status update
        """
        self.status.current_time = current_time
        self.status.is_weekday = self.time_window.is_weekday(current_time)
        self.status.in_window = self.time_window.is_in_manipulation_window(current_time)

    async def get_manipulation_status(self) -> ManipulationStatus:
        """Get current manipulation status.

        Returns:
            Current manipulation status
        """
        self._update_status(datetime.now())
        return self.status

    async def force_manipulation(self, target_time: Optional[datetime] = None) -> bool:
        """Force a manipulation operation (for testing).

        Args:
            target_time: Optional target time (generates random if None)

        Returns:
            True if successful, False otherwise
        """
        try:
            if target_time is None:
                target_time = self.time_generator.generate_random_timestamp()

            self.logger.info(f"Forcing device time to: {target_time.isoformat()}")

            success = await self.device_manager.execute_command(
                "set_time",
                target_time=target_time.isoformat()
            )

            if success:
                self.status.last_manipulation_time = datetime.now()
                self.status.successful_manipulations += 1
            else:
                self.status.failed_manipulations += 1

            return success

        except Exception as e:
            self.logger.error(f"Error in forced manipulation: {e}")
            self.status.failed_manipulations += 1
            return False

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "window_start": self.config.window_start,
            "window_end": self.config.window_end,
            "random_time_range": f"{self.config.min_time}-{self.config.max_time}",
            "interval_range": f"{self.config.min_interval_seconds}-{self.config.max_interval_seconds}s",
            "timezone": self.config.timezone,
            "enable_jitter": self.config.enable_jitter,
            "jitter_factor": self.config.jitter_factor,
            "max_failures_before_pause": self.config.max_failures_before_pause,
            "failure_pause_duration": self.config.failure_pause_duration
        }

    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed manipulation status including components.

        Returns:
            Detailed status dictionary
        """
        return {
            "manipulator": {
                "is_running": self._running,
                "consecutive_failures": self._consecutive_failures
            },
            "status": {
                "is_active": self.status.is_active,
                "in_window": self.status.in_window,
                "is_weekday": self.status.is_weekday,
                "current_time": self.status.current_time.isoformat() if self.status.current_time else None,
                "last_manipulation": self.status.last_manipulation_time.isoformat() if self.status.last_manipulation_time else None,
                "next_manipulation": self.status.next_manipulation_time.isoformat() if self.status.next_manipulation_time else None,
                "total_manipulations": self.status.total_manipulations,
                "successful_manipulations": self.status.successful_manipulations,
                "failed_manipulations": self.status.failed_manipulations,
                "success_rate": (
                    self.status.successful_manipulations / max(self.status.total_manipulations, 1) * 100
                )
            },
            "window_status": self.time_window.get_window_status(),
            "generator_stats": self.time_generator.get_generation_stats(),
            "interval_stats": self.interval_manager.get_stats()
        }

    @property
    def is_running(self) -> bool:
        """Check if manipulation cycle is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    @property
    def is_healthy(self) -> bool:
        """Check if manipulator is healthy.

        Returns:
            True if healthy (running and low failure rate), False otherwise
        """
        if not self._running:
            return False

        if self.status.total_manipulations == 0:
            return True  # Haven't failed any manipulations yet

        failure_rate = self.status.failed_manipulations / self.status.total_manipulations
        return failure_rate < 0.1  # Less than 10% failure rate

    @classmethod
    def create_with_env_config(cls, device_manager: DeviceManager) -> "TimeManipulator":
        """Create TimeManipulator with environment-based configuration.

        Args:
            device_manager: Device manager instance

        Returns:
            Configured TimeManipulator instance
        """
        env_config = get_config_from_env()
        config = ManipulationConfig(**env_config)
        return cls(device_manager, config)