# Parseable — binary standalone

Parseable ships as a single Rust binary. In standalone mode it uses local disk as the backing store (no object storage required).

## Install

```bash
curl -fsSL https://logg.ing/install | bash
```

Or download a specific release:

```bash
VERSION=1.7.2
curl -L -o parseable \
  "https://github.com/parseablehq/parseable/releases/download/v${VERSION}/parseable-linux-amd64"
chmod +x parseable
```

## Run (local store)

```bash
./parseable local-store
```

Open <http://localhost:8000>. Default credentials: `admin` / `admin`.

## Run (S3 store)

```bash
./parseable s3-store \
  --p.s3-url https://s3.amazonaws.com \
  --p.s3-bucket my-parseable-data \
  --p.s3-region us-east-1 \
  --p.s3-access-key "$AWS_ACCESS_KEY_ID" \
  --p.s3-secret-key "$AWS_SECRET_ACCESS_KEY"
```

## Notes

- Single-node standalone — not HA. For distributed mode use Docker Compose or Helm.
- OTLP ingestion on port 8000: `/v1/logs`, `/v1/metrics`, `/v1/traces`.
- All data stored as Apache Parquet — open format, zero lock-in.
- Pin the binary version for reproducible deployments.

Official sources:
- [GitHub releases](https://github.com/parseablehq/parseable/releases)
- [Installation guide](https://www.parseable.com/docs/self-hosted/installation)
