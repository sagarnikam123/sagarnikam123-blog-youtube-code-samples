# Grafana — Docker standalone

Run Grafana as a single Docker container.

## Run

```bash
docker run -d --name grafana \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana-oss:13.2.0
```

Open <http://localhost:3000>. Default credentials: `admin` / `admin`.

## Environment variables

Common configuration via env vars:

```bash
docker run -d --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=secret \
  -e GF_INSTALL_PLUGINS="grafana-clock-panel,grafana-piechart-panel" \
  grafana/grafana-oss:13.2.0
```

## Notes

- Use `grafana/grafana-oss` for the open-source edition.
- Use `grafana/grafana` for the enterprise edition (free tier includes basic features).
- Pin image tag for reproducibility.
- Mount `/var/lib/grafana` for persistent storage (dashboards, plugins, SQLite DB).

Official guide: [Run Grafana Docker image](https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/).
