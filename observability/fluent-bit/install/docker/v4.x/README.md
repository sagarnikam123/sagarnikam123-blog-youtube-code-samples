# Fluent Bit - Docker - v4.x

## Version
- **Image**: `fluent/fluent-bit:4.2.3.1`
- **Docs**: https://docs.fluentbit.io/manual/v/4.0

## Quick Start

```bash
docker run --rm fluent/fluent-bit:4.2.3.1 --version
```

## Run with Config

```bash
# Classic .conf format
docker run -d \
  --name fluent-bit \
  -v $(pwd)/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf \
  fluent/fluent-bit:4.2.3.1

# YAML format (recommended in v4.x)
docker run -d \
  --name fluent-bit \
  -v $(pwd)/fluent-bit.yaml:/fluent-bit/etc/fluent-bit.yaml \
  fluent/fluent-bit:4.2.3.1 \
  -c /fluent-bit/etc/fluent-bit.yaml
```

## Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Image Tags
- `fluent/fluent-bit:4.2.3.1`  — exact patch
- `fluent/fluent-bit:4.2`    — minor
- `fluent/fluent-bit:4`      — major (not recommended for prod)

## v4.x Notable Changes
- YAML config is now the recommended format
- Hot reload via `SIGHUP`
