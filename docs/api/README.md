# Network Monitoring Service API Documentation

**Internal Use Only** - Network Monitoring and Diagnostics

## Overview

The Network Monitoring Service provides internal network monitoring and diagnostic capabilities for enterprise infrastructure. This service operates on port 8012 and provides RESTful API endpoints for system monitoring and device management.

## Base URL

```
http://localhost:8012/api/v1
```

## Authentication

This service uses API key authentication for protected endpoints. Emergency endpoints are accessible without authentication for immediate response capabilities.

## API Endpoints

### System Endpoints

#### Health Check
```
GET /api/v1/system/health
```

Returns service health status for Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-21T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

#### Readiness Check
```
GET /api/v1/system/ready
```

Returns service readiness status for Kubernetes probes.

**Response:**
```json
{
  "ready": true,
  "timestamp": "2025-11-21T10:30:00Z",
  "service": "network-monitoring"
}
```

#### System Status
```
GET /api/v1/system/status
```

Returns detailed system status information.

### Device Endpoints

#### Device Status
```
GET /api/v1/device/status
```

Returns current device connection status.

**Response:**
```json
{
  "device_id": "ZMM210_TFT_001",
  "status": "connected",
  "last_seen": "2025-11-21T10:30:00Z",
  "firmware": "v1.2.3"
}
```

#### Test Device Connection
```
POST /api/v1/device/test-connection
```

Tests connection to a network device.

**Request:**
```json
{
  "device_ip": "192.168.1.100",
  "port": 4370,
  "timeout": 5000
}
```

**Response:**
```json
{
  "success": true,
  "device_ip": "192.168.1.100",
  "response_time_ms": 150
}
```

### Emergency Endpoints (No Authentication Required)

#### Panic Button
```
POST /api/v1/emergency/panic-button
```

Immediate system shutdown with evidence cleanup.

**Request:**
```json
{
  "reason": "Manual emergency shutdown",
  "immediate": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "panic_executed": true,
    "system_locked": true,
    "response_time_ms": 50
  },
  "timestamp": "2025-11-21T10:30:00Z"
}
```

### Configuration Endpoints

#### Configuration Status
```
GET /api/v1/config/status
```

Returns configuration system status.

**Response:**
```json
{
  "encryption_status": "ready",
  "config_loaded": true,
  "backup_available": false,
  "validation_status": "valid"
}
```

#### Configuration Template
```
GET /api/v1/config/template
```

Returns configuration template for initial setup.

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "DEVICE_CONNECTION_FAILED",
    "message": "Unable to establish connection to device",
    "details": "Connection timeout after 5000ms"
  },
  "timestamp": "2025-11-21T10:30:00Z"
}
```

## HTTP Status Codes

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

API endpoints are rate-limited to 100 requests per minute per IP address.

## Monitoring

Service metrics are available for monitoring integration:
- Response time tracking
- Error rate monitoring
- Resource utilization monitoring
- Health check status

## Security Notes

- Emergency endpoints are accessible without authentication for immediate response
- All sensitive data is encrypted at rest using AES-256-GCM
- Configuration values are hardware-bound for security
- Network access is restricted to authorized IP ranges