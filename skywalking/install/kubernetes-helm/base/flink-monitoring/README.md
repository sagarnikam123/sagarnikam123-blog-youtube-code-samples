# Apache Flink Monitoring for SkyWalking

This directory contains configurations for monitoring Apache Flink in SkyWalking.

## Overview

| Component | Method | Port | SkyWalking Menu |
|-----------|--------|------|-----------------|
| **Flink JobManager** | Built-in Prometheus | 9249 | Flink → JobManager |
| **Flink TaskManager** | Built-in Prometheus | 9249 | Flink → TaskManager |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Apache Flink Cluster                        │
│  ┌─────────────────┐           ┌─────────────────┐              │
│  │   JobManager    │           │  TaskManager(s) │              │
│  │    :9249        │           │     :9249       │              │
│  └────────┬────────┘           └────────┬────────┘              │
│           │                             │                        │
│           └──────────┬──────────────────┘                        │
│                      │ /metrics                                  │
└──────────────────────┼──────────────────────────────────────────┘
                       │
                       ▼
          ┌─────────────────────────┐
          │     OTel Collector      │
          │  (Prometheus Receiver)  │
          └────────────┬────────────┘
                       │ OTLP
                       ▼
          ┌─────────────────────────┐
          │    SkyWalking OAP       │
          └─────────────────────────┘
```

## Quick Start

### 1. Enable Flink Prometheus Metrics

Add to `flink-conf.yaml`:

```yaml
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
metrics.reporter.prom.port: 9249
```

### 2. Enable OAP Rule

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,flink,..."
```

### 3. Update OTel Collector

Add Flink scrape configs from `otel-collector-flink.yaml`.

## Files

| File | Description |
|------|-------------|
| `flink-config.yaml` | Flink Prometheus configuration |
| `otel-collector-flink.yaml` | OTel Collector scrape configs |

## References

- [Flink Metrics](https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/metrics/)
- [SkyWalking Flink Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-flink-monitoring/)
