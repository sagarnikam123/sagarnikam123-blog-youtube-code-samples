# Uptime Kuma — Docker standalone

Run a single-node Uptime Kuma instance with one `docker run` command. No external database required — metadata lives in SQLite inside the mounted volume.

## Run

```bash
docker run -d --restart=unless-stopped \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:2
```

Open <http://localhost:3001> and create the admin account on first run.

## Change port or volume

```bash
docker run -d --restart=unless-stopped \
  --name uptime-kuma \
  -p <YOUR_PORT>:3001 \
  -v <YOUR_DIR_OR_VOLUME>:/app/data \
  louislam/uptime-kuma:2
```

## Notes

- **Volume:** always map `/app/data` to a named volume or local directory. Filesystem POSIX file locks are required — do not use NFS (risk of SQLite corruption).
- **Tag:** `:2` tracks the v2 major line. Pin a specific patch (e.g. `2.x.y`) for fully reproducible deployments.
- **Update:** `docker pull louislam/uptime-kuma:2` then recreate the container; the volume persists your data.
- **Reverse proxy:** Uptime Kuma uses WebSocket — forward the `Upgrade` and `Connection` headers.

Official source: [Docker Hub — louislam/uptime-kuma](https://hub.docker.com/r/louislam/uptime-kuma) · [How to Install (wiki)](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%94%A7-How-to-Install).
