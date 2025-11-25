# GitHub Actions Docker Buildx Setup Guide

This guide covers the Docker buildx GitHub Actions workflow for the ZK-Communist Time Liberation Server.

## Overview

The GitHub Actions workflow provides automated:

- **Multi-platform builds** (linux/amd64, linux/arm64)
- **Container image testing** with integration tests
- **Security scanning** with Trivy
- **SBOM generation** for supply chain transparency
- **Automated deployment** to Kubernetes
- **Registry support** for GitHub Container Registry and Docker Hub

## Workflow Triggers

The workflow triggers on:

- **Push to main/develop**: Builds and pushes images
- **Pull requests**: Builds and tests without pushing
- **Tags**: Versioned releases (v1.0.0, etc.)
- **Releases**: Full production deployment

## Required Repository Secrets

### Basic Configuration

No secrets required for basic functionality (uses GitHub Container Registry).

### Optional Docker Hub Configuration

```bash
# Set these in your repository secrets
DOCKERHUB_USERNAME=your-dockerhub-username
DOCKERHUB_TOKEN=your-dockerhub-access-token
```

### Kubernetes Deployment (Optional)

```bash
# Base64 encoded kubeconfig file
KUBE_CONFIG=$(cat ~/.kube/config | base64 -w 0)
```

## Workflow Jobs

### 1. docker-build

**Core build and deployment job:**

- **Setup**: Docker buildx with multi-platform support
- **Authentication**: GitHub Container Registry (automatic) + optional Docker Hub
- **Metadata**: Automatic tagging based on git events
- **Testing**: Container integration tests before pushing
- **Security**: Trivy vulnerability scanning
- **SBOM**: Software Bill of Materials generation

**Platform Support:**
```yaml
platforms: linux/amd64,linux/arm64
```

**Image Tagging Strategy:**
- `main` branch → `latest`, `stable`
- `develop` branch → `develop-{sha}`
- Pull requests → `pr-{pr}`
- Tags (v1.0.0) → `1.0.0`, `1.0`, `1`

### 2. k8s-deployment

**Automated Kubernetes deployment:**
- Triggers on push to `main` branch
- Updates deployment with new image
- Creates namespace and resources
- Monitors rollout completion

### 3. deploy-staging

**Staging environment deployment:**
- Triggers on push to `develop` branch
- Protected environment with approval rules
- Configurable staging targets

### 4. notify

**Build status notifications:**
- Success/failure summaries
- Image and tag information
- Platform support details

## Local Development

### Testing the Workflow

```bash
# Install act for local GitHub Actions testing
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow locally
act -j docker-build

# Test specific steps
act -j docker-build -s GITHUB_TOKEN=your-token
```

### Local Buildx Testing

```bash
# Build with same settings as workflow
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --target production \
  -t zk-communist:test \
  .

# Run tests locally
docker run --rm \
  -e DEVICE_IP=192.168.1.100 \
  -e LOG_LEVEL=DEBUG \
  zk-communist:test \
  python -c "from src.services.device_manager import DeviceManager; print('✅ Container working')"
```

## Security Features

### Image Scanning

**Trivy Security Scans:**
- Vulnerability detection
- Security advisories
- Integration with GitHub Security tab

**SBOM Generation:**
- SPDX format software bill of materials
- Dependency transparency
- Supply chain security

### Container Security

**Multi-stage Dockerfile:**
```dockerfile
# Build stage
FROM python:3.11-slim as builder
# ... build process ...

# Production stage
FROM python:3.11-slim as production
# ... minimal runtime ...
USER 1000:1000  # Non-root user
```

**Security Context:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  capabilities:
    drop:
      - ALL
```

## Optimization Features

### Build Caching

**GitHub Actions Cache:**
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Docker Layer Caching:**
- Optimized Dockerfile layer structure
- BuildKit caching for faster builds
- Parallel multi-platform builds

### Resource Efficiency

**Build Resources:**
```yaml
runs-on: ubuntu-latest
# Efficient resource usage
# Parallel builds for multiple platforms
```

**Container Resources:**
```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

## Monitoring and Observability

### Build Monitoring

**Workflow Status:**
- Real-time build progress
- Step-by-step execution details
- Artifact tracking

**Security Monitoring:**
- Trivy scan results
- GitHub Security tab integration
- Vulnerability tracking

### Deployment Monitoring

**Kubernetes Integration:**
- Rollout status monitoring
- Pod health checks
- Resource usage tracking

## Configuration Examples

### Multi-Registry Setup

```yaml
# .github/workflows/docker-build.yml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

# Optional: Add Docker Hub
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    registry: docker.io
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### Custom Build Args

```yaml
- name: Extract metadata
  id: extra-meta
  run: |
    echo "build_date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> $GITHUB_OUTPUT
    echo "vcs_ref=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
    echo "git_commit=$(git rev-parse HEAD)" >> $GITHUB_OUTPUT
    echo "git_branch=$(git rev-parse --abbrev-ref HEAD)" >> $GITHUB_OUTPUT
```

### Environment-Specific Deployment

```yaml
# Production deployment (main branch)
k8s-deployment:
  if: github.ref == 'refs/heads/main'
  # ... production configuration ...

# Staging deployment (develop branch)
deploy-staging:
  if: github.ref == 'refs/heads/develop'
  environment: staging
  # ... staging configuration ...
```

## Troubleshooting

### Common Issues

**Build Failures:**
```bash
# Check workflow logs
# Verify Dockerfile syntax
# Check dependency installation
```

**Test Failures:**
```bash
# Run container tests locally
python tests/test_container_integration.py

# Debug container issues
docker run -it zk-communist:test /bin/bash
```

**Registry Issues:**
```bash
# Test registry authentication
docker login ghcr.io
docker push your-username/zk-communist:test
```

### Performance Optimization

**Build Speed:**
```yaml
# Use larger runners for complex builds
runs-on: ubuntu-latest-4-cores

# Optimize caching
cache-to: type=gha,mode=max
```

**Security Scan Speed:**
```yaml
# Limit scan scope
with:
  image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.version }}
  format: 'sarif'
  severity: 'HIGH,CRITICAL'
```

## Best Practices

### Workflow Design

- **Separate jobs** for build, test, and deployment
- **Conditional execution** based on branch/event
- **Comprehensive testing** before image pushing
- **Security scanning** for all pushed images

### Dockerfile Design

- **Multi-stage builds** for minimal image size
- **Security hardening** with non-root users
- **Optimized layer ordering** for better caching
- **Health checks** for runtime monitoring

### Kubernetes Integration

- **Rolling updates** for zero-downtime deployments
- **Health probes** for container monitoring
- **Resource limits** for cluster stability
- **Configuration externalization** for flexibility

## Conclusion

This GitHub Actions workflow provides a comprehensive CI/CD pipeline for the ZK-Communist Time Liberation Server with:

- ✅ **Automated builds** for multiple platforms
- ✅ **Security scanning** and vulnerability detection
- ✅ **Container testing** with integration tests
- ✅ **SBOM generation** for supply chain transparency
- ✅ **Kubernetes deployment** with monitoring
- ✅ **Multi-registry support** for distribution

The workflow is designed for production use with comprehensive security, monitoring, and optimization features.