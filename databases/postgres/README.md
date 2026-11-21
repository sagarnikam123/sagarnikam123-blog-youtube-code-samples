# PostgreSQL

PostgreSQL is a powerful open-source object-relational database with strong SQL standards compliance, JSONB support, and rich extensions. This directory covers PostgreSQL as a standalone data store — used as an application database and, in observability contexts, as a Grafana SQL datasource for dashboards and reporting.

## Installation modes

| Mode | Guide |
|:-----|:------|
| Homebrew (macOS) | [`install/brew/`](install/brew/) |
| Quick install (source/binary via pgenv) | [`install/binary/`](install/binary/) |
| DEB/APT (Debian/Ubuntu) | [`install/deb/`](install/deb/) |
| RPM (RHEL/CentOS) | [`install/rpm/`](install/rpm/) |
| Docker standalone | [`install/docker/`](install/docker/) |
| Docker Compose (server + Adminer + exporter) | [`install/docker-compose/`](install/docker-compose/) |
| Helm (Bitnami chart) | [`install/helm/`](install/helm/) |
| Kubernetes Operator (CloudNativePG) | [`install/operator/`](install/operator/) |

## Key facts

- Object-relational OLTP database, strong SQL standards compliance
- Native `JSONB`, full-text search, window functions, CTEs, extensions (PostGIS, pg_stat_statements, TimescaleDB)
- Widely supported as a [Grafana core datasource](https://grafana.com/docs/grafana/latest/datasources/postgres/)
- PostgreSQL License (permissive, BSD/MIT-style)
- Docker image: `postgres` (official) or `bitnami/postgresql`
- Default port: `5432`

Official site: [postgresql.org](https://www.postgresql.org/)
