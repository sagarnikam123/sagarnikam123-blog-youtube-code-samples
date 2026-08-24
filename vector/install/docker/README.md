# Vector — Docker / Docker Compose

## Quick start

```bash
docker compose up -d
docker logs -f vector
```

## Standalone docker run

```bash
docker run -d --name vector \
  -v $(pwd)/vector.yaml:/etc/vector/vector.yaml:ro \
  -v /var/log:/var/log:ro \
  -p 8686:8686 \
  timberio/vector:0.57.X-alpine
```

## Health check

```bash
curl http://localhost:8686/health
```

## Notes

- Mount your config at `/etc/vector/vector.yaml`.
- Mount log directories you want Vector to tail.
- Port 8686 exposes the Vector API (health, metrics, GraphQL).
- Replace the default `console` sink with a real backend from the [examples](../../examples/).

Official docs: [vector.dev/docs/setup/installation/platforms/docker](https://vector.dev/docs/setup/installation/platforms/docker/).
