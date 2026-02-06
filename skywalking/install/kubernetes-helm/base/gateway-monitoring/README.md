# Gateway Monitoring for SkyWalking

This directory contains configurations for monitoring API Gateways in SkyWalking.

## Supported Gateways

| Gateway | Exporter | SkyWalking Menu | Status |
|---------|----------|-----------------|--------|
| **Nginx** | nginx-prometheus-exporter | Gateway → NGINX | ✅ Ready |
| **APISIX** | Built-in Prometheus | Gateway → APISIX | ✅ Ready |
| **Kong** | kong-prometheus-plugin | Gateway → Kong | ✅ Ready |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Nginx       │     │     APISIX      │     │      Kong       │
│   (Gateway)     │     │   (Gateway)     │     │   (Gateway)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ nginx-exporter  │     │ Built-in Prom   │     │ kong-prometheus │
│    :9113        │     │    :9091        │     │    :8001        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     OTel Collector      │
                    │  (Prometheus Receiver)  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    SkyWalking OAP       │
                    └─────────────────────────┘
```

## Quick Start

### 1. Enable Gateway Rules in OAP

Update your values.yaml to include gateway rules:

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,nginx,apisix,kong,..."
```

### 2. Deploy Gateway Exporter

Choose your gateway and deploy the corresponding exporter:

```bash
# Nginx
kubectl apply -f nginx-exporter.yaml -n <nginx-namespace>

# APISIX (built-in, just enable in config)
# See apisix-config.yaml

# Kong
kubectl apply -f kong-prometheus.yaml -n <kong-namespace>
```

### 3. Update OTel Collector

Add the gateway scrape configs to your OTel Collector configuration.

## Files

| File | Description |
|------|-------------|
| `nginx-exporter.yaml` | Nginx Prometheus Exporter deployment |
| `apisix-config.yaml` | APISIX Prometheus plugin configuration |
| `kong-prometheus.yaml` | Kong Prometheus plugin configuration |
| `otel-collector-gateway.yaml` | OTel Collector scrape configs for gateways |

## References

- [SkyWalking Nginx Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-nginx-monitoring/)
- [SkyWalking APISIX Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-apisix-monitoring/)
- [SkyWalking Kong Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-kong-monitoring/)
