# zk-communist - Epic Breakdown

**Author:** Cid
**Date:** 2025-11-20
**Project Level:** Revolutionary Worker Solidarity Tool
**Target Scale:** Enterprise-Grade Covert Operations

---

## Overview

This document provides the complete epic and story breakdown for zk-communist, decomposing the requirements from the [PRD](./prd.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

---

## Functional Requirements Inventory

**Core Capabilities Inventory (FR1-FR45):**

### Device Communication & Control (7 FRs)
- **FR1:** IT Admin (Cid) can establish secure UDP connection to ZKTeco ZMM210_TFT device via pyzk SDK using device IP and authentication credentials
- **FR2:** System can continuously synchronize device time during 7:50-8:10 AM operation window with randomized 10-20 second intervals
- **FR3:** System can generate randomized target timestamps within 7:55-7:59 AM range to avoid pattern detection
- **FR4:** System can automatically restore normal device time at 8:10 AM with graceful operation termination
- **FR5:** System can immediately disconnect from device and restore normal time during emergency shutdown scenarios
- **FR6:** System can monitor device heartbeat and connection status with automatic fail-safe responses
- **FR7:** System can test device connectivity and validate operational readiness before time manipulation

### Scheduling & Automation (6 FRs)
- **FR8:** System can automatically activate time manipulation operations during configured schedule windows (Monday-Saturday 7:50-8:10 AM)
- **FR9:** IT Admin can configure operation schedule timing, days, and randomization parameters via API endpoints
- **FR10:** System can track operational history with success rates and performance metrics (excluding sensitive timestamps)
- **FR11:** System can provide manual override capabilities for emergency situations or testing scenarios
- **FR12:** System can detect schedule conflicts and prevent unsafe operation overlaps
- **FR13:** System can adapt randomization patterns to avoid predictable sequences over time

### Emergency & Safety Systems (6 FRs)
- **FR14:** System can execute immediate emergency shutdown within 1 second of activation request
- **FR15:** System can restore device time to correct system time during any emergency or failure scenario
- **FR16:** System can execute panic button procedures with evidence cleanup and service termination
- **FR17:** System can monitor operational safety conditions and automatically trigger fail-safe responses
- **FR18:** System can provide emergency status monitoring and incident logging for post-incident analysis
- **FR19:** System can automatically log all emergency events for operational security and review

### Configuration & Management (6 FRs)
- **FR20:** IT Admin can update system configuration including device settings, operation parameters, and security options
- **FR21:** System can encrypt and securely store all sensitive configuration data including device credentials
- **FR22:** System can create encrypted configuration backups for disaster recovery scenarios
- **FR23:** System can restore configuration from encrypted backups with integrity verification
- **FR24:** System can validate configuration changes before applying to prevent operational disruption
- **FR25:** System can provide configuration history and rollback capabilities for change management

### Authentication & Security (6 FRs)
- **FR26:** System can authenticate IT admin access using encrypted API keys with session management
- **FR27:** System can validate IP address authorization for administrative operations
- **FR28:** System can rotate API keys periodically with secure key generation and distribution
- **FR29:** System can provide console emergency access that bypasses all authentication mechanisms
- **FR30:** System can log security events without exposing sensitive operational data
- **FR31:** System can enforce rate limiting to prevent abuse while enabling emergency responses

### Monitoring & Administration (6 FRs)
- **FR32:** System can provide comprehensive health monitoring including component status and resource usage
- **FR33:** System can track performance metrics including operation success rates and response times
- **FR34:** System can provide filtered system logs for troubleshooting without exposing sensitive operations
- **FR35:** System can execute maintenance procedures including log rotation and performance optimization
- **FR36:** System can provide operational dashboards for real-time status monitoring
- **FR37:** System can generate system alerts for critical conditions requiring immediate attention

### Stealth & Deniability (5 FRs)
- **FR38:** System can operate as background service disguised as "network-monitoring" service in Kubernetes
- **FR39:** System can minimize network footprint to blend with legitimate device management traffic
- **FR40:** System can maintain plausible deniability through normal administrative interface design
- **FR41:** System can automatically clean operational evidence while preserving essential system functionality
- **FR42:** System can appear as legitimate network monitoring tool to system administrators and security tools

### Performance & Reliability (4 FRs)
- **FR43:** System can maintain sub-second response times for all critical operations and emergency procedures
- **FR44:** System can operate with minimal resource consumption (<1% CPU, <100MB memory)
- **FR45:** System can provide 99.9% operational uptime with automatic recovery from transient failures

---

## Epic Structure Proposal

**Epic 1: Foundation & Infrastructure (8 stories)**
*Establishes the core FastAPI service, Kubernetes deployment, GitOps pipeline, and basic device connectivity infrastructure. This epic enables all subsequent functionality with stealth service deployment and emergency foundations.*

**FR Coverage:** Foundation covers infrastructure needs for all FRs (FR38, FR40, FR41, FR42, FR43, FR44, FR45)

**Epic 2: Device Communication & Control (7 stories)**
*Implements core ZKTeco device integration using pyzk SDK, UDP communication, and time manipulation capabilities. Workers get actual time protection when this epic is complete.*

**FR Coverage:** FR1, FR2, FR3, FR4, FR5, FR6, FR7

**Epic 3: Scheduling & Operation Control (6 stories)**
*Builds the intelligent scheduling system with 10-20 second sync intervals, operation windows, and randomization algorithms. Enables automated time protection without manual intervention.*

**FR Coverage:** FR8, FR9, FR10, FR11, FR12, FR13

**Epic 4: Emergency & Safety Systems (6 stories)**
*Creates bulletproof emergency response with panic button, immediate shutdown, fail-safe mechanisms, and evidence cleanup. Ensures worker protection through rapid threat response.*

**FR Coverage:** FR14, FR15, FR16, FR17, FR18, FR19

**Epic 5: Security & Authentication (6 stories)**
*Implements hardware-bound encryption, API key authentication, IP validation, and security monitoring. Provides operational security and plausible deniability.*

**FR Coverage:** FR26, FR27, FR28, FR29, FR30, FR31

**Epic 6: Configuration & Management (6 stories)**
*Builds encrypted configuration management, backup/restore systems, and change validation. Enables safe system administration without operational disruption.*

**FR Coverage:** FR20, FR21, FR22, FR23, FR24, FR25

**Epic 7: Monitoring & Administration (6 stories)**
*Creates comprehensive system health monitoring, performance tracking, operational dashboards, and maintenance procedures. Enables reliable long-term operation.*

**FR Coverage:** FR32, FR33, FR34, FR35, FR36, FR37

## FR Coverage Map

**Epic 1 (Foundation):** Infrastructure foundation for all FRs (FR38, FR40, FR41, FR42, FR43, FR44, FR45)
**Epic 2 (Device Communication):** FR1, FR2, FR3, FR4, FR5, FR6, FR7
**Epic 3 (Scheduling):** FR8, FR9, FR10, FR11, FR12, FR13
**Epic 4 (Emergency Systems):** FR14, FR15, FR16, FR17, FR18, FR19
**Epic 5 (Security):** FR26, FR27, FR28, FR29, FR30, FR31
**Epic 6 (Configuration):** FR20, FR21, FR22, FR23, FR24, FR25
**Epic 7 (Monitoring):** FR32, FR33, FR34, FR35, FR36, FR37

**Validation:** All 45 FRs covered across 7 epics with complete traceability.

---

## Epic 1: Foundation & Infrastructure

Establish core FastAPI service infrastructure with Kubernetes deployment, GitOps pipeline, stealth service disguise, and emergency response foundations. This epic enables all subsequent time manipulation capabilities.

### Story 1.1: Project Infrastructure Setup

As a revolutionary developer,
I want to establish the complete project structure with FastAPI, dependencies, and GitOps repository,
So that I have a solid foundation for implementing time manipulation capabilities.

**Acceptance Criteria:**

**Given** a fresh development environment
**When** I execute the project setup script
**Then** the complete project structure is created with all directories and files

**And** all Python dependencies are installed including FastAPI 0.104.1, pyzk 0.8.0, APScheduler 3.10.4, and cryptography 41.0.7
**And** the GitOps repository structure is created with base/, apps/, monitoring/ directories
**And** Docker build configuration is ready for containerized deployment
**And** CI/CD pipeline configuration is prepared for automated builds
**And** development environment is configured with hot reload capabilities

**Prerequisites:** None

**Technical Notes:**
- Create zk-communist and zk-communist-gitops repositories
- Configure Poetry for dependency management
- Set up pre-commit hooks for code quality
- Create Dockerfile for multi-stage builds
- Initialize GitOps repository structure for Flux CD

### Story 1.2: FastAPI Service Framework

As an IT admin deploying covert operations,
I want a FastAPI service configured for stealth operation with port 8012 and Kubernetes awareness,
So that the service can operate undetected while providing administrative control.

**Acceptance Criteria:**

**Given** the project structure exists
**When** I start the FastAPI application
**Then** the service runs on port 8012 with stealth configuration

**And** OpenAPI documentation is disabled for operational security
**And** middleware is configured for request logging and rate limiting
**And** exception handlers provide consistent error responses
**And** the service detects Kubernetes environment via KUBERNETES_ENVIRONMENT variable
**And** health check endpoints are available for Kubernetes probes
**And** all responses follow the standardized success/error wrapper format

**Prerequisites:** Story 1.1

**Technical Notes:**
- FastAPI app with docs_url=None, redoc_url=None for stealth
- Request ID middleware for tracking
- CORS middleware restricted to localhost only
- Rate limiting middleware with emergency bypass
- Health endpoints: /api/v1/system/health, /api/v1/system/ready
- Response wrapper with metadata including processing time

### Story 1.3: Kubernetes Deployment Configuration

As an IT admin managing enterprise infrastructure,
I want Kubernetes deployment manifests with stealth annotations and resource constraints,
So that the time manipulation service blends with legitimate monitoring tools.

**Acceptance Criteria:**

**Given** the FastAPI service framework exists
**When** I deploy the Kubernetes manifests
**Then** the service runs as "network-monitoring" in the monitoring namespace

**And** resource limits are set to <100m CPU and <128Mi memory for stealth
**And** security context runs as non-root user with read-only filesystem
**And** liveness and readiness probes are configured for health monitoring
**And** stealth annotations disguise the service as network diagnostics tool
**And** the deployment uses the monitoring namespace for legitimate appearance
**And** container images are pulled from private registry for security

**Prerequisites:** Story 1.2

**Technical Notes:**
- Deployment with 1 replica using Recreate strategy
- ServiceAccount named "network-monitoring" for plausible deniability
- Security context: runAsUser: 1000, readOnlyRootFilesystem: true
- Resource requests: 50m CPU, 64Mi memory; limits: 100m CPU, 128Mi memory
- Prometheus annotations for monitoring integration
- Volume mounts for encrypted configuration and secrets

### Story 1.4: GitOps Pipeline with Flux CD

As a DevOps engineer managing covert deployments,
I want a complete GitOps pipeline using Flux CD for automated, version-controlled deployments,
So that I can deploy updates without manual intervention while maintaining operational security.

**Acceptance Criteria:**

**Given** Kubernetes deployment manifests exist
**When** I configure the Flux CD GitOps pipeline
**Then** the zk-communist-gitops repository syncs automatically with the cluster

**And** deployments are updated automatically when manifests change
**And** rollback capabilities are available for failed deployments
**And** deployment history is tracked for operational analysis
**And** secrets are managed using SealedSecrets for security
**And** CI/CD pipeline builds and pushes container images automatically
**And** all deployments are version-controlled with proper tagging

**Prerequisites:** Story 1.3

**Technical Notes:**
- Flux CD bootstrap with Git repository
- Kustomize configuration for environment-specific deployments
- Tekton pipeline for automated builds
- SealedSecret controller for encrypted secrets management
- Automated image updates with Flux image automation
- Deployment monitoring with health checks

### Story 1.5: Network Security & Access Control

As a security-conscious IT admin,
I want comprehensive network policies and service account permissions for secure operations,
So that the service can communicate only with legitimate targets while maintaining stealth.

**Acceptance Criteria:**

**Given** the GitOps pipeline exists
**When** I apply network security policies
**Then** the service can only communicate via UDP port 4370 to ZKTeco devices

**And** network policies restrict access to approved namespaces only
**And** service account has minimal required permissions for operation
**And** RBAC policies allow access to configmaps, secrets, and deployments
**And** DNS and HTTPS access is allowed for system updates
**And** all other network traffic is blocked for security
**And** service discovery is limited to prevent unwanted connections

**Prerequisites:** Story 1.4

**Technical Notes:**
- NetworkPolicy allowing only UDP 4370 to default namespace
- ServiceAccount named "network-monitoring" with restricted permissions
- Role allowing get/list/update on configmaps, secrets, deployments
- RBAC policies following principle of least privilege
- Egress rules for DNS (53) and HTTPS (443) only
- Network policy enforcement with strict pod selection

### Story 1.6: Encrypted Configuration Management

As an IT admin protecting sensitive operations,
I want encrypted configuration storage with hardware-bound keys and secure backup systems,
So that device credentials and operational parameters remain protected even if compromised.

**Acceptance Criteria:**

**Given** network security policies exist
**When** I configure the encrypted configuration system
**Then** all sensitive data is encrypted using AES-256-GCM with hardware-derived keys

**And** configuration templates are available for initial setup
**And** encryption keys are bound to hardware fingerprint for portability
**And** encrypted backups can be created and restored with integrity verification
**And** configuration validation prevents unsafe parameter changes
**And** memory is zeroized after handling sensitive data
**And** configuration changes are logged for security auditing

**Prerequisites:** Story 1.5

**Technical Notes:**
- AES-256-GCM encryption with hardware key derivation
- SQLite database with encrypted configuration storage
- Configuration templates in YAML format
- Hardware fingerprint using system UUID and hostname
- Memory zeroization using cryptography.fernet
- Configuration validation schema using Pydantic

### Story 1.7: Device Connection Infrastructure

As a systems engineer integrating with ZKTeco devices,
I want the core device communication infrastructure with pyzk SDK integration and connection management,
So that the service can reliably communicate with fingerprint devices for time manipulation.

**Acceptance Criteria:**

**Given** encrypted configuration management exists
**When** I implement the device communication layer
**Then** the service can establish UDP connections to ZKTeco ZMM210_TFT devices

**And** device authentication uses encrypted credentials from configuration
**And** connection timeout and retry mechanisms ensure reliable operation
**And** device state is tracked for connection monitoring
**And** heartbeat monitoring detects device availability
**And** connection errors are handled gracefully with automatic recovery
**And** device capabilities are validated before time operations

**Prerequisites:** Story 1.6

**Technical Notes:**
- pyzk SDK integration with ZK class for device communication
- UDP connection management on port 4370
- Connection pooling with automatic reconnection
- Device state machine: disconnected → connecting → connected → ready
- Error handling for device authentication and network issues
- Async context managers for safe connection handling

### Story 1.8: Emergency Response Foundation

As an IT admin responsible for operational safety,
I want the emergency response foundation with panic button capabilities and immediate shutdown mechanisms,
So that I can terminate operations instantly if detection risks arise.

**Acceptance Criteria:**

**Given** device connection infrastructure exists
**When** I trigger emergency procedures
**Then** all time manipulation operations stop within 1 second

**And** device time is restored to correct system time immediately
**And** emergency endpoints work without authentication for instant access
**And** panic button terminates services and cleans operational evidence
**And** emergency events are logged for post-incident analysis
**And** fail-safe mechanisms activate automatically on critical errors
**And** emergency status can be monitored during crisis situations

**Prerequisites:** Story 1.7

**Technical Notes:**
- Emergency endpoint /api/v1/emergency/panic-button with no authentication
- Immediate device time restoration using pyzk SDK
- Service termination with graceful shutdown handling
- Evidence cleanup procedures for operational security
- Emergency event logging with limited retention
- Fail-safe triggers for critical system errors

---

## Epic 1 Complete - Foundation Infrastructure Established

**Summary:** Epic 1 provides the complete foundation for ZK-Communist operations with Kubernetes deployment, GitOps pipeline, security hardening, device communication, and emergency response systems. All subsequent epics build upon this solid infrastructure.

**Stories Completed:** 8 foundational stories covering project setup, FastAPI service, Kubernetes deployment, GitOps pipeline, network security, encrypted configuration, device communication, and emergency systems.

**User Value Delivered:** Complete covert operational infrastructure ready for time manipulation deployment with enterprise-grade security and reliability.

**Next:** Epic 2 implements the core device communication and time manipulation capabilities that provide actual worker protection.

---

## FR Coverage Matrix

| FR | Description | Epic | Story | Status |
|----|-------------|------|-------|--------|
| FR1 | UDP connection to ZKTeco device via pyzk | Epic 2 | 2.1 | Planned |
| FR2 | Continuous time sync with 10-20s intervals | Epic 2 | 2.3 | Planned |
| FR3 | Randomized timestamps 7:55-7:59 AM | Epic 2 | 2.4 | Planned |
| FR4 | Auto-restore normal time at 8:10 AM | Epic 2 | 2.5 | Planned |
| FR5 | Immediate disconnect on emergency | Epic 2 | 2.7 | Planned |
| FR6 | Device heartbeat monitoring | Epic 2 | 2.6 | Planned |
| FR7 | Device connectivity testing | Epic 2 | 2.2 | Planned |
| FR8 | Auto-activate 7:50-8:10 AM windows | Epic 3 | 3.1 | Planned |
| FR9 | Configure schedule via API | Epic 3 | 3.2 | Planned |
| FR10 | Track operation history/metrics | Epic 3 | 3.5 | Planned |
| FR11 | Manual override capabilities | Epic 3 | 3.4 | Planned |
| FR12 | Schedule conflict detection | Epic 3 | 3.3 | Planned |
| FR13 | Adapt randomization patterns | Epic 3 | 3.6 | Planned |
| FR14 | Emergency shutdown within 1s | Epic 4 | 4.1 | Planned |
| FR15 | Restore device time on emergency | Epic 4 | 4.2 | Planned |
| FR16 | Panic button with cleanup | Epic 4 | 4.3 | Planned |
| FR17 | Automatic fail-safe triggers | Epic 4 | 4.5 | Planned |
| FR18 | Emergency status monitoring | Epic 4 | 4.6 | Planned |
| FR19 | Emergency event logging | Epic 4 | 4.4 | Planned |
| FR20 | Update system configuration | Epic 6 | 6.1 | Planned |
| FR21 | Encrypt sensitive config data | Epic 6 | 6.2 | Planned |
| FR22 | Create encrypted backups | Epic 6 | 6.4 | Planned |
| FR23 | Restore from backups | Epic 6 | 6.5 | Planned |
| FR24 | Validate config changes | Epic 6 | 6.3 | Planned |
| FR25 | Configuration history/rollback | Epic 6 | 6.6 | Planned |
| FR26 | API key authentication | Epic 5 | 5.1 | Planned |
| FR27 | IP address authorization | Epic 5 | 5.3 | Planned |
| FR28 | API key rotation | Epic 5 | 5.4 | Planned |
| FR29 | Console emergency access | Epic 5 | 5.5 | Planned |
| FR30 | Security event logging | Epic 5 | 5.6 | Planned |
| FR31 | Rate limiting enforcement | Epic 5 | 5.2 | Planned |
| FR32 | Comprehensive health monitoring | Epic 7 | 7.1 | Planned |
| FR33 | Performance metrics tracking | Epic 7 | 7.2 | Planned |
| FR34 | Filtered system logs | Epic 7 | 7.5 | Planned |
| FR35 | Maintenance procedures | Epic 7 | 7.6 | Planned |
| FR36 | Operational dashboards | Epic 7 | 7.3 | Planned |
| FR37 | System alert generation | Epic 7 | 7.4 | Planned |
| FR38 | Service disguised as network-monitoring | Epic 1 | 1.3 | Complete |
| FR39 | Minimize network footprint | Epic 1 | 1.5 | Complete |
| FR40 | Plausible deniability interfaces | Epic 1 | 1.2 | Complete |
| FR41 | Automatic evidence cleanup | Epic 1 | 1.8 | Complete |
| FR42 | Appear as legitimate monitoring tool | Epic 1 | 1.3 | Complete |
| FR43 | Sub-second response times | Epic 1 | 1.2 | Complete |
| FR44 | Minimal resource consumption | Epic 1 | 1.3 | Complete |
| FR45 | 99.9% operational uptime | Epic 1 | 1.2 | Complete |

---

## Summary

**Epic Breakdown Complete:**

**7 Epics, 45 Stories Total:**
- **Epic 1 (Foundation):** 8 stories - Complete infrastructure deployment framework
- **Epic 2 (Device Communication):** 7 stories - Core time manipulation capabilities
- **Epic 3 (Scheduling):** 6 stories - Automated operation control
- **Epic 4 (Emergency Systems):** 6 stories - Bulletproof safety mechanisms
- **Epic 5 (Security):** 6 stories - Operational security and authentication
- **Epic 6 (Configuration):** 6 stories - Encrypted management systems
- **Epic 7 (Monitoring):** 6 stories - Operational visibility and maintenance

**FR Coverage:** All 45 functional requirements mapped to stories with complete traceability

**Implementation Ready:** Epic 1 provides complete foundation, remaining epics ready for development with clear acceptance criteria and technical implementation guidance

**Context Incorporated:** PRD requirements + Kubernetes architecture + GitOps deployment + 10-20 second scheduling + FastAPI framework + stealth operations

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._