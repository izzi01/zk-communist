"""Scheduler for ZK-Communist Time Liberation Server.

This module provides continuous monitoring and coordination services
for the time manipulation system with efficient sleep cycles.
"""

import asyncio
import logging
import signal
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..services.device_manager import DeviceManager
from ..services.time_manipulator import TimeManipulator
from ..utils.time_helpers import get_config_from_env


class SchedulerState(Enum):
    """Scheduler operational states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class SchedulerMetrics:
    """Scheduler performance and operational metrics."""
    start_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    total_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    last_cycle_time: Optional[datetime] = None
    average_cycle_duration: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class SchedulerConfig:
    """Configuration for scheduler operation."""
    health_check_interval: int = 60  # seconds
    metrics_collection_interval: int = 300  # seconds
    graceful_shutdown_timeout: int = 30  # seconds
    max_restart_attempts: int = 3
    restart_delay: int = 10  # seconds
    enable_auto_restart: bool = True
    log_level: str = "INFO"
    enable_performance_monitoring: bool = True


class Scheduler:
    """Main scheduler for coordinating time manipulation operations.

    Provides continuous monitoring, health checks, and lifecycle management
    for the ZK-Communist Time Liberation Server.
    """

    def __init__(self,
                 device_manager: DeviceManager,
                 time_manipulator: TimeManipulator,
                 config: Optional[SchedulerConfig] = None):
        """Initialize scheduler.

        Args:
            device_manager: Device manager for device communication
            time_manipulator: Time manipulator for time operations
            config: Optional scheduler configuration
        """
        self.device_manager = device_manager
        self.time_manipulator = time_manipulator
        self.logger = logging.getLogger(__name__)

        # Load configuration
        if config is None:
            self.config = SchedulerConfig()
        else:
            self.config = config

        # State management
        self._state = SchedulerState.STOPPED
        self._shutdown_event = asyncio.Event()
        self._restart_count = 0
        self._should_restart = False

        # Task tracking
        self._scheduler_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Metrics
        self.metrics = SchedulerMetrics()

        # Callbacks for custom event handling
        self._callbacks: Dict[str, Callable] = {}

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        self.logger.info("Scheduler initialized with configuration: "
                        f"health_check_interval={self.config.health_check_interval}s, "
                        f"auto_restart={self.config.enable_auto_restart}")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            # Signal handlers only work in main thread
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, self._signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception as e:
            self.logger.warning(f"Could not setup signal handlers: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())

    async def start(self) -> bool:
        """Start the scheduler.

        Returns:
            True if started successfully, False otherwise
        """
        if self._state != SchedulerState.STOPPED:
            self.logger.warning(f"Scheduler already in state: {self._state.value}")
            return False

        self._state = SchedulerState.STARTING
        self._shutdown_event.clear()
        self.metrics.start_time = datetime.now()

        self.logger.info("Starting scheduler")

        try:
            # Start device manager if not already connected
            if not self.device_manager.is_connected:
                self.logger.info("Connecting device manager")
                # Note: In production, credentials should come from secure storage
                device_connected = await self.device_manager.connect(
                    ip_address="192.168.1.100",  # Should come from config
                    port=4370,
                    credentials={"password": "default"}  # Should come from secure storage
                )
                if not device_connected:
                    raise RuntimeError("Failed to connect device manager")

            # Start background tasks
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            if self.config.enable_performance_monitoring:
                self._metrics_task = asyncio.create_task(self._metrics_loop())

            # Start time manipulation cycle
            await self.time_manipulator.start_manipulation_cycle()

            self._state = SchedulerState.RUNNING
            self.logger.info("Scheduler started successfully")

            # Trigger start callback
            await self._trigger_callback("on_start")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            self._state = SchedulerState.ERROR
            return False

    async def stop(self) -> bool:
        """Stop the scheduler gracefully.

        Returns:
            True if stopped successfully, False otherwise
        """
        if self._state == SchedulerState.STOPPED:
            return True

        self._state = SchedulerState.STOPPING
        self.logger.info("Stopping scheduler")

        try:
            # Set shutdown event
            self._shutdown_event.set()

            # Stop time manipulation
            await self.time_manipulator.stop_manipulation_cycle()

            # Cancel background tasks with timeout
            tasks_to_cancel = [
                self._scheduler_task,
                self._health_check_task,
                self._metrics_task
            ]

            for task in tasks_to_cancel:
                if task and not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=5.0)
                    except asyncio.TimeoutError:
                        self.logger.warning("Task did not stop gracefully within timeout")
                    except asyncio.CancelledError:
                        pass

            # Disconnect device manager
            if self.device_manager.is_connected:
                await self.device_manager.disconnect()

            self._state = SchedulerState.STOPPED
            self.logger.info("Scheduler stopped successfully")

            # Trigger stop callback
            await self._trigger_callback("on_stop")

            return True

        except Exception as e:
            self.logger.error(f"Error during scheduler shutdown: {e}")
            self._state = SchedulerState.ERROR
            return False

    async def shutdown(self) -> bool:
        """Perform emergency shutdown with shorter timeout.

        Returns:
            True if shutdown completed
        """
        self.logger.info("Performing emergency shutdown")
        return await self.stop()

    async def restart(self) -> bool:
        """Restart the scheduler.

        Returns:
            True if restart successful
        """
        if self._restart_count >= self.config.max_restart_attempts:
            self.logger.error("Max restart attempts exceeded")
            return False

        self.logger.info(f"Restarting scheduler (attempt {self._restart_count + 1})")

        # Stop current instance
        await self.stop()

        # Wait before restart
        await asyncio.sleep(self.config.restart_delay)

        # Increment restart counter
        self._restart_count += 1

        # Start again
        return await self.start()

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop for coordination."""
        self.logger.info("Scheduler loop started")

        try:
            while not self._shutdown_event.is_set():
                cycle_start = time.time()

                try:
                    # Update metrics
                    self.metrics.total_cycles += 1
                    self.metrics.last_cycle_time = datetime.now()

                    # Perform health check of components
                    await self._component_health_check()

                    # Update average cycle duration
                    cycle_duration = time.time() - cycle_start
                    if self.metrics.total_cycles == 1:
                        self.metrics.average_cycle_duration = cycle_duration
                    else:
                        # Exponential moving average for smoother metrics
                        alpha = 0.1
                        self.metrics.average_cycle_duration = (
                            alpha * cycle_duration +
                            (1 - alpha) * self.metrics.average_cycle_duration
                        )

                    self.metrics.successful_cycles += 1

                    # Check if restart is needed
                    if self._should_restart and self.config.enable_auto_restart:
                        self.logger.info("Restart condition detected, initiating restart")
                        await self.restart()
                        self._should_restart = False
                        return

                except Exception as e:
                    self.logger.error(f"Error in scheduler cycle: {e}")
                    self.metrics.failed_cycles += 1

                    # Check if we need to restart due to errors
                    if self.metrics.failed_cycles > 5:  # Too many failures
                        self._should_restart = True

                # Sleep until next cycle
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            self.logger.info("Scheduler loop cancelled")
        except Exception as e:
            self.logger.error(f"Scheduler loop error: {e}")
            self._state = SchedulerState.ERROR
            raise

    async def _component_health_check(self) -> None:
        """Perform health check on all components."""
        # Check device manager health
        if not self.device_manager.is_connected:
            self.logger.warning("Device manager not connected")
            # Could trigger reconnection logic here

        # Check time manipulator health
        if not self.time_manipulator.is_healthy:
            self.logger.warning("Time manipulator unhealthy")

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")

    async def _perform_health_check(self) -> None:
        """Perform comprehensive health check."""
        health_status = {
            "scheduler": self._state.value,
            "device_manager": self.device_manager.is_connected,
            "time_manipulator": self.time_manipulator.is_healthy,
            "uptime_seconds": self._get_uptime(),
            "success_rate": self._get_success_rate()
        }

        # Log health status
        if all(health_status.values()):
            self.logger.debug("All components healthy")
        else:
            self.logger.warning(f"Health check issues detected: {health_status}")

        # Trigger health check callback
        await self._trigger_callback("on_health_check", health_status)

    async def _metrics_loop(self) -> None:
        """Periodic metrics collection loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.metrics_collection_interval)
                await self._collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")

    async def _collect_metrics(self) -> None:
        """Collect performance metrics."""
        if not self.config.enable_performance_monitoring:
            return

        try:
            # Collect memory usage (simplified)
            import psutil
            process = psutil.Process()
            self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            self.metrics.cpu_usage_percent = process.cpu_percent()

            self.logger.debug(f"Metrics - Memory: {self.metrics.memory_usage_mb:.1f}MB, "
                            f"CPU: {self.metrics.cpu_usage_percent:.1f}%")

        except ImportError:
            # psutil not available, skip detailed metrics
            self.logger.debug("psutil not available for detailed metrics")
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")

    async def sleep_with_monitoring(self, seconds: int) -> None:
        """Sleep while monitoring for shutdown events.

        Args:
            seconds: Number of seconds to sleep
        """
        self.logger.debug(f"Sleeping for {seconds} seconds with monitoring")

        start_time = time.time()
        while time.time() - start_time < seconds:
            if self._shutdown_event.is_set():
                self.logger.debug("Sleep interrupted by shutdown event")
                break

            # Sleep in small chunks to remain responsive
            chunk = min(1.0, seconds - (time.time() - start_time))
            if chunk <= 0:
                break
            await asyncio.sleep(chunk)

    def get_next_manipulation_time(self) -> Optional[datetime]:
        """Get next scheduled manipulation time.

        Returns:
            Next manipulation time or None if not available
        """
        return self.time_manipulator.status.next_manipulation_time

    def _get_uptime(self) -> float:
        """Get scheduler uptime in seconds."""
        if self.metrics.start_time:
            return (datetime.now() - self.metrics.start_time).total_seconds()
        return 0.0

    def _get_success_rate(self) -> float:
        """Get operation success rate percentage."""
        if self.metrics.total_cycles == 0:
            return 100.0
        return (self.metrics.successful_cycles / self.metrics.total_cycles) * 100.0

    def register_callback(self, event_name: str, callback: Callable) -> None:
        """Register a callback for scheduler events.

        Args:
            event_name: Event name (e.g., "on_start", "on_stop", "on_health_check")
            callback: Callback function
        """
        self._callbacks[event_name] = callback
        self.logger.debug(f"Registered callback for event: {event_name}")

    async def _trigger_callback(self, event_name: str, *args, **kwargs) -> None:
        """Trigger a registered callback.

        Args:
            event_name: Event to trigger
            *args: Arguments to pass to callback
            **kwargs: Keyword arguments to pass to callback
        """
        callback = self._callbacks.get(event_name)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in callback {event_name}: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive scheduler status.

        Returns:
            Dictionary with scheduler status
        """
        return {
            "state": self._state.value,
            "is_running": self._state == SchedulerState.RUNNING,
            "uptime_seconds": self._get_uptime(),
            "restart_count": self._restart_count,
            "metrics": {
                "total_cycles": self.metrics.total_cycles,
                "successful_cycles": self.metrics.successful_cycles,
                "failed_cycles": self.metrics.failed_cycles,
                "success_rate": self._get_success_rate(),
                "average_cycle_duration": self.metrics.average_cycle_duration,
                "last_cycle_time": self.metrics.last_cycle_time.isoformat() if self.metrics.last_cycle_time else None
            },
            "components": {
                "device_manager": {
                    "connected": self.device_manager.is_connected,
                    "status": await self.device_manager.get_connection_status()
                },
                "time_manipulator": self.time_manipulator.get_detailed_status()
            }
        }

    @property
    def state(self) -> SchedulerState:
        """Get current scheduler state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._state == SchedulerState.RUNNING

    @property
    def uptime(self) -> timedelta:
        """Get scheduler uptime as timedelta."""
        if self.metrics.start_time:
            return datetime.now() - self.metrics.start_time
        return timedelta(0)

    @classmethod
    def create_with_env_config(cls,
                              device_manager: DeviceManager,
                              time_manipulator: TimeManipulator) -> "Scheduler":
        """Create Scheduler with environment-based configuration.

        Args:
            device_manager: Device manager instance
            time_manipulator: Time manipulator instance

        Returns:
            Configured Scheduler instance
        """
        # Could load config from environment here
        config = SchedulerConfig()
        return cls(device_manager, time_manipulator, config)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()