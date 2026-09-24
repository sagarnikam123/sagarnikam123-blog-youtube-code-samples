# Gatus installation guide

Config-as-code health dashboard and uptime monitor (single Go binary). Monitors HTTP, ICMP, TCP, DNS, and more, with a powerful condition DSL over status code, response time, body, certificate expiration, and other values. All monitors live in a reviewable `config.yaml`; native Prometheus metrics export.

Installation modes are organized under [`install/`](install/).

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| Binary (`go install` / build from source) | Available | [`install/binary/standalone/`](install/binary/standalone/) |
| Docker standalone | Available | [`install/docker/standalone/`](install/docker/standalone/) |
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Kubernetes standalone | Available (raw manifests) | [`install/k8s/standalone/`](install/k8s/standalone/) |
| Helm standalone | Available (official chart) | [`install/helm/standalone/`](install/helm/standalone/) |

See the [installation mode index](install/README.md) for the full matrix.

## Quick Start

```bash
docker run -d --name gatus \
  -p 8080:8080 \
  -v "$PWD/configs/config.yaml:/config/config.yaml:ro" \
  twinproduction/gatus:latest
./scripts/check-health.sh
```

A ready-to-edit sample lives at [`configs/config.yaml`](configs/config.yaml). Open <http://localhost:8080>.

## Access

| Endpoint | URL |
|:---------|:----|
| Gatus dashboard | http://localhost:8080 |
| Health endpoint | http://localhost:8080/health |
| Prometheus metrics | http://localhost:8080/metrics (when `metrics: true`) |

## Notes

- **Config-as-code:** monitors live in `config.yaml` — keep it in Git and review changes like any other infra.
- **Storage:** in-memory by default; optional SQLite or PostgreSQL for persistent history (see `configs/config.yaml`).
- **No prebuilt binary:** upstream ships Docker images only; the binary path is `go install` or build-from-source.
- Lightest of the four uptime tools — tens of MB RAM.

Official sources:
- [Gatus site](https://gatus.io/)
- [GitHub repository](https://github.com/TwiN/gatus)
- [Sample config.yaml](https://github.com/TwiN/gatus/blob/master/config.yaml)
