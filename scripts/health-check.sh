#!/bin/bash
# ZK-Communist Time Liberation Server - Health Check Script
# Used by Docker HEALTHCHECK and Kubernetes liveness/readiness probes

set -euo pipefail

# Configuration
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-5}
METRICS_PORT=${METRICS_PORT:-8080}
LOG_FILE=${LOG_FILE:-/app/logs/health-check.log}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if the application process is running
check_process() {
    if pgrep -f "python.*main.py" > /dev/null; then
        log "INFO: Application process is running"
        return 0
    else
        log "ERROR: Application process is not running"
        return 1
    fi
}

# Check application health endpoint
check_http_health() {
    local url="http://localhost:${METRICS_PORT}/health"

    if curl -f -s --max-time "$HEALTH_CHECK_TIMEOUT" "$url" > /dev/null 2>&1; then
        log "INFO: HTTP health check passed"
        return 0
    else
        log "ERROR: HTTP health check failed for $url"
        return 1
    fi
}

# Check application readiness endpoint
check_readiness() {
    local url="http://localhost:${METRICS_PORT}/ready"

    if curl -f -s --max-time "$HEALTH_CHECK_TIMEOUT" "$url" > /dev/null 2>&1; then
        log "INFO: Readiness check passed"
        return 0
    else
        log "ERROR: Readiness check failed for $url"
        return 1
    fi
}

# Check device connectivity (if applicable)
check_device_connectivity() {
    # Check if device manager is connected
    if curl -f -s --max-time "$HEALTH_CHECK_TIMEOUT" \
           "http://localhost:${METRICS_PORT}/device/status" > /dev/null 2>&1; then
        log "INFO: Device connectivity check passed"
        return 0
    else
        log "WARNING: Device connectivity check failed (may be starting up)"
        return 0  # Don't fail health check for device issues during startup
    fi
}

# Check system resources
check_resources() {
    # Check memory usage
    local memory_usage=$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -C python | head -2 | tail -1 | awk '{print $4}')
    local memory_usage_int=${memory_usage%.*}  # Remove decimal

    if [ "$memory_usage_int" -gt 80 ]; then
        log "WARNING: High memory usage: ${memory_usage}%"
        return 1
    fi

    # Check disk space for logs
    local disk_usage=$(df /app/logs | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log "WARNING: High disk usage: ${disk_usage}%"
        return 1
    fi

    log "INFO: Resource check passed (memory: ${memory_usage}%, disk: ${disk_usage}%)"
    return 0
}

# Check time manipulation status
check_time_manipulation() {
    if curl -f -s --max-time "$HEALTH_CHECK_TIMEOUT" \
           "http://localhost:${METRICS_PORT}/manipulation/status" > /dev/null 2>&1; then
        log "INFO: Time manipulation status check passed"
        return 0
    else
        log "INFO: Time manipulation not yet active (normal outside 7:50-8:10 AM window)"
        return 0  # Not an error outside manipulation window
    fi
}

# Main health check function
main() {
    local check_type=${1:-"health"}  # health, ready, or startup

    log "INFO: Starting ${check_type} check"

    case "$check_type" in
        "health")
            # Full health check for liveness probe
            check_process && check_http_health && check_resources
            ;;
        "ready")
            # Readiness check - application should be ready to serve traffic
            check_process && check_readiness && check_device_connectivity
            ;;
        "startup")
            # Startup probe - less strict checks
            check_process && check_http_health
            ;;
        *)
            log "ERROR: Unknown check type: $check_type"
            echo "Usage: $0 [health|ready|startup]"
            exit 1
            ;;
    esac

    local result=$?

    if [ $result -eq 0 ]; then
        log "INFO: ${check_type} check completed successfully"
        exit 0
    else
        log "ERROR: ${check_type} check failed"
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"