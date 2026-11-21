# MySQL

MySQL is the world's most widely used open-source relational database. This directory covers MySQL as a standalone data store — used as an application database and, in observability contexts, as a Grafana SQL datasource for dashboards and reporting.

## Installation modes

| Mode | Guide |
|:-----|:------|
| Homebrew (macOS) | [`install/brew/`](install/brew/) |
| Quick install (generic binary tarball) | [`install/binary/`](install/binary/) |
| DEB/APT (Debian/Ubuntu) | [`install/deb/`](install/deb/) |
| RPM (RHEL/CentOS) | [`install/rpm/`](install/rpm/) |
| Docker standalone | [`install/docker/`](install/docker/) |
| Docker Compose (server + Adminer + exporter) | [`install/docker-compose/`](install/docker-compose/) |
| Helm (Bitnami chart) | [`install/helm/`](install/helm/) |
| Kubernetes Operator (official) | [`install/operator/`](install/operator/) |

## Key facts

- Row-oriented OLTP relational database
- SQL with InnoDB transactional storage engine
- Widely supported as a [Grafana core datasource](https://grafana.com/docs/grafana/latest/datasources/mysql/)
- GPLv2 license (community edition)
- Docker image: `mysql` (Oracle) or `bitnami/mysql`
- Default port: `3306`

Official site: [mysql.com](https://www.mysql.com/)
