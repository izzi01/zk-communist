# ZK-Communist Time Liberation Server - Kubernetes Deployment Guide

## Overview

This guide covers the complete deployment of the ZK-Communist Time Liberation Server to Kubernetes, providing production-ready containerization, configuration management, and operational procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Container Build](#container-build)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Configuration Management](#configuration-management)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Security Considerations](#security-considerations)
8. [Operational Procedures](#operational-procedures)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance and Updates](#maintenance-and-updates)

## Prerequisites

### Kubernetes Cluster
- Kubernetes 1.24+ with support for PodSecurityContext
- HostNetwork capability (for device communication)
- At least 1 node with network access to ZKTeco devices

### Build Environment
- Docker 20.10+ with BuildKit enabled
- Python 3.11+ development environment
- kubectl configured for cluster access

### Required Tools
```bash
# Kubernetes CLI
kubectl version --client

# Docker
docker --version

# Build tooling
make --version
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   ZK-Communist   │    │  ConfigMap      │                 │
│  │     Pod         │◄───┤  (Config)       │                 │
│  │                 │    │                 │                 │
│  │ ┌─────────────┐ │    └─────────────────┘                 │
│  │ │ Time        │ │    ┌─────────────────┐                 │
│  │ │ Manipulator │ │    │     Secret      │                 │
│  │ │ Scheduler   │ │◄───┤  (Credentials)  │                 │
│  │ │ Device      │ │    │                 │                 │
│  │ │ Manager     │ │    └─────────────────┘                 │
│  │ └─────────────┘ │                                        │
│  │                 │                                        │
│  │ HostNetwork:   │                                        │
│  │ true           │                                        │
│  └─────────────────┘                                        │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              ZKTeco Time Clock                         │ │
│  │             (192.168.1.100:4370)                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Container Build

### Multi-Stage Docker Build

The application uses a multi-stage Docker build for optimal image size and security:

```bash
# Build with labels
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t zk-communist:latest \
  -t zk-communist:v1.0.0 \
  .

# Build for specific platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t your-registry/zk-communist:v1.0.0 \
  --push \
  .
```

### Image Features

- **Multi-stage build**: Minimizes final image size (~100MB)
- **Non-root user**: Runs as UID 1000 for security
- **Health checks**: Built-in liveness/readiness probes
- **Optimized layers**: Efficient layer caching for faster builds

### Build Verification

```bash
# Test local image
docker run --rm \
  -e DEVICE_IP=192.168.1.100 \
  -e LOG_LEVEL=DEBUG \
  zk-communist:latest \
  python -c "from src.services.device_manager import DeviceManager; print('Import successful')"

# Security scan (if Trivy available)
trivy image zk-communist:latest
```

## Kubernetes Deployment

### Namespace Creation

```bash
# Create dedicated namespace
kubectl create namespace zk-communist

# Apply resource quotas
kubectl apply -f k8s/deployment.yaml
```

### Secrets Management

Create secrets for sensitive configuration:

```bash
# Create device credentials
kubectl create secret generic zk-communist-secrets \
  --from-literal=device-password="your-secure-password" \
  --from-literal=api-key="your-api-key" \
  --from-literal=encryption-key="$(openssl rand -base64 32)" \
  --namespace=zk-communist

# Create TLS certificates (optional)
kubectl create secret tls zk-communist-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  --namespace=zk-communist
```

### Configuration Deployment

```bash
# Deploy configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Verify configuration
kubectl get configmaps -n zk-communist
kubectl get secrets -n zk-communist
```

### Application Deployment

```bash
# Deploy the application
kubectl apply -f k8s/deployment.yaml

# Monitor deployment progress
kubectl rollout status deployment/zk-communist -n zk-communist

# Check pod status
kubectl get pods -n zk-communist
kubectl describe pod -n zk-communist -l app=zk-communist
```

### Deployment Verification

```bash
# Check pod logs
kubectl logs -f deployment/zk-communist -n zk-communist

# Check application status
kubectl port-forward -n zk-communist svc/zk-communist-metrics 8080:8080
curl http://localhost:8080/health

# Check device connectivity
curl http://localhost:8080/device/status
```

## Configuration Management

### Environment-Specific Configurations

The deployment supports multiple environments:

```bash
# Production configuration
kubectl apply -f k8s/configmap-prod.yaml

# Development configuration
kubectl apply -f k8s/configmap-dev.yaml

# Update deployment to use specific config
kubectl patch deployment zk-communist -n zk-communist -p '{"spec":{"template":{"spec":{"containers":[{"name":"zk-communist","envFrom":[{"configMapRef":{"name":"zk-communist-config-prod"}}]}]}}}'
```

### Configuration Parameters

| Parameter | Description | Default | Environment Variable |
|-----------|-------------|---------|----------------------|
| `DEVICE_IP` | ZKTeco device IP address | `192.168.1.100` | `DEVICE_IP` |
| `DEVICE_PORT` | ZKTeco device port | `4370` | `DEVICE_PORT` |
| `LOG_LEVEL` | Application log level | `INFO` | `LOG_LEVEL` |
| `TIMEZONE` | System timezone | `UTC` | `TIMEZONE` |
| `METRICS_PORT` | Metrics HTTP port | `8080` | `METRICS_PORT` |

### Dynamic Configuration Updates

```bash
# Update ConfigMap
kubectl edit configmap zk-communist-config -n zk-communist

# Restart deployment to apply changes
kubectl rollout restart deployment/zk-communist -n zk-communist
```

## Monitoring and Logging

### Prometheus Metrics

The application exposes metrics on port 8080:

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: zk-communist-metrics
  namespace: zk-communist
spec:
  selector:
    matchLabels:
      app: zk-communist
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Available Metrics

- `zk_communist_manipulation_total`: Total manipulation operations
- `zk_communist_manipulation_success_rate`: Success percentage
- `zk_communist_device_connection_status`: Device connection state
- `zk_communist_uptime_seconds`: Application uptime

### Log Management

Logs are structured JSON and can be collected with Fluent Bit:

```yaml
# Fluent Bit ConfigMap for log collection
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: zk-communist
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/containers/*zk-communist*.log
        Parser            docker
        Tag               zk-communist.*
        Refresh_Interval  5
        Mem_Buf_Limit     50MB

    [OUTPUT]
        Name  stdout
        Match *
```

### Health Monitoring

Kubernetes probes monitor application health:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

startupProbe:
  httpGet:
    path: /startup
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

## Security Considerations

### Network Security

- **NetworkPolicy**: Limits ingress to monitoring systems only
- **HostNetwork**: Required for device communication but increases attack surface
- **Service Account**: Minimal permissions via RBAC

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
      - ALL
```

### Secrets Management

- Use Kubernetes Secrets for sensitive data
- Enable encryption at rest in etcd
- Rotate secrets regularly
- Never commit secrets to version control

## Operational Procedures

### Deployment Updates

```bash
# Rolling update with zero downtime
kubectl set image deployment/zk-communist \
  zk-communist=zk-communist:v1.1.0 \
  -n zk-communist

# Monitor rollout
kubectl rollout status deployment/zk-communist -n zk-communist

# Rollback if issues
kubectl rollout undo deployment/zk-communist -n zk-communist
```

### Scaling Operations

```bash
# Scale up (usually not needed for single device)
kubectl scale deployment zk-communist --replicas=2 -n zk-communist

# Horizontal Pod Autoscaler (if multiple devices)
kubectl autoscale deployment zk-communist \
  --cpu-percent=50 \
  --min=1 \
  --max=3 \
  -n zk-communist
```

### Backup and Recovery

```bash
# Export configuration
kubectl get configmaps,secrets -n zk-communist -o yaml > backup-config.yaml

# Backup logs
kubectl logs deployment/zk-communist -n zk-communist > zk-communist-logs-$(date +%Y%m%d).txt

# Restore from backup
kubectl apply -f backup-config.yaml
```

## Troubleshooting

### Common Issues

#### Pod Startup Failures

```bash
# Check pod events
kubectl describe pod -n zk-communist -l app=zk-communist

# Check pod logs
kubectl logs -n zk-communist -l app=zk-communist --previous

# Check resource usage
kubectl top pods -n zk-communist
```

#### Device Connection Issues

```bash
# Check device connectivity from pod
kubectl exec -it deployment/zk-communist -n zk-communist -- \
  ping 192.168.1.100

# Check port accessibility
kubectl exec -it deployment/zk-communist -n zk-communist -- \
  nc -vz 192.168.1.100 4370

# Check device manager logs
kubectl logs -n zk-communist deployment/zk-communist | grep "DeviceManager"
```

#### Time Manipulation Issues

```bash
# Check manipulation status
kubectl exec -it deployment/zk-communist -n zk-communist -- \
  curl http://localhost:8080/manipulation/status

# Check current time window
kubectl exec -it deployment/zk-communist -n zk-communist -- \
  curl http://localhost:8080/window/status

# Force manipulation (testing only)
kubectl exec -it deployment/zk-communist -n zk-communist -- \
  curl -X POST http://localhost:8080/manipulation/force
```

### Debug Commands

```bash
# Shell access to pod
kubectl exec -it deployment/zk-communist -n zk-communist -- /bin/bash

# Check Python processes
kubectl exec deployment/zk-communist -n zk-communist -- ps aux

# Check application logs in real-time
kubectl logs -f deployment/zk-communist -n zk-communist

# Check metrics endpoint
kubectl port-forward -n zk-communist svc/zk-communist-metrics 8080:8080
curl http://localhost:8080/metrics
```

## Maintenance and Updates

### Regular Maintenance

```bash
# Monthly: Update base images
docker pull python:3.11-slim-bullseye
docker build --no-cache -t zk-communist:latest .

# Weekly: Rotate secrets
kubectl create secret generic zk-communist-secrets-new \
  --from-literal=device-password="$(openssl rand -base64 32)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Daily: Check resource usage
kubectl top pods -n zk-communist
kubectl describe nodes
```

### Update Procedures

1. **Testing Environment**
   ```bash
   # Deploy to test namespace first
   kubectl apply -n zk-communist-test -f k8s/
   ```

2. **Production Update**
   ```bash
   # Backup current configuration
   kubectl get all -n zk-communist -o yaml > backup.yaml

   # Apply update
   kubectl set image deployment/zk-communist \
     zk-communist=zk-communist:v1.1.0 -n zk-communist

   # Monitor rollback
   kubectl rollout status deployment/zk-communist -n zk-communist
   ```

3. **Post-Update Verification**
   ```bash
   # Verify health
   kubectl get pods -n zk-communist
   curl http://$(kubectl get svc zk-communist-metrics -n zk-communist -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8080/health

   # Check functionality
   kubectl logs -f deployment/zk-communist -n zk-communist | grep -E "(INFO|ERROR)"
   ```

### Cleanup

```bash
# Remove old resources
kubectl delete deployment zk-communist -n zk-communist --ignore-not-found
kubectl delete configmaps -l app=zk-communist -n zk-communist --ignore-not-found
kubectl delete secrets -l app=zk-communist -n zk-communist --ignore-not-found

# Clean up old images
docker image prune -f
```

## Conclusion

This deployment guide provides a comprehensive approach to deploying the ZK-Communist Time Liberation Server in production Kubernetes environments. Follow the security best practices and regularly update the deployment to maintain system reliability and security.

For additional support or questions, refer to the project documentation or create an issue in the repository.