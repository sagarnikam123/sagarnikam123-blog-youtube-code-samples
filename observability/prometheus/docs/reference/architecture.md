# Architecture

This document describes the architecture of the Prometheus Installation and Testing Framework.

## Overview

The framework consists of three main modules:

1. **Installation Module** - Scripts and configurations for deploying Prometheus
2. **Configuration Module** - Scrape configurations for various targets
3. **Testing Module** - Comprehensive test suite for validation and performance analysis

## High-Level Architecture

```mermaid
graph TB
    subgraph "Test Runner Host (Local Laptop)"
        CLI[CLI Interface]
        K6[k6 Load Testing]
        PY[Python3 Scripts]
    end

    subgraph "Installation Module"
        BI[Binary Installer]
        DI[Docker Installer]
        HI[Helm Installer]
        OI[Operator Installer]
    end

    subgraph "Configuration Module"
        SC[Scrape Configs]
        SM[ServiceMonitors]
        PM[PodMonitors]
    end

    subgraph "Testing Module"
        TF[Test Framework Core]
        TR[Test Runner]
        TM[Metrics Collector]
        RP[Report Generator]
        PA[Prometheus API Client]
    end

    subgraph "Test Types"
        ST[Sanity Tests]
        IT[Integration Tests]
        LT[Load Tests]
        PT[Performance Tests]
        ScT[Scalability Tests]
        StT[Stress Tests]
        ET[Endurance Tests]
        RT[Reliability Tests]
        CT[Chaos Tests]
        RgT[Regression Tests]
        SeT[Security Tests]
    end

    subgraph "Deployment Modes"
        MP[Monolithic Prometheus]
        DP[Distributed Prometheus]
    end

    subgraph "Platforms"
        MK[Minikube]
        EKS[AWS EKS]
        GKE[Google GKE]
        AKS[Azure AKS]
        DC[Docker]
        BM[Bare Metal]
    end

    CLI --> TF
    K6 --> LT
    K6 --> StT
    K6 --> PT
    K6 --> ScT
    K6 --> ET
    PY --> TF

    BI --> BM
    DI --> DC
    HI --> MK
    HI --> EKS
    HI --> GKE
    HI --> AKS
    OI --> MK
    OI --> EKS
    OI --> GKE
    OI --> AKS

    BM --> MP
    DC --> MP
    MK --> MP
    MK --> DP
    EKS --> MP
    EKS --> DP
    GKE --> MP
    GKE --> DP
    AKS --> MP
    AKS --> DP

    TF --> TR
    TR --> TM
    TM --> RP
    TR --> PA

    TR --> ST
    TR --> IT
    TR --> LT
    TR --> PT
    TR --> ScT
    TR --> StT
    TR --> ET
    TR --> RT
    TR --> CT
    TR --> RgT
    TR --> SeT
```

## Directory Structure

```
prometheus/
├── install/                    # Installation Module
│   ├── binary/                 # Binary installation scripts
│   │   ├── install-linux.sh
│   │   ├── install-macos.sh
│   │   ├── install-windows.ps1
│   │   ├── prometheus.yml
│   │   ├── systemd/           # Linux service config
│   │   ├── launchd/           # macOS service config
│   │   └── windows/           # Windows service config
│   ├── docker/                # Docker installation
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.full.yml
│   │   ├── Dockerfile
│   │   └── prometheus.yml
│   ├── helm/                  # Helm installation
│   │   └── kube-prometheus-stack/
│   │       ├── base/
│   │       ├── versions/
│   │       └── environments/
│   └── operator/              # Operator installation
│       ├── olm/
│       ├── openshift/
│       └── prometheus/
├── conf/                      # Configuration Module
│   ├── scrape-configs/
│   │   ├── static/
│   │   ├── file-sd/
│   │   ├── kubernetes/
│   │   ├── exporters/
│   │   └── observability/
│   ├── servicemonitors/
│   └── podmonitors/
├── tests/                     # Testing Module
│   ├── framework/             # Core framework
│   ├── config/                # Test configurations
│   ├── k6/                    # k6 load test scripts
│   ├── sanity/
│   ├── integration/
│   ├── load-tests/
│   ├── stress-tests/
│   ├── performance/
│   ├── scalability/
│   ├── endurance/
│   ├── reliability/
│   ├── chaos/
│   ├── regression/
│   └── security/
└── docs/                      # Documentation
    ├── installation/
    ├── configuration/
    ├── testing/
    └── reference/
```

## Installation Module

