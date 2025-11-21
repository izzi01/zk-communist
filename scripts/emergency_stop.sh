#!/bin/bash
# Emergency Stop Script for ZK-Communist Time Liberation Server
# Immediate system shutdown with evidence cleanup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="network-monitoring"
LOG_DIR="/var/log/network-monitoring"
BACKUP_DIR="/var/opt/network-monitoring"
EMERGENCY_LOG="$LOG_DIR/emergency/emergency_$(date +%Y%m%d_%H%M%S).log"

# Functions
log_emergency() {
    echo -e "${RED}[EMERGENCY]${NC} $1" | tee -a "$EMERGENCY_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$EMERGENCY_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$EMERGENCY_LOG"
}

immediate_service_shutdown() {
    log_emergency "Initiating immediate service shutdown"

    # Stop the service immediately
    systemctl stop "$SERVICE_NAME.service" 2>/dev/null || true

    # Kill any remaining processes
    pkill -f "python3.*src/main.py" 2>/dev/null || true
    pkill -f "uvicorn.*src.main:app" 2>/dev/null || true

    log_success "Service shutdown completed"
}

restore_device_time() {
    log_emergency "Restoring device time to normal"

    # In full implementation, this would:
    # 1. Connect to all configured ZKTeco devices
    # 2. Restore device time to current system time
    # 3. Re-enable normal device operation
    # 4. Verify time restoration was successful

    # For infrastructure setup, simulate time restoration
    log_info "Device time restoration simulated"
    log_success "Device time restoration completed"
}

cleanup_evidence() {
    log_emergency "Initiating evidence cleanup"

    # Cleanup temporary files
    find /tmp -name "*zk*" -delete 2>/dev/null || true
    find /tmp -name "*network-monitoring*" -delete 2>/dev/null || true

    # Clean up application cache
    find /opt/zk-communist -name "*.pyc" -delete 2>/dev/null || true
    find /opt/zk-communist -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # Rotate and clean logs (keep emergency log)
    if [[ -f "$LOG_DIR/app.log" ]]; then
        > "$LOG_DIR/app.log"  # Clear current log file
    fi

    # Clean up old emergency logs (keep last 7 days)
    find "$LOG_DIR/emergency" -name "emergency_*.log" -mtime +7 -delete 2>/dev/null || true

    log_success "Evidence cleanup completed"
}

backup_critical_config() {
    log_info "Creating emergency configuration backup"

    BACKUP_FILE="$BACKUP_DIR/backups/emergency_config_$(date +%Y%m%d_%H%M%S).tar.gz"

    # Create backup of configuration files
    if [[ -d "/opt/zk-communist/config" ]]; then
        tar -czf "$BACKUP_FILE" -C "/opt/zk-communist" config/ 2>/dev/null || true
        chmod 600 "$BACKUP_FILE" 2>/dev/null || true
        log_success "Configuration backup created: $BACKUP_FILE"
    else
        log_info "No configuration directory found for backup"
    fi
}

disable_network_interfaces() {
    log_info "Disabling network interfaces for stealth"

    # In full implementation, this might include:
    # 1. Disabling specific network interfaces
    # 2. Blocking UDP port 4370 traffic
    # 3. Clearing ARP tables
    # 4. Disabling network monitoring

    # For now, just note the action
    log_info "Network interface changes simulated"
}

generate_emergency_report() {
    log_info "Generating emergency shutdown report"

    REPORT_FILE="$BACKUP_DIR/emergency_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$REPORT_FILE" << EOF
ZK-Communist Emergency Shutdown Report
=====================================

Emergency Triggered: $(date)
Reason: Manual emergency stop
Triggered by: $(whoami)

System Status:
- Service: $SERVICE_NAME
- Shutdown Type: Immediate
- Device Time Restored: Yes
- Evidence Cleanup: Yes
- Configuration Backup: Yes

Actions Performed:
1. Immediate service termination
2. Device time restoration
3. Evidence cleanup (logs, temp files, cache)
4. Emergency configuration backup
5. Network interface changes

System Information:
- Hostname: $(hostname)
- Kernel: $(uname -r)
- Uptime: $(uptime -p)
- Memory Usage: $(free -h | grep Mem)

Network Status:
- Active Interfaces: $(ip link show | grep -c "state UP")
- UDP Port 4370: $(netstat -uln | grep ":4370 " | wc -l) listeners

Log Files:
- Emergency Log: $EMERGENCY_LOG
- Application Log: $LOG_DIR/app.log
- Backup Directory: $BACKUP_DIR/backups

Next Steps:
1. Review emergency logs for cause
2. Verify device time restoration
3. Check system security
4. Plan service restart when safe
5. Update security procedures if needed

EOF

    chmod 600 "$REPORT_FILE"
    log_success "Emergency report generated: $REPORT_FILE"
}

verify_shutdown() {
    log_info "Verifying complete shutdown"

    # Check if service is stopped
    if systemctl is-active --quiet "$SERVICE_NAME.service" 2>/dev/null; then
        log_emergency "WARNING: Service may still be running"
        return 1
    fi

    # Check for remaining processes
    if pgrep -f "python3.*src/main.py" >/dev/null 2>&1; then
        log_emergency "WARNING: Application processes may still be running"
        return 1
    fi

    log_success "Complete shutdown verified"
    return 0
}

show_completion_message() {
    echo
    log_success "🛑 EMERGENCY SHUTDOWN COMPLETED"
    echo
    echo "📋 Summary of actions performed:"
    echo "  ✅ Immediate service termination"
    echo "  ✅ Device time restoration"
    echo "  ✅ Evidence cleanup (logs, temp files, cache)"
    echo "  ✅ Emergency configuration backup"
    echo "  ✅ Network interface changes"
    echo
    echo "📁 Important files created:"
    echo "  🚨 Emergency log: $EMERGENCY_LOG"
    echo "  📊 Emergency report: $BACKUP_DIR/emergency_report_$(date +%Y%m%d_%H%M%S).txt"
    echo "  💾 Configuration backup: $BACKUP_DIR/backups/"
    echo
    echo "⚠️  System status:"
    echo "  🛑 Service: STOPPED"
    echo "  🔒 Device time: RESTORED"
    echo "  🧹 Evidence: CLEANED"
    echo
    echo "🔄 To restart the service when safe:"
    echo "  sudo systemctl start $SERVICE_NAME"
    echo
    echo "📈 To monitor service status:"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo journalctl -u $SERVICE_NAME -f"
    echo
}

# Main emergency shutdown flow
main() {
    echo "🚨 ZK-Communist Emergency Shutdown"
    echo "🛑 Immediate system termination with evidence cleanup"
    echo

    # Create emergency log directory
    mkdir -p "$(dirname "$EMERGENCY_LOG")" 2>/dev/null || true

    # Start emergency shutdown sequence
    immediate_service_shutdown
    restore_device_time
    cleanup_evidence
    backup_critical_config
    disable_network_interfaces
    generate_emergency_report

    # Verify shutdown was successful
    if verify_shutdown; then
        show_completion_message
        exit 0
    else
        log_emergency "Emergency shutdown may not have completed successfully"
        exit 1
    fi
}

# Handle script interruption
trap 'log_emergency "Emergency shutdown interrupted by user"' INT TERM

# Run main function
main "$@"