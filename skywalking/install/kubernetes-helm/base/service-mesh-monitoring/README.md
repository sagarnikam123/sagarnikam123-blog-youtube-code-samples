# Service Mesh Monitoring for SkyWalking

This directory contains configurations for monitoring Service Mesh (Istio/Envoy) in SkyWalking.

## Overview

SkyWalking supports Service Mesh monitoring through:
1. **Envoy ALS (Access Log Service)** - Direct integration with Envoy proxies
2. **Prometheus Metrics** - Scraping Istio control plane and data plane metrics

## Supported Components

| Component | Method | SkyWalking Menu | Status |
|-----------|--------|-----------------|--------|
| **Istio Control Plane** | Prometheus | Service Mesh → Control Plane | ✅ Ready |
| **Istio Data Plane** | Envoy ALS + Prometheus | Service Mesh → Data Plane | ✅ Ready |
| **Envoy Proxy** | ALS (gRPC) | Service Mesh → Services | ✅ Ready |
| **Services** | Envoy ALS | Service Mesh → Services | ✅ Ready |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Cluster                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Istio Control Plane                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │   istiod    │  │   istiod    │  │   istiod    │  (HA mode)       │   │
│  │  │   :15014    │  │   :15014    │  │   :15014    │                  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │   │
│  │         └────────────────┼────────────────┘                          │   │
│  │                          │ Prometheus metrics                        │   │
│  └──────────────────────────┼──────────────────────────────────────────┘   │
│                             │                                               │
│  ┌──────────────────────────┼──────────────────────────────────────────┐   │
│  │                    Data Plane (Envoy Sidecars)                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ App + Envoy │  │ App + Envoy │  │ App + Envoy │                  │   │
│  │  │   :15090    │  │   :15090    │  │   :15090    │                  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │   │
│  │         │                │                │                          │   │
│  │         │ ALS (gRPC)     │                │                          │   │
│  │         └────────────────┼────────────────┘                          │   │
│  └──────────────────────────┼──────────────────────────────────────────┘   │
│                             │                                               │
│                             ▼                                               │
│              ┌─────────────────────────────┐                                │
│              │      SkyWalking OAP         │                                │
│              │  (Envoy ALS Receiver)       │                                │
│              │       :11800                │                                │
│              └─────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Method 1: Envoy ALS (Recommended)

Envoy Access Log Service sends telemetry directly to SkyWalking OAP.

#### 1. Enable ALS Receiver in OAP

```yaml
oap:
  env:
    SW_ENVOY_METRIC_ALS_HTTP_ANALYSIS: "k8s-mesh"
    SW_ENVOY_METRIC_ALS_TCP_ANALYSIS: "k8s-mesh"
```

#### 2. Configure Istio to Send ALS to SkyWalking

```bash
kubectl apply -f istio-als-config.yaml
```

### Method 2: Prometheus Metrics

For control plane metrics and additional data plane metrics.

#### 1. Enable OAP Rules

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "istio-controlplane"
```

#### 2. Update OTel Collector

Add Istio scrape configs from `otel-collector-mesh.yaml`.

## Files

| File | Description |
|------|-------------|
| `istio-als-config.yaml` | Istio EnvoyFilter for ALS |
| `oap-mesh-config.yaml` | OAP configuration for mesh |
| `otel-collector-mesh.yaml` | OTel Collector scrape configs |

## References

- [SkyWalking Service Mesh](https://skywalking.apache.org/docs/main/latest/en/setup/envoy/als_setting/)
- [Istio Observability](https://istio.io/latest/docs/tasks/observability/)
- [Envoy ALS](https://www.envoyproxy.io/docs/envoy/latest/api-v3/service/accesslog/v3/als.proto)