### Binary Installation

```mermaid
flowchart LR
    subgraph "Binary Installer"
        DL[Download Binary]
        CF[Create Config]
        SV[Setup Service]
        DT[Create Data Dir]
    end

    DL --> CF --> SV --> DT

    subgraph "Platforms"
        LX[Linux/systemd]
        MC[macOS/launchd]
        WN[Windows/Service]
    end

    SV --> LX
    SV --> MC
    SV --> WN
```

Supports:
- Linux (amd64, arm64, armv7) with systemd
- macOS (amd64, arm64) with launchd
- Windows (amd64) with Windows Service

### Docker Installation

```mermaid
flowchart LR
    subgraph "Docker Compose"
        DC[docker-compose.yml]
        DCF[docker-compose.full.yml]
    end

    DC --> |Single Node| P[Prometheus]
    DCF --> |Full Stack| P
    DCF --> G[Grafana]
    DCF --> A[Alertmanager]
```

Provides:
- Single-node Prometheus deployment
- Full monitoring stack (Prometheus + Grafana + Alertmanager)
- Custom image builds with baked-in configuration

### Helm Installation

```mermaid
flowchart TB
    subgraph "Values Files"
        BV[base/values.yaml]
        VV[versions/values.yaml]
        EV[environments/values.yaml]
    end

    BV --> M[Merged Config]
    VV --> M
    EV --> M

    M --> H[Helm Install]
    H --> K[Kubernetes Cluster]
```

Supports:
- Environment-specific values (dev, staging, prod, minikube)
- Version-specific values (LTS v3.5.0, Latest v3.9.0)
- High availability configuration

### Operator Installation

```mermaid
flowchart LR
    subgraph "Installation Methods"
        OLM[OLM]
        OS[OpenShift]
        DIR[Direct]
    end

    OLM --> OP[Prometheus Operator]
    OS --> OP
    DIR --> OP

    OP --> CR[Prometheus CR]
    CR --> P[Prometheus Instance]
```

Supports:
- OpenShift OperatorHub
- OLM on vanilla Kubernetes
- Direct bundle installation
- Size templates (demo, small, medium, large)

## Testing Module

### Test Framework Core

```mermaid
classDiagram
    class TestConfig {
        +name: str
        +platform: str
        +deployment_mode: str
        +prometheus: PrometheusConfig
        +from_yaml()
        +merge_cli_args()
    }

    class TestRunner {
        +config: TestConfig
        +run_all()
        +run_suite()
        +get_exit_code()
    }

    class TestResult {
        +test_name: str
        +status: TestStatus
        +duration_seconds: float
        +errors: list
        +metrics: list
    }

    class ReportGenerator {
        +output_dir: Path
        +create_report()
        +save_report()
    }

    class PrometheusAPIClient {
        +base_url: str
        +healthcheck()
        +query()
        +query_range()
    }

    class PlatformDeployer {
        +deploy()
        +teardown()
        +get_prometheus_url()
        +is_healthy()
    }

    TestRunner --> TestConfig
    TestRunner --> TestResult
    TestRunner --> ReportGenerator
    TestRunner --> PrometheusAPIClient
    TestRunner --> PlatformDeployer
```

### Platform Deployers

```mermaid
classDiagram
    class PlatformDeployer {
        <<abstract>>
        +deploy()
        +teardown()
        +get_prometheus_url()
        +is_healthy()
        +is_ready()
        +get_deployment_mode()
    }

    class MinikubeDeployer {
        +deploy()
        +teardown()
    }

    class EKSDeployer {
        +deploy()
        +teardown()
    }

    class GKEDeployer {
        +deploy()
        +teardown()
    }

    class AKSDeployer {
        +deploy()
        +teardown()
    }

    class DockerDeployer {
        +deploy()
        +teardown()
    }

    class BinaryDeployer {
        +deploy()
        +teardown()
    }

    PlatformDeployer <|-- MinikubeDeployer
    PlatformDeployer <|-- EKSDeployer
    PlatformDeployer <|-- GKEDeployer
    PlatformDeployer <|-- AKSDeployer
    PlatformDeployer <|-- DockerDeployer
    PlatformDeployer <|-- BinaryDeployer
```

### Test Execution Flow

