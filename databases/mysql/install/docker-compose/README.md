# MySQL — Docker Compose standalone

Single-node MySQL with two companions:

- **Adminer** — lightweight web DB client (browse/query without a local mysql client).
- **mysqld-exporter** — Prometheus metrics exporter, so the DB can be scraped and visualized in Grafana.

## Start

```bash
docker compose up -d
```

## Access

```bash
# MySQL client
docker exec -it mysql mysql -u root -p        # password: changeme

# Adminer UI
open http://localhost:8080                     # server: mysql, user: root, db: appdb

# Exporter metrics
curl -s http://localhost:9104/metrics | head
```

## Ports

| Service | Port | Purpose |
|:--------|:-----|:--------|
| mysql | 3306 | Client protocol |
| adminer | 8080 | Web DB UI |
| mysqld-exporter | 9104 | Prometheus metrics |

## Notes

- The exporter reads credentials from `MYSQLD_EXPORTER_PASSWORD` / a `.my.cnf`; here it uses the `exporter` user created by the init script.
- Point Prometheus at `mysqld-exporter:9104`, then use Grafana's Prometheus datasource — or connect Grafana's MySQL datasource straight to `mysql:3306` for SQL-based panels.
- For persistent config, mount files into `/etc/mysql/conf.d/`.

Official sources:
- [MySQL Docker](https://dev.mysql.com/doc/refman/8.4/en/docker-mysql-getting-started.html)
- [mysqld_exporter](https://github.com/prometheus/mysqld_exporter)
