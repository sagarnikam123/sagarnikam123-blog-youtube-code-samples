# Beyla — Docker / Docker Compose

Run Beyla as a Docker container that instruments another container via eBPF. The key requirement is sharing the PID namespace with the target container.

## Docker Compose (recommended)

```bash
docker compose up -d
# Generate traffic:
curl http://localhost:8080/greeting
# Check Beyla metrics:
curl http://localhost:9400/metrics
```

The included `docker-compose.yml` starts:
- An example HTTP app on port 8080
- Beyla instrumenting it via shared PID namespace
- An OTel Collector receiving traces on port 4318

## Standalone Docker run

```bash
# Start your app first
docker run -d --name my-app -p 8080:8080 my-service:latest

# Run Beyla instrumenting the app container
docker run -d --name beyla \
  --privileged \
  --pid="container:my-app" \
  -e BEYLA_OPEN_PORT=8080 \
  -e BEYLA_PROMETHEUS_PORT=9400 \
  -p 9400:9400 \
  grafana/beyla:2.8.4
```

## Notes

- `--privileged` and `--pid="container:<target>"` are required for eBPF access.
- Linux host with kernel 5.8+ required (Docker Desktop on macOS/Windows won't work for eBPF).
- For Kubernetes, use the [Helm chart](../helm/) or [DaemonSet manifests](../k8s/).

Official guide: [Run Beyla as a Docker container](https://grafana.com/docs/beyla/latest/setup/docker/).