```mermaid
sequenceDiagram
    participant CLI
    participant Config
    participant Runner
    participant Deployer
    participant API
    participant Tests
    participant Reporter

    CLI->>Config: Load configuration
    Config-->>CLI: TestConfig
    CLI->>Runner: Create runner
    Runner->>Deployer: Deploy Prometheus
    Deployer-->>Runner: Deployment ready
    Runner->>API: Verify health
    API-->>Runner: Healthy

    loop For each test type
        Runner->>Tests: Execute tests
        Tests->>API: Query Prometheus
        API-->>Tests: Results
        Tests-->>Runner: TestResult
    end

    Runner->>Deployer: Teardown
    Runner->>Reporter: Generate report
    Reporter-->>CLI: Report files
```

## Deployment Modes

### Monolithic Prometheus

```mermaid
flowchart TB
    subgraph "Monolithic Deployment"
        P[Prometheus Server]
        TSDB[(TSDB)]
        WAL[(WAL)]
    end

    T1[Target 1] --> P
    T2[Target 2] --> P
    T3[Target N] --> P

    P --> TSDB
    P --> WAL

    Q[Queries] --> P
    A[Alerts] --> AM[Alertmanager]
    P --> A
```

Characteristics:
- Single instance
- Local TSDB storage
- Suitable for: development, small deployments
- Platforms: All (binary, Docker, Kubernetes)

### Distributed Prometheus

```mermaid
flowchart TB
    subgraph "Distributed Deployment"
        subgraph "Prometheus Replicas"
            P1[Prometheus 1]
            P2[Prometheus 2]
            P3[Prometheus N]
        end

        subgraph "Long-term Storage"
            TH[Thanos/Mimir]
            S3[(Object Storage)]
        end
    end

    T[Targets] --> P1
    T --> P2
    T --> P3

    P1 --> TH
    P2 --> TH
    P3 --> TH

    TH --> S3

    Q[Queries] --> TH
```

Characteristics:
- Multiple replicas for HA
- Federation or Thanos/Mimir for scaling
- Suitable for: production, large deployments
- Platforms: Kubernetes only (Minikube, EKS, GKE, AKS)

## Test Types Architecture

### Load Testing with k6

```mermaid
flowchart LR
    subgraph "Test Runner Host"
        K6[k6]
        SC[Scripts]
    end

    subgraph "Prometheus"
        API[/api/v1/query]
        RW[/api/v1/write]
    end

    SC --> K6
    K6 --> |HTTP Load| API
    K6 --> |Remote Write| RW
    K6 --> |Metrics| R[Results]
```

k6 scripts:
- `query-load.js` - Query endpoint load testing
- `query-range-load.js` - Range query load testing
- `remote-write-load.js` - Remote write load testing
- `stress-ramp.js` - Stress test ramping
- `scaling.js` - Scalability testing
- `soak.js` - Endurance/soak testing
- `benchmark.js` - Performance benchmarks

### Chaos Testing

```mermaid
flowchart TB
    subgraph "Chaos Framework"
        CM[Chaos Mesh]
        LT[Litmus]
    end

    subgraph "Chaos Scenarios"
        PK[Pod Kill]
        CK[Container Kill]
        NP[Network Partition]
        RP[Resource Pressure]
    end

    CM --> PK
    CM --> NP
    CM --> RP
    LT --> PK
    LT --> CK

    PK --> P[Prometheus]
    CK --> P
    NP --> P
    RP --> P
```

## Data Flow

### Test Results Flow

```mermaid
flowchart LR
    subgraph "Test Execution"
        T[Tests]
        M[Metrics]
        E[Errors]
    end

    subgraph "Results"
        TR[TestResult]
        TSR[TestSuiteResult]
    end

    subgraph "Reports"
        JSON[JSON]
        MD[Markdown]
        HTML[HTML]
        CSV[CSV]
    end

    T --> TR
    M --> TR
    E --> TR

    TR --> TSR
    TSR --> JSON
    TSR --> MD
    TSR --> HTML
    TSR --> CSV
```

### Configuration Flow

```mermaid
flowchart LR
    subgraph "Configuration Sources"
        YML[YAML File]
        CLI[CLI Args]
        ENV[Environment]
    end

    subgraph "Processing"
        LOAD[Load Config]
        VAL[Validate]
        MERGE[Merge]
    end

    subgraph "Output"
        TC[TestConfig]
    end

    YML --> LOAD
    LOAD --> VAL
    VAL --> MERGE
    CLI --> MERGE
    ENV --> MERGE
    MERGE --> TC
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface reference
- [Configuration Schema](config-schema.md) - YAML configuration reference
- [Glossary](glossary.md) - Terms and definitions
- [Test Types](../testing/test-types.md) - Description of each test type
