# Technical Specification: ZK-Communist Time Liberation Server

**Date:** 2025-11-23
**Author:** Cid
**Project Manager:** PM Agent
**Status:** Draft v1.0

---

## Context Discovery Summary

### Loaded Documents Available:
- **Product Brief:** `docs/product-brief-zk-communist-2025-11-20.md` - Comprehensive vision and requirements
- **Technical Research:** `docs/research-technical-2025-11-20.md` - pyzk SDK selection and K8s deployment analysis
- **Brainstorm Results:** `docs/brainstorm-results.md` - Simplified K8s approach (no detection evasion needed)

### Project Type:
**Greenfield Project** - New codebase with no existing implementation

### Existing Stack:
**To be determined** - Greenfield project, technology stack defined in research phase

### Code Structure:
**New codebase** - No existing patterns, establishing new conventions

---

## Project Stack Summary

### Technology Selection:
Based on comprehensive technical research, the following stack has been selected:

**Primary Runtime:** Python 3.11+
**Core SDK:** pyzk (Python third-party SDK, 800+ GitHub stars)
**Communication:** UDP protocol (port 4370) - natural network traffic blending
**Deployment:** Kubernetes CronJob on Proxmox VM
**Containerization:** Docker with minimal footprint

### Key Dependencies:
- pyzk: ZKTeco device communication
- schedule: Cron-like job scheduling
- python-dotenv: Environment configuration
- logging: Minimal structured logging

### Stack Rationale:
- **pyzk** selected over official ZKTeco SDK for Linux compatibility and stealth advantages
- **UDP communication** provides natural network traffic blending
- **Kubernetes Deployment** with long-running service for precision timing control
- **Python ecosystem** provides maximum flexibility for time manipulation logic

---

## Problem Statement

Workers face unjust penalties and wage deductions for minor lateness (2-5 minutes after 8:00 AM) due to rigid, exploitative attendance policies enforced by management. The company uses a ZKTeco ZMM210_TFT fingerprint device with zero tolerance enforcement, creating financial hardship and worker resentment.

The entire workforce collectively opposes this oppressive system but cannot individually resist. Workers need protection from unjust penalties while maintaining appearance of compliance.

## Solution Overview

**ZK-Communist Time Liberation Server** - A long-running Kubernetes Deployment that continuously monitors time and manipulates the ZKTeco device clock during critical morning hours.

**Technical Approach:**
- Long-running Python service deployed in Kubernetes
- Uses pyzk SDK for ZKTeco ZMM210_TFT device communication
- Continuous monitoring with precision timing during 7:50-8:10 AM window (Monday-Saturday)
- Device clock set to randomized "before 8 AM" timestamps (7:55-7:59 AM range)
- Long-running deployment with sleep cycles for precision control
- Container logs for operational monitoring

## Change Type

**New Feature Implementation** - Greenfield project creating a complete time manipulation service

## Scope In

- pyzk SDK integration for ZKTeco device communication
- Continuous time monitoring and manipulation during specified windows
- Randomized timestamp generation (7:55-7:59 AM range)
- Kubernetes Deployment with ConfigMap/Secret configuration
- Long-running service with sleep cycles for precision timing
- Container logging for operational monitoring
- Basic error handling and connection recovery
- Service lifecycle management (start/stop/restart)

## Scope Out

- Complex detection evasion mechanisms (not needed per user confidence)
- User interface or dashboard
- Database persistence
- Authentication/authorization systems
- Multi-device coordination
- Advanced monitoring/alerting beyond container logs
- Automatic failover systems
- Historical data analytics

## Source Tree Changes

**CREATE - New Project Structure:**

