# ClickHouse

ClickHouse is an open-source, column-oriented OLAP database for real-time analytics. This directory covers ClickHouse as a standalone data store — used by SigNoz, Uptrace, ClickStack, Coroot, and others as their telemetry backend.

## Installation modes

| Mode | Guide |
|:-----|:------|
| Homebrew (macOS, cask) | [`install/brew/`](install/brew/) |
| Quick install (single binary) | [`install/binary/`](install/binary/) |
| DEB/APT (Debian/Ubuntu) | [`install/deb/`](install/deb/) |
| RPM (RHEL/CentOS) | [`install/rpm/`](install/rpm/) |
| Docker standalone | [`install/docker/`](install/docker/) |
| Docker Compose (server + Keeper) | [`install/docker-compose/`](install/docker-compose/) |
| Kubernetes Operator (official) | [`install/operator/`](install/operator/) |

## Key facts

- Column-oriented OLAP database
- Sub-second analytical queries on billions of rows
- Native SQL with extensions for time-series and observability
- Supports Prometheus remote write, OTLP, and 50+ integrations
- Apache 2.0 license
- Docker image: `clickhouse/clickhouse-server`

Official site: [clickhouse.com](https://clickhouse.com/)
