# ClickHouse installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Quick install (curl → binary) | Available | [`binary/`](binary/) | Single binary, no deps, all platforms |
| DEB/APT packages | Available | [`deb/`](deb/) | Debian, Ubuntu — systemd services |
| RPM packages | Available | [`rpm/`](rpm/) | RHEL, CentOS, Fedora — systemd services |
| Docker standalone | Available | [`docker/`](docker/) | Single-node with `docker run` |
| Docker Compose (cluster) | Available | [`docker-compose/`](docker-compose/) | Multi-node with ClickHouse Keeper |
| Kubernetes Operator (official) | Available | [`operator/`](operator/) | CRD-managed clusters via Helm or kubectl |

Official sources:
- [Install overview](https://clickhouse.com/docs/get-started/setup/self-managed/overview)
- [Quick install](https://clickhouse.com/docs/get-started/setup/self-managed/quick-install)
- [Docker](https://clickhouse.com/docs/get-started/setup/self-managed/docker)
- [Debian/Ubuntu](https://clickhouse.com/docs/get-started/setup/self-managed/debian-ubuntu)
- [RHEL/CentOS](https://clickhouse.com/docs/get-started/setup/self-managed/redhat)
- [Kubernetes Operator](https://clickhouse.com/docs/products/kubernetes-operator/install/helm)
