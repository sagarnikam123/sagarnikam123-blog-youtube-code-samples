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

## Concepts in short

| Term | What it is | Why it matters |
|:-----|:-----------|:---------------|
| **Endpoint** | One thing you watch, declared in `config.yaml` — a `url` (HTTP, `tcp://`, `icmp://`, DNS…) with an `interval`. | The core unit. Everything is config-as-code: add an endpoint = add a monitor. |
| **Condition** | A rule the result must satisfy, e.g. `[STATUS] == 200`, `[RESPONSE_TIME] < 300`, `[CERTIFICATE_EXPIRATION] > 48h`. | Gatus's strength — expressive assertions over status, latency, body, JSON path, and certs decide up/down. |
| **Group** | An optional label that buckets endpoints on the dashboard (`group: core`). | Organizes many endpoints into readable sections. |
| **Storage** | Where history lives: in-memory (default), SQLite, or PostgreSQL. | In-memory resets on restart; pick SQLite/PostgreSQL to keep history. |
| **Metrics** | Prometheus metrics at `/metrics` when `metrics: true`. | Lets Prometheus/Grafana scrape uptime and latency natively. |

Mental model: **one Go binary reads `config.yaml`, checks each endpoint, and serves the dashboard, `/health`, and `/metrics`.**

## Quick Start

```bash
docker run -d --name gatus \
  -p 8080:8080 \
  -v "$PWD/configs/config.yaml:/config/config.yaml:ro" \
  twinproduction/gatus:latest
./scripts/check-health.sh
```

A ready-to-edit sample lives at [`configs/config.yaml`](configs/config.yaml). Open <http://localhost:8080>.

## Hello-world example: your first monitor

Gatus is config-as-code, so the "first monitor" is a few lines of YAML.

```bash
# 1. Write the smallest possible config
cat > config.yaml <<'EOF'
endpoints:
  - name: hello-world
    group: core
    url: "https://example.com"
    interval: 60s
    conditions:
      - "[STATUS] == 200"
      - "[RESPONSE_TIME] < 500"
EOF

# 2. Run Gatus with that config mounted at /config/config.yaml
docker run -d --name gatus \
  -p 8080:8080 \
  -v "$PWD/config.yaml:/config/config.yaml:ro" \
  twinproduction/gatus:latest

# 3. Verify
curl -s http://localhost:8080/health          # {"status":"UP"}
```

Open <http://localhost:8080> — the `hello-world` endpoint appears under the `core` group and turns green once both conditions pass.

Add more checks by appending endpoints (TCP, DNS, ICMP, cert expiry, JSON body…). A fuller sample with each type is in [`configs/config.yaml`](configs/config.yaml). After editing, reload with `docker restart gatus`.

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
