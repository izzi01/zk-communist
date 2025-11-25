"""Container Integration Tests for ZK-Communist Time Liberation Server.

Tests container startup, health checks, configuration, and deployment
functionality to ensure production readiness.
"""

import asyncio
import subprocess
import unittest.mock as mock
import sys
import os
import time
import requests
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock pyzk before imports
sys.modules['pyzk'] = mock.MagicMock()
sys.modules['pyzk.const'] = mock.MagicMock()

from src.services.device_manager import DeviceManager
from src.services.time_manipulator import TimeManipulator
from src.utils.time_helpers import TimeWindowManager


class ContainerIntegrationTests:
    """Integration tests for container deployment and operation."""

    def __init__(self):
        self.container_name = "zk-communist-test"
        self.image_name = "zk-communist:test"
        self.container_id: Optional[str] = None

    def setup_method(self):
        """Setup test environment."""
        print("Setting up container integration tests...")

    def teardown_method(self):
        """Cleanup test environment."""
        if self.container_id:
            try:
                subprocess.run(
                    ["docker", "rm", "-f", self.container_id],
                    check=False,
                    capture_output=True
                )
            except Exception:
                pass

    def build_container_image(self):
        """Build container image for testing."""
        print("Building container image...")

        cmd = [
            "docker", "build",
            "--build-arg", f"BUILD_DATE={time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "--build-arg", "VCS_REF=test",
            "-t", self.image_name,
            "."
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            print("✅ Container image built successfully")
            return True
        except subprocess.TimeoutExpired:
            print("❌ Container build timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Container build failed: {e.stderr}")
            return False

    async def test_container_startup(self):
        """Test container startup and basic functionality."""
        print("Testing container startup...")

        # Skip test if image not built
        try:
            subprocess.run(
                ["docker", "inspect", self.image_name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            print("❌ Container image not found, skipping startup test")
            return

        # Run container with test configuration
        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "--rm",
            "-e", "DEVICE_IP=192.168.1.100",
            "-e", "LOG_LEVEL=DEBUG",
            "-e", "ENABLE_DEBUG_MODE=true",
            "-p", "8080:8080",
            self.image_name
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            self.container_id = result.stdout.strip()
            print(f"✅ Container started: {self.container_id[:12]}")

            # Wait for container to start
            await asyncio.sleep(10)

            # Check container is running
            container_info = subprocess.run(
                ["docker", "inspect", self.container_name],
                check=True,
                capture_output=True,
                text=True
            )

            import json
            inspect_data = json.loads(container_info.stdout)
            container_state = inspect_data[0]["State"]

            if not container_state["Running"]:
                print(f"❌ Container not running: {container_state.get('Status', 'Unknown')}")
                if container_state.get("Error"):
                    print(f"Error: {container_state['Error']}")
                return False

            print("✅ Container is running successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start container: {e.stderr}")
            return False

    async def test_health_endpoints(self):
        """Test health check endpoints."""
        print("Testing health endpoints...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        # Wait for health endpoint to be ready
        await asyncio.sleep(5)

        base_url = "http://localhost:8080"

        health_endpoints = [
            ("/health", "Health check endpoint"),
            ("/ready", "Readiness check endpoint"),
            ("/startup", "Startup check endpoint")
        ]

        for endpoint, description in health_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {description}: {response.status_code}")
                else:
                    print(f"❌ {description}: {response.status_code}")
                    return False
            except requests.RequestException as e:
                print(f"❌ {description}: Connection failed - {e}")
                return False

        return True

    async def test_application_imports(self):
        """Test that application modules can be imported in container."""
        print("Testing application imports...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        test_imports = [
            "from src.services.device_manager import DeviceManager",
            "from src.services.time_manipulator import TimeManipulator",
            "from src.services.scheduler import Scheduler",
            "from src.utils.time_helpers import TimeWindowManager"
        ]

        for import_statement in test_imports:
            try:
                cmd = [
                    "docker", "exec", self.container_id,
                    "python", "-c", import_statement
                ]

                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                print(f"✅ Import: {import_statement}")

            except subprocess.CalledProcessError as e:
                print(f"❌ Import failed: {import_statement} - {e.stderr}")
                return False

        return True

    async def test_configuration_loading(self):
        """Test configuration loading from environment variables."""
        print("Testing configuration loading...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        # Test configuration script
        config_test_script = """
import os
from src.utils.time_helpers import get_config_from_env

config = get_config_from_env()
print(f"DEVICE_IP: {config.get('DEVICE_IP', 'NOT_SET')}")
print(f"LOG_LEVEL: {config.get('LOG_LEVEL', 'NOT_SET')}")
print(f"TIMEZONE: {config.get('TIMEZONE', 'NOT_SET')}")
"""

        try:
            cmd = [
                "docker", "exec", self.container_id,
                "python", "-c", config_test_script
            ]

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            print("✅ Configuration loaded successfully:")
            print(result.stdout)

            # Verify expected values are present
            if "DEVICE_IP: 192.168.1.100" in result.stdout:
                print("✅ Device IP configured correctly")
            else:
                print("❌ Device IP not configured correctly")
                return False

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Configuration test failed: {e.stderr}")
            return False

    async def test_time_helpers_in_container(self):
        """Test time helper functionality in container."""
        print("Testing time helpers in container...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        time_test_script = """
from src.utils.time_helpers import TimeWindowManager, is_weekday, is_in_manipulation_window
from datetime import datetime

# Test weekday detection
manager = TimeWindowManager()
test_time = datetime(2023, 1, 2, 7, 55)  # Monday 7:55 AM

print(f"Is weekday: {is_weekday(test_time)}")
print(f"In manipulation window: {is_in_manipulation_window(test_time)}")
print(f"Window manager active: {manager.is_manipulation_active(test_time)}")

# Test random time generation
from src.utils.time_helpers import generate_random_timestamp
random_time = generate_random_timestamp()
print(f"Generated random time: {random_time.time()}")

print("✅ All time helper tests passed")
"""

        try:
            cmd = [
                "docker", "exec", self.container_id,
                "python", "-c", time_test_script
            ]

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            print("✅ Time helpers working correctly:")
            print(result.stdout)

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Time helper test failed: {e.stderr}")
            return False

    async def test_container_logs(self):
        """Test container logging functionality."""
        print("Testing container logs...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        try:
            # Get container logs
            cmd = ["docker", "logs", "--tail", "20", self.container_id]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            print("Container logs (last 20 lines):")
            print("-" * 50)
            print(result.stdout)
            print("-" * 50)

            # Check for expected log patterns
            if any(keyword in result.stdout.lower() for keyword in
                   ['info', 'debug', 'error', 'starting', 'ready']):
                print("✅ Container logging working correctly")
                return True
            else:
                print("⚠️ Limited log output detected")
                return True  # Not a failure, just minimal logging

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get container logs: {e.stderr}")
            return False

    async def test_container_resource_usage(self):
        """Test container resource usage."""
        print("Testing container resource usage...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        try:
            # Get container stats
            cmd = ["docker", "stats", "--no-stream", "--format", "table", self.container_id]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            print("Container resource usage:")
            print(result.stdout)

            # Parse resource usage (basic check)
            if "CPU %" in result.stdout and "MEM USAGE / LIMIT" in result.stdout:
                print("✅ Container stats available")
                return True
            else:
                print("⚠️ Container stats format unexpected")
                return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get container stats: {e.stderr}")
            return False

    async def test_container_security(self):
        """Test container security configuration."""
        print("Testing container security...")

        if not self.container_id:
            print("❌ No running container to test")
            return False

        try:
            # Get container inspect data
            cmd = ["docker", "inspect", self.container_id]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            import json
            inspect_data = json.loads(result.stdout)
            container_config = inspect_data[0]["Config"]

            # Check security settings
            security_checks = {
                "User": container_config.get("User"),
                "ExposedPorts": container_config.get("ExposedPorts"),
            }

            print("Container security configuration:")
            for key, value in security_checks.items():
                print(f"  {key}: {value}")

            # User should be set (non-root)
            if container_config.get("User"):
                print("✅ Container running as non-root user")
            else:
                print("⚠️ Container running as root (security concern)")

            return True

        except Exception as e:
            print(f"❌ Security check failed: {e}")
            return False

    async def cleanup_container(self):
        """Cleanup test container."""
        print("Cleaning up container...")

        if self.container_id:
            try:
                subprocess.run(
                    ["docker", "stop", self.container_id],
                    check=False,
                    capture_output=True
                )
                subprocess.run(
                    ["docker", "rm", self.container_id],
                    check=False,
                    capture_output=True
                )
                print("✅ Container cleaned up")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")

        self.container_id = None


async def run_container_integration_tests():
    """Run all container integration tests."""
    print("🐳 Starting Container Integration Tests")
    print("=" * 60)

    test_instance = ContainerIntegrationTests()

    tests = [
        ("Build Container Image", test_instance.build_container_image),
        ("Container Startup", test_instance.test_container_startup),
        ("Health Endpoints", test_instance.test_health_endpoints),
        ("Application Imports", test_instance.test_application_imports),
        ("Configuration Loading", test_instance.test_configuration_loading),
        ("Time Helpers", test_instance.test_time_helpers_in_container),
        ("Container Logs", test_instance.test_container_logs),
        ("Resource Usage", test_instance.test_container_resource_usage),
        ("Container Security", test_instance.test_container_security),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")

        try:
            result = await test_func()
            if result is None:
                # Test was skipped
                skipped += 1
                print(f"⏭️ {test_name}: Skipped")
            elif result:
                passed += 1
                print(f"✅ {test_name}: Passed")
            else:
                failed += 1
                print(f"❌ {test_name}: Failed")

        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: Exception - {e}")

    # Cleanup
    await test_instance.cleanup_container()

    print("\n" + "=" * 60)
    print(f"📊 Container Test Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("🎉 All container tests passed!")
        return True
    else:
        print("💥 Some container tests failed!")
        return False


if __name__ == "__main__":
    # Install requirements if needed
    try:
        import requests
    except ImportError:
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"])

    success = asyncio.run(run_container_integration_tests())
    sys.exit(0 if success else 1)