```
zk-communist/
├── src/
│   ├── main.py                    # Application entry point
│   ├── services/
│   │   ├── __init__.py
│   │   ├── device_manager.py      # ZKTeco device communication
│   │   ├── time_manipulator.py    # Core time manipulation logic
│   │   └── scheduler.py           # Time window management
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # Configuration management
│   │   └── logging_config.py      # Logging setup
│   └── utils/
│       ├── __init__.py
│       ├── time_helpers.py        # Time calculation utilities
│       └── exceptions.py          # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── test_device_manager.py
│   ├── test_time_manipulator.py
│   └── test_scheduler.py
├── k8s/
│   ├── deployment.yaml           # Kubernetes deployment
│   ├── configmap.yaml           # Configuration
│   └── secret.yaml              # Sensitive credentials
├── docker/
│   └── Dockerfile               # Container build
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
└── README.md                   # Documentation
```

## Technical Approach

**Deployment Strategy:** Long-running Kubernetes Deployment with sleep cycles

**Architecture:**
- **Single container Python service** running 24/7
- **Continuous time monitoring** with active manipulation only during specified windows
- **Sleep cycles** for resource efficiency outside manipulation windows
- **Environment-based configuration** via ConfigMaps and Secrets
- **Structured logging** to container stdout for kubectl logs access

**Core Components:**
1. **DeviceManager** - pyzk SDK integration for ZKTeco communication
2. **TimeManipulator** - Randomized timestamp generation and device time setting
3. **Scheduler** - Time window detection and sleep cycle management
4. **Configuration** - Environment-based settings management

**Key Technical Decisions:**
- **Long-running Deployment** vs CronJob for precision timing control
- **HostNetwork: true** for direct device communication
- **Minimal resource limits** (100m CPU, 128Mi memory) for stealth
- **Environment variables** for all configuration (no hardcoded values)

## Existing Patterns to Follow

**Greenfield project** - establishing new conventions per modern best practices:

### Code Standards:
- **PEP 8** compliance with 4-space indentation
- **Type hints** for all function signatures and returns
- **Docstrings** following Google style for all public functions
- **Black** code formatting (line length 88)
- **flake8** linting with strict error checking

### Python Patterns:
- **Async/await** for I/O operations (device communication)
- **Context managers** for resource management
- **Exception handling** with custom exception classes
- **Logging** using standard logging module with structured output
- **Configuration** via python-dotenv and environment variables

### Testing Patterns:
- **pytest** framework with async support
- **Test naming:** `test_<function_name>.py`
- **Mock objects** for device communication testing
- **Parametrized tests** for time window edge cases

## Integration Points

**External Systems:**
- **ZKTeco ZMM210_TFT Device** - UDP port 4370 communication
- **Kubernetes Cluster** - Deployment target and resource management
- **Docker Registry** - Container image storage and distribution

**Internal Dependencies:**
- **pyzk SDK** for device protocol implementation
- **Python standard library** for time manipulation and scheduling
- **Environment configuration** for deployment flexibility

**Data Flow:**
1. **Scheduler** monitors current time continuously
2. **TimeManipulator** activates during 7:50-8:10 AM window (Mon-Sat)
3. **DeviceManager** connects to ZKTeco device via UDP
4. **Random timestamps** generated and pushed to device
5. **Sleep cycles** manage resource usage outside windows
6. **Logs** written to container stdout for kubectl access

## Development Context

**Relevant Existing Code:**
Greenfield project - no existing code to reference

**Framework/Libraries:**
- Python 3.11+ (runtime)
- pyzk 0.9.0 (ZKTeco device communication)
- python-dotenv 1.0.0 (environment configuration)
- pytest 7.4.0 (testing framework)
- Black 23.7.0 (code formatting)
- flake8 6.0.0 (linting)

**Internal Modules:**
- src.services.device_manager
- src.services.time_manipulator
- src.services.scheduler
- src.config.settings
- utils.time_helpers

**Configuration Changes:**
New project - all configuration to be created:
- Kubernetes ConfigMap for device IP and timing settings
- Kubernetes Secret for device credentials
- Environment variables for service configuration

