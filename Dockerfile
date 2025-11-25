# ZK-Communist Time Liberation Server
# Multi-stage production Dockerfile for minimal image size and security

# Stage 1: Builder stage - Build and install dependencies
FROM python:3.11-slim-bullseye AS builder

# Set build arguments for caching optimization
ARG BUILD_DATE
ARG VCS_REF

# Set labels for container metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="zk-communist" \
      org.label-schema.description="ZK-Communist Time Liberation Server - Protect workers from attendance exploitation" \
      org.label-schema.url="https://github.com/your-org/zk-communist" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/zk-communist.git" \
      org.label-schema.vendor="ZK-Communist Collective" \
      org.label-schema.version="1.0.0" \
      org.label-schema.schema-version="1.0"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Stage 2: Production stage - Minimal runtime image
FROM python:3.11-slim-bullseye AS production

# Set security arguments
ARG BUILD_DATE
ARG VCS_REF

# Maintain the same labels
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="zk-communist" \
      org.label-schema.description="ZK-Communist Time Liberation Server - Protect workers from attendance exploitation" \
      org.label-schema.url="https://github.com/your-org/zk-communist" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/zk-communist.git" \
      org.label-schema.vendor="ZK-Communist Collective" \
      org.label-schema.version="1.0.0" \
      org.label-schema.schema-version="1.0"

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    ZK_COMMUNIST_ENV="production"

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
        libffi7 \
        libssl1.1 \
        && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r zkcommunist && \
    useradd -r -g zkcommunist -d /app -s /sbin/nologin -c "ZK-Communist Time Liberation Server" zkcommunist

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory with correct permissions
RUN mkdir -p /app && \
    chown -R zkcommunist:zkcommunist /app

# Switch to non-root user
USER zkcommunist
WORKDIR /app

# Copy application code
COPY --chown=zkcommunist:zkcommunist src/ ./src/
COPY --chown=zkcommunist:zkcommunist main.py ./

# Create health check script
COPY --chown=zkcommunist:zkcommunist scripts/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Set up proper Python path
ENV PYTHONPATH="/app:/app/src:$PYTHONPATH"

# Expose application metrics port (if using metrics)
EXPOSE 8080

# Set up health checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Default command
CMD ["python", "main.py"]

# Add volume for logs and potential data persistence
VOLUME ["/app/logs", "/app/data"]

# Set security context
# These will be used by Kubernetes pod security context
USER 1000:1000

# Multi-platform support (for Apple Silicon, etc.)
FROM production AS multi-platform
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Architecture-specific optimizations
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        echo "Optimizing for ARM64 architecture"; \
    elif [ "$TARGETARCH" = "amd64" ]; then \
        echo "Optimizing for AMD64 architecture"; \
    fi

# Final production stage
FROM multi-platform AS final

# Display container information on startup
RUN echo "ZK-Communist Time Liberation Server v1.0.0" && \
    echo "Built for: ${TARGETOS:-linux}/${TARGETARCH:-unknown}" && \
    echo "Image created: ${BUILD_DATE:-unknown}" && \
    echo "Git commit: ${VCS_REF:-unknown}"

# Documentation in container image
RUN echo """
╔══════════════════════════════════════════════════════════════╗
║           ZK-Communist Time Liberation Server                ║
║                                                              ║
║  Deploying Workers from Exploitative Attendance Systems      ║
║                                                              ║
║  This container provides:                                     ║
║  - Device communication with ZKTeco time clocks             ║
║  - Intelligent time manipulation during 7:50-8:10 AM         ║
║  - Randomized timestamp generation for protection          ║
║  - Production-ready monitoring and health checks            ║
║                                                              ║
║  Usage:                                                      ║
║  docker run -d --name zk-communist zk-communist:latest     ║
║                                                              ║
║  Configuration:                                              ║
║  - Set device IP via DEVICE_IP environment variable         ║
║  - Set device credentials via Kubernetes Secret              ║
║  - Configure manipulation windows via ConfigMap             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""" > /app/MOTD

# End of Dockerfile