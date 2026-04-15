# Fluent Bit - Docker - v5.x

## Version
- **Image**: `fluent/fluent-bit:5.0.1`
- **Docs**: https://docs.fluentbit.io/manual

## Quick Start

```bash
docker run --rm fluent/fluent-bit:5.0.1 --version
```

## Run with Config

```bash
docker run -d \
  --name fluent-bit \
  -v $(pwd)/fluent-bit.yaml:/fluent-bit/etc/fluent-bit.yaml \
  fluent/fluent-bit:5.0.1 \
  -c /fluent-bit/etc/fluent-bit.yaml
```

## Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Image Tags
- `fluent/fluent-bit:5.0.1`  — exact patch
- `fluent/fluent-bit:5.0`    — minor
- `fluent/fluent-bit:5`      — major (not recommended for prod)

## v5.x Notable Changes
- YAML config is the default and only recommended format
- Improved plugin ecosystem and performance