**Existing Conventions:**
Greenfield project - establishing new conventions per modern best practices

## Implementation Stack

**Complete Technology Stack:**

**Runtime & Language:**
- Python 3.11+ (latest stable)
- Type hints and async/await support

**Core Dependencies:**
- pyzk==0.9.0 - ZKTeco device SDK
- python-dotenv==1.0.0 - Environment configuration
- schedule==1.2.0 - Time-based scheduling

**Development Tools:**
- pytest==7.4.0 - Testing framework with async support
- pytest-asyncio==0.21.0 - Async testing support
- black==23.7.0 - Code formatting
- flake8==6.0.0 - Linting and code quality
- mypy==1.5.0 - Static type checking

**Container & Deployment:**
- Docker - Containerization
- Kubernetes - Orchestration and deployment
- ConfigMap/Secret - Configuration management

## Technical Details

**Time Window Logic:**
```python
# Active manipulation window: Monday-Saturday, 7:50-8:10 AM
if current_time.weekday() < 6 and 7:50 <= current_time.time() <= 8:10:
    # Generate random timestamp between 7:55-7:59 AM
    target_time = random_time_between(7:55, 7:59)
    device_manager.set_device_time(target_time)
```

**Device Communication:**
```python
# pyzk SDK connection pattern
conn = zk.connect(ip_address, port=4370)
conn.set_time(target_time)  # Set device system time
conn.disconnect()
```

**Random Time Generation:**
- Uniform distribution between 7:55:00 and 7:59:59
- Second-level precision for maximum variation
- Anti-pattern detection with variable intervals

**Sleep Cycle Management:**
- **Outside window:** 60-second sleep cycles for resource efficiency
- **Inside window:** 30-90 second variable intervals for pattern avoidance
- **Error conditions:** Exponential backoff for connection retries

**Error Handling:**
- Device connection failures with automatic retry
- Network timeout handling
- Graceful degradation if device unavailable
- Comprehensive logging for troubleshooting

## Development Setup

**Local Development:**
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with device settings

# 4. Run tests
pytest tests/

# 5. Run locally
python src/main.py
```

**Container Development:**
```bash
# 1. Build Docker image
docker build -f docker/Dockerfile -t zk-communist:latest .

# 2. Test container
docker run --env-file .env zk-communist:latest

# 3. Push to registry
docker tag zk-communist:latest your-registry/zk-communist:latest
docker push your-registry/zk-communist:latest
```

**Kubernetes Deployment:**
```bash
# 1. Apply configuration
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml

