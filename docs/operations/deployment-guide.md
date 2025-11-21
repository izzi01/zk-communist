# Network Monitoring Service Deployment Guide

**Internal Infrastructure Documentation**

## Overview

This guide covers the deployment of the Network Monitoring Service for enterprise network monitoring and diagnostics. The service is designed for stealth operation with minimal system footprint.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- **Python**: 3.8 or higher
- **Memory**: Minimum 128MB RAM
- **Storage**: Minimum 50MB disk space
- **Network**: UDP port 4370 access for device communication
- **Privileges**: Root access for systemd service installation

### Software Dependencies
- Python 3.8+ with pip
- systemd (for service management)
- Firewall configuration access
- Network access to target devices

## Installation Methods

### Method 1: Automated Installation (Recommended)

1. **Download the installation package:**
   ```bash
   # Extract the service files
   tar -xzf zk-communist.tar.gz
   cd zk-communist
   ```

2. **Run the installation script:**
   ```bash
   sudo ./scripts/install.sh
   ```

3. **Verify installation:**
   ```bash
   sudo systemctl status network-monitoring
   ```

### Method 2: Manual Installation

1. **Create directories:**
   ```bash
   sudo mkdir -p /opt/zk-communist
   sudo mkdir -p /var/log/network-monitoring
   sudo mkdir -p /var/opt/network-monitoring
   ```

2. **Copy application files:**
   ```bash
   sudo cp -r src/ config/ scripts/ docs/ /opt/zk-communist/
   sudo chmod -R 755 /opt/zk-communist
   ```

3. **Install Python dependencies:**
   ```bash
   sudo pip3 install -r requirements.txt
   ```

4. **Configure systemd service:**
   ```bash
   sudo cp config/systemd/network-monitoring.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable network-monitoring
   ```

5. **Start the service:**
   ```bash
   sudo systemctl start network-monitoring
   ```

## Configuration

### Basic Configuration

1. **Edit the configuration file:**
   ```bash
   sudo nano /opt/zk-communist/config/config.yaml
   ```

2. **Configure essential settings:**
   ```yaml
   system_config:
     api_port: 8012
     bind_address: "0.0.0.0"

   device_config:
     device_ip_encrypted: "aes256:gcm:encrypted_device_ip"
     device_port: 4370

   security_config:
     api_key_encrypted: "aes256:gcm:encrypted_api_key"
   ```

### Encryption Setup

1. **Generate encryption keys:**
   ```bash
   sudo python3 /opt/zk-communist/scripts/generate_keys.py
   ```

2. **Encrypt sensitive values:**
   ```bash
   # Use the encryption utility to encrypt device IPs and API keys
   sudo python3 /opt/zk-communist/scripts/encrypt_config.py
   ```

### Firewall Configuration

1. **Configure UFW (Ubuntu):**
   ```bash
   sudo ufw allow 8012/tcp comment "Network monitoring service"
   sudo ufw allow 4370/udp comment "Device communication"
   ```

2. **Configure firewalld (CentOS/RHEL):**
   ```bash
   sudo firewall-cmd --permanent --add-port=8012/tcp
   sudo firewall-cmd --permanent --add-port=4370/udp
   sudo firewall-cmd --reload
   ```

## Service Management

### Starting and Stopping

```bash
# Start the service
sudo systemctl start network-monitoring

# Stop the service
sudo systemctl stop network-monitoring

# Restart the service
sudo systemctl restart network-monitoring

# Check service status
sudo systemctl status network-monitoring
```

### Monitoring the Service

```bash
# View real-time logs
sudo journalctl -u network-monitoring -f

# View recent logs
sudo journalctl -u network-monitoring --since "1 hour ago"

# Check service health
curl http://localhost:8012/api/v1/system/health
```

### Emergency Procedures

1. **Emergency Shutdown:**
   ```bash
   # Immediate shutdown with evidence cleanup
   sudo /opt/zk-communist/scripts/emergency_stop.sh
   ```

2. **Panic Button API:**
   ```bash
   # Emergency shutdown via API (no authentication required)
   curl -X POST http://localhost:8012/api/v1/emergency/panic-button \
        -H "Content-Type: application/json" \
        -d '{"reason": "Emergency shutdown", "immediate": true}'
   ```

## Troubleshooting

### Common Issues

1. **Service fails to start:**
   ```bash
   # Check service status for error details
   sudo systemctl status network-monitoring

   # View detailed logs
   sudo journalctl -u network-monitoring -n 50
   ```

2. **Port already in use:**
   ```bash
   # Check what's using port 8012
   sudo netstat -tlnp | grep 8012

   # Kill conflicting processes
   sudo kill -9 <PID>
   ```

3. **Permission denied errors:**
   ```bash
   # Check file permissions
   ls -la /opt/zk-communist/

   # Fix permissions if needed
   sudo chown -R root:root /opt/zk-communist
   sudo chmod -R 755 /opt/zk-communist
   ```

4. **Device connection issues:**
   ```bash
   # Test network connectivity
   ping <device_ip>

   # Check UDP port access
   sudo nmap -sU -p 4370 <device_ip>
   ```

### Log Analysis

```bash
# View application logs
sudo tail -f /var/log/network-monitoring/app.log

# View emergency logs
sudo ls -la /var/log/network-monitoring/emergency/
sudo cat /var/log/network-monitoring/emergency/emergency_*.log

# Check systemd logs
sudo journalctl -u network-monitoring --since "today"
```

### Performance Monitoring

```bash
# Check resource usage
sudo top -p $(pgrep -f "python3.*src/main.py")

# Check memory usage
sudo ps aux | grep python3

# Monitor network connections
sudo netstat -tlnp | grep 8012
```

## Maintenance

### Regular Maintenance Tasks

1. **Log rotation:** Automatically handled by logrotate configuration
2. **Backup configuration:** Daily automated backups
3. **Security updates:** Regular system package updates
4. **Performance monitoring:** Check resource utilization weekly

### Updates and Upgrades

1. **Backup current configuration:**
   ```bash
   sudo cp -r /opt/zk-communist/config /tmp/config-backup
   ```

2. **Stop the service:**
   ```bash
   sudo systemctl stop network-monitoring
   ```

3. **Update application files:**
   ```bash
   # Extract new version
   tar -xzf zk-communist-v2.0.0.tar.gz
   sudo cp -r zk-communist-v2.0.0/* /opt/zk-communist/
   ```

4. **Update dependencies:**
   ```bash
   sudo pip3 install -r /opt/zk-communist/requirements.txt
   ```

5. **Restore configuration and restart:**
   ```bash
   sudo cp -r /tmp/config-backup/* /opt/zk-communist/config/
   sudo systemctl start network-monitoring
   ```

## Security Considerations

### Access Control
- Service runs as non-root user with restricted permissions
- Network access limited to required ports only
- API authentication required for sensitive operations
- Emergency endpoints accessible without authentication for safety

### Data Protection
- All sensitive configuration data encrypted at rest
- Hardware-bound encryption keys prevent unauthorized access
- Automatic log rotation and cleanup to minimize evidence
- Secure backup encryption and storage

### Network Security
- Firewall rules restrict access to authorized networks
- Network policies limit communication to required targets
- SSL/TLS encryption for web interface (if configured)
- Regular security scanning and updates

## Support

For technical support and assistance:

1. **Check logs:** Review application and system logs
2. **Verify configuration:** Ensure all settings are correct
3. **Test connectivity:** Confirm network access to devices
4. **Emergency procedures:** Use emergency shutdown if needed

**Important:** This service is designed for internal network monitoring only. Ensure proper authorization before deployment.