"""
Pytest configuration and fixtures for ZK-Communist tests.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config_manager import ConfigurationManager
from src.core.device_manager import ZKDeviceManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def config_manager(temp_config_dir):
    """Create a configuration manager instance with temporary directory."""
    config = ConfigurationManager()
    # Override paths for testing
    config.config_path = str(temp_config_dir / "config.yaml")
    config.encryption_key_path = str(temp_config_dir / "encryption_keys.yaml")
    return config


@pytest.fixture
async def initialized_config_manager(config_manager):
    """Initialize configuration manager for testing."""
    await config_manager.initialize()
    return config_manager


@pytest.fixture
def device_manager():
    """Create a device manager instance for testing."""
    return ZKDeviceManager()


@pytest.fixture
async def initialized_device_manager(device_manager):
    """Initialize device manager for testing."""
    await device_manager.initialize("192.168.1.100", 4370, 5000)
    return device_manager


@pytest.fixture
def mock_device_connection():
    """Mock device connection for testing."""
    with patch('src.core.device_manager.socket') as mock_socket:
        mock_socket.inet_aton.return_value = True
        yield mock_socket


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "system_config": {
            "api_port": 8012,
            "bind_address": "0.0.0.0",
            "service_name": "network-monitoring.service",
            "environment": "testing"
        },
        "device_config": {
            "device_port": 4370,
            "device_model": "ZMM210_TFT",
            "connection_timeout": 5000,
            "retry_attempts": 3
        },
        "security_config": {
            "encryption_algorithm": "AES-256-GCM",
            "key_derivation": "hardware_fingerprint"
        }
    }


@pytest.fixture
def mock_hardware_fingerprint():
    """Mock hardware fingerprint for testing."""
    return "test_hardware_fingerprint_12345"


@pytest.fixture
def mock_encryption_key():
    """Mock encryption key for testing."""
    return "test_encryption_key_32bytes_long"


@pytest.fixture
def mock_zk_device():
    """Mock ZK device for testing."""
    device = Mock()
    device.connect.return_value = True
    device.disable_device.return_value = True
    device.enable_device.return_value = True
    device.disconnect.return_value = True
    return device


# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
    config.addinivalue_line(
        "markers", "infrastructure: Infrastructure tests"
    )


@pytest.fixture(scope="session")
def test_environment_setup():
    """Set up test environment variables."""
    # Store original values
    original_env = {}
    test_env_vars = {
        "CONFIG_PATH": "/tmp/test_config.yaml",
        "ENCRYPTION_KEY_PATH": "/tmp/test_encryption_keys.yaml",
        "OPERATION_MODE": "testing",
        "KUBERNETES_ENVIRONMENT": "false",
        "LOG_LEVEL": "DEBUG"
    }

    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    # Cleanup can be added here if needed


# Async test helper
@pytest.fixture
def async_test():
    """Helper fixture for async tests."""
    def wrapper(async_func):
        def sync_func(*args, **kwargs):
            return asyncio.run(async_func(*args, **kwargs))
        return sync_func
    return wrapper