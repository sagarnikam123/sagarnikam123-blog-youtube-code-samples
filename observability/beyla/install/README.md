# Beyla (OpenTelemetry eBPF Instrumentation) — installation modes

Beyla provides eBPF-based zero-code auto-instrumentation for HTTP/gRPC applications. It produces OpenTelemetry traces and RED metrics without modifying application code.

> **Note:** Beyla has been donated to CNCF as [OpenTelemetry eBPF Instrumentation (OBI)](https://github.com/open-telemetry/opentelemetry-ebpf-instrumentation). The `grafana/beyla` distribution remains actively maintained.

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available | [`binary/`](binary/) | Download + run with env vars or config file |
| Docker / Docker Compose | Available | [`docker/`](docker/) | Shared PID namespace with target container |
| Kubernetes DaemonSet (raw YAML) | Available | [`k8s/`](k8s/) | Plain manifests — privileged DaemonSet |
| Helm chart (DaemonSet) | Available | [`helm/`](helm/) | Official `grafana/beyla` chart |

## Requirements

- Linux kernel 5.8+ with BTF enabled (`/sys/kernel/btf/vmlinux` must exist)
- Privileged access (sudo, CAP_SYS_ADMIN + CAP_BPF, or privileged pods)
- Does NOT work on macOS/Windows Docker Desktop (no eBPF support)

## Supported languages

Go, Java, .NET, Node.js, Python, Ruby, Rust, C/C++ — any language producing HTTP/gRPC traffic.

## Export modes

- **Prometheus**: scrape metrics at `:9400/metrics`
- **OTLP direct**: push traces + metrics to any OTLP endpoint
- **Alloy mode**: send to Grafana Alloy for processing

Official sources:
- [Grafana Beyla docs](https://grafana.com/docs/beyla/latest/)
- [GitHub — grafana/beyla](https://github.com/grafana/beyla)
- [OBI upstream](https://github.com/open-telemetry/opentelemetry-ebpf-instrumentation)
- [Helm chart docs](https://grafana.com/docs/beyla/latest/setup/kubernetes-helm/)
