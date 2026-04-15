# Fluent Bit - Docker - v3.x

## Version
- **Image**: `fluent/fluent-bit:3.0.4`
- **Docs**: https://docs.fluentbit.io/manual/v/3.0

## Quick Start

```bash
docker run --rm fluent/fluent-bit:3.0.4 --version
```

## Run with Config

```bash
docker run -d \
  --name fluent-bit \
  -v $(pwd)/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf \
  fluent/fluent-bit:3.0.4
```

## Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Image Tags
- `fluent/fluent-bit:3.0.4`  — exact patch
- `fluent/fluent-bit:3.0`    — minor
- `fluent/fluent-bit:3`      — major (not recommended for prod)
