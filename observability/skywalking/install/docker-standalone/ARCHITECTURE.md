# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Compose Network                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Storage Layer                                │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  BanyanDB (Standalone)                                       │   │    │
│  │  │  • Metadata storage                                          │   │    │
│  │  │  • Measure data (metrics)                                    │   │    │
│  │  │  • Stream data (logs, traces)                                │   │    │
│  │  │  • Property data                                             │   │    │
│  │  │                                                              │   │    │
│  │  │  Ports:                                                      │   │    │
│  │  │  • 17912 (gRPC)                                              │   │    │
│  │  │  • 17913 (HTTP/Health)                                       │   │    │
│  │  │  • 2121 (Prometheus Metrics)                                 │   │    │
│  │  │                                                              │   │    │
│  │  │  Volume: banyandb-data                                       │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                         │
│                                    │ gRPC (17912)                            │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Processing Layer                                │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  SkyWalking OAP Server                                       │   │    │
│  │  │  • Receives logs/traces/metrics from agents                  │   │    │
│  │  │  • Processes and stores in BanyanDB                          │   │    │
│  │  │  • Evaluates alarm rules                                     │   │    │
│  │  │  • Sends alerts to Teams webhook                             │   │    │
│  │  │  • Exposes GraphQL API                                       │   │    │
│  │  │                                                              │   │    │
│  │  │  Ports:                                                      │   │    │
│  │  │  • 11800 (gRPC - Agent communication)                        │   │    │
│  │  │  • 12800 (HTTP - REST API, GraphQL)                          │   │    │
│  │  │  • 1234 (Prometheus Metrics)                                 │   │    │
│  │  │                                                              │   │    │
│  │  │  Config: config/alarm-settings.yml                           │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                         │
│                                    │ HTTP (12800)                            │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Presentation Layer                              │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  SkyWalking UI                                               │   │    │
│  │  │  • Web interface for visualization                           │   │    │
│  │  │  • Service topology                                          │   │    │
│  │  │  • Trace viewer                                              │   │    │
│  │  │  • Log viewer                                                │   │    │
│  │  │  • Metrics dashboards                                        │   │    │
│  │  │                                                              │   │    │
│  │  │  Port: 8080 (HTTP)                                           │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                    ▲                                         │
│                                    │ gRPC (11800)                            │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Data Generation Layer                           │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────┐    ┌──────────────────────────┐       │    │
│  │  │  fuzzy-train-python      │    │  fuzzy-train-java        │       │    │
│  │  │  • Python SkyWalking     │    │  • Java SkyWalking       │       │    │
│  │  │    agent                 │    │    agent                 │       │    │
│  │  │  • Generates fake logs   │    │  • Generates fake logs   │       │    │
│  │  │  • 1 log per second      │    │  • 1 log per second      │       │    │
│  │  │  • Random log levels     │    │  • Random log levels     │       │    │
│  │  │  • Sends to OAP:11800    │    │  • Sends to OAP:11800    │       │    │
│  │  └──────────────────────────┘    └──────────────────────────┘       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ HTTPS Webhook
                                     ▼
                          ┌──────────────────────┐
                          │  Microsoft Teams     │
                          │  Power Automate      │
                          │  Webhook             │
                          └──────────────────────┘
```

## Data Flow

### 1. Log Generation Flow
```
fuzzy-train-python ──┐
                     ├──► OAP Server (11800) ──► BanyanDB (17912) ──► Storage
