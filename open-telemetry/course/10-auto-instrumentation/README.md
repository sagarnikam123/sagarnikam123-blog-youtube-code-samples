# Module 10 — Zero-Code Auto-Instrumentation & Agents

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. What is Zero-Code Auto-Instrumentation?

**Auto-instrumentation** (also called zero-code or codeless instrumentation) generates telemetry from popular frameworks and libraries (HTTP servers, database drivers, RPC frameworks, message brokers) **without altering a single line of application source code**.

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Java Auto-Instrumentation (-javaagent)                   │
│    JVM Startup: java -javaagent:opentelemetry-javaagent.jar │
│    Mechanism: Bytecode manipulation via ByteBuddy at class- │
│               loading time. Instruments Spring, JDBC, etc.  │
├─────────────────────────────────────────────────────────────┤
│ 2. Python Auto-Instrumentation (opentelemetry-instrument)   │
│    Execution: opentelemetry-instrument python app.py        │
│    Mechanism: Runtime monkey-patching of imported modules   │
│               (Flask, Django, Requests, SQLAlchemy).        │
├─────────────────────────────────────────────────────────────┤
│ 3. Kubernetes Operator Auto-Injection                       │
│    Pod Annotation: instrumentation.opentelemetry.io/inject  │
│    Mechanism: Mutating Admission Webhook automatically      │
│               injects agent JARs/wheels via initContainers. │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Java Agent Configuration

The Java Agent (`opentelemetry-javaagent.jar`) is configured entirely via environment variables or Java system properties:

```bash
# Basic Execution
java -javaagent:./opentelemetry-javaagent.jar \
     -Dotel.service.name=catalog-service \
     -Dotel.exporter.otlp.endpoint=http://localhost:4317 \
     -jar app.jar
```

### Useful Java Agent Environment Variables

- `OTEL_JAVAAGENT_ENABLED=true` (global toggle)
- `OTEL_INSTRUMENTATION_COMMON_DEFAULT_ENABLED=true`
- `OTEL_INSTRUMENTATION_<NAME>_ENABLED=false` (e.g. `OTEL_INSTRUMENTATION_KAFKA_ENABLED=false` to silence noisy libraries)
- `OTEL_JAVAAGENT_DEBUG=true` (prints all instrumented classes to stdout)

---

## 3. Python Auto-Instrumentation CLI

```bash
# 1. Install standard agent & auto-detector
pip install opentelemetry-distro opentelemetry-instrumentation

# 2. Automatically install instrumentation packages for installed libraries
opentelemetry-bootstrap -a install

# 3. Run application wrapped in the agent
opentelemetry-instrument \
    --service_name order-service \
    --exporter_otlp_endpoint http://localhost:4318 \
    python app.py
```

---

## 4. Kubernetes Operator Auto-Injection

In Kubernetes, the **OpenTelemetry Operator** uses a Mutating Admission Webhook to inject the agent into your application pods automatically:

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: default-instrumentation
  namespace: observability
spec:
  exporter:
    endpoint: http://otel-collector.observability.svc.cluster.local:4318
  java:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:2.31.1
  python:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:0.45b0
---
# In your application Deployment:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: store-frontend
spec:
  template:
    metadata:
      annotations:
        # This single line injects the OpenTelemetry Agent!
        instrumentation.opentelemetry.io/inject-python: "true"
```

> [!IMPORTANT]
> **OTCA Exam Tip: Combining Zero-Code and Manual Instrumentation**
> Zero-code and manual instrumentation can be safely used together in the same application. The auto-instrumentation agent initializes the global `TracerProvider`, intercepts HTTP requests, and establishes the parent `SERVER` span. Developers can then call `trace.get_tracer()` inside business logic to create custom child spans with domain-specific attributes.

---

## 5. Official Documentation Links

- [OpenTelemetry Java Agent](https://opentelemetry.io/docs/zero-code/java/agent/)
- [OpenTelemetry Python Auto-Instrumentation](https://opentelemetry.io/docs/zero-code/python/)
- [OpenTelemetry Operator for Kubernetes](https://opentelemetry.io/docs/kubernetes/operator/)

---

## 6. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
| ------------ | ---------- | ------ | ------------- |
| [`01-python-auto`](./01-python-auto/) | Python | Wrap an uninstrumented HTTP server using `opentelemetry-instrument` | `opentelemetry-instrument python server.py` |
| [`02-java-agent`](./02-java-agent/) | Java | Launch an uninstrumented Java HTTP application with `-javaagent` | `java -javaagent:... -jar app.jar` |
| [`03-k8s-operator`](./03-k8s-operator/) | Kubernetes | Review and apply an `Instrumentation` CRD for Minikube | `kubectl apply -f instrumentation.yaml` |
