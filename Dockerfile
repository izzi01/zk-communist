# Multi-stage Docker build for ZK-Communist Network Monitoring Service
# Optimized for minimal container size and stealth operation

# Stage 1: Build stage with all dependencies
FROM python:3.11-slim-bullseye AS builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels for build metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="network-monitoring" \
      org.label-schema.description="Network monitoring and diagnostics service" \
      org.label-schema.url="https://internal.company/network-monitoring" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.company/internal/zk-communist" \
      org.label-schema.vendor="Company Internal" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        libyaml-dev \
        libpq-dev \
        git && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install -r requirements.txt

# Copy application source code
COPY src/ /app/src/
COPY config/ /app/config/
COPY scripts/ /app/scripts/

# Install the application in development mode
RUN pip install -e /app/

# Run application tests if they exist (optional for CI builds)
# RUN if [ -d "/app/tests" ]; then \
#         cd /app && \
#         python -m pytest tests/ -v --tb=short; \
#     fi

# Stage 2: Production runtime stage
FROM python:3.11-slim-bullseye AS runtime

# Set runtime arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Security and runtime labels
LABEL maintainer="ops@company.internal" \
      description="Network Monitoring Service - Internal Infrastructure" \
      version=$VERSION \
      build-date=$BUILD_DATE \
      vcs-ref=$VCS_REF

# Create non-root user for security
RUN groupadd -r networkmon && \
    useradd -r -g networkmon -d /app -s /bin/bash networkmon

# Install runtime system dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        netcat-openbsd \
        dnsutils \
        iputils-ping && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    CONFIG_PATH="/app/config/config.yaml" \
    ENCRYPTION_KEY_PATH="/app/secrets/encryption-keys.yaml"

# Create application directories
RUN mkdir -p /app /app/secrets /var/log/network-monitoring /var/opt/network-monitoring && \
    chown -R networkmon:networkmon /app /var/log/network-monitoring /var/opt/network-monitoring

# Copy application files from builder stage
COPY --from=builder /app/src /app/src
COPY --from=builder /app/config /app/config
COPY --from=builder /app/scripts /app/scripts

# Set proper ownership
RUN chown -R networkmon:networkmon /app

# Copy entrypoint script and set permissions
COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chown networkmon:networkmon /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER networkmon

# Set working directory
WORKDIR /app

# Health check configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8012/api/v1/system/health || exit 1

# Expose application port
EXPOSE 8012

# Expose metrics port
EXPOSE 9090

# Set entrypoint and command
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "src/main.py"]

---
# Stage 3: Development stage (optional)
FROM runtime AS development

# Switch back to root for development setup
USER root

# Install development dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        vim \
        htop \
        less \
        tcpdump \
        strace && \
    rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
        pytest==7.4.3 \
        pytest-asyncio==0.21.0 \
        black==23.0.0 \
        mypy==1.7.0 \
        isort==5.12.0 \
        ipdb

# Copy test files
COPY tests/ /app/tests/

# Create development directories
RUN mkdir -p /app/.pytest_cache && \
    chown -R networkmon:networkmon /app

# Switch back to non-root user
USER networkmon

# Override command for development
CMD ["python", "-m", "pytest", "-v", "/app/tests/", "--tb=short"]