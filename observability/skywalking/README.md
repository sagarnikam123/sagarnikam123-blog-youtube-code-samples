# SkyWalking OpenTelemetry Integration

## OpenTelemetry Support in Satellite → OAP

### ✅ Metrics (Fully Supported)
- Satellite has dedicated plugins for OTLP metrics:
  - **Receiver**: `grpc-otlp-metrics-v1-receiver`
  - **Forwarder**: `otlp-metrics-v1-grpc-forwarder`
- Flow: `OpenTelemetry SDK/Collector → Satellite (OTLP receiver) → Satellite (OTLP forwarder) → OAP Server`

### ❌ Traces (Not via Satellite)
- OAP Server supports OTLP traces directly (via `otlp-traces` handler)
- But Satellite doesn't have OTLP trace receiver/forwarder plugins
- Flow: `OpenTelemetry SDK/Collector → OAP Server directly`

### ❌ Logs (Not via Satellite)
- OAP Server supports OTLP logs directly (via `otlp-logs` handler)
- But Satellite doesn't have OTLP log receiver/forwarder plugins
- Flow: `OpenTelemetry SDK/Collector → OAP Server directly`

## How to Send Metrics via Satellite

### Satellite Configuration Example

```yaml
# Satellite configuration
pipes:
  - common_config:
      pipe_name: otlp-metrics-pipe
    receiver:
      type: grpc-otlp-metrics-v1-receiver
      # Receives OTLP metrics on gRPC
    queue:
      type: memory-queue
    forwarder:
      type: otlp-metrics-v1-grpc-forwarder
      # Forwards to OAP server
      routing_label_keys: "net.host.name,host.name,job,service.name"
```

### OAP Server Configuration

```yaml
receiver-otel:
  selector: default
  default:
    enabledHandlers: "otlp-metrics,otlp-logs,otlp-traces"
```

## Summary

Only **Metrics** can be sent through Satellite using OpenTelemetry protocol. For **Traces** and **Logs**, you need to send them directly to the OAP server, bypassing Satellite.

## Sending Traces Directly to OAP (Without Satellite)

### OpenTelemetry Collector Configuration

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  otlp/skywalking:
    endpoint: skywalking-oap.skywalking.svc.cluster.local:11800
    tls:
      insecure: true

processors:
  batch: {}

service:
  pipelines:
    traces:
      receivers:
        - otlp
      processors:
        - batch
      exporters:
        - otlp/skywalking
```

### SkyWalking OAP Configuration

```yaml
receiver-otel:
  selector: default
  default:
    enabledHandlers: "otlp-traces,otlp-metrics,otlp-logs"

core:
  default:
    gRPCHost: 0.0.0.0
    gRPCPort: 11800  # Default port for receiving OTLP data
    restHost: 0.0.0.0
    restPort: 12800
```

### Key Points

- OTLP traces are sent to OAP's gRPC port (default: **11800**)
- The endpoint format is `host:port` (no protocol prefix)
- OAP must have `otlp-traces` handler enabled
- Use `insecure: true` for non-TLS connections in Kubernetes

## References

- [OpenTelemetry Metrics Receiver](https://skywalking.apache.org/docs/main/next/en/setup/backend/opentelemetry-receiver/)
- [OTLP Trace Format](https://skywalking.apache.org/docs/main/next/en/setup/backend/otlp-trace/)
- [OTLP Log Format](https://skywalking.apache.org/docs/main/next/en/setup/backend/log-otlp/)
- [Satellite OTLP Metrics Receiver](https://skywalking.apache.org/docs/skywalking-satellite/next/en/setup/plugins/receiver_grpc-otlp-metrics-v1-receiver/)
- [Satellite OTLP Metrics Forwarder](https://skywalking.apache.org/docs/skywalking-satellite/next/en/setup/plugins/forwarder_otlp-metrics-v1-grpc-forwarder/)
