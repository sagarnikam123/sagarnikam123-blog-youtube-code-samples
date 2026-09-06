# OpenTelemetry Field Cheatsheet

> Quick reference guide for the OpenTelemetry Certified Associate (OTCA) exam, daily pipeline operations, and SDK instrumentation.

---

## 1. Standard Port Mapping

| Port | Protocol / Path | Purpose |
| ------ | ----------------- | --------- |
| **4317** | gRPC | Standard OTLP gRPC receiver endpoint |
| **4318** | HTTP (`/v1/*`) | Standard OTLP HTTP receiver endpoint (`/v1/traces`, `/v1/metrics`, `/v1/logs`) |
| **16686** | HTTP | Jaeger v2 Web UI |
| **9090** | HTTP | Prometheus Web UI & query API |
| **3000** | HTTP | Grafana Web UI |
| **3100** | HTTP | Loki HTTP API |
| **3200** | HTTP | Tempo HTTP API |
| **8888** | HTTP | OpenTelemetry Collector internal Prometheus metrics (`/metrics`) |
| **8889** | HTTP | Prometheus exporter endpoint for scraped metrics |
| **13133** | HTTP | Collector Health Check extension (`/`) |
| **55679** | HTTP | Collector zPages extension (`/debug/tracez`, `/debug/servicez`) |

---

## 2. Standard Environment Variables

### Universal SDK Configuration

| Environment Variable | Default Value | Description |
| ---------------------- | --------------- | ------------- |
| `OTEL_SERVICE_NAME` | `unknown_service` | Logical name of the service |
| `OTEL_RESOURCE_ATTRIBUTES` | *(empty)* | Key-value pairs: `service.version=1.0.0,deployment.environment=production` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` (HTTP) or `http://localhost:4317` (gRPC) | Base OTLP receiver endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` or `grpc` | Transport protocol: `grpc`, `http/protobuf`, `http/json` |
| `OTEL_EXPORTER_OTLP_HEADERS` | *(empty)* | Key-value headers: `api-key=secret,Authorization=Bearer xxx` |
| `OTEL_EXPORTER_OTLP_TIMEOUT` | `10000` (10s) | Max timeout in milliseconds |
| `OTEL_LOG_LEVEL` | `info` | Internal SDK logging level (`debug`, `info`, `warn`, `error`) |

### Signal-Specific Endpoints (Overrides Universal)

| Environment Variable | Description |
|----------------------|-------------|
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | Target endpoint for traces only (e.g., `http://collector:4318/v1/traces`) |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`| Target endpoint for metrics only (e.g., `http://collector:4318/v1/metrics`) |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | Target endpoint for logs only (e.g., `http://collector:4318/v1/logs`) |

### Traces & Sampling

| Environment Variable | Values | Description |
| ---------------------- | -------- | ------------- |
| `OTEL_TRACES_SAMPLER` | `always_on`, `always_off`, `traceidratio`, `parentbased_always_on`, `parentbased_traceidratio` | Built-in sampler strategy |
| `OTEL_TRACES_SAMPLER_ARG` | `0.0` - `1.0` | Ratio argument when using `traceidratio` or `parentbased_traceidratio` |
| `OTEL_PROPAGATORS` | `tracecontext,baggage` | Comma-separated list of propagators: `tracecontext`, `baggage`, `b3`, `b3multi`, `jaeger` |

---

## 3. Distributed Context Propagation Headers

### W3C Trace Context (`traceparent`)

