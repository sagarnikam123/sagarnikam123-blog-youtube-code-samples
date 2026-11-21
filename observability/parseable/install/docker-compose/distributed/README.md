# Parseable — Docker Compose distributed

Distributed mode runs separate ingestor and querier nodes backed by object storage (S3/MinIO). This mode is required for horizontal scaling and HA.

Follow the official Docker Compose distributed guide:

- [Parseable distributed installation — Docker Compose](https://www.parseable.com/docs/self-hosted/installation/distributed/docker-compose)

Key differences from standalone:
- Requires an S3-compatible object store (MinIO for local testing).
- Multiple ingestor pods handle ingestion load.
- Querier nodes handle SQL queries independently.
- HA cluster features require Parseable Enterprise.

For Kubernetes distributed deployment, see the [Helm distributed guide](../../helm/distributed/).
