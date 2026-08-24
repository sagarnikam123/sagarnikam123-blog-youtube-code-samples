# Highlight.io — Docker Compose development

For contributing to Highlight.io, the development deployment supports local filesystem mounts, hot reloading, and debug tooling.

## Install

```bash
git clone --recurse-submodules https://github.com/highlight/highlight
cd highlight/docker
# The dev compose file includes hot-reload flags and source mounts
docker compose up -d
```

## Notes

- Not intended for benchmarking or production use.
- Requires more disk space due to source mounts.
- See the upstream dev deployment guide for current instructions.

Official source: [Development deployment guide](https://github.com/highlight/highlight/blob/main/docs-content/getting-started/self-host/dev-deployment-guide.md).
