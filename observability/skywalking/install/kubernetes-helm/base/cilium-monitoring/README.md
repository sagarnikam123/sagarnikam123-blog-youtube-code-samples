# Cilium Monitoring for SkyWalking

This directory contains configurations for monitoring Cilium in SkyWalking.

## Overview

Cilium provides eBPF-based networking, security, and observability for Kubernetes.
SkyWalking can monitor Cilium through its built-in Prometheus metrics.

## Supported Components

| Component | Method | Port | SkyWalking Menu | Status |
|-----------|--------|------|-----------------|--------|
| **Cilium Agent** | Prometheus | 9962 | Cilium → Cilium Service | ✅ Ready |
| **Cilium Operator** | Prometheus | 9963 | Cilium → Cilium Service | ✅ Ready |
| **Hubble** | Prometheus | 9965 | Cilium → Cilium Service | ✅ Ready |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Cluster                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Cilium Control Plane                              │   │
│  │  ┌─────────────────┐           ┌─────────────────┐                  │   │
│  │  │ Cilium Operator │           │  Hubble Relay   │                  │   │
│  │  │     :9963       │           │     :9965       │                  │   │
│  │  └────────┬────────┘           └────────┬────────┘                  │   │
│  │           └────────────────────────────┬┘                           │   │
│  └────────────────────────────────────────┼────────────────────────────┘   │
│                                           │                                 │
│  ┌────────────────────────────────────────┼────────────────────────────┐   │
│  │                    Cilium Data Plane (DaemonSet)                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │Cilium Agent │  │Cilium Agent │  │Cilium Agent │  (per node)      │   │
│  │  │   :9962     │  │   :9962     │  │   :9962     │                  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │   │
│  │         └────────────────┼────────────────┘                          │   │
│  └──────────────────────────┼──────────────────────────────────────────┘   │
│                             │ /metrics                                      │
│                             ▼                                               │
│              ┌─────────────────────────────┐                                │
│              │      OTel Collector         │                                │
│              │   (Prometheus Receiver)     │                                │
│              └──────────────┬──────────────┘                                │
│                             │ OTLP                                          │
│                             ▼                                               │
│              ┌─────────────────────────────┐                                │
│              │      SkyWalking OAP         │                                │
│              └─────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Enable Cilium Prometheus Metrics

Cilium metrics are enabled by default. Verify with:

```bash
# Check Cilium agent metrics
kubectl exec -n kube-system ds/cilium -- cilium metrics list

# Check metrics endpoint
kubectl port-forward -n kube-system ds/cilium 9962:9962
curl http://localhost:9962/metrics
```

### 2. Enable OAP Rule

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,cilium-service,..."
```

### 3. Update OTel Collector

Add Cilium scrape configs from `otel-collector-cilium.yaml`.

## Cilium Installation with Metrics

If installing Cilium fresh, enable metrics:

```bash
helm install cilium cilium/cilium \
  --namespace kube-system \
  --set prometheus.enabled=true \
  --set operator.prometheus.enabled=true \
  --set hubble.enabled=true \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}" \
  --set hubble.relay.enabled=true
```

## Files

| File | Description |
|------|-------------|
| `cilium-config.yaml` | Cilium Prometheus configuration |
| `otel-collector-cilium.yaml` | OTel Collector scrape configs |

## Key Metrics

| Metric | Description |
|--------|-------------|
| `cilium_endpoint_count` | Number of endpoints managed |
| `cilium_policy_count` | Number of policies |
| `cilium_datapath_errors_total` | Datapath errors |
| `hubble_flows_processed_total` | Flows processed by Hubble |
| `cilium_bpf_map_ops_total` | BPF map operations |

## References

- [Cilium Metrics](https://docs.cilium.io/en/stable/observability/metrics/)
- [SkyWalking Cilium Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-cilium-monitoring/)
- [Hubble Observability](https://docs.cilium.io/en/stable/observability/hubble/)
