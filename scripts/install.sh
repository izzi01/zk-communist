#!/bin/bash
# ZK-Communist Time Liberation Server Installation Script
# Disguised as network monitoring service installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation constants
SERVICE_NAME="network-monitoring"
INSTALL_DIR="/opt/zk-communist"
SERVICE_USER="root"
LOG_DIR="/var/log/network-monitoring"
BACKUP_DIR="/var/opt/network-monitoring"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking installation prerequisites..."

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        log_error "Python 3.8 or higher is required (found $python_version)"
        exit 1
    fi

    # Check systemd
    if ! command -v systemctl &> /dev/null; then
        log_error "systemd is not available"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

create_directories() {
    log_info "Creating directory structure..."

    # Create main installation directory
    mkdir -p "$INSTALL_DIR"
    chmod 750 "$INSTALL_DIR"

    # Create log directory
    mkdir -p "$LOG_DIR"
    mkdir -p "$LOG_DIR/emergency"
    chmod 750 "$LOG_DIR"
    chmod 700 "$LOG_DIR/emergency"

    # Create backup directory
    mkdir -p "$BACKUP_DIR/backups"
    chmod 750 "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR/backups"

    log_success "Directory structure created"
}

copy_files() {
    log_info "Copying application files..."

    # Get the current script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

    # Copy application files
    cp -r "$PROJECT_DIR/src" "$INSTALL_DIR/"
    cp -r "$PROJECT_DIR/config" "$INSTALL_DIR/"
    cp -r "$PROJECT_DIR/scripts" "$INSTALL_DIR/"
    cp -r "$PROJECT_DIR/docs" "$INSTALL_DIR/"

    # Copy requirements file
    if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
        cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"
    fi

    # Set proper permissions
    chmod -R 644 "$INSTALL_DIR/src"/*.py
    chmod -R 644 "$INSTALL_DIR/config"/*
    chmod +x "$INSTALL_DIR/scripts"/*.sh
    chmod 750 "$INSTALL_DIR"

    log_success "Application files copied"
}

install_dependencies() {
    log_info "Installing Python dependencies..."

    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi

    # Install dependencies
    if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
        pip3 install -r "$INSTALL_DIR/requirements.txt"
    else
        log_warning "requirements.txt not found, installing basic dependencies"
        pip3 install fastapi==0.104.1 uvicorn pydantic python-multipart
    fi

    log_success "Python dependencies installed"
}

setup_systemd_service() {
    log_info "Setting up systemd service..."

    # Copy systemd service file
    cp "$INSTALL_DIR/config/systemd/network-monitoring.service" /etc/systemd/system/

    # Reload systemd daemon
    systemctl daemon-reload

    # Enable the service
    systemctl enable "$SERVICE_NAME.service"

    log_success "Systemd service configured"
}

generate_encryption_keys() {
    log_info "Generating encryption keys..."

    # Create encryption key generation script if it doesn't exist
    if [[ ! -f "$INSTALL_DIR/scripts/generate_keys.py" ]]; then
        cat > "$INSTALL_DIR/scripts/generate_keys.py" << 'EOF'
#!/usr/bin/env python3
"""
Generate encryption keys for ZK-Communist configuration.
"""

import os
import hashlib
import uuid
import yaml
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def generate_hardware_key():
    """Generate hardware-bound encryption key."""
    # Get system information for hardware fingerprint
    system_uuid = uuid.getnode()
    hostname = os.uname().nodename

    # Create hardware fingerprint
    fingerprint_data = f"{system_uuid}_{hostname}"
    fingerprint = hashlib.sha256(fingerprint_data.encode()).digest()

    return fingerprint[:32]  # 256-bit key

def generate_encryption_keys():
    """Generate and save encryption keys."""
    hardware_key = generate_hardware_key()

    # Generate salt for key derivation
    salt = os.urandom(32)

    # Save keys (in production, this would be more secure)
    keys_data = {
        'hardware_key': base64.b64encode(hardware_key).decode(),
        'salt': base64.b64encode(salt).decode(),
        'generated_at': str(os.datetime.now())
    }

    # Save to encrypted file
    key_file = '/opt/zk-communist/config/encryption_keys.yaml'
    with open(key_file, 'w') as f:
        yaml.dump(keys_data, f, default_flow_style=False)

    # Set secure permissions
    os.chmod(key_file, 0o600)

    print("✅ Encryption keys generated successfully")
    print(f"🔑 Keys saved to: {key_file}")

if __name__ == "__main__":
    generate_encryption_keys()
EOF
        chmod +x "$INSTALL_DIR/scripts/generate_keys.py"
    fi

    # Generate keys
    python3 "$INSTALL_DIR/scripts/generate_keys.py"

    log_success "Encryption keys generated"
}

configure_firewall() {
    log_info "Configuring firewall rules..."

    # Configure firewall for service port (8012)
    if command -v ufw &> /dev/null; then
        # UFW firewall
        ufw allow 8012/tcp comment "Network monitoring service"
        log_success "UFW firewall configured"
    elif command -v firewall-cmd &> /dev/null; then
        # firewalld
        firewall-cmd --permanent --add-port=8012/tcp
        firewall-cmd --reload
        log_success "Firewalld configured"
    else
        log_warning "No supported firewall found, manual configuration may be required"
    fi
}

create_configuration() {
    log_info "Setting up initial configuration..."

    CONFIG_FILE="$INSTALL_DIR/config/config.yaml"

    # Create initial configuration from template
    if [[ -f "$INSTALL_DIR/config/config.yaml.template" ]]; then
        cp "$INSTALL_DIR/config/config.yaml.template" "$CONFIG_FILE"

        # Set proper permissions
        chmod 640 "$CONFIG_FILE"

        log_success "Configuration template created"
        log_warning "Please edit $CONFIG_FILE and encrypt sensitive values"
    else
        log_warning "Configuration template not found"
    fi
}

start_service() {
    log_info "Starting network monitoring service..."

    # Start the service
    systemctl start "$SERVICE_NAME.service"

    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        log_success "Service started successfully"
    else
        log_error "Service failed to start"
        systemctl status "$SERVICE_NAME.service"
        exit 1
    fi
}

show_status() {
    log_info "Installation completed successfully!"
    echo
    echo "📁 Installation directory: $INSTALL_DIR"
    echo "📋 Configuration file: $INSTALL_DIR/config/config.yaml"
    echo "📝 Log directory: $LOG_DIR"
    echo "⚙️  Service status: $(systemctl is-active $SERVICE_NAME.service)"
    echo
    echo "🔧 Useful commands:"
    echo "  Check service status: systemctl status $SERVICE_NAME"
    echo "  View logs: journalctl -u $SERVICE_NAME -f"
    echo "  Restart service: systemctl restart $SERVICE_NAME"
    echo "  Stop service: systemctl stop $SERVICE_NAME"
    echo
    echo "⚠️  Next steps:"
    echo "  1. Edit configuration file: $INSTALL_DIR/config/config.yaml"
    echo "  2. Encrypt sensitive configuration values"
    echo "  3. Test device connectivity"
    echo "  4. Configure monitoring and alerting"
}

# Main installation flow
main() {
    echo "🚀 ZK-Communist Time Liberation Server Installation"
    echo "🔍 Disguised as Network Monitoring Service"
    echo

    check_prerequisites
    create_directories
    copy_files
    install_dependencies
    setup_systemd_service
    generate_encryption_keys
    configure_firewall
    create_configuration
    start_service
    show_status
}

# Error handling
trap 'log_error "Installation failed on line $LINENO"' ERR

# Run main function
main "$@"