Format: `version-trace_id-parent_id-trace_flags`
Example: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`

- `00`: 1-byte version (currently `00`)
- `4bf92f3577b34da6a3ce929d0e0e4736`: 16-byte (32-hex-char) Trace ID
- `00f067aa0ba902b7`: 8-byte (16-hex-char) Parent / Span ID
- `01`: 1-byte Trace Flags bitmask (`01` = Sampled, `00` = Not Sampled)

### W3C Baggage

Format: Comma-separated `key=value` pairs with optional metadata:
Example: `userId=alice,region=us-east-1;ttl=30`

- **Notice**: Baggage is passed across distributed services but is **NOT** automatically attached to span attributes unless explicitly mapped.

---

## 4. Modern Semantic Conventions (v1.28+)

| Domain | Attribute | Description / Example |
| -------- | ----------- | ----------------------- |
| **Service** | `service.name` | Name of the service (e.g., `order-service`) |
| | `service.version` | Service build version (e.g., `1.4.2`) |
| | `service.namespace` | Logical grouping (e.g., `checkout`) |
| **HTTP (Client/Server)** | `http.request.method` | `GET`, `POST`, `PUT`, `DELETE` *(replaces `http.method`)* |
| | `http.response.status_code` | Integer HTTP status: `200`, `404`, `500` *(replaces `http.status_code`)* |
| | `url.full` | Full URL (e.g., `https://api.example.com/orders?id=123`) |
| | `url.path` | URL path component (e.g., `/orders`) |
| | `server.address` | Server hostname/IP (e.g., `api.example.com`) *(replaces `net.peer.name`)* |
| | `server.port` | Server port (e.g., `443`, `8080`) |
| **Database** | `db.system` | `postgresql`, `mysql`, `redis`, `mongodb` |
| | `db.operation` | `SELECT`, `INSERT`, `UPDATE`, `HGET` |
| | `db.name` | Target database catalog name |

---

## 5. OpenTelemetry Collector Architecture

A collector configuration YAML comprises four root blocks:

```yaml
receivers:       # 1. How data enters the collector (push or pull)
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:      # 2. How data is batched, filtered, modified, or scrubbed
  memory_limiter:
    check_interval: 1s
    limit_percentage: 75
    spike_limit_percentage: 20
  batch:
    send_batch_size: 8192
    timeout: 200ms

exporters:       # 3. Where telemetry is sent (Jaeger, Prometheus, Loki, etc.)
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  debug:
    verbosity: detailed

extensions:      # 4. Auxiliary capabilities (health check, pprof, zPages)
  health_check:
    endpoint: 0.0.0.0:13133
  zpages:
    endpoint: 0.0.0.0:55679

service:
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo, debug]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug]
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888
```

---

## 6. OpenTelemetry Transformation Language (OTTL)

OTTL operates directly on contexts: `resource`, `scope`, `span`, `spanevent`, `metric`, `datapoint`, `log`.

```yaml
processors:
  transform:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          # Add custom attribute
          - set(attributes["env"], "production")
          # Mask sensitive query params
          - replace_pattern(attributes["url.full"], "password=[^&]+", "password=REDACTED")
          # Promote attribute to resource level
          - set(resource.attributes["region"], attributes["cloud.region"])
```

---

## 7. Minimal SDK Quickstarts

### Python (Manual SDK Initializer)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# 1. Define Resource
resource = Resource.create({"service.name": "order-service", "service.version": "1.0.0"})

# 2. Configure Tracer Provider
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# 3. Create Span
tracer = trace.get_tracer("order-tracer")
with tracer.start_as_current_span("process-order") as span:
    span.set_attribute("http.request.method", "POST")
    span.set_attribute("order.id", "45892")
```

### Java (Manual SDK Initializer)

```java
import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;

Resource resource = Resource.getDefault()
    .merge(Resource.create(Attributes.of(AttributeKey.stringKey("service.name"), "order-service")));

OtlpGrpcSpanExporter exporter = OtlpGrpcSpanExporter.builder()
    .setEndpoint("http://localhost:4317")
    .build();

SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
    .setResource(resource)
    .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
    .build();

OpenTelemetrySdk openTelemetry = OpenTelemetrySdk.builder()
    .setTracerProvider(tracerProvider)
    .buildAndRegisterGlobal();

Tracer tracer = openTelemetry.getTracer("order-tracer");
Span span = tracer.spanBuilder("process-order").startSpan();
try {
    span.setAttribute("http.request.method", "POST");
} finally {
    span.end();
}
```
