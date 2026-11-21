# Apache SkyWalking Installation Guide

Comprehensive installation scripts for Apache SkyWalking APM with BanyanDB storage.

## Storage: BanyanDB

All installation methods use **BanyanDB** as the storage backend - the native, optimized storage solution developed by the SkyWalking team.

## Installation Methods

| Method | Mode | Use Case | Directory |
|--------|------|----------|-----------|
| Binary | Standalone | Dev/Test, Single node | `install/binary-standalone/` |
| Docker | Standalone | Quick setup, Containers | `install/docker-standalone/` |
| Docker | Cluster | HA with load balancing | `install/docker-cluster/` |
| Helm | Standalone/Cluster | Kubernetes native | `install/kubernetes-helm/` |
| SWCK | Operator-managed | GitOps, K8s native | `install/kubernetes-swck/` |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SkyWalking Architecture                               │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Agents     │───▶│  OAP Server  │───▶│   BanyanDB   │                   │
│  │ (Java, Go,   │    │  (Backend)   │    │  (Storage)   │                   │
│  │  Python...)  │    │              │    │              │                   │
│  └──────────────┘    └──────┬───────┘    └──────────────┘                   │
│                             │                                                │
│                      ┌──────▼───────┐                                       │
│                      │     UI       │                                       │
│                      │  (Frontend)  │                                       │
│                      └──────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Docker Standalone (Simplest)

```bash
cd install/docker-standalone/
docker-compose up -d
# Access UI: http://localhost:8080
```

### Option 2: Binary Installation

```bash
cd install/binary-standalone/
./install-prerequisites.sh
./install-banyandb.sh
./install-skywalking.sh
cd ../../
./scripts/start-all.sh
```

### Option 3: Kubernetes Helm (Recommended for K8s)

```bash
cd install/kubernetes-helm/
./install.sh standalone   # or 'cluster' for HA
```

### Option 4: Kubernetes SWCK (Operator)

```bash
cd install/kubernetes-swck/
./install-operator.sh
./deploy-all.sh
```

## Component Versions

| Component | Version | Notes |
|-----------|---------|-------|
| SkyWalking APM | 10.3.0 | OAP Server + UI |
| BanyanDB | 0.9.0 | Native storage backend |
| Java Agent | 9.5.0 | Application monitoring |
| SWCK Operator | 0.9.0 | Kubernetes operator |
| Helm Chart | 4.8.0 | Kubernetes deployment |

## Ports Reference

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| OAP gRPC | 11800 | gRPC | Agent communication |
| OAP HTTP | 12800 | HTTP | REST API, GraphQL |
| UI | 8080 | HTTP | Web interface |
| BanyanDB gRPC | 17912 | gRPC | Storage backend |
| BanyanDB HTTP | 17913 | HTTP | Health check |

## Directory Structure

```
skywalking/
├── conf/                           # Shared configuration files
│   └── bydb.yaml                   # BanyanDB storage config
├── docs/                           # Documentation
├── install/
│   ├── binary-standalone/          # Native binary installation
│   ├── docker-standalone/          # Single-node Docker (BanyanDB)
│   ├── docker-cluster/             # Multi-node Docker cluster
│   ├── kubernetes-helm/            # Helm chart (BanyanDB)
│   └── kubernetes-swck/            # SWCK Operator (BanyanDB)
├── scripts/                        # Operational scripts
└── tests/                          # Validation tests
```

## Agent Configuration

Configure your application agents to connect to OAP:

```properties
# Java Agent
-javaagent:/path/to/skywalking-agent.jar
-Dskywalking.agent.service_name=my-service
-Dskywalking.collector.backend_service=localhost:11800
```

## Documentation

- [Official SkyWalking Docs](https://skywalking.apache.org/docs/)
- [BanyanDB Docs](https://skywalking.apache.org/docs/skywalking-banyandb/latest/)
- [SkyWalking Helm](https://github.com/apache/skywalking-helm)
- [SWCK Docs](https://skywalking.apache.org/docs/skywalking-swck/latest/)
