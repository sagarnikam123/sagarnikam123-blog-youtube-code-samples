# ClickStack installation guide

Installation modes for ClickStack are organized under [`install/`](install/).

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| ClickHouse-embedded binary | Available | [`install/binary/standalone/`](install/binary/standalone/) |
| Docker all-in-one | Available | [`install/docker/standalone/`](install/docker/standalone/) |
| Docker HyperDX-only | Available | [`install/docker/hyperdx-only/`](install/docker/hyperdx-only/) |
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Browser local mode | Available | [`install/browser/local-mode/`](install/browser/local-mode/) |
| Helm standalone/cluster | Available | [`install/helm/`](install/helm/) |

The Docker Compose setup is the Phase 1 benchmark deployment. Run it from its mode directory so its ClickHouse configuration mounts resolve correctly.

## Terraform configuration management

For free/self-hosted ClickStack, use the [Terraform example](terraform/self-hosted/) after ClickStack is running. It manages ClickStack dashboards with the official ClickHouse provider; it does not provision the ClickStack platform.
