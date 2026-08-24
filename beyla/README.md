# Beyla — eBPF auto-instrumentation

Beyla (now also [OpenTelemetry eBPF Instrumentation / OBI](https://github.com/open-telemetry/opentelemetry-ebpf-instrumentation)) provides zero-code, eBPF-based automatic instrumentation for HTTP/gRPC applications. It generates OpenTelemetry traces and RED metrics without any code changes.

## Installation modes

| Mode | Guide |
|:-----|:------|
| Binary standalone | [`install/binary/`](install/binary/) |
| Docker / Docker Compose | [`install/docker/`](install/docker/) |
| Kubernetes DaemonSet | [`install/k8s/`](install/k8s/) |
| Helm chart | [`install/helm/`](install/helm/) |

## Quick start (binary)

```bash
export BEYLA_OPEN_PORT=8080
export BEYLA_PROMETHEUS_PORT=9400
sudo -E ./beyla
```

Metrics at <http://localhost:9400/metrics>.

## Key facts

- eBPF-based: kernel 5.8+, Linux only, privileged access required
- Zero code changes: instruments Go, Java, .NET, Node.js, Python, Ruby, Rust, C/C++
- Vendor-agnostic: exports OTLP or Prometheus
- Donated to CNCF OpenTelemetry as OBI; `grafana/beyla` remains the active distribution
- Apache 2.0 license

Official site: [grafana.com/oss/beyla-ebpf](https://grafana.com/oss/beyla-ebpf/)
