# PostgreSQL installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Homebrew (macOS) | Available | [`brew/`](brew/) | Native macOS install (formula or Postgres.app) |
| Quick install (pgenv / source) | Available | [`binary/`](binary/) | Build/manage versions locally, no root repo |
| DEB/APT packages | Available | [`deb/`](deb/) | Debian, Ubuntu — PGDG repo, systemd service |
| RPM packages | Available | [`rpm/`](rpm/) | RHEL, CentOS, Fedora, Amazon Linux — PGDG repo, systemd |
| Docker standalone | Available | [`docker/`](docker/) | Single-node with `docker run` |
| Docker Compose (standalone) | Available | [`docker-compose/`](docker-compose/) | Server + Adminer UI + postgres-exporter |
| Helm (Bitnami) | Available | [`helm/`](helm/) | Standalone or read-replica, on Kubernetes |
| Kubernetes Operator (CloudNativePG) | Available | [`operator/`](operator/) | CRD-managed HA clusters with failover |

Official sources:
- [Download overview](https://www.postgresql.org/download/)
- [APT repository (PGDG)](https://www.postgresql.org/download/linux/ubuntu/)
- [Yum repository (PGDG)](https://www.postgresql.org/download/linux/redhat/)
- [Docker Official Image](https://hub.docker.com/_/postgres)
- [Bitnami PostgreSQL chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql)
- [CloudNativePG operator](https://cloudnative-pg.io/documentation/current/)
