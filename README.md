# Network Monitoring Service

**Internal Network Monitoring and Diagnostics Service**

> **⚠️ Internal Use Only** - This service is designed for internal network monitoring and diagnostic purposes only.

## Overview

The Network Monitoring Service provides comprehensive network monitoring capabilities for enterprise infrastructure. This service operates with minimal system footprint and includes emergency response capabilities for operational safety.

## Features

- **Network Device Monitoring**: Monitor and diagnose network device connectivity
- **Performance Metrics**: Track network latency and performance indicators
- **Emergency Response**: Immediate shutdown capabilities with evidence cleanup
- **Secure Configuration**: Hardware-bound encryption for sensitive data
- **Stealth Operation**: Minimal system footprint and logging for operational security
- **API Integration**: RESTful API for integration with monitoring systems

## Quick Start

### Prerequisites

- Linux operating system (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- Python 3.8 or higher
- Root privileges for service installation
- Network access to target devices

### Installation

```bash
# Clone or extract the service files
tar -xzf network-monitoring.tar.gz
cd network-monitoring

# Run the automated installation
sudo ./scripts/install.sh
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure the service
cp config/config.yaml.template config/config.yaml
# Edit config.yaml with your settings

# Start the service
python src/main.py
```

## Configuration

### Basic Setup

1. **Edit configuration file**:
   ```bash
   nano config/config.yaml
   ```

2. **Configure device settings**:
   ```yaml
   device_config:
     device_ip_encrypted: "aes256:gcm:your_encrypted_device_ip"
     device_port: 4370
   ```

3. **Generate encryption keys**:
   ```bash
   python scripts/generate_keys.py
   ```

### Environment Variables

- `CONFIG_PATH`: Path to configuration file (default: `config/config.yaml`)
- `ENCRYPTION_KEY_PATH`: Path to encryption keys (default: `config/encryption_keys.yaml`)
- `OPERATION_MODE`: Service operation mode (`standalone` | `kubernetes`)
- `KUBERNETES_ENVIRONMENT`: Set to `true` when running in Kubernetes

## API Documentation

### Base URL
```
http://localhost:8012/api/v1
```

### Key Endpoints

- **Health Check**: `GET /api/v1/system/health`
- **Device Status**: `GET /api/v1/device/status`
- **Emergency Stop**: `POST /api/v1/emergency/panic-button`
- **Configuration**: `GET /api/v1/config/status`

For complete API documentation, see [docs/api/README.md](docs/api/README.md).

## Service Management

### Starting and Stopping

```bash
# Using systemctl
sudo systemctl start network-monitoring
sudo systemctl stop network-monitoring
sudo systemctl status network-monitoring

# View logs
sudo journalctl -u network-monitoring -f
```

### Emergency Procedures

```bash
# Emergency shutdown with evidence cleanup
sudo ./scripts/emergency_stop.sh

# Panic button via API
curl -X POST http://localhost:8012/api/v1/emergency/panic-button \
     -H "Content-Type: application/json" \
     -d '{"reason": "Emergency", "immediate": true}'
```

## Development

### Setting Up Development Environment

```bash
# Install Poetry (recommended)
curl -sSL https://install.python-poetry.org | python3 -

# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
pre-commit install

# Run development server with hot reload
uvicorn src.main:app --reload --host 127.0.0.1 --port 8080
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m security      # Security tests only
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

## Security

### Data Protection

- **Encryption**: All sensitive data encrypted with AES-256-GCM
- **Key Management**: Hardware-bound encryption keys
- **Secure Storage**: Encrypted configuration files
- **Memory Protection**: Immediate zeroization of sensitive data

### Access Control

- **API Authentication**: API key-based authentication
- **Network Restrictions**: Limited to authorized IP ranges
- **Service Isolation**: Non-root user execution with minimal privileges
- **Emergency Access**: Unauthenticated emergency endpoints for safety

### Monitoring

- **Log Management**: Automatic log rotation and cleanup
- **Evidence Control**: Minimal evidence generation and retention
- **Security Scanning**: Automated vulnerability scanning
- **Performance Monitoring**: Resource utilization tracking

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   # Check status and logs
   sudo systemctl status network-monitoring
   sudo journalctl -u network-monitoring -n 50
   ```

2. **Permission errors**:
   ```bash
   # Fix file permissions
   sudo chown -R root:root /opt/network-monitoring
   sudo chmod -R 755 /opt/network-monitoring
   ```

3. **Device connection issues**:
   ```bash
   # Test network connectivity
   ping <device_ip>
   nmap -sU -p 4370 <device_ip>
   ```

### Logs and Diagnostics

```bash
# Application logs
tail -f /var/log/network-monitoring/app.log

# System service logs
journalctl -u network-monitoring -f

# Emergency logs
ls /var/log/network-monitoring/emergency/
```

## Support

For technical support:

1. Check the [deployment guide](docs/operations/deployment-guide.md)
2. Review the [API documentation](docs/api/README.md)
3. Check system logs for error details
4. Use emergency procedures if immediate shutdown is required

## License

Internal Use Only - Not for distribution or external deployment.

## Version History

- **v1.0.0**: Initial release with core monitoring capabilities
- **v1.1.0**: Enhanced security features and emergency procedures
- **v1.2.0**: Kubernetes deployment support and GitOps integration

---

**Important**: This service is designed for internal network monitoring only. Ensure proper authorization and security procedures before deployment.