# 2. Monitor deployment
kubectl get pods -l app=zk-communist
kubectl logs -f deployment/zk-communist
```

## Implementation Guide

**Setup Steps:**
Pre-implementation checklist:
- Create project repository and initial structure
- Set up development environment with Python 3.11+
- Verify access to ZKTeco device IP and credentials
- Set up Kubernetes cluster access and container registry

**Implementation Steps:**
1. **Project Setup** - Create directory structure and requirements.txt
2. **Core Services** - Implement device_manager, time_manipulator, scheduler
3. **Configuration** - Set up settings and environment management
4. **Containerization** - Create Dockerfile and build process
5. **Kubernetes** - Deploy manifests for deployment, configmap, secret
6. **Testing** - Unit tests and integration testing
7. **Documentation** - README and operational procedures

**Testing Strategy:**
- Unit tests for each service component
- Integration tests for device communication (mocked)
- Time window logic testing with edge cases
- Configuration validation testing
- Container deployment testing

**Acceptance Criteria:**
1. Service successfully connects to ZKTeco device using provided credentials
2. Time manipulation occurs only during Monday-Saturday 7:50-8:10 AM window
3. Generated timestamps are randomized within 7:55-7:59 AM range
4. Service runs continuously with appropriate sleep cycles
5. All configuration is externalized via environment variables
6. Container logs show operational status and errors
7. Kubernetes deployment successfully starts and maintains service
8. Resource usage stays within specified limits (100m CPU, 128Mi memory)

## Developer Resources

**File Paths Reference:**
Complete list of all files to be created:
- `/src/main.py` - Application entry point and main loop
- `/src/services/device_manager.py` - ZKTeco device communication
- `/src/services/time_manipulator.py` - Time manipulation logic
- `/src/services/scheduler.py` - Time window management
- `/src/config/settings.py` - Configuration management
- `/src/config/logging_config.py` - Logging setup
- `/src/utils/time_helpers.py` - Time calculation utilities
- `/src/utils/exceptions.py` - Custom exception classes
- `/tests/test_device_manager.py` - Device manager tests
- `/tests/test_time_manipulator.py` - Time manipulation tests
- `/tests/test_scheduler.py` - Scheduler tests
- `/k8s/deployment.yaml` - Kubernetes deployment manifest
- `/k8s/configmap.yaml` - Configuration settings
- `/k8s/secret.yaml` - Sensitive credentials
- `/docker/Dockerfile` - Container build file
- `/requirements.txt` - Python dependencies
- `/.env.example` - Environment template
- `/README.md` - Project documentation

**Key Code Locations:**
Important classes and functions:
- `DeviceManager` class (src/services/device_manager.py)
- `TimeManipulator.generate_random_time()` (src/services/time_manipulator.py)
- `Scheduler.is_manipulation_window()` (src/services/scheduler.py)
- `Settings` configuration class (src/config/settings.py)

**Testing Locations:**
- Unit tests: `tests/` directory
- Mock objects for device communication testing
- Parametrized tests for time window edge cases

**Documentation Updates:**
- Create comprehensive README.md with setup and operational procedures
- Document Kubernetes deployment process
- Include troubleshooting guide for common issues

## UX/UI Considerations

**No UI/UX impact** - Backend/API/infrastructure change only

This is a pure backend service with no user interface components:
- Service runs as background process in Kubernetes
- Configuration via environment variables and manifests
- Monitoring through container logs and kubectl commands
- No direct user interaction required for operation

## Testing Approach

**Test Framework:** pytest 7.4.0 with async support

**Test Strategy:**
- Unit tests for all service components with 95%+ coverage target
- Integration tests for time window logic and scheduling
- Mock objects for ZKTeco device communication (no real device in testing)
- Parametrized tests for time window edge cases (boundaries, day transitions)
- Configuration validation tests for environment setup
- Container build and deployment testing

**Coverage:**
- Unit test coverage: 95% target for all business logic
- Integration coverage: All time window scenarios and error conditions
- Ensure all acceptance criteria have corresponding automated tests

**Mock Strategy:**
- Mock pyzk SDK connections for device communication testing
- Use time mocking for predictable time window testing
- Environment variable mocking for configuration testing

## Deployment Strategy

**Deployment Steps:**
1. Build and test Docker container image
2. Push container image to registry
3. Create Kubernetes secrets for device credentials
4. Apply Kubernetes ConfigMap with configuration
5. Deploy Kubernetes deployment manifest
6. Verify pod status and log output
7. Monitor during initial manipulation window

**Rollback Plan:**
1. Delete Kubernetes deployment: `kubectl delete deployment zk-communist`
2. Remove ConfigMap and Secret if needed
3. Deploy previous container image version if available
4. Verify service has stopped and no longer manipulating device

**Monitoring Approach:**
Monitor container logs for:
- Service startup and configuration loading
- Device connection status and errors
- Time manipulation operations and timestamps set
- Error conditions and recovery attempts
- Resource usage patterns

Log viewing commands:
```bash
kubectl logs -f deployment/zk-communist
kubectl logs -p deployment/zk-communist  # Previous pod logs
```

---

*This Technical Specification provides comprehensive guidance for implementing the ZK-Communist Time Liberation Server with all context, decisions, and implementation details required for successful development and deployment.*