fuzzy-train-java ────┘
```

### 2. Visualization Flow
```
User Browser ──► UI (8080) ──► OAP GraphQL API (12800) ──► BanyanDB (17912) ──► Data
```

### 3. Alerting Flow
```
OAP Alarm Engine ──► Evaluate Rules ──► Trigger Alert ──► Teams Webhook ──► Teams Channel
```

## Component Details

### BanyanDB
- **Type**: Time-series database optimized for observability
- **Mode**: Standalone (single node)
- **Storage**: Docker volume `banyandb-data`
- **Data Types**:
  - Metadata: Service/instance/endpoint definitions
  - Measure: Metrics data (counters, gauges, histograms)
  - Stream: Logs and traces
  - Property: Tags and labels

### OAP Server
- **Type**: Observability Analysis Platform
- **Functions**:
  - Receives telemetry from agents
  - Processes and aggregates data
  - Stores in BanyanDB
  - Evaluates alarm rules
  - Exposes GraphQL API
- **Receivers**:
  - SkyWalking native protocol (gRPC)
  - OpenTelemetry (OTLP)
  - Zipkin
  - Jaeger

### SkyWalking UI
- **Type**: Web application
- **Features**:
  - Service topology visualization
  - Distributed trace viewer
  - Log search and viewer
  - Metrics dashboards
  - Alarm viewer

### Fuzzy-Train Generators
- **Type**: Fake log generators
- **Purpose**: Testing and demonstration
- **Languages**: Python and Java
- **Output**: Random logs with various levels (INFO, WARN, ERROR)
- **Rate**: Configurable (default 1 log/sec)

## Network Communication

| From | To | Port | Protocol | Purpose |
|------|-----|------|----------|---------|
| fuzzy-train-python | oap | 11800 | gRPC | Send logs |
| fuzzy-train-java | oap | 11800 | gRPC | Send logs |
| oap | banyandb | 17912 | gRPC | Store data |
| ui | oap | 12800 | HTTP | Query data |
| oap | Teams | 443 | HTTPS | Send alerts |
| Browser | ui | 8080 | HTTP | Access UI |

## Alarm Rules

Configured in `config/alarm-settings.yml`:

### Performance Alarms
- Service response time > 1s for 3 minutes
- Service SLA < 80% for 2 minutes
- Service percentile (p50/75/90/95/99) > 1s
- Instance response time > 1s for 2 minutes
- Endpoint response time > 1s for 2 minutes
- Database response time > 1s for 2 minutes

### Log-based Alarms
- ERROR logs > 10 in 5 minutes
- WARN logs > 50 in 5 minutes

### Alert Delivery
- Destination: Microsoft Teams
- Method: Power Automate webhook
- Format: JSON payload with alarm details

## Resource Requirements

### Minimum
- CPU: 2 cores
- Memory: 2 GB
- Disk: 5 GB

### Recommended
- CPU: 4 cores
- Memory: 4 GB
- Disk: 20 GB

### Per Container
| Container | CPU | Memory |
|-----------|-----|--------|
| banyandb | 500m | 512Mi |
| oap | 1000m | 1024Mi |
| ui | 200m | 256Mi |
| fuzzy-train-python | 100m | 128Mi |
| fuzzy-train-java | 200m | 256Mi |

## Scaling Considerations

### Current Setup (Standalone)
- Single BanyanDB instance
- Single OAP instance
- Single UI instance
- Suitable for: Development, testing, small deployments

### Production Setup (Cluster)
For production, consider:
- BanyanDB cluster mode (liaison + data nodes)
- Multiple OAP instances with load balancer
- Multiple UI instances
- External etcd for BanyanDB coordination
- Persistent storage (not Docker volumes)

## Monitoring

### Self-Observability
- OAP metrics: http://localhost:1234/metrics
- BanyanDB metrics: http://localhost:2121/metrics

### Health Checks
- OAP: http://localhost:12800/healthcheck
- BanyanDB: http://localhost:17913/api/healthz

### Logs
```bash
docker compose -f docker-compose.fuzzy-train.yml logs -f [service]
```

## Security Considerations

### Current Setup
- No authentication/authorization
- HTTP only (no TLS)
- Suitable for: Local development only

### Production Recommendations
- Enable TLS for all communications
- Implement authentication (OAuth, OIDC)
- Use secrets management for webhook URLs
- Network isolation (private networks)
- Regular security updates
