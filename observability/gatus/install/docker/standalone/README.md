# Gatus — Docker standalone

Run a single Gatus container. The whole configuration is a `config.yaml` bind-mounted at `/config/config.yaml`.

## Run

```bash
docker run -d --name gatus \
  -p 8080:8080 \
  -v "$PWD/config.yaml:/config/config.yaml:ro" \
  twinproduction/gatus:latest
```

A ready-to-edit sample is in [`../../../configs/config.yaml`](../../../configs/config.yaml):

```bash
docker run -d --name gatus \
  -p 8080:8080 \
  -v "$(git rev-parse --show-toplevel)/gatus/configs/config.yaml:/config/config.yaml:ro" \
  twinproduction/gatus:latest
```

Open <http://localhost:8080>.

## Notes

- Gatus listens on `:8080` inside the container.
- Config path is `/config/config.yaml` (override with the `GATUS_CONFIG_PATH` env var).
- Default storage is in-memory — history resets on restart. Add a `storage:` block (SQLite/PostgreSQL) and mount a volume for persistence.
- Pin a version tag (e.g. `twinproduction/gatus:v5.37.0`) instead of `latest` for reproducibility.
- Health endpoint: `GET /health`.

Official source: [Docker Hub — twinproduction/gatus](https://hub.docker.com/r/twinproduction/gatus) · [Configuration](https://github.com/TwiN/gatus#configuration).
