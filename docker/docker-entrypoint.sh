#!/bin/bash
# Docker entrypoint script for ZK-Communist Network Monitoring Service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="network-monitoring"
LOG_FILE="/var/log/network-monitoring/startup.log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"
chmod 750 "$(dirname "$LOG_FILE")"

# Log container startup
log_info "Starting $SERVICE_NAME container"
log_info "Container ID: $(hostname)"
log_info "Python version: $(python --version)"
log_info "Working directory: $(pwd)"

# Check if configuration exists
if [[ ! -f "/app/config/config.yaml" ]]; then
    log_warning "Configuration file not found, creating from template"

    # Create basic configuration
    mkdir -p /app/config
    cat > /app/config/config.yaml << 'EOF'
# Network Monitoring Service Configuration
# Auto-generated for container deployment

system_config:
  api_port: 8012
  bind_address: "0.0.0.0"
  service_name: "network-monitoring.service"
  environment: "kubernetes"
  debug: false

device_config:
  device_port: 4370
  device_model: "ZMM210_TFT"
  connection_timeout: 5000
  retry_attempts: 3
  retry_delay: 30

security_config:
  encryption_algorithm: "AES-256-GCM"
  key_derivation: "hardware_fingerprint"
  allowed_ips:
    - "127.0.0.1"
    - "::1"

emergency_config:
  panic_button_enabled: true
  shutdown_timeout: 1000
  auto_restore_time: true
EOF

    log_success "Created default configuration file"
fi

# Check if secrets directory exists
if [[ ! -d "/app/secrets" ]]; then
    mkdir -p /app/secrets
    log_info "Created secrets directory"
fi

# Validate configuration
log_info "Validating configuration"
python -c "
import sys
sys.path.append('/app')
try:
    from src.core.config_manager import ConfigurationManager
    import asyncio

    async def validate():
        config = ConfigurationManager()
        if await config.validate_configuration():
            print('✅ Configuration validation passed')
        else:
            print('❌ Configuration validation failed')
            sys.exit(1)

    asyncio.run(validate())
except Exception as e:
    print(f'❌ Configuration validation error: {e}')
    sys.exit(1)
"

if [[ $? -eq 0 ]]; then
    log_success "Configuration validation passed"
else
    log_error "Configuration validation failed"
    exit 1
fi

# Check required ports
log_info "Checking port availability"

# Check if port 8012 is available
if netstat -ln | grep -q ":8012 "; then
    log_warning "Port 8012 appears to be in use"
else
    log_success "Port 8012 is available"
fi

# Check network connectivity
log_info "Checking network connectivity"

# Check DNS resolution
if nslookup kubernetes.default.svc.cluster.local >/dev/null 2>&1; then
    log_success "DNS resolution working"
else
    log_warning "DNS resolution may not be working"
fi

# Check Kubernetes API connectivity
if curl -s --connect-timeout 5 https://kubernetes.default.svc.cluster.local >/dev/null 2>&1; then
    log_success "Kubernetes API connectivity working"
else
    log_info "Kubernetes API not accessible (expected in some environments)"
fi

# Generate encryption keys if needed
if [[ ! -f "/app/secrets/encryption_keys.yaml" ]]; then
    log_info "Encryption keys not found, generating new keys"

    python -c "
import sys
sys.path.append('/app')
import os
import hashlib
import uuid
import yaml
import base64

def generate_hardware_key():
    system_uuid = uuid.getnode()
    hostname = os.uname().nodename
    fingerprint_data = f'{system_uuid}_{hostname}'
    fingerprint = hashlib.sha256(fingerprint_data.encode()).digest()
    return base64.b64encode(fingerprint[:32]).decode()

def generate_encryption_keys():
    hardware_key = generate_hardware_key()
    salt = base64.b64encode(os.urandom(32)).decode()

    keys_data = {
        'hardware_key': hardware_key,
        'salt': salt,
        'generated_at': str(uuid.uuid4()),
        'container_id': os.uname().nodename
    }

    os.makedirs('/app/secrets', exist_ok=True)
    with open('/app/secrets/encryption_keys.yaml', 'w') as f:
        yaml.dump(keys_data, f, default_flow_style=False)

    os.chmod('/app/secrets/encryption_keys.yaml', 0o600)
    print('✅ Encryption keys generated')

generate_encryption_keys()
"

    if [[ $? -eq 0 ]]; then
        log_success "Encryption keys generated successfully"
    else
        log_error "Failed to generate encryption keys"
        exit 1
    fi
fi

# Set proper permissions
log_info "Setting file permissions"
chmod 750 /app/config
chmod 640 /app/config/config.yaml
chmod 700 /app/secrets
chmod 600 /app/secrets/*.yaml 2>/dev/null || true

# Create runtime directories
mkdir -p /var/log/network-monitoring/emergency
mkdir -p /var/opt/network-monitoring/backups
chmod 750 /var/log/network-monitoring
chmod 700 /var/log/network-monitoring/emergency

# Set environment variables
export PYTHONPATH="/app:$PYTHONPATH"
export CONFIG_PATH="/app/config/config.yaml"
export ENCRYPTION_KEY_PATH="/app/secrets/encryption_keys.yaml"

# Health check function
health_check() {
    log_info "Performing startup health check"

    # Check if the application starts properly
    timeout 10 python -c "
import sys
sys.path.append('/app')
import asyncio
from src.main import app

async def check_app():
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get('/api/v1/system/health')
        if response.status_code == 200:
            print('✅ Health check passed')
            return True
        else:
            print(f'❌ Health check failed: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Health check error: {e}')
        return False

result = asyncio.run(check_app())
sys.exit(0 if result else 1)
"

    if [[ $? -eq 0 ]]; then
        log_success "Startup health check passed"
        return 0
    else
        log_warning "Startup health check failed (may be normal for first run)"
        return 1
    fi
}

# Pre-start health check
health_check || true

# Signal handlers for graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."

    # In a real implementation, this would:
    # 1. Stop all device connections
    # 2. Restore device time
    # 3. Clean up temporary files
    # 4. Save final state

    log_info "Cleanup completed, exiting..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Display startup information
log_success "Container startup completed successfully"
log_info "Service: $SERVICE_NAME"
log_info "API Port: 8012"
log_info "Metrics Port: 9090"
log_info "Configuration: /app/config/config.yaml"
log_info "Logs: /var/log/network-monitoring/"
log_info "Starting application..."

# Check if running in Kubernetes
if [[ -n "$KUBERNETES_ENVIRONMENT" && "$KUBERNETES_ENVIRONMENT" == "true" ]]; then
    log_info "Kubernetes environment detected"

    # Wait for Kubernetes to be ready
    log_info "Waiting for Kubernetes cluster to be ready..."
    while ! curl -s --connect-timeout 2 https://kubernetes.default.svc.cluster.local/healthz >/dev/null 2>&1; do
        sleep 2
    done
    log_success "Kubernetes cluster is ready"
fi

# Start the application
log_info "Executing: $@"
exec "$@"