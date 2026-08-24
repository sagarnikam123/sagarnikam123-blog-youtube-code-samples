# Beyla — binary standalone

Download and run Beyla as a standalone process on Linux. Requires kernel 5.8+ with BTF enabled.

## Install

```bash
VERSION=2.8.4
ARCH=amd64  # or arm64
curl -L -o beyla.tar.gz \
  "https://github.com/grafana/beyla/releases/download/v${VERSION}/beyla-linux-${ARCH}-v${VERSION}.tar.gz"
tar -xzf beyla.tar.gz
chmod +x beyla
```

## Run (Prometheus export)

```bash
export BEYLA_OPEN_PORT=8080
export BEYLA_PROMETHEUS_PORT=9400
sudo -E ./beyla
```

Metrics available at <http://localhost:9400/metrics>.

## Run (OTLP export)

```bash
export BEYLA_OPEN_PORT=8080
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
sudo -E ./beyla
```

## Run with config file

```bash
sudo ./beyla --config config.yaml
```

## Notes

- Requires `sudo` or `CAP_SYS_ADMIN` + `CAP_BPF` capabilities.
- Linux kernel 5.8+ with BTF enabled (`/sys/kernel/btf/vmlinux` must exist).
- Instruments Go, Java, .NET, Node.js, Python, Ruby, Rust, C/C++ applications.
- Zero code changes required.

Official sources:
- [GitHub releases](https://github.com/grafana/beyla/releases)
- [Quickstart](https://grafana.com/docs/beyla/latest/quickstart/golang/)
