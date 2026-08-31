# MySQL installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Generic binary tarball | Available | [`binary/`](binary/) | Self-contained tarball, all Linux, manual init |
| DEB/APT packages | Available | [`deb/`](deb/) | Debian, Ubuntu — systemd service |
| RPM packages | Available | [`rpm/`](rpm/) | RHEL, CentOS, Fedora, Amazon Linux — systemd service |
| Docker standalone | Available | [`docker/`](docker/) | Single-node with `docker run` |
| Docker Compose (standalone) | Available | [`docker-compose/`](docker-compose/) | Server + Adminer UI + mysqld-exporter |
| Helm (Bitnami) | Available | [`helm/`](helm/) | Standalone or replication, on Kubernetes |
| Kubernetes Operator (official) | Available | [`operator/`](operator/) | CRD-managed InnoDBCluster via Oracle operator |

Official sources:
- [Install overview](https://dev.mysql.com/doc/refman/8.4/en/installing.html)
- [Generic binary tarball](https://dev.mysql.com/doc/refman/8.4/en/binary-installation.html)
- [APT repository](https://dev.mysql.com/doc/mysql-apt-repo-quick-guide/en/)
- [Yum repository](https://dev.mysql.com/doc/mysql-yum-repo-quick-guide/en/)
- [Docker](https://dev.mysql.com/doc/refman/8.4/en/docker-mysql-getting-started.html)
- [Bitnami Helm chart](https://github.com/bitnami/charts/tree/main/bitnami/mysql)
- [MySQL Operator for Kubernetes](https://dev.mysql.com/doc/mysql-operator/en/)
