# Module 12 — Collector Deployment Patterns (Agent vs Gateway)

> **OTCA Exam Alignment:** Domain 3 — OpenTelemetry Collector (26% Exam Weight)

---

## 1. The Four Deployment Topologies

Selecting the right Collector deployment model balances infrastructure resource cost, operational resilience, and processing capabilities.

```text
1. HOST AGENT (DaemonSet)          2. GATEWAY CLUSTER (Service)
┌────────────┐ ┌────────────┐      ┌────────────────────────────┐
│ App Pod 1  │ │ App Pod 2  │      │ Load Balancer (NLB)        │
└─────┬──────┘ └─────┬──────┘      └─────────────┬──────────────┘
      │ localhost    │                           │
      ▼              ▼             ┌─────────────┴──────────────┐
┌───────────────────────────┐      │                            │
│ Node Agent Collector      │      ▼                            ▼
│ (DaemonSet on K8s Node)   │   ┌───────────────┐        ┌───────────────┐
└─────────────┬─────────────┘   │ Gateway Pod 1 │        │ Gateway Pod 2 │
              │                 └───────┬───────┘        └───────┬───────┘
              └─────────────────────────┼────────────────────────┘
                                        ▼
                            Observability Backends
```

### Topology Comparison Matrix

| Pattern | Where It Runs | Primary Benefits | Trade-offs |
| --------- | --------------- | ------------------ | ------------ |
| **1. Host Agent** | DaemonSet (per node) or systemd (per VM) | Near-zero network hop latency from apps; can collect host/node OS metrics; adds node metadata. | Cannot do centralized tail sampling across multiple nodes. |
| **2. Gateway Cluster** | Centralized auto-scaling deployment behind an NLB | Centralizes API credentials and vendor secrets; handles high-CPU tail sampling and OTTL; shields backends. | Additional network hop; requires load balancing. |
| **3. Pod Sidecar** | Container inside the application pod | Complete security isolation per pod; local loopback network. | Extremely high resource overhead (wastes memory across thousands of pods). |
| **4. Hybrid (Agent + Gateway)** | **Production Gold Standard** | Agent enriches host/pod metadata; Gateway clusters handle heavy batching, sampling, and vendor auth. | Highest operational complexity. |

---

## 2. Why Never Send Direct from App to Backend?

Sending telemetry directly from application code to a vendor or backend (e.g. Jaeger or Datadog) is an enterprise anti-pattern:

1. **Secret Leakage:** Every application container must be provisioned with backend API secrets.
2. **Brittle Upgrades:** Changing backend URLs or auth methods requires redeploying every microservice in the company.
3. **No Centralized Filtering:** Applications burn bandwidth transmitting unwanted debug spans and unmasked PII.

---

## 3. Official Documentation Links

- [OpenTelemetry Collector Deployment Topologies](https://opentelemetry.io/docs/collector/deployment/)
- [Kubernetes DaemonSet Architecture Guide](https://opentelemetry.io/docs/kubernetes/collector/)

---

## 4. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-agent-gateway`](./01-agent-gateway/) | YAML / Docker | Deploy a 2-tier architecture (Agent Collector forwarding to Gateway Collector) | `docker compose up` |
